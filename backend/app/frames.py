"""Decodes single frames with OpenCV, the same decoder the tracker uses, so the
picture the operator sees for frame k is the picture the tracker gets for frame k."""
import threading
from collections import OrderedDict

import cv2


class FrameUnreadable(Exception):
    def __init__(self, index: int):
        super().__init__(f"frame {index} cannot be read")
        self.index = index


class FrameReader:
    CACHE = 96                                   # recently shown pictures, for instant stepping back

    def __init__(self, path, frame_count: int):
        self.path, self.frame_count = str(path), frame_count
        self._lock = threading.Lock()            # one decode at a time (AC-6.6)
        self._capture = None
        self._next = 0                           # index the capture will deliver next
        self._jpegs: OrderedDict[int, bytes] = OrderedDict()

    def read(self, index: int):
        """The decoded picture of frame `index` (counted from 0)."""
        with self._lock:
            return self._read(index)

    def jpeg(self, index: int) -> bytes:
        with self._lock:
            if index in self._jpegs:
                self._jpegs.move_to_end(index)
                return self._jpegs[index]
            ok, encoded = cv2.imencode(".jpg", self._read(index), [cv2.IMWRITE_JPEG_QUALITY, 90])
            if not ok:
                raise FrameUnreadable(index)
            data = encoded.tobytes()
            self._jpegs[index] = data
            if len(self._jpegs) > self.CACHE:
                self._jpegs.popitem(last=False)
            return data

    def _read(self, index: int):
        if self._capture is None:
            self._capture, self._next = cv2.VideoCapture(self.path), 0
        if index != self._next:
            self._capture.set(cv2.CAP_PROP_POS_FRAMES, index)
            if int(round(self._capture.get(cv2.CAP_PROP_POS_FRAMES))) != index:
                self._drop()
                raise FrameUnreadable(index)
        ok, frame = self._capture.read()
        if not ok or frame is None:
            self._drop()                         # the decoder's state is unknown now: start afresh next time
            raise FrameUnreadable(index)
        self._next = index + 1
        return frame

    def _drop(self) -> None:
        if self._capture is not None:
            self._capture.release()
        self._capture = None

    def close(self) -> None:
        with self._lock:
            self._drop()
            self._jpegs.clear()
