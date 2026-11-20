"""US-1 Upload a drone video (AC-1.1 to AC-1.5)."""
import hashlib

from .helpers import assert_no_video, codes, fx, problem, upload


def test_ac_1_1_valid_h264_mp4_is_accepted(client):
    assert_no_video(client)
    r = upload(client, "ref_720p.mp4")
    assert r.status_code == 201
    body = r.json()
    assert body["video"]["name"] == "ref_720p.mp4"
    assert "problems" not in body
    current = client.get("/api/video")
    assert current.status_code == 200
    assert current.json()["video"]["id"] == body["video"]["id"]
    assert current.json()["video"]["name"] == "ref_720p.mp4"


def test_ac_1_2_stored_video_is_byte_identical(client):
    original = fx("ref_720p.mp4")
    video = upload(client, "ref_720p.mp4").json()["video"]
    assert video["size"] == len(original)
    served = client.get(f"/api/video/{video['id']}/file")
    assert served.status_code == 200
    assert len(served.content) == len(original)
    assert hashlib.sha256(served.content).hexdigest() == hashlib.sha256(original).hexdigest()


def test_ac_1_3_name_with_spaces_and_non_english_letters(client):
    name = "İHA görüntüsü 01.mp4"
    r = upload(client, name, data=fx("ref_720p.mp4"))
    assert r.status_code == 201
    assert r.json()["video"]["name"] == name
    assert client.get("/api/video").json()["video"]["name"] == name


def test_ac_1_3_name_with_path_parts_cannot_leave_the_data_folder(client, settings):
    import pathlib
    r = upload(client, "../../evil.mp4", data=fx("ref_720p.mp4"))
    assert r.status_code == 201
    assert r.json()["video"]["name"] == "../../evil.mp4"
    data_dir = pathlib.Path(settings.data_dir).resolve()
    stored = [p.resolve() for p in data_dir.rglob("*") if p.is_file()]
    assert len(stored) == 1 and data_dir in stored[0].parents
    assert not (data_dir.parent.parent / "evil.mp4").exists()


def test_ac_1_4_nothing_is_loaded_before_any_upload(client):
    assert_no_video(client)


def test_ac_1_5_upload_without_a_file_is_refused(client):
    r = client.post("/api/upload", content=b"")
    assert r.status_code == 400
    assert codes(r) == ["no_file"]
    assert "no file was provided" in problem(r, "no_file")["message"].lower()
    assert_no_video(client)
