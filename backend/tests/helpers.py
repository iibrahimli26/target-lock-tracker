"""Shared test helpers. Expected values in tests come from how each fixture
was generated (see fixtures/generate_fixtures.sh), never from the app."""
import pathlib
from urllib.parse import quote

FIXTURES = pathlib.Path(__file__).parent / "fixtures"


def fx(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


def upload(client, name: str, data: bytes | None = None):
    """Upload fixture `name` (or the given bytes under that name)."""
    body = fx(name) if data is None else data
    return client.post("/api/upload", content=body, headers={"X-File-Name": quote(name)})


def codes(response) -> list[str]:
    return sorted(p["code"] for p in response.json()["problems"])


def problem(response, code: str) -> dict:
    matches = [p for p in response.json()["problems"] if p["code"] == code]
    assert len(matches) == 1, f"expected exactly one '{code}' problem, got {response.json()}"
    return matches[0]


def assert_no_video(client):
    r = client.get("/api/video")
    assert r.status_code == 404
    assert codes(r) == ["no_video"]


def marker(jpeg: bytes, x0: int = 108, row: int = 325):
    """Which frame is this picture? The reference videos carry a white rectangle whose
    left edge is at x0 + 8 * n for source frame n (see generate_fixtures.sh)."""
    import cv2
    import numpy as np
    image = cv2.imdecode(np.frombuffer(jpeg, np.uint8), cv2.IMREAD_COLOR)
    assert image is not None, "not a decodable picture"
    bright = np.where(image[row, :, 1] > 128)[0]
    return None if len(bright) == 0 else round((int(bright[0]) - x0) / 8)


def vfr_source_frame(k: int) -> int:
    """REF-V keeps source frames 0, 2, 3, 5, 6, 8, ... (those with n mod 3 != 1)."""
    return 3 * (k // 2) + (0 if k % 2 == 0 else 2)


def marker_of_picture(picture, x0: int = 108, row: int = 325):
    """Like marker(), for a decoded picture (what the tracker is given)."""
    import numpy as np
    bright = np.where(picture[row, :, 1] > 128)[0]
    return None if len(bright) == 0 else round((int(bright[0]) - x0) / 8)


class ScriptedTracker:
    """Stands in for the OpenCV tracker (the one true external dependency, AQ-16).
    For each frame of REF-A it returns whatever `script(frame_index)` says:
    a Box, or None for "the tracker reports failure". It finds the frame index
    from the picture's marker, so the script is written in absolute frame indexes."""
    def __init__(self, script, delay: float = 0.0):
        self.script, self.delay = script, delay

    def init(self, picture, box):
        pass

    def update(self, picture):
        import time
        if self.delay:
            time.sleep(self.delay)
        return self.script(marker_of_picture(picture))


def wait_for_tracking(client, base, timeout: float = 120.0) -> dict:
    import time
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        state = client.get(f"{base}/tracking").json()
        if state["run"]["state"] != "running":
            return state
        time.sleep(0.02)
    raise AssertionError("tracking did not finish in time")
