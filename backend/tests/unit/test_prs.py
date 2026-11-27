import datetime

import pytest

from app.analytics import prs


def make_set(day, weight_kg, reps):
    """A small helper so the tests stay short. day is the day of January 2026."""
    return {"date": datetime.date(2026, 1, day), "weight_kg": weight_kg, "reps": reps}


# ---------- the small building blocks ----------


def test_max_weight():
    sets = [make_set(1, 100, 5), make_set(2, 110, 3), make_set(3, 90, 8)]
    assert prs.max_weight(sets) == 110


def test_max_weight_with_no_sets_is_none():
    assert prs.max_weight([]) is None


def test_session_volume_adds_up_the_sets_of_one_day():
    sets = [
        make_set(1, 100, 5),  # day 1: 500 + 500 = 1000
        make_set(1, 100, 5),
        make_set(2, 120, 3),  # day 2: 360
    ]
    assert prs.best_session_volume(sets) == 1000


def test_max_reps_at_weight():
    sets = [make_set(1, 100, 5), make_set(2, 100, 7), make_set(3, 90, 12)]
    assert prs.max_reps_at_weight(sets, 100) == 7
    assert prs.max_reps_at_weight(sets, 95) is None


def test_personal_bests():
    sets = [make_set(1, 100, 5), make_set(2, 110, 1)]
    bests = prs.personal_bests(sets)
    assert bests["max_weight"] == 110
    assert bests["best_one_rm"] == pytest.approx(116.67, abs=0.01)
    assert bests["best_session_volume"] == 500


# ---------- records in a period ----------


def test_a_heavier_weight_in_the_period_is_a_weight_pr():
    sets = [make_set(1, 100, 5), make_set(10, 105, 5)]
    result = prs.prs_in_period(sets, datetime.date(2026, 1, 5), datetime.date(2026, 1, 31))
    assert result["weight_pr"] == {"value": 105, "previous": 100}


def test_a_better_estimated_1rm_is_a_1rm_pr():
    sets = [make_set(1, 100, 5), make_set(10, 105, 5)]
    result = prs.prs_in_period(sets, datetime.date(2026, 1, 5), datetime.date(2026, 1, 31))
    assert result["one_rm_pr"]["value"] == pytest.approx(122.5)
    assert result["one_rm_pr"]["previous"] == pytest.approx(116.67, abs=0.01)


def test_a_bigger_day_of_work_is_a_volume_pr():
    sets = [make_set(1, 100, 5), make_set(10, 100, 5), make_set(10, 100, 5)]
    result = prs.prs_in_period(sets, datetime.date(2026, 1, 5), datetime.date(2026, 1, 31))
    assert result["volume_pr"] == {"value": 1000, "previous": 500}


def test_more_reps_at_a_weight_used_before_is_a_rep_pr():
    sets = [make_set(1, 100, 5), make_set(10, 100, 7)]
    result = prs.prs_in_period(sets, datetime.date(2026, 1, 5), datetime.date(2026, 1, 31))
    assert result["rep_prs"] == [{"weight_kg": 100, "reps": 7, "previous_reps": 5}]


def test_a_new_weight_is_not_a_rep_pr():
    # 102.5 kg was never used before, so there is nothing to compare its reps with
    sets = [make_set(1, 100, 5), make_set(10, 102.5, 3)]
    result = prs.prs_in_period(sets, datetime.date(2026, 1, 5), datetime.date(2026, 1, 31))
    assert result["rep_prs"] == []


def test_no_improvement_means_no_records():
    sets = [make_set(1, 100, 5), make_set(10, 95, 5)]
    result = prs.prs_in_period(sets, datetime.date(2026, 1, 5), datetime.date(2026, 1, 31))
    assert result["weight_pr"] is None
    assert result["one_rm_pr"] is None
    assert result["volume_pr"] is None
    assert result["rep_prs"] == []


def test_the_first_ever_sets_are_a_starting_point_not_a_record():
    sets = [make_set(10, 100, 5)]
    result = prs.prs_in_period(sets, datetime.date(2026, 1, 5), datetime.date(2026, 1, 31))
    assert result["weight_pr"] is None
    assert result["one_rm_pr"] is None


def test_first_and_last_day_of_the_period_count_as_inside():
    sets = [make_set(1, 100, 5), make_set(5, 110, 5), make_set(31, 120, 5)]
    result = prs.prs_in_period(sets, datetime.date(2026, 1, 5), datetime.date(2026, 1, 31))
    # 110 on the first day and 120 on the last day are both inside, 100 is the 'before'
    assert result["weight_pr"] == {"value": 120, "previous": 100}


def test_sets_after_the_period_are_ignored():
    sets = [make_set(1, 100, 5), make_set(10, 105, 5), make_set(20, 200, 5)]
    result = prs.prs_in_period(sets, datetime.date(2026, 1, 5), datetime.date(2026, 1, 15))
    assert result["weight_pr"] == {"value": 105, "previous": 100}
