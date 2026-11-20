"""US-13 Select the target again and resume (AC-13.1 to AC-13.5).
Scripted stand-in tracker on REF-A (90 frames); indexes from 0."""
from fastapi.testclient import TestClient

from app.geometry import Box

from .helpers import ScriptedTracker, codes, upload, wait_for_tracking

BIG, SMALL = Box(100, 100, 100, 100), Box(100, 100, 52.5, 40)       # areas 10,000 and 2,100
ZONE = [50, 50, 400, 400]


def lost_at_40(settings, script, zone=None, frame=0):
    from app.main import create_app
    client = TestClient(create_app(settings, tracker_factory=lambda: ScriptedTracker(script)))
    base = f"/api/video/{upload(client, 'ref_720p.mp4').json()['video']['id']}"
    if zone:
        client.put(f"{base}/zone", json={"box": zone})
    client.put(f"{base}/target", json={"frame": frame, "box": [100, 100, 100, 100]})
    client.post(f"{base}/tracking")
    state = wait_for_tracking(client, base)
    assert state["run"]["state"] == "lost" and state["run"]["lost_at"] == 40
    return client, base, state


def reselect(client, base, frame, box):
    assert client.put(f"{base}/target", json={"frame": frame, "box": box}).status_code == 200
    assert client.post(f"{base}/tracking").status_code == 202
    return wait_for_tracking(client, base)


def test_ac_13_1_tracking_resumes_from_the_frame_of_the_new_box(settings):
    script = lambda i: None if i == 40 else (BIG if i < 40 else Box(300, 300, 100, 100))
    client, base, lost = lost_at_40(settings, script)
    state = reselect(client, base, 50, [300, 300, 100, 100])
    items = state["results"]["items"]
    assert state["run"]["state"] == "completed" and state["run"]["revision"] == lost["run"]["revision"] + 1
    assert state["run"]["lost_at"] is None and state["run"]["lost_message"] is None
    assert items[:40] == [[100, 100, 100, 100]] * 40            # frames 1 to 40 keep their results
    assert items[40:50] == ["lost"] * 10                        # frames 41 to 50 stay LOST
    assert items[50:] == [[300, 300, 100, 100]] * 40            # frames 51 onward are new


def test_ac_13_2_lock_periods_before_and_after_the_loss_are_separate(settings):
    script = lambda i: None if i == 40 else BIG
    client, base, _ = lost_at_40(settings, script, zone=ZONE, frame=20)
    script_after = reselect(client, base, 50, [100, 100, 100, 100])
    periods = script_after["analytics"]["periods"]
    assert [(p["start"], p["end"]) for p in periods] == [(20, 39), (50, 89)]        # frames 21-40 and 51-90
    assert script_after["analytics"]["lock_periods"] == 2 and script_after["analytics"]["lost"]["frames"] == 10
    assert script_after["segments"] == [["not_tracked", 0, 19], ["locked", 20, 39], ["lost", 40, 49], ["locked", 50, 89]]


def test_ac_13_3_the_area_rule_starts_afresh_from_the_new_box(settings):
    script = lambda i: None if i == 40 else (BIG if i < 40 else SMALL)      # 10,000 before; 2,100 after
    client, base, _ = lost_at_40(settings, script)
    state = reselect(client, base, 50, [100, 100, 50, 40])                  # the new box has an area of 2,000
    assert state["run"]["state"] == "completed"                              # 2,000 -> 2,100 is +5 %: not a loss
    assert state["results"]["items"][51] == [100, 100, 52.5, 40]


def test_ac_13_4_selecting_on_an_earlier_frame_tracks_again_from_there(settings):
    phase = {"box": BIG}
    from app.main import create_app
    client = TestClient(create_app(settings, tracker_factory=lambda: ScriptedTracker(lambda i: phase["box"])))
    base = f"/api/video/{upload(client, 'ref_720p.mp4').json()['video']['id']}"
    client.put(f"{base}/target", json={"frame": 0, "box": [100, 100, 100, 100]})
    client.post(f"{base}/tracking")
    assert wait_for_tracking(client, base)["run"]["state"] == "completed"
    phase["box"] = Box(400, 300, 100, 100)
    state = reselect(client, base, 30, [400, 300, 100, 100])
    items = state["results"]["items"]
    assert items[:30] == [[100, 100, 100, 100]] * 30 and items[30:] == [[400, 300, 100, 100]] * 60
    assert state["run"]["start_frame"] == 30


def test_ac_13_5_a_refused_box_does_not_resume_tracking(settings):
    client, base, lost = lost_at_40(settings, lambda i: None if i == 40 else BIG)
    r = client.put(f"{base}/target", json={"frame": 50, "box": [100, 100, 7, 7]})
    assert r.status_code == 422 and codes(r) == ["box_too_small"]
    after = client.get(f"{base}/tracking").json()
    assert after["run"] == lost["run"] and after["results"] == lost["results"]       # still lost, nothing tracked
    assert after["target"] == {"frame": 0, "box": [100, 100, 100, 100]}
