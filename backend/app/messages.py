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
