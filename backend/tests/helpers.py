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
