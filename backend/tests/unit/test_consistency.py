import datetime

from app.analytics import consistency


def day(number):
    """A day of January 2026. January 1, 2026 is a Thursday."""
    return datetime.date(2026, 1, number)


FIRST = day(1)
LAST_OF_TWO_WEEKS = day(14)


def test_three_sessions_a_week_for_two_weeks():
    dates = [day(1), day(3), day(5), day(8), day(10), day(12)]
    result = consistency.summarize(dates, FIRST, LAST_OF_TWO_WEEKS)

    assert result["sessions"] == 6
    assert result["avg_per_week"] == 3.0
    assert result["weeks_trained"] == 2
    assert result["total_weeks"] == 2
    # the longest rest: Jan 5 -> Jan 8 has 2 rest days, and Jan 13 and 14 after the last session also 2
    assert result["longest_rest_streak_days"] == 2


def test_the_same_day_twice_counts_once():
    dates = [day(1), day(1), day(3)]
    result = consistency.summarize(dates, FIRST, LAST_OF_TWO_WEEKS)
    assert result["sessions"] == 2


def test_dates_outside_the_period_are_ignored():
    dates = [datetime.date(2025, 12, 20), day(3), datetime.date(2026, 2, 1)]
    result = consistency.summarize(dates, FIRST, LAST_OF_TWO_WEEKS)
    assert result["sessions"] == 1


def test_no_sessions_at_all():
    result = consistency.summarize([], FIRST, LAST_OF_TWO_WEEKS)
    assert result["sessions"] == 0
    assert result["avg_per_week"] == 0
    assert result["weeks_trained"] == 0
    assert result["longest_rest_streak_days"] == 14


def test_a_long_break_in_the_middle():
    # sessions on Jan 1 and Jan 10: 8 rest days between them (Jan 2 to Jan 9)
    result = consistency.summarize([day(1), day(10)], FIRST, LAST_OF_TWO_WEEKS)
    assert result["longest_rest_streak_days"] == 8


def test_rest_before_the_first_session_counts():
    # the first session is on Jan 6, so Jan 1 to Jan 5 (5 days) were rest
    result = consistency.summarize([day(6), day(7), day(8)], FIRST, LAST_OF_TWO_WEEKS)
    # after the last session: Jan 9 to Jan 14 = 6 rest days, which is longer
    assert result["longest_rest_streak_days"] == 6


def test_weeks_trained_counts_weeks_that_had_a_workout():
    # both sessions are in the first week, none in the second
    result = consistency.summarize([day(2), day(4)], FIRST, LAST_OF_TWO_WEEKS)
    assert result["weeks_trained"] == 1
    assert result["total_weeks"] == 2


def test_a_short_last_week_still_counts_as_a_week():
    # 10 days = one full week and a short second week
    result = consistency.summarize([day(1)], FIRST, day(10))
    assert result["total_weeks"] == 2
