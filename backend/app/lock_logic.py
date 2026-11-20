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


def segments(frame_statuses: list) -> list:
    """Timeline (US-15): one [status, start, end] entry per run of equal status; indexes from 0, inclusive."""
    runs = []
    for index, status in enumerate(frame_statuses):
        if runs and runs[-1][0] == status:
            runs[-1][2] = index
        else:
            runs.append([status, index, index])
    return runs


def analytics(frame_statuses: list, fps) -> dict:
    """Totals for the analytics panel (US-14). Unlocked time leaves out lost and
    not-tracked frames (OQ-26); with no lock periods everything about locks is 0."""
    def amount(frames) -> dict:
        return {"frames": frames, "seconds": float(frames / fps) if fps else 0.0}

    count = {status: 0 for status in (LOCKED, UNLOCKED, LOST, NOT_TRACKED)}
    for status in frame_statuses:
        count[status] += 1
    periods = lock_periods(frame_statuses, fps)
    longest = max((p["frames"] for p in periods), default=0)
    average = count[LOCKED] / len(periods) if periods else 0.0
    return {
        "total_frames": len(frame_statuses),
        "locked": amount(count[LOCKED]), "unlocked": amount(count[UNLOCKED]),
        "lost": amount(count[LOST]), "not_tracked": amount(count[NOT_TRACKED]),
        "lock_periods": len(periods),
        "longest_lock": amount(longest),
        "average_lock": {"frames": float(average), "seconds": float(average / fps) if fps else 0.0},
        "periods": periods,
    }
