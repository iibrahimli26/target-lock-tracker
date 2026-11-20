"""Holds the one current video (OQ-10) and decides which of two overlapping
uploads wins: the one that was started last."""
import pathlib
import threading
from dataclasses import dataclass, field


@dataclass
class Video:
    id: str
    name: str
    size: int
    path: pathlib.Path
    metadata: dict = field(default_factory=dict)
    warnings: list = field(default_factory=list)
    resources: dict = field(default_factory=dict)   # frame reader, tracking session, ...

    def public(self) -> dict:
        return {"id": self.id, "name": self.name, "size": self.size,
                "metadata": self.metadata, "warnings": [w.to_json() for w in self.warnings]}

    def close(self) -> None:
        for resource in self.resources.values():
            close = getattr(resource, "close", None)
            if close:
                close()
        self.resources.clear()
        self.path.unlink(missing_ok=True)


class VideoStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._last_token = 0
        self._current: Video | None = None

    def begin_upload(self) -> int:
        """Called when an upload starts. Returns its token; higher = started later."""
        with self._lock:
            self._last_token += 1
            return self._last_token

    def commit(self, token: int, video: Video) -> bool:
        """Make `video` current, unless a later upload has started meanwhile."""
        with self._lock:
            if token != self._last_token:
                return False
            previous, self._current = self._current, video
        if previous is not None:
            previous.close()
        return True

    @property
    def current(self) -> Video | None:
        with self._lock:
            return self._current

    def get(self, video_id: str) -> Video | None:
        video = self.current
        return video if video is not None and video.id == video_id else None
