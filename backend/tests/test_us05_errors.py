"""US-5 Clear errors and a stable application on bad input (AC-5.1 to AC-5.8).

AC-5.7 (a frame that cannot be read) is tested with the frame endpoint in
test_us06_frames.py. The confirmation dialog of AC-5.8a/b/e is page
behaviour and is tested in frontend/src/lib/upload.test.ts and e2e/.
"""
import asyncio
import pathlib
import re

import pytest
from fastapi.testclient import TestClient

from .helpers import assert_no_video, codes, fx, problem, upload

TEXT = b"Flight notes, 20 November.\n"
BAD_FILES = [  # (name, bytes or None for a fixture, expected problem codes)
    ("photo.png", bytes.fromhex("89504e470d0a1a0a") + b"\x00" * 40, ["not_mp4"]),
    ("notes.txt", TEXT, ["not_mp4"]),
    ("clip.avi", None, ["not_mp4"]), ("clip.mkv", None, ["not_mp4"]), ("clip.webm", None, ["not_mp4"]),
    ("clip_hevc.mp4", None, ["codec"]), ("clip_mpeg4.mp4", None, ["codec"]),
    ("fake.mp4", TEXT, ["not_mp4"]), ("audio_only.mp4", None, ["no_video_track"]),
    ("empty.mp4", b"", ["empty_file"]), ("truncated.mp4", None, ["damaged"]),
]


def test_ac_5_1_valid_upload_works_straight_after_a_refused_one(client):
    refused = upload(client, "notes.txt", data=TEXT)
    assert refused.status_code == 422
    accepted = upload(client, "ref_720p.mp4")
    assert accepted.status_code == 201 and "problems" not in accepted.json()


def test_ac_5_2_cut_off_mp4_is_refused(client):
    r = upload(client, "truncated.mp4")
    assert r.status_code == 422 and codes(r) == ["damaged"]
    assert "damaged or incomplete" in problem(r, "damaged")["message"]
    assert_no_video(client)


INTERNALS = re.compile(r"Traceback|Exception|Error\b|\.py\b|File \"|/tmp/|\\\\|<class|0x[0-9a-f]{6,}")


@pytest.mark.parametrize("name,data,expected", BAD_FILES + [
    ("three_problems.mp4", None, ["resolution", "rotation", "too_short"]), ("two_videos.mp4", None, ["too_many_video_tracks"]),
    ("h264_10bit.mp4", None, ["colour_format"]), ("fragmented.mp4", None, ["fragmented"]),
])
def test_ac_5_3_messages_are_readable_and_hide_internals(client, settings, name, data, expected):
    r = upload(client, name, data=data)
    assert codes(r) == sorted(expected)
    for p in r.json()["problems"]:
        text = p["message"]
        assert text[0].isupper() and text.rstrip().endswith(".") and len(text.split()) >= 4
        assert not INTERNALS.search(text), text
        assert settings.data_dir not in text


def test_ac_5_3_unexpected_failure_gives_a_plain_message_and_the_app_keeps_running(settings, monkeypatch):
    from app import main

    def explode(path, size, settings):
        raise RuntimeError("secret internal detail at /srv/app/validation.py")

    monkeypatch.setattr(main, "validate", explode)
    with TestClient(main.create_app(settings), raise_server_exceptions=False) as c:
        r = upload(c, "ref_720p.mp4")
        assert r.status_code == 500 and codes(r) == ["internal_error"]
        text = problem(r, "internal_error")["message"]
        assert "secret" not in text and not INTERNALS.search(text)
        assert c.get("/api/video").status_code == 404          # still answering
        assert list(pathlib.Path(settings.data_dir).glob("*")) == []   # nothing left behind


def test_ac_5_4_interrupted_upload_leaves_nothing_half_loaded(client, settings):
    async def broken():
        yield fx("bench_720p_30s.mp4")[:50_000]
        raise ConnectionError("client went away")

    status, body = asyncio.run(client.app.state.uploads.receive(broken(), "bench.mp4", None))
    assert status == 400 and [p["code"] for p in body["problems"]] == ["upload_interrupted"]
    assert_no_video(client)
    assert list(pathlib.Path(settings.data_dir).glob("*")) == []
    assert upload(client, "ref_720p.mp4").status_code == 201


def test_ac_5_5_application_survives_a_series_of_bad_files(client):
    for name, data, expected in BAD_FILES:
        r = upload(client, name, data=data)
        assert r.status_code == 422 and codes(r) == expected, name
        assert all(p["message"] for p in r.json()["problems"])
    assert upload(client, "ref_720p.mp4").status_code == 201


