"""US-7 Draw the target box: the backend part (AC-7.1, AC-7.4 to AC-7.8).

Dragging, direction, screen-to-picture scaling and clamping at the edge
(AC-7.2, AC-7.3, AC-7.7) are page logic: frontend/src/lib/geometry.test.ts.
Frames are indexes from 0 here.
"""
import pytest

from .helpers import codes, problem, upload


@pytest.fixture
def ref_c(client):
    video = upload(client, "bench_720p_30s.mp4").json()["video"]
    base = f"/api/video/{video['id']}"
    return client, base


def put_target(client, base, box, frame=0):
    return client.put(f"{base}/target", json={"frame": frame, "box": box})


def stored_target(client, base):
    return client.get(f"{base}/tracking").json()["target"]


def test_ac_7_1_drawing_a_box_stores_it_in_picture_pixels(ref_c):
    client, base = ref_c
    assert stored_target(client, base) is None
    r = put_target(client, base, [592, 328, 96, 64])
    assert r.status_code == 200
    assert r.json()["target"] == {"frame": 0, "box": [592, 328, 96, 64]}
    assert stored_target(client, base) == {"frame": 0, "box": [592, 328, 96, 64]}


def test_ac_7_4_a_new_box_replaces_the_stored_one(ref_c):
    client, base = ref_c
    put_target(client, base, [592, 328, 96, 64])
    put_target(client, base, [600.5, 330, 80, 60])
    assert stored_target(client, base) == {"frame": 0, "box": [600.5, 330, 80, 60]}


def test_ac_7_5_the_box_can_be_drawn_on_any_frame(ref_c):
    client, base = ref_c
    assert put_target(client, base, [100, 100, 50, 50], frame=300).status_code == 200
    assert stored_target(client, base)["frame"] == 300
    assert put_target(client, base, [100, 100, 50, 50], frame=899).status_code == 200     # the last frame


@pytest.mark.parametrize("frame", [-1, 900])
def test_ac_7_5_a_frame_outside_the_video_is_refused(ref_c, frame):
    client, base = ref_c
    put_target(client, base, [592, 328, 96, 64])
    r = put_target(client, base, [100, 100, 50, 50], frame=frame)
    assert r.status_code == 404 and codes(r) == ["frame_out_of_range"]
    assert stored_target(client, base) == {"frame": 0, "box": [592, 328, 96, 64]}


def test_ac_7_6_a_box_of_exactly_8_by_8_is_stored(ref_c):
    client, base = ref_c
    assert put_target(client, base, [10, 10, 8, 8]).status_code == 200
    assert stored_target(client, base)["box"] == [10, 10, 8, 8]


@pytest.mark.parametrize("w,h", [(7, 40), (40, 7), (7.99, 8), (0, 50), (-20, 50)])
def test_ac_7_6_a_box_smaller_than_8_pixels_on_a_side_is_refused(ref_c, w, h):
    client, base = ref_c
    put_target(client, base, [592, 328, 96, 64])
    r = put_target(client, base, [10, 10, w, h])
    assert r.status_code == 422 and codes(r) == ["box_too_small"]
    p = problem(r, "box_too_small")
    assert p["allowed"] == "at least 8 × 8 pixels" and f"{w:g} × {h:g}" in p["found"]
    assert stored_target(client, base) == {"frame": 0, "box": [592, 328, 96, 64]}     # the earlier box is kept


@pytest.mark.parametrize("box,ok", [
    ([1184, 656, 96, 64], True),       # touching the right and bottom edges of 1280 x 720
    ([0, 0, 1280, 720], True),         # the whole picture
    ([1185, 656, 96, 64], False),      # 1 pixel past the right edge
    ([1184, 657, 96, 64], False),      # 1 pixel past the bottom edge
    ([-1, 100, 96, 64], False),        # 1 pixel past the left edge
    ([100, -0.5, 96, 64], False),      # half a pixel past the top edge
])
def test_ac_7_7_a_box_must_lie_inside_the_picture(ref_c, box, ok):
    client, base = ref_c
    put_target(client, base, [592, 328, 96, 64])
    r = put_target(client, base, box)
    if ok:
        assert r.status_code == 200 and stored_target(client, base)["box"] == box
    else:
        assert r.status_code == 422 and codes(r) == ["box_outside_picture"]
        assert "1280 × 720" in problem(r, "box_outside_picture")["allowed"]
        assert stored_target(client, base)["box"] == [592, 328, 96, 64]


@pytest.mark.parametrize("body", [
    {"frame": 0, "box": [1, 2, 3]}, {"frame": 0, "box": "here"}, {"frame": 0}, {"frame": "first", "box": [1, 2, 30, 30]},
    {"frame": 0, "box": [1, 2, None, 30]},
])
def test_a_malformed_box_is_refused_plainly(ref_c, body):
    client, base = ref_c
    put_target(client, base, [592, 328, 96, 64])
    r = client.put(f"{base}/target", json=body)
    assert r.status_code == 422 and codes(r) == ["bad_request"]
    assert stored_target(client, base)["box"] == [592, 328, 96, 64]


def test_a_box_with_numbers_that_are_not_finite_is_refused(ref_c):
    client, base = ref_c
    r = client.put(f"{base}/target", content='{"frame": 0, "box": [1, 2, Infinity, 30]}', headers={"Content-Type": "application/json"})
    assert r.status_code == 422 and codes(r) == ["bad_request"]


def test_ac_7_8_no_box_without_a_video(client):
    r = client.put("/api/video/nothing/target", json={"frame": 0, "box": [1, 1, 20, 20]})
    assert r.status_code == 404 and codes(r) == ["no_video"]
    assert client.get("/api/video/nothing/tracking").status_code == 404
