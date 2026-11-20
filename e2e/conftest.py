"""End-to-end tests: a real browser (Chromium, through Playwright) against the
real application. Skipped as a whole when Playwright or its browser is missing."""
import pathlib
import socket
import sys
import threading
import time

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "backend" / "tests" / "fixtures"
sys.path.insert(0, str(ROOT / "backend"))

playwright_api = pytest.importorskip("playwright.sync_api", reason="Playwright is not installed")


def _serve(tmp_path_factory, tracker_factory=None):
    import uvicorn
    from app.main import create_app
    from app.settings import Settings
    settings = Settings(data_dir=str(tmp_path_factory.mktemp("data")))
    if not pathlib.Path(settings.frontend_dir).is_dir():
        pytest.skip("the page is not built: run `npm run build` in frontend/ (python run.py test does it)")
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(create_app(settings, tracker_factory), host="127.0.0.1", port=port, log_level="warning"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + 15
    while not server.started and time.monotonic() < deadline:
        time.sleep(0.05)
    return server, thread, f"http://127.0.0.1:{port}"


@pytest.fixture(scope="session")
def browser():
    with playwright_api.sync_playwright() as p:
        try:
            chromium = p.chromium.launch()
        except Exception as problem:                      # browser not downloaded
            pytest.skip(f"Chromium for Playwright is not available: {str(problem).splitlines()[0]}")
        yield chromium
        chromium.close()


@pytest.fixture
def app_url(tmp_path_factory):
    """The application with the real OpenCV tracker."""
    server, thread, url = _serve(tmp_path_factory)
    yield url
    server.should_exit = True
    thread.join(timeout=10)


@pytest.fixture
def scripted_url(tmp_path_factory):
    """The application with a stand-in tracker that loses the target on frame 41 of REF-A."""
    sys.path.insert(0, str(ROOT / "backend" / "tests"))
    from app.geometry import Box
    from helpers import ScriptedTracker
    script = lambda i: None if i == 40 else Box(100 + 8 * i, 292, 96, 66)
    server, thread, url = _serve(tmp_path_factory, lambda: ScriptedTracker(script))
    yield url
    server.should_exit = True
    thread.join(timeout=10)


@pytest.fixture
def slow_url(tmp_path_factory):
    """A stand-in tracker that takes 40 ms per frame of REF-A and never loses the target."""
    sys.path.insert(0, str(ROOT / "backend" / "tests"))
    from app.geometry import Box
    from helpers import ScriptedTracker
    script = lambda i: Box(100 + 8 * i, 292, 96, 66)
    server, thread, url = _serve(tmp_path_factory, lambda: ScriptedTracker(script, delay=0.04))
    yield url
    server.should_exit = True
    thread.join(timeout=10)


@pytest.fixture
def new_page(browser):
    opened = []

    def open_page(url: str, locale: str = "en-US", init_script: str | None = None):
        context = browser.new_context(locale=locale, viewport={"width": 1440, "height": 900})
        page = context.new_page()
        if init_script:
            page.add_init_script(init_script)
        page.set_default_timeout(15_000)
        page.goto(url)
        opened.append(context)
        return page

    yield open_page
    for context in opened:
        context.close()


def upload(page, name: str, data: bytes | None = None):
    payload = {"name": name, "mimeType": "application/octet-stream", "buffer": data if data is not None else (FIXTURES / name).read_bytes()}
    page.get_by_test_id("upload-input").set_input_files(payload)


def shown_frame(page) -> int | None:
    """Which frame is the picture on screen? Reads the marker of the reference videos (frame index from 0)."""
    return page.evaluate("""async () => {
        const img = document.querySelector('[data-testid="frame-image"]');
        if (!img) return null;
        await img.decode();
        const c = document.createElement('canvas'); c.width = img.naturalWidth; c.height = img.naturalHeight;
        const g = c.getContext('2d'); g.drawImage(img, 0, 0);
        const row = g.getImageData(0, 325, c.width, 1).data;
        for (let x = 0; x < c.width; x++) if (row[4 * x + 1] > 128) return Math.round((x - 108) / 8);
        return null;
    }""")


def drag_on_picture(page, start, end, picture_width=1280):
    """Drag with the mouse between two points given in picture pixels."""
    box = page.get_by_test_id("overlay").bounding_box()
    scale = box["width"] / picture_width
    to_screen = lambda point: (box["x"] + point[0] * scale, box["y"] + point[1] * scale)
    page.mouse.move(*to_screen(start))
    page.mouse.down()
    page.mouse.move(*to_screen(((start[0] + end[0]) / 2, (start[1] + end[1]) / 2)))
    page.mouse.move(*to_screen(end))
    page.mouse.up()
