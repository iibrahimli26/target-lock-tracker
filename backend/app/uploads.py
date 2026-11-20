"""Receives an upload: streams it to disk while counting bytes, runs the
checks, and hands the result to the store."""
import pathlib
import uuid
from typing import AsyncIterator, Callable

from . import messages as msg
from .settings import Settings
from .store import Video, VideoStore

# (path, size, settings) -> (metadata, problems, warnings)
Validator = Callable[[pathlib.Path, int, Settings], tuple[dict, list, list]]


def accept_everything(path: pathlib.Path, size: int, settings: Settings):
    return {}, [], []


class Uploads:
    def __init__(self, settings: Settings, store: VideoStore, validate: Validator = accept_everything):
        self.settings, self.store, self.validate = settings, store, validate
        self.data_dir = pathlib.Path(settings.data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        for leftover in self.data_dir.glob("*.mp4"):      # AQ-10: nothing survives a restart
            leftover.unlink()

    async def receive(self, chunks: AsyncIterator[bytes], name: str, declared_size: int | None) -> tuple[int, dict]:
        """Returns (HTTP status, JSON body)."""
        token = self.store.begin_upload()
        video_id = uuid.uuid4().hex
        path = self.data_dir / f"{video_id}.mp4"          # never built from the client's file name
        size = 0
        try:
            with open(path, "wb") as out:
                async for chunk in chunks:
                    size += len(chunk)
                    out.write(chunk)
        except Exception:
            path.unlink(missing_ok=True)
            return refused(400, [msg.upload_interrupted()])

        if size == 0:
            path.unlink(missing_ok=True)
            return refused(400, [msg.no_file()])

        metadata, problems, warnings = self.validate(path, size, self.settings)
        if problems:
            path.unlink(missing_ok=True)
            return refused(422, problems)

        video = Video(id=video_id, name=name, size=size, path=path, metadata=metadata, warnings=warnings)
        if not self.store.commit(token, video):
            video.close()
            return refused(409, [msg.superseded()])
        return 201, {"video": video.public()}


def refused(status: int, problems: list) -> tuple[int, dict]:
    return status, {"problems": [p.to_json() for p in problems]}
