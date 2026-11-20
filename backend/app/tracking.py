"""What belongs to one loaded video besides the file: the target box, the lock
zone, and the tracking run with its per-frame results."""
import threading
import time
from fractions import Fraction

import cv2

from . import messages as msg
from .geometry import Box
from .lock_logic import LOST_RESULT, analytics, segments, statuses


def area_changed(previous: Box, current: Box, limit: float = 0.5) -> bool:
    """Feature 5: True when the box area changed by MORE than `limit` (50 %) of the
    previous frame's area. Exactly 50 % is not a loss (OQ-28)."""
    return abs(current.area - previous.area) > limit * previous.area


class OpenCvTracker:
    """Thin wrapper so the rest of the code only sees Box in, Box (or None = failure) out."""
    FACTORIES = {"CSRT": "TrackerCSRT_create", "KCF": "TrackerKCF_create", "MIL": "TrackerMIL_create"}

    def __init__(self, name: str = "CSRT"):
        factory = self.FACTORIES[name]
        create = getattr(cv2, factory, None) or getattr(cv2.legacy, factory)
        self._tracker = create()

    def init(self, picture, box: Box) -> None:
        self._tracker.init(picture, tuple(int(round(v)) for v in (box.x, box.y, box.w, box.h)))

    def update(self, picture) -> Box | None:
        ok, (x, y, w, h) = self._tracker.update(picture)
        if not ok or w <= 0 or h <= 0:               # AQ-17: an empty box is a failure
            return None
        return Box(float(x), float(y), float(w), float(h))


class Session:
    def __init__(self, video_path, metadata: dict, settings, tracker_factory=None):
        self.path, self.metadata, self.settings = str(video_path), metadata, settings
        self.tracker_factory = tracker_factory or (lambda: OpenCvTracker(settings.tracker))
        self.frame_count = metadata["frame_count"]
        self.fps = Fraction(metadata["fps"]["num"], metadata["fps"]["den"])
        self.lock = threading.RLock()
        self.target: dict | None = None            # {"frame": index from 0, "box": Box}
        self.zone: Box | None = None
        self.results: list = [None] * self.frame_count      # per frame: None | LOST_RESULT | Box
        self.run = {"state": "idle", "revision": 0, "start_frame": None, "current_frame": None,
                    "processed_frames": 0, "total_frames": self.frame_count, "processing_fps": 0.0,
                    "lost_at": None, "lost_reason": None, "lost_message": None}
        self._thread: threading.Thread | None = None
        self._cancel = threading.Event()

    # --- what the operator sets ---------------------------------------------
    def set_target(self, frame: int, box: Box) -> None:
        with self.lock:
            self.target = {"frame": frame, "box": box}

    def set_zone(self, box: Box) -> None:
        with self.lock:
            self.zone = box

    # --- the tracking run ---------------------------------------------------
    def start(self) -> bool:
        """(Re)start tracking at the frame of the target box. Results before that frame
        are kept; from it on they are replaced (OQ-29). False if there is no target."""
        self._stop_run()
        with self.lock:
            if self.target is None:
                return False
            frame, box = self.target["frame"], self.target["box"]
            self.results[frame:] = [None] * (self.frame_count - frame)
            self.run.update(state="running", revision=self.run["revision"] + 1, start_frame=frame,
                            current_frame=frame, processed_frames=0, processing_fps=0.0,
                            lost_at=None, lost_reason=None, lost_message=None)
            self._cancel = threading.Event()
            self._thread = threading.Thread(target=self._track, args=(frame, box, self._cancel), daemon=True)
            self._thread.start()
        return True

    def _track(self, start: int, box: Box, cancel: threading.Event) -> None:
        capture = cv2.VideoCapture(self.path)        # read-only: the uploaded file is never written (AC-8.4)
        try:
            if start:
                capture.set(cv2.CAP_PROP_POS_FRAMES, start)
            ok, picture = capture.read()
            if not ok:
                return self._lose(cancel, start, "frame_unreadable")
            tracker = self.tracker_factory()
            tracker.init(picture, box)
            began = time.monotonic()
            self._record(cancel, start, box, 1, began)
            previous = box                           # the area rule starts afresh from the selected box
            for index in range(start + 1, self.frame_count):
                if cancel.is_set():
                    return
                ok, picture = capture.read()
                if not ok:                           # OQ-32: damaged file
                    return self._lose(cancel, index, "frame_unreadable")
                found = tracker.update(picture)
                if found is None:
                    return self._lose(cancel, index, "tracker_failed")
                if area_changed(previous, found, self.settings.area_change_limit):
                    return self._lose(cancel, index, "area_change")
                self._record(cancel, index, found, index - start + 1, began)
                previous = found
            self._finish(cancel, "completed")
        finally:
            capture.release()

    def _record(self, cancel, index: int, result, done: int, began: float) -> None:
        with self.lock:
            if cancel.is_set():
                return
            self.results[index] = result
            elapsed = max(time.monotonic() - began, 1e-6)
            self.run.update(current_frame=index, processed_frames=done, processing_fps=round(done / elapsed, 1))

    def _lose(self, cancel, index: int, reason: str) -> None:
        """Tracking stops at `index` and waits for a new target box. That frame and all
        frames after it count as LOST until then (OQ-27)."""
        with self.lock:
            if cancel.is_set():
                return
            self.results[index:] = [LOST_RESULT] * (self.frame_count - index)
            self.run.update(state="stopped" if reason == "frame_unreadable" else "lost", current_frame=index,
                            lost_at=index, lost_reason=reason, lost_message=msg.tracking_lost(reason, index).message)

    def _finish(self, cancel, state: str) -> None:
        with self.lock:
            if not cancel.is_set():
                self.run["state"] = state

    def _stop_run(self) -> None:
        thread = self._thread
        if thread is not None and thread.is_alive():
            self._cancel.set()
            thread.join(timeout=30)
        self._thread = None

    # --- what the page reads ------------------------------------------------
    def snapshot(self, since: int = 0, revision: int | None = None) -> dict:
        with self.lock:
            if revision != self.run["revision"]:
                since = 0                           # the page's data is from an older run: send everything
            since = max(0, min(since, self.frame_count))
            frame_statuses = statuses(self.results, self.zone)
            target = None if self.target is None else {"frame": self.target["frame"], "box": self.target["box"].as_list()}
            return {
                "target": target,
                "zone": None if self.zone is None else self.zone.as_list(),
                "run": dict(self.run),
                "results": {"from": since, "items": [_json(r) for r in self.results[since:]]},
                "analytics": analytics(frame_statuses, self.fps),
                "segments": segments(frame_statuses),
            }

    def close(self) -> None:
        self._stop_run()


def _json(result):
    return result.as_list() if isinstance(result, Box) else result
