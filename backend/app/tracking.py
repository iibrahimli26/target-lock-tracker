"""What belongs to one loaded video besides the file: the target box, the lock
zone and the tracking results."""
import threading

from .geometry import Box


class Session:
    def __init__(self, video_path, metadata: dict, settings):
        self.path, self.metadata, self.settings = str(video_path), metadata, settings
        self.lock = threading.RLock()
        self.target: dict | None = None            # {"frame": index from 0, "box": Box}
        self.zone: Box | None = None

    def set_target(self, frame: int, box: Box) -> None:
        with self.lock:
            self.target = {"frame": frame, "box": box}

    def set_zone(self, box: Box) -> None:
        with self.lock:
            self.zone = box

    def snapshot(self) -> dict:
        with self.lock:
            target = None if self.target is None else {"frame": self.target["frame"], "box": self.target["box"].as_list()}
            return {"target": target, "zone": None if self.zone is None else self.zone.as_list()}

    def close(self) -> None:
        pass
