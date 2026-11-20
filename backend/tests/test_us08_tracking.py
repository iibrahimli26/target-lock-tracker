"""US-8 Track the target through the video (AC-8.1 to AC-8.8, AC-10.2).

Rules are tested with a scripted stand-in for the tracker on REF-A (90 frames);
AC-8.1 and AC-8.5 use the real OpenCV tracker on REF-C against the target's
known path. Frames are indexes from 0 here.
"""
import hashlib
import math
import time

import pytest
from fastapi.testclient import TestClient

from app.geometry import Box

from .helpers import ScriptedTracker, codes, fx, problem, upload, wait_for_tracking

STEADY = Box(150, 150, 50, 50)


def app_with(settings, script, delay=0.0):
    from app.main import create_app
    return create_app(settings, tracker_factory=lambda: ScriptedTracker(script, delay))


def load_ref_a(client):
    video = upload(client, "ref_720p.mp4").json()["video"]
    return f"/api/video/{video['id']}"


def start(client, base, frame=0, box=(150, 150, 50, 50)):
    assert client.put(f"{base}/target", json={"frame": frame, "box": list(box)}).status_code == 200
    r = client.post(f"{base}/tracking")
    assert r.status_code == 202, r.json()
    return r


def test_ac_8_2_tracking_starts_at_the_frame_of_the_target_box(settings):
    with TestClient(app_with(settings, lambda i: Box(150 + i, 150, 50, 50))) as client:
        base = load_ref_a(client)
        start(client, base, frame=30)
        state = wait_for_tracking(client, base)
        items = state["results"]["items"]
        assert state["run"]["state"] == "completed" and state["run"]["start_frame"] == 30
        assert len(items) == 90
        assert items[:30] == [None] * 30                               # frames before the box: not tracked
        assert items[30] == [150, 150, 50, 50]                         # the frame of the box: the box itself
        assert items[31:] == [[150 + i, 150, 50, 50] for i in range(31, 90)]   # then the tracker's answer per frame


def test_ac_8_3_progress_is_reported_while_tracking_runs(settings):
    with TestClient(app_with(settings, lambda i: STEADY, delay=0.01)) as client:
        base = load_ref_a(client)
        first = start(client, base).json()["run"]
        assert first["state"] == "running" and first["total_frames"] == 90
        seen = []
        while True:
            run = client.get(f"{base}/tracking").json()["run"]
            seen.append(run)
            if run["state"] != "running":
                break
            time.sleep(0.05)
        running = [r for r in seen if r["state"] == "running"]
        assert running and any(0 < r["processed_frames"] < 90 for r in running)
        assert [r["processed_frames"] for r in seen] == sorted(r["processed_frames"] for r in seen)   # never goes back
        assert seen[-1]["state"] == "completed" and seen[-1]["processed_frames"] == 90
        assert seen[-1]["current_frame"] == 89 and seen[-1]["processing_fps"] > 0


def test_ac_8_4_the_original_video_is_unchanged_by_tracking(settings):
    with TestClient(app_with(settings, lambda i: STEADY)) as client:
        base = load_ref_a(client)
        start(client, base)
        wait_for_tracking(client, base)
        served = client.get(f"{base}/file").content
        assert hashlib.sha256(served).hexdigest() == hashlib.sha256(fx("ref_720p.mp4")).hexdigest()


def test_ac_8_6_tracking_cannot_start_without_a_target_box(client):
    base = load_ref_a(client)
    r = client.post(f"{base}/tracking")
    assert r.status_code == 409 and codes(r) == ["no_target"]
    assert "Select a target first" in problem(r, "no_target")["message"]
    assert client.get(f"{base}/tracking").json()["run"]["state"] == "idle"


def test_ac_8_7_tracking_cannot_start_without_a_video(client):
    r = client.post("/api/video/nothing/tracking")
    assert r.status_code == 404 and codes(r) == ["no_video"]


def test_ac_8_8_replacing_the_video_discards_target_zone_and_results(settings):
    with TestClient(app_with(settings, lambda i: STEADY)) as client:
        old = load_ref_a(client)
        client.put(f"{old}/zone", json={"box": [100, 100, 200, 200]})
        start(client, old)
        wait_for_tracking(client, old)
        new = f"/api/video/{upload(client, 'ref_360p.mp4').json()['video']['id']}"
        assert client.get(f"{old}/tracking").status_code == 404
        fresh = client.get(f"{new}/tracking").json()
        assert fresh["target"] is None and fresh["zone"] is None
        assert fresh["run"]["state"] == "idle" and fresh["results"]["items"] == [None] * 50


