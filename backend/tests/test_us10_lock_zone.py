"""US-10 Define the lock zone: the backend part (AC-10.1, AC-10.4).

AC-10.2 (changing the zone after tracking) is tested with tracking results in
test_us08_tracking.py; AC-10.3 (no zone, nothing locked) in test_us11_lock_logic.py.
"""
import pytest

from .helpers import codes, problem, upload


@pytest.fixture
def ref_c(client):
    video = upload(client, "bench_720p_30s.mp4").json()["video"]
    return client, f"/api/video/{video['id']}"


def stored_zone(client, base):
    return client.get(f"{base}/tracking").json()["zone"]


def test_ac_10_1_drawing_the_zone_stores_it(ref_c):
    client, base = ref_c
    assert stored_zone(client, base) is None
    r = client.put(f"{base}/zone", json={"box": [440, 210, 400, 300]})
    assert r.status_code == 200 and r.json()["zone"] == [440, 210, 400, 300]
    assert stored_zone(client, base) == [440, 210, 400, 300]


def test_the_zone_and_the_target_are_stored_separately(ref_c):
    client, base = ref_c
    client.put(f"{base}/target", json={"frame": 0, "box": [592, 328, 96, 64]})
    client.put(f"{base}/zone", json={"box": [440, 210, 400, 300]})
    state = client.get(f"{base}/tracking").json()
    assert state["target"] == {"frame": 0, "box": [592, 328, 96, 64]} and state["zone"] == [440, 210, 400, 300]


@pytest.mark.parametrize("box,code", [
    ([440, 210, 7, 300], "box_too_small"),             # 7 pixels wide
    ([440, 210, 400, 7], "box_too_small"),
    ([900, 210, 400, 300], "box_outside_picture"),     # reaches x 1300 in a 1280-wide picture
    ([440, 500, 400, 300], "box_outside_picture"),     # reaches y 800 in a 720-high picture
])
def test_ac_10_4_a_zone_that_is_too_small_or_leaves_the_picture_is_refused(ref_c, box, code):
    client, base = ref_c
    client.put(f"{base}/zone", json={"box": [440, 210, 400, 300]})
    r = client.put(f"{base}/zone", json={"box": box})
    assert r.status_code == 422 and codes(r) == [code]
    p = problem(r, code)
    assert p["found"] and p["allowed"] and p["found"] in p["message"]
    assert stored_zone(client, base) == [440, 210, 400, 300]          # the earlier zone is kept


@pytest.mark.parametrize("box", [[440, 210, 8, 8], [0, 0, 1280, 720]])
def test_the_smallest_and_the_largest_zone_are_accepted(ref_c, box):
    client, base = ref_c
    assert client.put(f"{base}/zone", json={"box": box}).status_code == 200
    assert stored_zone(client, base) == box


def test_no_zone_without_a_video(client):
    r = client.put("/api/video/nothing/zone", json={"box": [1, 1, 20, 20]})
    assert r.status_code == 404 and codes(r) == ["no_video"]
