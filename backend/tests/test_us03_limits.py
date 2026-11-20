"""US-3 Enforce file size, resolution and duration limits (AC-3.1 to AC-3.5f)."""
import asyncio
import pathlib
import struct

import pytest
from fastapi.testclient import TestClient

from .helpers import assert_no_video, codes, fx, problem, upload

GIB = 1_073_741_824


def padded(data: bytes, total: int) -> bytes:
    """A still-valid MP4 of exactly `total` bytes: a 'free' (padding) box is appended."""
    pad = total - len(data)
    assert pad >= 8
    return data + struct.pack(">I4s", pad, b"free") + b"\x00" * (pad - 8)


def test_ac_3_1_benchmark_sized_video_is_within_all_limits(client):
    r = upload(client, "bench_720p_30s.mp4")
    assert r.status_code == 201 and "problems" not in r.json()


def test_ac_3_2_empty_file_is_refused(client):
    r = upload(client, "empty.mp4", data=b"")
    assert r.status_code == 422
    assert codes(r) == ["empty_file"]
    p = problem(r, "empty_file")
    assert "file is empty" in p["message"] and p["found"] == "0 bytes"
    assert_no_video(client)


# --- AC-3.3: size limit 1 GB = 1,073,741,824 bytes, inclusive (OQ-2) --------
def test_ac_3_3_default_limit_is_exactly_one_gib():
    from app.settings import Settings
    assert Settings().max_upload_bytes == GIB == 1024 * 1024 * 1024


@pytest.mark.parametrize("size", [GIB - 1, GIB])
def test_ac_3_3a_size_at_or_just_under_the_limit_is_allowed(size):
    from app.settings import Settings
    from app.validation import size_problem
    assert size_problem(size, Settings()) is None


def test_ac_3_3b_one_byte_over_the_limit_is_refused():
    from app.settings import Settings
    from app.validation import size_problem
    p = size_problem(GIB + 1, Settings())
    assert p.code == "too_large"
    assert p.found == "1,073,741,825 bytes" and p.allowed == "1,073,741,824 bytes (1 GB)"
    assert "larger than the maximum allowed size" in p.message


@pytest.fixture
def small_limit(tmp_path):
    """The same application with the size limit lowered, to exercise the real upload path."""
    from app.main import create_app
    from app.settings import Settings
    limit = len(fx("ref_720p.mp4")) + 1000
    settings = Settings(data_dir=str(tmp_path / "data"), max_upload_bytes=limit)
    with TestClient(create_app(settings)) as c:
        yield c, limit, pathlib.Path(settings.data_dir)


@pytest.mark.parametrize("delta", [-1, 0])
def test_ac_3_3a_upload_at_or_just_under_the_limit_is_accepted(small_limit, delta):
    client, limit, _ = small_limit
    r = upload(client, "at_limit.mp4", data=padded(fx("ref_720p.mp4"), limit + delta))
    assert r.status_code == 201
    assert r.json()["video"]["size"] == limit + delta


def test_ac_3_3b_upload_one_byte_over_the_limit_is_refused(small_limit):
    client, limit, data_dir = small_limit
    r = upload(client, "over_limit.mp4", data=padded(fx("ref_720p.mp4"), limit + 1))
    assert r.status_code == 413
    assert codes(r) == ["too_large"]
    p = problem(r, "too_large")
    assert p["found"] == f"{limit + 1:,} bytes" and p["allowed"] == f"{limit:,} bytes"
    assert_no_video(client)
    assert list(data_dir.glob("*")) == []          # nothing of the refused file is kept


def test_ac_3_3b_over_limit_is_caught_while_reading_when_no_size_is_declared(small_limit):
    client, limit, data_dir = small_limit

    async def chunks():
        body = padded(fx("ref_720p.mp4"), limit + 1)
        for i in range(0, len(body), 4096):
            yield body[i:i + 4096]

    status, body = asyncio.run(client.app.state.uploads.receive(chunks(), "stream.mp4", None))
    assert status == 413 and [p["code"] for p in body["problems"]] == ["too_large"]
    assert list(data_dir.glob("*")) == []


