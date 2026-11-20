"""HTTP API of the Target-Lock Video Tracker."""
from urllib.parse import unquote

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, Response

from . import messages as msg
from .frames import FrameReader, FrameUnreadable
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

    @app.exception_handler(RequestValidationError)
    async def not_understood(request: Request, exc: RequestValidationError):
        return answer(refused(422, [msg.bad_request()]))

    def frames_of(video) -> FrameReader:
        if "frames" not in video.resources:
            video.resources["frames"] = FrameReader(video.path, video.metadata["frame_count"])
        return video.resources["frames"]

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

    @app.get("/api/video/{video_id}/frames/{index}")
    def frame(video_id: str, index: int):
        """The picture of one frame, counted from 0, as a JPEG."""
        video = store.get(video_id)
        if video is None:
            return answer(refused(404, [msg.no_video()]))
        frame_count = video.metadata["frame_count"]
        if not 0 <= index < frame_count:
            return answer(refused(404, [msg.frame_out_of_range(index, frame_count)]))
        try:
            jpeg = frames_of(video).jpeg(index)
        except FrameUnreadable:                                 # OQ-8: the damage shows only now
            return answer(refused(422, [msg.frame_unreadable(index)]))
        return Response(content=jpeg, media_type="image/jpeg", headers={"Cache-Control": "no-store"})

    return app
