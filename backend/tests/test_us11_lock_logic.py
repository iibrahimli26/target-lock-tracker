"""US-11 Lock status and lock periods (AC-11.1 to AC-11.5, AC-10.3).

Pure logic, tested with generated sequences whose answers are known by
construction (brief §3). No video and no tracker is involved.
Frame indexes here count from 0; the scenarios in the design count from 1.
"""
from fractions import Fraction

import pytest

from app.geometry import Box
from app.lock_logic import LOCKED, LOST, NOT_TRACKED, UNLOCKED, LOST_RESULT, lock_periods, status_of, statuses

ZONE = Box(100, 100, 200, 200)


def seq(*runs):
    return [status for status, count in runs for _ in range(count)]


S1 = seq((UNLOCKED, 10), (LOCKED, 30), (UNLOCKED, 5), (LOCKED, 15), (LOST, 3), (LOCKED, 7))


@pytest.mark.parametrize("x,y,w,h,expected", [
    (150, 150, 50, 50, LOCKED),      # well inside
    (100, 100, 50, 50, LOCKED),      # touching the top-left corner
    (99, 100, 50, 50, UNLOCKED),     # 1 pixel past the left edge
    (100, 99, 50, 50, UNLOCKED),     # 1 pixel past the top edge
    (250, 250, 50, 50, LOCKED),      # touching the bottom-right corner
    (251, 250, 50, 50, UNLOCKED),    # 1 pixel past the right edge
    (250, 251, 50, 50, UNLOCKED),    # 1 pixel past the bottom edge
    (100, 100, 200, 200, LOCKED),    # exactly the size of the zone
    (90, 90, 220, 220, UNLOCKED),    # larger than the zone
    (400, 400, 50, 50, UNLOCKED),    # completely outside
    (99.99, 150, 50, 50, UNLOCKED),  # a hundredth of a pixel outside is outside
])
def test_ac_11_1_locked_means_the_whole_box_is_inside_the_zone(x, y, w, h, expected):
    assert status_of(Box(x, y, w, h), ZONE) == expected


def test_status_of_frames_without_a_box():
    assert status_of(None, ZONE) == NOT_TRACKED
    assert status_of(LOST_RESULT, ZONE) == LOST


def test_ac_10_3_without_a_lock_zone_nothing_is_locked():
    results = [Box(150, 150, 50, 50)] * 5
    assert statuses(results, None) == [UNLOCKED] * 5
    assert lock_periods(statuses(results, None), 30) == []


def test_ac_11_2_every_continuous_lock_period_of_s1():
    periods = lock_periods(S1, 30)
    assert [(p["start"], p["end"], p["frames"]) for p in periods] == [(10, 39, 30), (45, 59, 15), (63, 69, 7)]
    assert [p["seconds"] for p in periods] == pytest.approx([1.0, 0.5, 7 / 30])


def test_ac_11_3_a_period_that_reaches_the_last_frame_ends_there():
    periods = lock_periods(seq((UNLOCKED, 5), (LOCKED, 10)), 30)
    assert [(p["start"], p["end"]) for p in periods] == [(5, 14)]


def test_ac_11_4_a_single_locked_frame_is_a_period_of_one_frame():
    periods = lock_periods([UNLOCKED, LOCKED, UNLOCKED], 30)
    assert [(p["start"], p["end"], p["frames"]) for p in periods] == [(1, 1, 1)]
    assert periods[0]["seconds"] == pytest.approx(1 / 30)


@pytest.mark.parametrize("sequence", [[], [UNLOCKED] * 9, [LOST] * 4, [NOT_TRACKED] * 3, seq((NOT_TRACKED, 2), (UNLOCKED, 2), (LOST, 2))])
def test_ac_11_5_no_locked_frames_no_periods(sequence):
    assert lock_periods(sequence, 30) == []


def test_lost_and_not_tracked_frames_break_a_lock_period():
    periods = lock_periods(seq((LOCKED, 3), (LOST, 1), (LOCKED, 2), (NOT_TRACKED, 1), (LOCKED, 4)), 30)
    assert [(p["start"], p["end"]) for p in periods] == [(0, 2), (4, 5), (7, 10)]


def test_period_seconds_use_the_exact_frame_rate():
    periods = lock_periods([LOCKED] * 30, Fraction(30000, 1001))
    assert periods[0]["seconds"] == pytest.approx(1.001)


# --- generated box sequences with known answers ------------------------------
def test_box_crossing_the_zone_gives_one_period_with_known_ends():
    # A 50 x 50 box moves right 5 px per frame at y = 150: x = 5 * k.
    # Inside the zone (x 100..300) exactly while 100 <= x and x + 50 <= 300, i.e. k = 20 .. 50.
    results = [Box(5 * k, 150, 50, 50) for k in range(80)]
    periods = lock_periods(statuses(results, ZONE), 30)
    assert [(p["start"], p["end"], p["frames"]) for p in periods] == [(20, 50, 31)]
    assert periods[0]["seconds"] == pytest.approx(31 / 30)


def test_box_entering_twice_with_a_loss_in_between():
    inside_box, outside_box = Box(150, 150, 50, 50), Box(0, 0, 50, 50)
    results = [None] * 3 + [outside_box] * 4 + [inside_box] * 6 + [LOST_RESULT] * 5 + [inside_box] * 2 + [outside_box]
    assert statuses(results, ZONE) == seq((NOT_TRACKED, 3), (UNLOCKED, 4), (LOCKED, 6), (LOST, 5), (LOCKED, 2), (UNLOCKED, 1))
    periods = lock_periods(statuses(results, ZONE), 25)
    assert [(p["start"], p["end"]) for p in periods] == [(7, 12), (18, 19)]
    assert [p["seconds"] for p in periods] == pytest.approx([6 / 25, 2 / 25])


def test_growing_box_unlocks_when_it_outgrows_the_zone():
    # Centred at (200, 200), side grows 10 px per frame from 150: inside while side <= 200, i.e. k = 0 .. 5.
    results = [Box(200 - (150 + 10 * k) / 2, 200 - (150 + 10 * k) / 2, 150 + 10 * k, 150 + 10 * k) for k in range(10)]
    assert statuses(results, ZONE) == [LOCKED] * 6 + [UNLOCKED] * 4
