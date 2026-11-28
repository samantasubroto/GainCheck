import datetime

import pytest

from app.services.report_service import month_period

TODAY = datetime.date(2026, 11, 27)


def test_a_past_month_covers_all_its_days():
    assert month_period("2026-10", TODAY) == (datetime.date(2026, 10, 1), datetime.date(2026, 10, 31))


def test_february_in_a_leap_year():
    assert month_period("2024-02", TODAY) == (datetime.date(2024, 2, 1), datetime.date(2024, 2, 29))


def test_december_rolls_into_the_next_year_correctly():
    assert month_period("2025-12", TODAY) == (datetime.date(2025, 12, 1), datetime.date(2025, 12, 31))


def test_the_current_month_stops_at_today():
    assert month_period("2026-11", TODAY) == (datetime.date(2026, 11, 1), TODAY)


def test_a_future_month_is_rejected():
    with pytest.raises(ValueError):
        month_period("2026-12", TODAY)


@pytest.mark.parametrize("bad", ["2026-13", "2026-00", "26-10", "2026/10", "October", "", "2026-1"])
def test_badly_written_months_are_rejected(bad):
    with pytest.raises(ValueError):
        month_period(bad, TODAY)
