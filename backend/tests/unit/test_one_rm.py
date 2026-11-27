import pytest

from app.analytics.one_rm import best_one_rm, estimate_one_rm


def test_one_rep_is_the_weight_itself():
    assert estimate_one_rm(100, 1) == 100


def test_five_reps_uses_the_epley_formula():
    # 100 x (1 + 5/30) = 116.666...
    assert estimate_one_rm(100, 5) == pytest.approx(116.67, abs=0.01)


def test_ten_reps_is_still_allowed():
    assert estimate_one_rm(60, 10) == pytest.approx(80.0)


def test_more_than_ten_reps_is_ignored():
    assert estimate_one_rm(40, 11) is None


def test_zero_weight_is_ignored():
    # for example a pull-up with no extra weight
    assert estimate_one_rm(0, 8) is None


def test_zero_reps_is_ignored():
    assert estimate_one_rm(100, 0) is None


def test_best_one_rm_picks_the_highest_estimate():
    sets = [
        {"weight_kg": 100, "reps": 5},  # 116.67
        {"weight_kg": 105, "reps": 3},  # 115.5
        {"weight_kg": 80, "reps": 8},   # 101.33
    ]
    assert best_one_rm(sets) == pytest.approx(116.67, abs=0.01)


def test_best_one_rm_skips_sets_that_cannot_be_used():
    sets = [
        {"weight_kg": 0, "reps": 10},
        {"weight_kg": 50, "reps": 20},
        {"weight_kg": 90, "reps": 1},
    ]
    assert best_one_rm(sets) == 90


def test_best_one_rm_with_no_sets_is_none():
    assert best_one_rm([]) is None
