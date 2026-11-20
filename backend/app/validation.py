"""All checks on an uploaded file. Every problem that can be found is
reported in one go (OQ-11)."""
import math
import pathlib
from fractions import Fraction

from . import messages as msg
from . import mp4probe
from .geometry import Box
from .settings import Settings

H264 = {"avc1", "avc3"}
CODEC_NAMES = {
    "hvc1": "H.265 (HEVC)", "hev1": "H.265 (HEVC)", "mp4v": "MPEG-4 Part 2", "s263": "H.263", "h263": "H.263",
    "av01": "AV1", "vp09": "VP9", "vp08": "VP8", "jpeg": "Motion JPEG", "mjpa": "Motion JPEG", "mjpb": "Motion JPEG",
    "apch": "Apple ProRes", "apcn": "Apple ProRes", "apcs": "Apple ProRes", "apco": "Apple ProRes", "ap4h": "Apple ProRes",
}


def size_problem(size: int | None, settings: Settings):
    """OQ-2: a file of exactly the limit is accepted; one byte more is refused."""
    if size is not None and size <= settings.max_upload_bytes:
        return None
    return msg.too_large(size, settings.max_upload_bytes)


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
    if info.fragmented and track.frame_count == 0:          # AQ-5
        problems.append(msg.fragmented())
    elif track.frame_count < settings.min_frames:           # OQ-3
        problems.append(msg.too_short(track.frame_count, settings.min_frames))
    if track.width * track.height > settings.max_pixels:    # OQ-4, OQ-18
        problems.append(msg.resolution(track.width, track.height, settings.max_pixels))
    if track.width < track.height:                          # OQ-4: landscape or square (stored size, AQ-9)
        problems.append(msg.orientation(track.width, track.height))
    if track.rotation != 0:                                 # OQ-9
        problems.append(msg.rotation(track.rotation))
    if problems:
        return {}, problems, []

    variable = is_variable_frame_rate(track.runs)
    if variable:                                            # OQ-7
        warnings.append(msg.variable_frame_rate())
    return metadata(track, variable), [], warnings


def metadata(track: mp4probe.Track, variable: bool) -> dict:
    """Header values of the picture track (OQ-8): nothing is decoded."""
    listed = sum(count * ticks for count, ticks in track.runs)
    ticks = track.duration or listed                        # the track header's own duration
    seconds = Fraction(ticks, track.timescale) if track.timescale else Fraction(0)
    rate = Fraction(track.frame_count) / seconds if seconds else Fraction(0)
    return {
        "width": track.width, "height": track.height,
        "frame_count": track.frame_count,
        "duration_seconds": float(seconds),
        "fps": {"num": rate.numerator, "den": rate.denominator, "value": float(rate)},   # frames / duration: the average
        "variable_frame_rate": variable,
        "timing": {"timescale": track.timescale, "runs": [list(run) for run in track.runs]},
    }


def is_variable_frame_rate(runs: list) -> bool:
    """AQ-3. Gaps between the starts of consecutive frames, in header ticks; the last
    frame's own length is not a gap. Variable when the longest and the shortest gap
    differ by more than max(1 tick, 1 % of the median gap)."""
    gaps = [[ticks, count] for count, ticks in runs if count > 0]
    if gaps:
        gaps[-1][1] -= 1
    gaps = sorted(g for g in gaps if g[1] > 0)
    total = sum(count for _, count in gaps)
    if total < 2:
        return False
    shortest, longest = gaps[0][0], gaps[-1][0]
    return (longest - shortest) > max(1.0, 0.01 * _median(gaps, total))


def _median(sorted_gaps: list, total: int) -> float:
    def value_at(position: int) -> int:
        seen = 0
        for ticks, count in sorted_gaps:
            seen += count
            if position < seen:
                return ticks
        return sorted_gaps[-1][0]
    return (value_at((total - 1) // 2) + value_at(total // 2)) / 2


def box_problem(box: Box, width: int, height: int, settings: Settings):
    """Checks a box the operator drew (target box or lock zone). None means it is fine."""
    if not all(math.isfinite(v) for v in (box.x, box.y, box.w, box.h)):
        return msg.bad_request()
    if box.w < settings.min_box_side or box.h < settings.min_box_side:          # OQ-21
        return msg.box_too_small(box.w, box.h, settings.min_box_side)
    if box.x < 0 or box.y < 0 or box.x + box.w > width or box.y + box.h > height:   # OQ-22
        return msg.box_outside_picture(box, width, height)
    return None
