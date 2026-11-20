"""US-14 Lock analytics and US-15 Timeline (AC-14.1 to AC-14.5, AC-15.1, AC-15.4).

Generated sequences with known answers. Indexes count from 0 here.
"""
from fractions import Fraction

import pytest

from app.lock_logic import LOCKED, LOST, NOT_TRACKED, UNLOCKED, analytics, segments


def seq(*runs):
    return [status for status, count in runs for _ in range(count)]


S1 = seq((UNLOCKED, 10), (LOCKED, 30), (UNLOCKED, 5), (LOCKED, 15), (LOST, 3), (LOCKED, 7))


def test_ac_14_1_the_numbers_for_s1_are_exact():
    a = analytics(S1, 30)
    assert (a["locked"]["frames"], a["unlocked"]["frames"], a["lost"]["frames"], a["not_tracked"]["frames"]) == (52, 15, 3, 0)
    assert a["locked"]["seconds"] == pytest.approx(52 / 30)        # 1.733 s
    assert a["unlocked"]["seconds"] == pytest.approx(0.5)
    assert a["lost"]["seconds"] == pytest.approx(0.1)
    assert a["lock_periods"] == 3
    assert (a["longest_lock"]["frames"], a["longest_lock"]["seconds"]) == (30, pytest.approx(1.0))
    assert a["average_lock"]["frames"] == pytest.approx(52 / 3)    # 17.333 frames
    assert a["average_lock"]["seconds"] == pytest.approx(52 / 3 / 30)   # 0.578 s
    assert a["total_frames"] == 70


@pytest.mark.parametrize("sequence", [[], [UNLOCKED] * 12, seq((NOT_TRACKED, 4), (LOST, 4))])
def test_ac_14_2_no_lock_periods_and_no_division_by_zero(sequence):
    a = analytics(sequence, 30)
    assert a["lock_periods"] == 0
    assert a["longest_lock"] == {"frames": 0, "seconds": 0.0}
    assert a["average_lock"] == {"frames": 0.0, "seconds": 0.0}
    assert a["locked"] == {"frames": 0, "seconds": 0.0}


def test_ac_14_3_unlocked_leaves_out_lost_and_not_tracked_frames():
    a = analytics(seq((NOT_TRACKED, 10), (UNLOCKED, 20), (LOST, 30)), 30)
    assert (a["unlocked"]["frames"], a["lost"]["frames"], a["not_tracked"]["frames"]) == (20, 30, 10)
    assert a["unlocked"]["seconds"] == pytest.approx(20 / 30)
    assert a["locked"]["frames"] + a["unlocked"]["frames"] + a["lost"]["frames"] + a["not_tracked"]["frames"] == a["total_frames"] == 60


def test_ac_14_5_durations_use_the_exact_frame_rate():
    a = analytics([LOCKED] * 30, Fraction(30000, 1001))
    assert a["locked"]["seconds"] == pytest.approx(1.001)
    assert a["longest_lock"]["seconds"] == pytest.approx(1.001)


def test_one_long_and_one_short_period_longest_and_average():
    a = analytics(seq((LOCKED, 40), (UNLOCKED, 1), (LOCKED, 10)), 25)
    assert a["lock_periods"] == 2
    assert a["longest_lock"]["frames"] == 40 and a["longest_lock"]["seconds"] == pytest.approx(1.6)
    assert a["average_lock"]["frames"] == pytest.approx(25.0) and a["average_lock"]["seconds"] == pytest.approx(1.0)


def test_ac_15_1_one_segment_per_run_of_equal_status():
    assert segments(S1) == [
        [UNLOCKED, 0, 9], [LOCKED, 10, 39], [UNLOCKED, 40, 44], [LOCKED, 45, 59], [LOST, 60, 62], [LOCKED, 63, 69],
    ]
    covered = sum(end - start + 1 for _, start, end in segments(S1))
    assert covered == len(S1)                       # widths add up to the whole video


def test_ac_15_4_before_tracking_the_timeline_is_one_not_tracked_segment():
    assert segments([NOT_TRACKED] * 90) == [[NOT_TRACKED, 0, 89]]
    assert segments([]) == []


def test_segments_never_merge_different_statuses():
    assert segments([LOCKED, UNLOCKED, LOCKED]) == [[LOCKED, 0, 0], [UNLOCKED, 1, 1], [LOCKED, 2, 2]]
