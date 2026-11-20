"""US-2 Refuse files that are not H.264 MP4 (AC-2.1 to AC-2.10)."""
import pytest

from .helpers import assert_no_video, codes, fx, problem, upload

PNG = bytes.fromhex("89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489") + b"\x00" * 32
PDF = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF\n"
TEXT = b"Flight notes, 20 November: battery 2 used for the second run.\n" * 4


def assert_refused(client, response, expected_codes):
    assert response.status_code == 422, response.json()
    assert codes(response) == sorted(expected_codes)
    assert_no_video(client)


def test_ac_2_1_h264_mp4_passes_type_and_codec_checks(client):
    r = upload(client, "ref_360p.mp4")
    assert r.status_code == 201
    assert "problems" not in r.json()


@pytest.mark.parametrize("name,data", [("photo.png", PNG), ("notes.txt", TEXT), ("report.pdf", PDF)])
def test_ac_2_2_non_video_file_is_refused(client, name, data):
    r = upload(client, name, data=data)
    assert_refused(client, r, ["not_mp4"])
    message = problem(r, "not_mp4")["message"]
    assert "not a valid MP4 video" in message


@pytest.mark.parametrize("name,kind", [("clip.avi", "AVI"), ("clip.mkv", "Matroska"), ("clip.webm", "WebM")])
def test_ac_2_3_other_container_is_refused(client, name, kind):
    r = upload(client, name)
    assert_refused(client, r, ["not_mp4"])
    p = problem(r, "not_mp4")
    assert "Only MP4 (H.264) files are supported" in p["message"]
    assert kind in p["found"] and p["found"] in p["message"]


@pytest.mark.parametrize("name,found", [("clip_hevc.mp4", "H.265 (HEVC)"), ("clip_mpeg4.mp4", "MPEG-4 Part 2")])
def test_ac_2_4_mp4_with_other_codec_is_refused(client, name, found):
    r = upload(client, name)
    assert_refused(client, r, ["codec"])
    p = problem(r, "codec")
    assert p["found"] == found and p["allowed"] == "H.264"
    assert "codec is not H.264" in p["message"] and found in p["message"]


def test_ac_2_5_text_file_renamed_to_mp4_is_refused(client):
    r = upload(client, "fake.mp4", data=TEXT)
    assert_refused(client, r, ["not_mp4"])
    assert "not a valid MP4 video" in problem(r, "not_mp4")["message"]


def test_ac_2_6_mp4_without_video_track_is_refused(client):
    r = upload(client, "audio_only.mp4")
    assert_refused(client, r, ["no_video_track"])
    assert "No H.264 video was found" in problem(r, "no_video_track")["message"]


@pytest.mark.parametrize("name", ["DJI_0001.MP4", "clip.m4v", "clip.mov", "clip", "clip.txt"])
def test_ac_2_7a_content_counts_not_the_file_name(client, name):
    r = upload(client, name, data=fx("ref_720p.mp4"))
    assert r.status_code == 201
    assert r.json()["video"]["name"] == name


def test_ac_2_7b_quicktime_with_h264_is_accepted(client):
    assert upload(client, "phone.mov").status_code == 201


def test_ac_2_7c_quicktime_with_other_codec_is_refused(client):
    r = upload(client, "phone_hevc.mov")
    assert_refused(client, r, ["codec"])
    assert problem(r, "codec")["found"] == "H.265 (HEVC)"


def test_ac_2_8a_full_range_8bit_420_is_accepted(client):
    assert upload(client, "h264_fullrange.mp4").status_code == 201


@pytest.mark.parametrize("name,found", [
    ("h264_10bit.mp4", "10-bit colour, 4:2:0"),
    ("h264_422.mp4", "8-bit colour, 4:2:2"),
    ("h264_444.mp4", "8-bit colour, 4:4:4"),
])
def test_ac_2_8b_colour_formats_browsers_cannot_play_are_refused(client, name, found):
    r = upload(client, name)
    assert_refused(client, r, ["colour_format"])
    p = problem(r, "colour_format")
    assert p["found"] == found and p["allowed"] == "8-bit colour, 4:2:0"
    assert "colour format is not supported" in p["message"]


@pytest.mark.parametrize("name", ["with_sound.mp4", "with_data.mp4", "with_sound_data.mp4"])
def test_ac_2_9a_sound_and_data_tracks_are_ignored(client, name):
    assert upload(client, name).status_code == 201


@pytest.mark.parametrize("name", ["two_videos.mp4", "with_preview.mp4"])
def test_ac_2_9b_more_than_one_picture_track_is_refused(client, name):
    r = upload(client, name)
    assert_refused(client, r, ["too_many_video_tracks"])
    p = problem(r, "too_many_video_tracks")
    assert p["found"] == "2" and p["allowed"] == "1"
    assert "more than one video track" in p["message"]


def test_aq_4_cover_picture_in_tags_is_not_a_track(client):
    assert upload(client, "with_cover_tag.mp4").status_code == 201


def test_ac_2_10a_3gp_with_h264_is_accepted(client):
    assert upload(client, "old_phone.3gp").status_code == 201


def test_ac_2_10b_3gp_with_h263_is_refused(client):
    r = upload(client, "old_phone_h263.3gp")
    assert_refused(client, r, ["codec"])
    p = problem(r, "codec")
    assert p["found"] == "H.263" and p["allowed"] == "H.264"
