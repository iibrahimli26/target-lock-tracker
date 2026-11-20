"""HTTP API of the Target-Lock Video Tracker."""
from urllib.parse import unquote

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse

from . import messages as msg
from .settings import Settings
from .store import VideoStore
from .uploads import Uploads, refused
from .validation import validate


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    app = FastAPI(title="Target-Lock Video Tracker")
    store = VideoStore()
    uploads = Uploads(settings, store, validate)
    app.state.settings, app.state.store, app.state.uploads = settings, store, uploads

    def answer(result: tuple[int, dict]) -> JSONResponse:
        return JSONResponse(status_code=result[0], content=result[1])

    @app.exception_handler(Exception)
    async def unexpected(request: Request, exc: Exception):      # AC-5.3: never leak internals
        return answer(refused(500, [msg.internal_error()]))

    @app.post("/api/upload")
    async def upload(request: Request):
        name = unquote(request.headers.get("x-file-name", "")).strip()
        declared = request.headers.get("content-length")
        declared_size = int(declared) if declared and declared.isdigit() else None
        return answer(await uploads.receive(request.stream(), name, declared_size))

    @app.get("/api/video")
    def current_video():
        video = store.current
        if video is None:
            return answer(refused(404, [msg.no_video()]))
        return {"video": video.public()}

    @app.get("/api/video/{video_id}/file")
    def video_file(video_id: str):
        video = store.get(video_id)
        if video is None:
            return answer(refused(404, [msg.no_video()]))
        return FileResponse(video.path, media_type="video/mp4")

    return app
