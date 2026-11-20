"""US-4 See the video's metadata after upload (AC-4.1 to AC-4.7c, AC-2.9a).

Expected numbers come from how each fixture was generated. How the numbers
are written on screen (AC-4.7a, AC-4.7b) is tested with the page's format
functions in frontend/src/lib/format.test.ts.
"""
from fractions import Fraction

import pytest

from .helpers import assert_no_video, codes, problem, upload


def metadata_of(client, name):
    r = upload(client, name)
    assert r.status_code == 201, r.json()
    return r.json()["video"]["metadata"], r.json()["video"]["warnings"]


def fps(meta) -> Fraction:
    return Fraction(meta["fps"]["num"], meta["fps"]["den"])


@pytest.mark.parametrize("name,width,height,rate,frames,seconds", [
    ("ref_720p.mp4", 1280, 720, Fraction(30), 90, 3.0),                 # AC-4.1
    ("ref_360p.mp4", 640, 360, Fraction(25), 50, 2.0),                  # AC-4.2: values follow the file
    ("long_720p_10min.mp4", 1280, 720, Fraction(30), 18_000, 600.0),    # REF-D
    ("ntsc_720p.mp4", 1280, 720, Fraction(30000, 1001), 90, 3.003),     # AC-4.7c
])
def test_ac_4_1_4_2_4_7c_metadata_follows_the_file(client, name, width, height, rate, frames, seconds):
    meta, warnings = metadata_of(client, name)
    assert (meta["width"], meta["height"]) == (width, height)
    assert fps(meta) == rate and meta["fps"]["value"] == pytest.approx(float(rate))
    assert meta["frame_count"] == frames
    assert meta["duration_seconds"] == pytest.approx(seconds, abs=1e-9)
    assert meta["variable_frame_rate"] is False and warnings == []      # AC-4.4b


def test_ac_4_3_no_metadata_for_a_refused_file(client):
    r = upload(client, "notes.txt", data=b"just some notes\n")
    assert r.status_code == 422
    assert "video" not in r.json() and "metadata" not in r.json()
    assert_no_video(client)


def test_ac_4_4a_variable_frame_rate_is_accepted_with_average_fps_and_a_warning(client):
    meta, warnings = metadata_of(client, "vfr_720p.mp4")
    assert fps(meta) == Fraction(20) and meta["frame_count"] == 60
    assert meta["duration_seconds"] == pytest.approx(3.0, abs=1e-9)
    assert meta["variable_frame_rate"] is True
    assert [w["code"] for w in warnings] == ["variable_frame_rate"]
    assert "variable frame rate" in warnings[0]["message"] and "approximate" in warnings[0]["message"]


@pytest.mark.parametrize("gaps,variable", [
    ([512] * 89, False),                    # perfectly constant
    ([33, 34, 33, 33, 34], False),          # 1 tick of rounding: constant
    ([33, 35, 33], True),                   # 2 ticks apart, more than 1 % of 33
    ([1000] * 5 + [1010], False),           # exactly 1 % of the median: constant
    ([1000] * 5 + [1011], True),            # just over 1 %
    ([3003, 3033], False),                  # 30 ticks < 1 % of 3018
    ([3003, 3034], True),                   # 31 ticks > 1 % of 3018.5
    ([1024, 512] * 29 + [1024], True),      # REF-V
    ([512], False), ([], False),            # one gap or none: nothing to compare
])
def test_aq_3_variable_frame_rate_predicate(gaps, variable):
    from app.validation import is_variable_frame_rate
    runs = [(1, g) for g in gaps] + [(1, 512)]      # the last frame's own length is ignored
    assert is_variable_frame_rate(runs) is variable


def test_ac_4_5_damaged_file_shows_the_headers_numbers(client):
    meta, _ = metadata_of(client, "damaged_720p.mp4")
    assert meta["frame_count"] == 90 and meta["duration_seconds"] == pytest.approx(3.0)


@pytest.mark.parametrize("angle", [90, 180, 270])
def test_ac_4_6_video_with_a_rotation_note_is_refused(client, angle):
    r = upload(client, f"rot_{angle}.mp4")
    assert r.status_code == 422 and codes(r) == ["rotation"]
    p = problem(r, "rotation")
    assert p["found"] == f"rotation of {angle} degrees" and p["allowed"] == "no rotation"
    assert "Rotated videos are not supported" in p["message"]
    assert_no_video(client)


@pytest.mark.parametrize("name", ["with_sound.mp4", "with_data.mp4", "with_sound_data.mp4"])
def test_ac_2_9a_metadata_is_that_of_the_picture_track(client, name):
    meta, _ = metadata_of(client, name)             # the sound track lasts 4.0 s; the picture 3.0 s
    assert (meta["width"], meta["height"], meta["frame_count"]) == (1280, 720, 90)
    assert fps(meta) == Fraction(30) and meta["duration_seconds"] == pytest.approx(3.0, abs=1e-9)


def test_timing_runs_cover_every_frame(client):
    meta, _ = metadata_of(client, "vfr_720p.mp4")
    assert sum(count for count, _ in meta["timing"]["runs"]) == meta["frame_count"] == 60
    assert meta["timing"]["timescale"] == 15360
