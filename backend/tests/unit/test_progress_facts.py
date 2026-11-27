import datetime

import pytest

from app.analytics import progress_facts


def make_set(month, day, weight_kg, reps, year=2026):
    return {"date": datetime.date(year, month, day), "weight_kg": weight_kg, "reps": reps}


# ---------- monthly best 1RM ----------


def test_monthly_best_picks_the_best_set_of_each_month():
    sets = [
        make_set(1, 5, 100, 5),   # 116.7
        make_set(1, 20, 105, 5),  # 122.5  <- best in January
        make_set(2, 3, 90, 1),    # 90
    ]
    result = progress_facts.monthly_best_one_rm(sets)
    assert result == [
        {"month": "2026-01", "best_one_rm": 122.5},
        {"month": "2026-02", "best_one_rm": 90.0},
    ]


def test_monthly_best_is_sorted_oldest_first():
    sets = [make_set(3, 1, 100, 1), make_set(1, 1, 80, 1), make_set(2, 1, 90, 1)]
    months = [point["month"] for point in progress_facts.monthly_best_one_rm(sets)]
    assert months == ["2026-01", "2026-02", "2026-03"]


def test_monthly_best_skips_months_without_a_usable_set():
    sets = [make_set(1, 1, 100, 5), make_set(2, 1, 20, 25)]  # 25 reps cannot be used
    months = [point["month"] for point in progress_facts.monthly_best_one_rm(sets)]
    assert months == ["2026-01"]


def test_monthly_best_with_no_sets():
    assert progress_facts.monthly_best_one_rm([]) == []


# ---------- facts about one lift ----------

# The period is March 2026 (31 days), so the period before it is Jan 29 to Feb 28.
MARCH_START = datetime.date(2026, 3, 1)
MARCH_END = datetime.date(2026, 3, 31)


def test_lift_facts_compares_with_the_previous_period():
    sets = [
        make_set(2, 10, 100, 5),  # in the previous period, 1RM about 116.7
        make_set(3, 10, 105, 5),  # in the period, 1RM 122.5
    ]
    facts = progress_facts.lift_facts("Bench Press", sets, MARCH_START, MARCH_END)

    assert facts["exercise"] == "Bench Press"
    assert facts["one_rm_now"] == 122.5
    assert facts["one_rm_before"] == 116.7
    assert facts["change_kg"] == 5.8
    assert facts["change_percent"] == 5.0


def test_lift_facts_counts_sessions_by_day():
    sets = [make_set(3, 10, 100, 5), make_set(3, 10, 100, 5), make_set(3, 12, 100, 5)]
    facts = progress_facts.lift_facts("Deadlift", sets, MARCH_START, MARCH_END)
    assert facts["sessions_in_period"] == 2


def test_lift_facts_includes_records_and_the_all_time_best():
    sets = [make_set(1, 5, 100, 5), make_set(3, 10, 110, 5)]
    facts = progress_facts.lift_facts("Barbell Squat", sets, MARCH_START, MARCH_END)

    assert facts["prs"]["weight_pr"] == {"value": 110, "previous": 100}
    assert facts["all_time_best_one_rm"] == 128.3  # 110 x (1 + 5/30) = 128.33


def test_lift_facts_with_nothing_in_the_period():
    sets = [make_set(1, 5, 100, 5)]
    facts = progress_facts.lift_facts("Barbell Row", sets, MARCH_START, MARCH_END)

    assert facts["one_rm_now"] is None
    assert facts["change_kg"] is None
    assert facts["sessions_in_period"] == 0
    assert facts["all_time_best_one_rm"] == 116.7  # the all-time best still shows


def test_lift_facts_with_nothing_in_the_previous_period():
    sets = [make_set(3, 10, 100, 5)]
    facts = progress_facts.lift_facts("Overhead Press", sets, MARCH_START, MARCH_END)

    assert facts["one_rm_now"] == 116.7
    assert facts["one_rm_before"] is None
    assert facts["change_kg"] is None


def test_lift_facts_includes_the_monthly_series():
    sets = [make_set(1, 5, 100, 5), make_set(3, 10, 110, 5)]
    facts = progress_facts.lift_facts("Barbell Squat", sets, MARCH_START, MARCH_END)
    assert [p["month"] for p in facts["monthly_one_rm"]] == ["2026-01", "2026-03"]


# ---------- bodyweight ----------


def test_bodyweight_summary():
    entries = [
        {"date": datetime.date(2026, 3, 20), "weight_kg": 81.0},
        {"date": datetime.date(2026, 3, 2), "weight_kg": 80.0},   # the oldest in March
        {"date": datetime.date(2026, 2, 20), "weight_kg": 70.0},  # outside the period
    ]
    result = progress_facts.bodyweight_summary(entries, MARCH_START, MARCH_END)
    assert result == {"start_kg": 80.0, "latest_kg": 81.0, "change_kg": 1.0}


def test_bodyweight_summary_with_no_entries_in_the_period():
    result = progress_facts.bodyweight_summary([], MARCH_START, MARCH_END)
    assert result == {"start_kg": None, "latest_kg": None, "change_kg": None}


def test_bodyweight_loss_is_negative():
    entries = [
        {"date": datetime.date(2026, 3, 2), "weight_kg": 82.0},
        {"date": datetime.date(2026, 3, 30), "weight_kg": 80.5},
    ]
    result = progress_facts.bodyweight_summary(entries, MARCH_START, MARCH_END)
    assert result["change_kg"] == pytest.approx(-1.5)