@pytest.mark.slow
@pytest.mark.parametrize("delta,status", [(-1, 201), (0, 201), (1, 413)])
def test_ac_3_3_real_one_gib_files(client, tmp_path, delta, status):
    """Opt-in (pytest -m slow): uploads real files of about 1 GB, created here and never committed."""
    total = GIB + delta
    base = fx("ref_720p.mp4")

    def body():
        yield base
        yield struct.pack(">I4s", total - len(base), b"free")
        left = total - len(base) - 8
        block = b"\x00" * (4 * 1024 * 1024)
        while left > 0:
            yield block[:left]
            left -= len(block)

    r = client.post("/api/upload", content=body(), headers={"X-File-Name": "big.mp4", "Content-Length": str(total)})
    assert r.status_code == status


# --- AC-3.4: no maximum duration; at least 2 frames (OQ-3) ------------------
def test_ac_3_4a_video_far_longer_than_the_benchmark_is_accepted(client):
    assert upload(client, "long_720p_10min.mp4").status_code == 201


@pytest.mark.parametrize("name", ["two_frames.mp4", "three_frames.mp4"])
def test_ac_3_4b_minimum_number_of_frames_or_one_more_is_accepted(client, name):
    assert upload(client, name).status_code == 201


def test_ac_3_4c_single_frame_video_is_refused(client):
    r = upload(client, "one_frame.mp4")
    assert r.status_code == 422 and codes(r) == ["too_short"]
    p = problem(r, "too_short")
    assert p["found"] == "1 frame" and p["allowed"] == "at least 2 frames"
    assert "too short" in p["message"]
    assert_no_video(client)


def test_aq_5_fragmented_layout_is_refused(client):
    r = upload(client, "fragmented.mp4")
    assert r.status_code == 422 and codes(r) == ["fragmented"]


# --- AC-3.5: at most 921,600 pixels, landscape or square (OQ-4, OQ-18) ------
@pytest.mark.parametrize("name", ["ref_720p.mp4", "res_1278x720.mp4", "res_1280x718.mp4", "res_722x720.mp4"])
def test_ac_3_5a_landscape_at_or_just_inside_the_limits_is_accepted(client, name):
    assert upload(client, name).status_code == 201


@pytest.mark.parametrize("name,w,h,pixels", [
    ("res_1282x720.mp4", 1282, 720, "923,040"),
    ("res_1280x722.mp4", 1280, 722, "924,160"),
    ("res_1920x1080.mp4", 1920, 1080, "2,073,600"),
    ("res_962x962.mp4", 962, 962, "925,444"),       # AC-3.5f
    ("res_1602x576.mp4", 1602, 576, "922,752"),     # AC-3.5f
])
def test_ac_3_5b_and_f_too_many_pixels_is_refused(client, name, w, h, pixels):
    r = upload(client, name)
    assert r.status_code == 422 and codes(r) == ["resolution"]
    p = problem(r, "resolution")
    assert p["found"].startswith(f"{pixels} pixels") and str(w) in p["found"] and str(h) in p["found"]
    assert p["allowed"] == "921,600 pixels"
    assert "larger than the maximum allowed" in p["message"]
    assert_no_video(client)


def test_ac_3_5c_very_small_landscape_video_is_accepted(client):
    assert upload(client, "res_32x18.mp4").status_code == 201


@pytest.mark.parametrize("name,w,h", [("res_360x640.mp4", 360, 640), ("res_718x720.mp4", 718, 720)])
def test_ac_3_5d_portrait_video_is_refused(client, name, w, h):
    r = upload(client, name)
    assert r.status_code == 422 and codes(r) == ["orientation"]
    p = problem(r, "orientation")
    assert str(w) in p["found"] and str(h) in p["found"] and "portrait" in p["found"]
    assert p["allowed"] == "landscape or square"
    assert_no_video(client)


@pytest.mark.parametrize("name", ["res_720x720.mp4", "res_960x960.mp4", "res_1440x480.mp4", "res_1600x576.mp4"])
def test_ac_3_5e_square_and_wide_within_the_pixel_maximum_is_accepted(client, name):
    assert upload(client, name).status_code == 201
