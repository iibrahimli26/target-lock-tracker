"""All checks on an uploaded file. Every problem that can be found is
reported in one go (OQ-11)."""
import pathlib

from . import messages as msg
from . import mp4probe
from .settings import Settings

H264 = {"avc1", "avc3"}
CODEC_NAMES = {
    "hvc1": "H.265 (HEVC)", "hev1": "H.265 (HEVC)", "mp4v": "MPEG-4 Part 2", "s263": "H.263", "h263": "H.263",
    "av01": "AV1", "vp09": "VP9", "vp08": "VP8", "jpeg": "Motion JPEG", "mjpa": "Motion JPEG", "mjpb": "Motion JPEG",
    "apch": "Apple ProRes", "apcn": "Apple ProRes", "apcs": "Apple ProRes", "apco": "Apple ProRes", "ap4h": "Apple ProRes",
}


def validate(path: pathlib.Path, size: int, settings: Settings) -> tuple[dict, list, list]:
    """Returns (metadata, problems, warnings). Any problem means the file is refused."""
    try:
        info = mp4probe.read(path)
    except mp4probe.NotMp4 as not_mp4:
        return {}, [msg.not_mp4(not_mp4.looks_like)], []
    except (mp4probe.Damaged, OSError, ValueError, IndexError):
        return {}, [msg.damaged()], []

    pictures = info.video_tracks
    if not pictures:
        return {}, [msg.no_video_track()], []

    problems, warnings = [], []
    if len(pictures) > 1:                                   # OQ-12
        problems.append(msg.too_many_video_tracks(len(pictures)))
    track = pictures[0]
    if track.codec not in H264:
        problems.append(msg.codec(CODEC_NAMES.get(track.codec, f"'{track.codec.strip()}'")))
    elif (track.bit_depth, track.chroma) != (8, "4:2:0"):   # OQ-6
        problems.append(msg.colour_format(track.bit_depth or 0, track.chroma or "unknown"))
    return {}, problems, warnings
