"""HTTP API of the Target-Lock Video Tracker. Also serves the built page."""
import pathlib
from urllib.parse import unquote

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import messages as msg
from .frames import FrameReader, FrameUnreadable
from .geometry import Box
from .settings import Settings
from .store import VideoStore
from .tracking import Session
from .uploads import Uploads, refused
from .validation import box_problem, validate


class BoxBody(BaseModel):
    box: tuple[float, float, float, float]      # x, y, width, height in picture pixels
    frame: int = 0                              # frame index from 0


def create_app(settings: Settings | None = None, tracker_factory=None) -> FastAPI:
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

    def session_of(video) -> Session:
        if "session" not in video.resources:
            video.resources["session"] = Session(video.path, video.metadata, settings, tracker_factory)
        return video.resources["session"]

    def checked_box(video, body: BoxBody):
        """(Box, None) when the box is acceptable, else (None, refusal)."""
        box = Box(*body.box)
        meta = video.metadata
        problem = box_problem(box, meta["width"], meta["height"], settings)
        if problem is not None:
            return None, answer(refused(422, [problem]))
        return box, None

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

    @app.put("/api/video/{video_id}/target")
    def set_target(video_id: str, body: BoxBody):
        video = store.get(video_id)
        if video is None:
            return answer(refused(404, [msg.no_video()]))
        frame_count = video.metadata["frame_count"]
        if not 0 <= body.frame < frame_count:
            return answer(refused(404, [msg.frame_out_of_range(body.frame, frame_count)]))
        box, refusal = checked_box(video, body)
        if refusal is not None:
            return refusal
        session = session_of(video)
        session.set_target(body.frame, box)
        return {"target": session.snapshot()["target"]}

    @app.put("/api/video/{video_id}/zone")
    def set_zone(video_id: str, body: BoxBody):
        video = store.get(video_id)
        if video is None:
            return answer(refused(404, [msg.no_video()]))
        box, refusal = checked_box(video, body)
        if refusal is not None:
            return refusal
        session = session_of(video)
        session.set_zone(box)
        return {"zone": session.snapshot()["zone"]}

    @app.post("/api/video/{video_id}/tracking")
    def start_tracking(video_id: str):
        """Start, restart or resume tracking at the frame of the stored target box."""
        video = store.get(video_id)
        if video is None:
            return answer(refused(404, [msg.no_video()]))
        session = session_of(video)
        if not session.start():
            return answer(refused(409, [msg.no_target()]))
        return JSONResponse(status_code=202, content=session.snapshot(since=session.frame_count))

    @app.get("/api/video/{video_id}/tracking")
    def tracking_state(video_id: str, since: int = 0, revision: int | None = None):
        video = store.get(video_id)
        if video is None:
            return answer(refused(404, [msg.no_video()]))
        return session_of(video).snapshot(since, revision)

    page = pathlib.Path(settings.frontend_dir)
    if page.is_dir():                                       # built by `npm run build` (run.py does it)
        app.mount("/", StaticFiles(directory=page, html=True), name="page")
    return app
