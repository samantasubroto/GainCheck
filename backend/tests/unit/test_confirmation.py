import datetime

from app.analytics import confirmation

# Every test set has 1 rep, so its estimated 1RM is simply its weight. That keeps the numbers easy.
BASE = datetime.date(2026, 3, 1)


def session(day_offset, weight_kg):
    """One set on the day that is day_offset days after BASE."""
    return {"date": BASE + datetime.timedelta(days=day_offset), "weight_kg": weight_kg, "reps": 1}


# The period under test is days 30 to 59 (30 days). The 30 days before it are days 0 to 29.
PERIOD_START = BASE + datetime.timedelta(days=30)
PERIOD_END = BASE + datetime.timedelta(days=59)


def before_sessions(weights):
    """Sessions in the previous period, a few days apart."""
    return [session(5 + 7 * i, w) for i, w in enumerate(weights)]


def now_sessions(weights):
    """Sessions in the period under test, a few days apart."""
    return [session(35 + 7 * i, w) for i, w in enumerate(weights)]


# ---------- the small helpers ----------


def test_session_values_keeps_the_best_set_of_each_day():
    sets = [session(0, 100), session(0, 110), session(2, 90)]
    values = confirmation.session_values(sets)
    assert values == [(BASE, 110), (BASE + datetime.timedelta(days=2), 90)]


def test_session_values_skips_sets_that_cannot_be_used():
    sets = [
        {"date": BASE, "weight_kg": 0, "reps": 10},
        {"date": BASE, "weight_kg": 30, "reps": 25},
        session(1, 80),
    ]
    assert confirmation.session_values(sets) == [(BASE + datetime.timedelta(days=1), 80)]


def test_repeatable_level_is_the_second_best():
    assert confirmation.repeatable_level([100, 120, 110]) == 110


def test_repeatable_level_of_a_single_value_is_that_value():
    assert confirmation.repeatable_level([100]) == 100


def test_repeatable_level_of_nothing_is_none():
    assert confirmation.repeatable_level([]) is None


# ---------- classify ----------


def classify(before, now):
    sets = before_sessions(before) + now_sessions(now)
    return confirmation.classify(sets, PERIOD_START, PERIOD_END)


def test_a_repeated_higher_level_is_a_confirmed_gain():
    result = classify([100, 100, 100], [105, 105, 106])
    assert result["status"] == "confirmed_gain"
    assert result["level_before"] == 100
    assert result["level_now"] == 105
    assert result["level_change_percent"] == 5.0


def test_one_great_day_is_a_spike_not_a_gain():
    result = classify([100, 100, 100], [100, 100, 112])
    assert result["status"] == "spike"
    assert result["spike"] is True
    assert result["peak"] == 112
    assert result["level_now"] == 100


def test_a_gain_can_still_contain_a_spike():
    # the level went up to 105, but the best day (112) is well above even that
    result = classify([100, 100, 100], [105, 105, 112])
    assert result["status"] == "confirmed_gain"
    assert result["spike"] is True


def test_a_slow_steady_rise_is_not_called_a_spike():
    result = classify([100, 100, 100], [100, 102, 104, 106])
    assert result["spike"] is False


def test_one_plate_up_on_a_light_lift_is_not_a_spike():
    # 42.5 is more than 5 percent above 40, but it is only one 2.5 kg plate
    result = classify([40, 40, 40], [40, 40, 42.5])
    assert result["spike"] is False
    assert result["status"] == "plateau"


def test_one_plate_down_on_a_light_lift_is_not_regressing():
    # 45 is more than 5 percent below 48, but that is only 3 kg
    result = classify([48, 48, 48], [45, 45, 45])
    assert result["status"] == "plateau"


def test_no_real_change_is_a_plateau():
    result = classify([100, 101, 100], [100, 101, 100])
    assert result["status"] == "plateau"


def test_a_clear_drop_is_regressing():
    result = classify([100, 100, 100], [90, 92, 91])
    assert result["status"] == "regressing"
    assert result["level_change_percent"] < 0


def test_too_few_sessions_in_the_period_is_not_judged():
    result = classify([100, 100, 100], [110, 110])
    assert result["status"] == "insufficient_data"
    assert result["sessions_now"] == 2
    assert result["peak"] == 110  # we still report what we can see


def test_too_few_sessions_before_is_not_judged():
    result = classify([100, 100], [105, 105, 105])
    assert result["status"] == "insufficient_data"


def test_no_sets_at_all():
    result = confirmation.classify([], PERIOD_START, PERIOD_END)
    assert result["status"] == "insufficient_data"
    assert result["peak"] is None
    assert result["level_now"] is None


# ---------- plateau length ----------


def test_plateau_weeks_counts_from_the_last_real_gain():
    sets = [session(0, 90), session(3, 90)]  # the first level: 90
    sets += [session(28, 100), session(31, 100)]  # a real gain on day 31
    sets += [session(day, 100) for day in range(35, 101, 7)]  # then nothing new for weeks

    as_of = BASE + datetime.timedelta(days=101)
    # 101 - 31 = 70 days = 10 weeks
    assert confirmation.plateau_weeks(sets, as_of) == 10


def test_plateau_weeks_is_zero_right_after_a_gain():
    sets = [session(0, 90), session(3, 90), session(28, 100), session(31, 100)]
    as_of = BASE + datetime.timedelta(days=33)
    assert confirmation.plateau_weeks(sets, as_of) == 0


def test_plateau_weeks_ignores_sets_after_the_date():
    sets = [session(0, 90), session(3, 90), session(28, 100), session(31, 100)]
    as_of = BASE + datetime.timedelta(days=20)  # before the gain happened
    assert confirmation.plateau_weeks(sets, as_of) == 2  # 20 - 3 = 17 days = 2 weeks


def test_plateau_weeks_with_too_little_history_is_none():
    assert confirmation.plateau_weeks([session(0, 100)], BASE + datetime.timedelta(days=10)) is None
    assert confirmation.plateau_weeks([], BASE) is None
