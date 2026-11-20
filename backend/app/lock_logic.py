"""Lock status, lock periods and analytics. Pure functions: boxes and a zone
in, numbers out. Nothing here knows about videos or trackers, which is what
lets the task's "generated box sequences with known answers" test it."""
from .geometry import Box, inside

LOCKED, UNLOCKED, LOST, NOT_TRACKED = "locked", "unlocked", "lost", "not_tracked"
LOST_RESULT = "lost"            # a frame's result is None (not tracked), LOST_RESULT, or a Box


def status_of(result, zone: Box | None) -> str:
    if result is None:
        return NOT_TRACKED
    if result == LOST_RESULT:
        return LOST
    return LOCKED if zone is not None and inside(result, zone) else UNLOCKED


def statuses(results: list, zone: Box | None) -> list:
    return [status_of(result, zone) for result in results]


def lock_periods(frame_statuses: list, fps) -> list:
    """Every continuous run of LOCKED frames. `start` and `end` are frame indexes
    from 0, both inclusive; a period of n frames lasts n / fps seconds (OQ-25)."""
    periods, start = [], None
    for index, status in enumerate(frame_statuses):
        if status == LOCKED and start is None:
            start = index
        elif status != LOCKED and start is not None:
            periods.append(_period(start, index - 1, fps))
            start = None
    if start is not None:
        periods.append(_period(start, len(frame_statuses) - 1, fps))
    return periods


def _period(start: int, end: int, fps) -> dict:
    frames = end - start + 1
    return {"start": start, "end": end, "frames": frames, "seconds": float(frames / fps) if fps else 0.0}
