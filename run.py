#!/usr/bin/env python3
"""One command to run the Target-Lock Video Tracker, one to test it.

    python run.py              start the application (http://127.0.0.1:8000)
    python run.py test         run every automated test
    python run.py test --slow  also the opt-in tests with real 1 GB files

Needs Python 3.10+ and Node.js 18+ (for building the page). On the first run
it creates .venv/, installs the Python and Node packages and builds the page.
Options: --port N, --no-open (do not open the browser), --system-python (use
this interpreter instead of .venv), --no-browser-install (do not download the
test browser).
"""
import hashlib
import os
import pathlib
import shutil
import subprocess
import sys
import threading
import webbrowser

ROOT = pathlib.Path(__file__).resolve().parent
BACKEND, FRONTEND, VENV = ROOT / "backend", ROOT / "frontend", ROOT / ".venv"


def say(text: str) -> None:
    print(f"[run.py] {text}", flush=True)


def run(command: list, cwd: pathlib.Path, env: dict | None = None) -> int:
    return subprocess.call([str(part) for part in command], cwd=str(cwd), env=env)


def must(command: list, cwd: pathlib.Path, what: str) -> None:
    if run(command, cwd) != 0:
        sys.exit(f"[run.py] Stopped: {what} failed. The output above says why.")


def python_for(args: list, dev: bool) -> str:
    """The interpreter to use, with the needed packages installed."""
    if sys.version_info < (3, 10):
        sys.exit("[run.py] Python 3.10 or newer is needed.")
    if "--system-python" in args:
        return sys.executable
    python = VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not python.exists():
        say("creating .venv ...")
        must([sys.executable, "-m", "venv", VENV], ROOT, "creating the virtual environment")
    wanted = BACKEND / ("requirements-dev.txt" if dev else "requirements.txt")
    stamp = VENV / (".installed-dev" if dev else ".installed")
    digest = hashlib.sha256((BACKEND / "requirements.txt").read_bytes() + wanted.read_bytes()).hexdigest()
    if not stamp.exists() or stamp.read_text() != digest:
        say(f"installing Python packages from backend/{wanted.name} ...")
        must([python, "-m", "pip", "install", "--quiet", "--disable-pip-version-check", "-r", wanted], ROOT, "installing Python packages")
        stamp.write_text(digest)
    return str(python)


def npm() -> str:
    found = shutil.which("npm")
    if not found:
        sys.exit("[run.py] Node.js (with npm) is needed to build the page. Install Node.js 18 or newer and run again.")
    return found


def build_page() -> None:
    if not (FRONTEND / "node_modules").is_dir():
        say("installing Node packages ...")
        must([npm(), "ci" if (FRONTEND / "package-lock.json").exists() else "install", "--no-audit", "--no-fund"], FRONTEND, "installing Node packages")
    built = FRONTEND / "dist" / "index.html"
    sources = [p for p in FRONTEND.rglob("*") if p.is_file() and "node_modules" not in p.parts and "dist" not in p.parts]
    if not built.exists() or built.stat().st_mtime < max(p.stat().st_mtime for p in sources):
        say("building the page ...")
        must([npm(), "run", "build"], FRONTEND, "building the page")


def start(args: list) -> int:
    port = args[args.index("--port") + 1] if "--port" in args else "8000"
    python = python_for(args, dev=False)
    build_page()
    url = f"http://127.0.0.1:{port}"
    say(f"starting at {url}  (Ctrl+C stops it)")
    if "--no-open" not in args:
        threading.Timer(1.5, lambda: webbrowser.open(url)).start()
    try:
        return run([python, "-m", "uvicorn", "app.main:create_app", "--factory", "--host", "127.0.0.1", "--port", port], BACKEND)
    except KeyboardInterrupt:
        return 0


def test(args: list) -> int:
    python = python_for(args, dev=True)
    build_page()
    results = {}
    say("1/3 backend tests (pytest) ...")
    results["backend (pytest)"] = run([python, "-m", "pytest", "-q"] + (["-m", "slow or not slow"] if "--slow" in args else []), BACKEND)
    say("2/3 page logic tests (Vitest) ...")
    results["page logic (Vitest)"] = run([npm(), "test"], FRONTEND)
    say("3/3 browser tests (Playwright) ...")
    if "--no-browser-install" not in args and "--system-python" not in args:
        run([python, "-m", "playwright", "install", "chromium"], ROOT)      # skipped tests explain themselves if this fails
    results["browser (Playwright)"] = run([python, "-m", "pytest", "-q", "-rs"], ROOT / "e2e")
    print()
    for name, code in results.items():
        say(f"{'passed' if code == 0 else 'FAILED'}  {name}")
    return 0 if all(code == 0 for code in results.values()) else 1


if __name__ == "__main__":
    arguments = sys.argv[1:]
    sys.exit(test(arguments) if arguments[:1] == ["test"] else start(arguments))
