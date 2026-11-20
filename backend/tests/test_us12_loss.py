"""US-12 Detect that tracking is lost (AC-12.1 to AC-12.4, OQ-32).
Scripted stand-in tracker on REF-A (90 frames); indexes from 0."""
import pytest
from fastapi.testclient import TestClient

from app.geometry import Box
from app.tracking import area_changed

from .helpers import ScriptedTracker, upload, wait_for_tracking

BIG = Box(100, 100, 100, 100)                 # area 10,000, inside the zone below
ZONE = [50, 50, 400, 400]


def run(settings, script, name="ref_720p.mp4", frame=0, box=(100, 100, 100, 100), zone=None):
    from app.main import create_app
    client = TestClient(create_app(settings, tracker_factory=lambda: ScriptedTracker(script)))
    base = f"/api/video/{upload(client, name).json()['video']['id']}"
    if zone:
        client.put(f"{base}/zone", json={"box": zone})
    client.put(f"{base}/target", json={"frame": frame, "box": list(box)})
    assert client.post(f"{base}/tracking").status_code == 202
    return client, base, wait_for_tracking(client, base)


@pytest.mark.parametrize("previous,current,changed", [
    (10_000, 15_000, False),    # exactly 50 % larger: not a loss
    (10_000, 15_001, True),     # just over
    (10_000, 5_000, False),     # exactly 50 % smaller
    (10_000, 4_999, True),      # just over
    (10_000, 10_000, False),
    (10_000, 30_000, True),
])
def test_ac_12_2_area_rule_at_its_boundary(previous, current, changed):
    assert area_changed(Box(0, 0, previous / 100, 100), Box(0, 0, current / 100, 100)) is changed


def test_ac_12_1_and_12_4_tracker_failure_means_lost_and_tracking_waits(settings):
    client, base, state = run(settings, lambda i: None if i == 40 else BIG)
    r, items = state["run"], state["results"]["items"]
    assert r["state"] == "lost" and r["lost_at"] == 40 and r["lost_reason"] == "tracker_failed"
    assert "frame 41" in r["lost_message"] and "tracker reported failure" in r["lost_message"]
    assert items[:40] == [[100, 100, 100, 100]] * 40          # results before the loss are kept
    assert items[40:] == ["lost"] * 50                         # frames 41 to 90 count as LOST (AC-12.4)
    assert r["current_frame"] == 40                            # it stopped there; nothing after was processed
    assert state["analytics"]["lost"]["frames"] == 50


@pytest.mark.parametrize("width,lost", [(150, False), (150.01, True), (50, False), (49.99, True)])
def test_ac_12_2_area_change_of_more_than_half_between_two_frames_means_lost(settings, width, lost):
    changed = Box(100, 100, width, 100)                        # area 15,000 / 15,001 / 5,000 / 4,999
    client, base, state = run(settings, lambda i: BIG if i < 20 else changed)
    r = state["run"]
    if lost:
        assert r["state"] == "lost" and r["lost_at"] == 20 and r["lost_reason"] == "area_change"
        assert "more than 50 %" in r["lost_message"] and "frame 21" in r["lost_message"]
        assert state["results"]["items"][19] == [100, 100, 100, 100] and state["results"]["items"][20] == "lost"
    else:
        assert r["state"] == "completed" and r["lost_at"] is None
        assert state["results"]["items"][20] == [100, 100, width, 100]


def test_ac_12_3_a_lock_period_in_progress_ends_at_the_loss(settings):
    client, base, state = run(settings, lambda i: None if i == 40 else BIG, frame=20, zone=ZONE)
    periods = state["analytics"]["periods"]
    assert [(p["start"], p["end"]) for p in periods] == [(20, 39)]          # frames 21 to 40
    assert state["segments"] == [["not_tracked", 0, 19], ["locked", 20, 39], ["lost", 40, 89]]


def test_loss_on_the_very_next_frame_after_the_selection(settings):
    client, base, state = run(settings, lambda i: None)
    assert state["run"]["state"] == "lost" and state["run"]["lost_at"] == 1
    assert state["results"]["items"][0] == [100, 100, 100, 100] and state["results"]["items"][1:] == ["lost"] * 89


def test_oq_32_tracking_stops_at_a_frame_that_cannot_be_read(settings):
    client, base, state = run(settings, lambda i: BIG, name="damaged_720p.mp4")
    r, items = state["run"], state["results"]["items"]
    assert r["state"] == "stopped" and r["lost_reason"] == "frame_unreadable"
    stop = r["lost_at"]
    assert 10 <= stop <= 60                                    # REF-X: the first 10 frames read, the last 30 do not
    assert "damaged" in r["lost_message"] and f"frame {stop + 1}" in r["lost_message"]
    assert all(isinstance(item, list) for item in items[:stop]) and items[stop:] == ["lost"] * (90 - stop)
    assert client.get("/api/video").status_code == 200          # the application keeps running