def test_the_run_before_is_cancelled_when_tracking_starts_again(settings):
    with TestClient(app_with(settings, lambda i: Box(200, 200, 60, 60), delay=0.01)) as client:
        base = load_ref_a(client)
        first = start(client, base).json()["run"]["revision"]
        second = start(client, base, frame=10, box=(300, 300, 40, 40)).json()["run"]["revision"]
        state = wait_for_tracking(client, base)
        assert second == first + 1 and state["run"]["revision"] == second
        assert state["results"]["items"][10] == [300, 300, 40, 40]      # only the second run's result is there
        assert state["run"]["state"] == "completed" and state["run"]["start_frame"] == 10


def test_starting_on_the_last_frame_completes_at_once(settings):
    with TestClient(app_with(settings, lambda i: STEADY)) as client:
        base = load_ref_a(client)
        start(client, base, frame=89)
        state = wait_for_tracking(client, base)
        assert state["run"]["state"] == "completed"
        assert state["results"]["items"][88] is None and state["results"]["items"][89] == [150, 150, 50, 50]


def test_results_can_be_fetched_from_a_frame_onward(settings):
    with TestClient(app_with(settings, lambda i: Box(100 + i, 100, 50, 50))) as client:
        base = load_ref_a(client)
        start(client, base)
        revision = wait_for_tracking(client, base)["run"]["revision"]
        tail = client.get(f"{base}/tracking", params={"since": 80, "revision": revision}).json()["results"]
        assert tail["from"] == 80 and tail["items"] == [[100 + i, 100, 50, 50] for i in range(80, 90)]
        stale = client.get(f"{base}/tracking", params={"since": 80, "revision": revision - 1}).json()["results"]
        assert stale["from"] == 0 and len(stale["items"]) == 90        # a page with old data gets everything again


def test_ac_10_2_changing_the_zone_after_tracking_needs_no_new_run(settings):
    with TestClient(app_with(settings, lambda i: STEADY)) as client:
        base = load_ref_a(client)
        client.put(f"{base}/zone", json={"box": [100, 100, 200, 200]})       # STEADY is inside this zone
        start(client, base)
        before = wait_for_tracking(client, base)
        assert before["analytics"]["locked"]["frames"] == 90 and before["segments"] == [["locked", 0, 89]]
        client.put(f"{base}/zone", json={"box": [300, 300, 100, 100]})       # ... and outside this one
        after = client.get(f"{base}/tracking").json()
        assert after["analytics"]["locked"]["frames"] == 0 and after["analytics"]["unlocked"]["frames"] == 90
        assert after["segments"] == [["unlocked", 0, 89]]
        assert after["run"]["revision"] == before["run"]["revision"] and after["run"]["state"] == "completed"


# --- the real OpenCV tracker on REF-C ---------------------------------------
def true_target(n: int) -> Box:
    """Where the 96 x 64 target of REF-C really is in frame n (see generate_fixtures.sh)."""
    return Box(640 + 300 * math.sin(2 * math.pi * n / 450) - 48, 360 + 150 * math.sin(2 * math.pi * n / 300) - 32, 96, 64)


def overlap(a: Box, b: Box) -> float:
    width = max(0.0, min(a.x + a.w, b.x + b.w) - max(a.x, b.x))
    height = max(0.0, min(a.y + a.h, b.y + b.h) - max(a.y, b.y))
    shared = width * height
    return shared / (a.area + b.area - shared)


def test_ac_8_1_and_8_5_the_real_tracker_follows_the_target_within_the_time_limit(client):
    video = upload(client, "bench_720p_30s.mp4").json()["video"]
    base = f"/api/video/{video['id']}"
    assert client.put(f"{base}/target", json={"frame": 0, "box": [592, 328, 96, 64]}).status_code == 200
    started = time.monotonic()
    assert client.post(f"{base}/tracking").status_code == 202
    state = wait_for_tracking(client, base, timeout=180)
    elapsed = time.monotonic() - started
    assert state["run"]["state"] == "completed"
    assert elapsed < 60, f"30 s of 720p video took {elapsed:.1f} s to track; the limit is 60 s"     # AC-8.5
    items = state["results"]["items"]
    assert len(items) == 900 and all(isinstance(item, list) for item in items)        # a box on every frame
    overlaps = [overlap(Box(*item), true_target(n)) for n, item in enumerate(items)]
    assert min(overlaps) > 0.3                                                         # never off the target
    assert sum(overlaps) / len(overlaps) >= 0.5
