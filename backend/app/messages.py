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