def test_ac_5_6a_file_with_several_problems_gets_one_message_per_problem(client):
    r = upload(client, "three_problems.mp4")       # 1920 x 1080, 1 frame, 180-degree rotation note
    assert r.status_code == 422
    assert codes(r) == ["resolution", "rotation", "too_short"]      # these three and no other
    assert problem(r, "resolution")["found"] == "2,073,600 pixels (1920 × 1080)"
    assert problem(r, "resolution")["allowed"] == "921,600 pixels"
    assert (problem(r, "too_short")["found"], problem(r, "too_short")["allowed"]) == ("1 frame", "at least 2 frames")
    assert problem(r, "rotation")["found"] == "rotation of 180 degrees"
    assert_no_video(client)


@pytest.mark.parametrize("name,code,found,allowed", [
    ("clip_hevc.mp4", "codec", "H.265 (HEVC)", "H.264"),
    ("h264_10bit.mp4", "colour_format", "10-bit colour, 4:2:0", "8-bit colour, 4:2:0"),
    ("res_1920x1080.mp4", "resolution", "2,073,600 pixels (1920 × 1080)", "921,600 pixels"),
    ("res_360x640.mp4", "orientation", "360 × 640, portrait", "landscape or square"),
    ("one_frame.mp4", "too_short", "1 frame", "at least 2 frames"),
    ("rot_90.mp4", "rotation", "rotation of 90 degrees", "no rotation"),
])
def test_ac_5_6b_each_message_gives_the_value_found_and_the_value_allowed(client, name, code, found, allowed):
    p = problem(upload(client, name), code)
    assert (p["found"], p["allowed"]) == (found, allowed)
    assert found in p["message"] and allowed in p["message"]


def test_ac_5_6b_size_message_gives_found_and_allowed():
    from app.settings import Settings
    from app.validation import size_problem
    p = size_problem(1_073_741_825, Settings())
    assert p.found in p.message and p.allowed in p.message


def test_ac_5_6c_messages_are_english_whatever_language_the_browser_asks_for(client):
    body = fx("res_1920x1080.mp4")
    english = client.post("/api/upload", content=body, headers={"X-File-Name": "a.mp4", "Accept-Language": "en-US"})
    turkish = client.post("/api/upload", content=body, headers={"X-File-Name": "a.mp4", "Accept-Language": "tr-TR,tr;q=0.9"})
    assert turkish.json() == english.json()
    assert "2,073,600" in problem(turkish, "resolution")["message"]     # not 2.073.600


def test_ac_5_8a_a_second_valid_upload_replaces_the_first(client, settings):
    first = upload(client, "ref_720p.mp4").json()["video"]
    second = upload(client, "ref_360p.mp4").json()["video"]
    current = client.get("/api/video").json()["video"]
    assert current["id"] == second["id"] != first["id"]
    assert (current["metadata"]["width"], current["metadata"]["frame_count"]) == (640, 50)
    assert client.get(f"/api/video/{first['id']}/file").status_code == 404
    assert len(list(pathlib.Path(settings.data_dir).glob("*"))) == 1    # the old file is gone


def test_ac_5_8c_a_refused_new_file_leaves_the_loaded_video_in_place(client):
    loaded = upload(client, "ref_720p.mp4").json()["video"]
    assert upload(client, "notes.txt", data=TEXT).status_code == 422
    current = client.get("/api/video").json()["video"]
    assert current == loaded
    assert client.get(f"/api/video/{loaded['id']}/file").content == fx("ref_720p.mp4")


@pytest.mark.parametrize("first_finishes_first", [True, False])
def test_ac_5_8d_of_two_overlapping_uploads_the_one_started_last_wins(client, settings, first_finishes_first):
    uploads = client.app.state.uploads

    async def scenario():
        release = {"C": asyncio.Event(), "B": asyncio.Event()}
        started = {"C": asyncio.Event(), "B": asyncio.Event()}

        async def body(key, name):
            data = fx(name)
            yield data[:1000]
            started[key].set()
            await release[key].wait()
            yield data[1000:]

        task_c = asyncio.create_task(uploads.receive(body("C", "bench_720p_30s.mp4"), "bench_720p_30s.mp4", None))
        await started["C"].wait()                       # REF-C is in progress ...
        task_b = asyncio.create_task(uploads.receive(body("B", "ref_360p.mp4"), "ref_360p.mp4", None))
        await started["B"].wait()                       # ... when REF-B is started
        for key in (("C", "B") if first_finishes_first else ("B", "C")):
            release[key].set()
            await (task_c if key == "C" else task_b)
        return task_c.result(), task_b.result()

    (status_c, body_c), (status_b, body_b) = asyncio.run(scenario())
    assert status_b == 201
    assert status_c == 409 and [p["code"] for p in body_c["problems"]] == ["superseded"]
    current = client.get("/api/video").json()["video"]
    assert current["name"] == "ref_360p.mp4" and current["metadata"]["width"] == 640
    assert len(list(pathlib.Path(settings.data_dir).glob("*"))) == 1    # nothing of REF-C is kept
