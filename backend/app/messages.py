"""The one list of messages the application shows (Stage 1 note 11).

OQ-11: English only; each message gives the value found and the value
allowed where a check compares a value with a limit or an allowed set.
Numbers are written the English way (2,073,600) regardless of locale.
"""
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Message:
    code: str
    message: str
    found: str | None = None
    allowed: str | None = None

    def to_json(self) -> dict:
        return asdict(self)


def num(value: int) -> str:
    return f"{value:,}"


def no_file() -> Message:
    return Message("no_file", "No file was provided. Choose a video file to upload.")


def no_video() -> Message:
    return Message("no_video", "No video is loaded.")


def upload_interrupted() -> Message:
    return Message("upload_interrupted", "The upload was interrupted before it finished. Nothing was loaded.")


def superseded() -> Message:
    return Message("superseded", "A newer upload was started, so this one was discarded.")


def internal_error() -> Message:
    return Message("internal_error", "Something went wrong while handling the request. The application is still running; please try again.")


ALLOWED_FILE = "an MP4 file with H.264 video"


def not_mp4(looks_like: str | None) -> Message:
    hint = f" (it looks like {looks_like})" if looks_like else ""
    return Message("not_mp4", f"This file is not a valid MP4 video{hint}. Only MP4 (H.264) files are supported.",
                   found=looks_like, allowed=ALLOWED_FILE)


def damaged() -> Message:
    return Message("damaged", "The file is damaged or incomplete: its index is missing or cut off, so the video cannot be read.")


def no_video_track() -> Message:
    return Message("no_video_track", "No H.264 video was found in the file: it has no video track.",
                   found="no video track", allowed="1 video track with H.264 video")


def too_many_video_tracks(count: int) -> Message:
    return Message("too_many_video_tracks", f"The file has more than one video track: found {count}, allowed 1.",
                   found=str(count), allowed="1")


def codec(found: str) -> Message:
    return Message("codec", f"The video codec is not H.264: found {found}, allowed H.264.", found=found, allowed="H.264")


def colour_format(bit_depth: int, chroma: str) -> Message:
    found, allowed = f"{bit_depth}-bit colour, {chroma}", "8-bit colour, 4:2:0"
    return Message("colour_format", f"The video's colour format is not supported: found {found}, allowed {allowed}.",
                   found=found, allowed=allowed)


def empty_file() -> Message:
    return Message("empty_file", f"The file is empty: found 0 bytes, allowed {ALLOWED_FILE}.",
                   found="0 bytes", allowed=ALLOWED_FILE)


def too_large(found_bytes: int | None, limit: int) -> Message:
    found = f"{num(found_bytes)} bytes" if found_bytes is not None else f"more than {num(limit)} bytes"
    allowed = f"{num(limit)} bytes" + (" (1 GB)" if limit == 1024 ** 3 else "")
    return Message("too_large", f"The file is larger than the maximum allowed size: found {found}, allowed {allowed}.",
                   found=found, allowed=allowed)


def fragmented() -> Message:
    return Message("fragmented", "This MP4 uses a fragmented (streaming) layout: its frames are not listed in the "
                                 "main index, so it cannot be used. Save it as a regular MP4 first.",
                   found="fragmented MP4", allowed="regular MP4")


def too_short(frames: int, minimum: int) -> Message:
    found, allowed = f"{num(frames)} frame" + ("" if frames == 1 else "s"), f"at least {minimum} frames"
    return Message("too_short", f"The video is too short: found {found}, allowed {allowed}.", found=found, allowed=allowed)


def resolution(width: int, height: int, max_pixels: int) -> Message:
    found, allowed = f"{num(width * height)} pixels ({width} × {height})", f"{num(max_pixels)} pixels"
    return Message("resolution", f"The resolution is larger than the maximum allowed: found {found}, "
                                 f"allowed at most {allowed} (for example 1280 × 720).", found=found, allowed=allowed)


def orientation(width: int, height: int) -> Message:
    found, allowed = f"{width} × {height}, portrait", "landscape or square"
    return Message("orientation", f"Only landscape or square videos are supported: found {found}, allowed {allowed}.",
                   found=found, allowed=allowed)
