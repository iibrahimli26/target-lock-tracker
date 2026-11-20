"""US-6 Step through the video frame by frame: the backend part.

The frame endpoint is what every step, slider move and target selection uses.
Frames are addressed by index from 0 here; the page shows index + 1 (OQ-16).
Buttons, slider and the on-screen position are tested in frontend/ and e2e/.
"""
from concurrent.futures import ThreadPoolExecutor

import pytest

from .helpers import assert_no_video, codes, marker, problem, upload, vfr_source_frame


@pytest.fixture
def ref_a(client):
    video = upload(client, "ref_720p.mp4").json()["video"]
    return lambda index: client.get(f"/api/video/{video['id']}/frames/{index}")


def test_ac_6_1_first_frame_is_available_after_upload(ref_a):
    r = ref_a(0)
    assert r.status_code == 200 and r.headers["content-type"] == "image/jpeg"
    assert marker(r.content) == 0
    import cv2
    import numpy as np
    assert cv2.imdecode(np.frombuffer(r.content, np.uint8), 1).shape[:2] == (720, 1280)


def test_ac_6_2_and_6_3_next_and_previous_frame(ref_a):
    assert marker(ref_a(0).content) == 0
    assert marker(ref_a(1).content) == 1          # step forward: the second frame
    for index in range(2, 6):
        ref_a(index)
    assert marker(ref_a(4).content) == 4          # five steps forward, one back: the fifth frame


def test_ac_6_4_every_frame_in_order_without_skips_or_repeats(ref_a):
    assert [marker(ref_a(i).content) for i in range(90)] == list(range(90))


def test_ac_6_5_forward_and_back_returns_to_exactly_the_same_frame(ref_a):
    path = list(range(39, 50)) + list(range(48, 38, -1))      # 40th frame, +10, -10
    seen = [marker(ref_a(i).content) for i in path]
    assert seen == path and seen[-1] == 39


@pytest.mark.parametrize("index", [44, 0, 89, 45, 1, 88])
def test_ac_6_9a_b_any_frame_can_be_reached_directly(ref_a, index):
    assert marker(ref_a(index).content) == index


def test_ac_6_6_many_requests_at_once_each_get_their_own_frame(ref_a):
    wanted = [(7 * i) % 90 for i in range(30)]
    with ThreadPoolExecutor(max_workers=8) as pool:
        answers = list(pool.map(lambda i: marker(ref_a(i).content), wanted))
    assert answers == wanted


def test_ac_6_7_no_frames_when_no_video_is_loaded(client):
    r = client.get("/api/video/0123456789abcdef0123456789abcdef/frames/0")
    assert r.status_code == 404 and codes(r) == ["no_video"]
    assert "No video is loaded" in problem(r, "no_video")["message"]


def test_ac_6_8_no_frames_after_a_refused_upload(client):
    assert upload(client, "notes.txt", data=b"notes\n").status_code == 422
    assert_no_video(client)
    assert client.get("/api/video/anything/frames/0").status_code == 404


def test_frames_of_a_replaced_video_are_gone(client):
    old = upload(client, "ref_720p.mp4").json()["video"]
    new = upload(client, "ref_360p.mp4").json()["video"]
    assert client.get(f"/api/video/{old['id']}/frames/0").status_code == 404
    assert marker(client.get(f"/api/video/{new['id']}/frames/49").content, x0=48, row=165) == 49


def test_ac_6_12a_every_frame_of_a_variable_frame_rate_video_in_order(client):
    video = upload(client, "vfr_720p.mp4").json()["video"]
    seen = [marker(client.get(f"/api/video/{video['id']}/frames/{k}").content) for k in range(60)]
    assert seen == [vfr_source_frame(k) for k in range(60)]


@pytest.mark.parametrize("index,ok", [(0, True), (89, True), (-1, False), (90, False), (91, False)])
def test_ac_6_11_there_is_no_frame_before_the_first_or_after_the_last(ref_a, index, ok):
    r = ref_a(index)
    if ok:
        assert r.status_code == 200 and marker(r.content) == index
    else:
        assert r.status_code == 404 and codes(r) == ["frame_out_of_range"]
        assert "frames 1 to 90" in problem(r, "frame_out_of_range")["message"]


def test_a_frame_address_that_is_not_a_number_is_refused_plainly(ref_a):
    r = ref_a("abc")
    assert r.status_code == 422 and codes(r) == ["bad_request"]
    assert "Traceback" not in r.text and "pydantic" not in r.text.lower()


# --- REF-X: header says 90 frames, but only an early part can be read -------
@pytest.fixture
def ref_x(client):
    video = upload(client, "damaged_720p.mp4").json()["video"]
    return lambda index: client.get(f"/api/video/{video['id']}/frames/{index}")


def test_ac_5_7_unreadable_frame_gives_a_warning_not_a_crash(ref_x):
    assert [marker(ref_x(i).content) for i in range(10)] == list(range(10))      # the start can be read
    first_bad = next(i for i in range(10, 90) if ref_x(i).status_code != 200)   # step forward until one cannot
    r = ref_x(first_bad)
    assert r.status_code == 422 and codes(r) == ["frame_unreadable"]
    message = problem(r, "frame_unreadable")["message"]
    assert "damaged" in message and "cannot be read" in message and f"frame {first_bad + 1}" in message
    assert marker(ref_x(first_bad - 1).content) == first_bad - 1                # stepping back still works
    assert marker(ref_x(4).content) == 4


def test_ac_6_9g_the_last_frames_of_the_damaged_file_cannot_be_read(ref_x):
    for index in (89, 75, 60):
        r = ref_x(index)
        assert r.status_code == 422 and codes(r) == ["frame_unreadable"], index
    assert marker(ref_x(0).content) == 0          # and the application keeps running
