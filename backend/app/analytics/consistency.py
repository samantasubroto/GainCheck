"""How regularly someone trains.

These functions take a list of workout dates (datetime.date) and a period
(a first day and a last day, both included).
"""

import math


def longest_rest_streak(dates, period_start, period_end):
    """The most days in a row without training inside the period.

    dates must be sorted, with no repeats, and all inside the period.
    The days before the first session and after the last session count too.
    Example: sessions on Monday and Friday -> 3 rest days between them (Tue, Wed, Thu).
    """
    if not dates:
        return (period_end - period_start).days + 1  # the whole period was rest

    longest = (dates[0] - period_start).days  # rest days before the first session
    longest = max(longest, (period_end - dates[-1]).days)  # and after the last one

    for i in range(len(dates) - 1):
        rest_days = (dates[i + 1] - dates[i]).days - 1
        longest = max(longest, rest_days)

    return longest


def summarize(workout_dates, period_start, period_end):
    """Numbers that describe how consistent the training was in the period.

    sessions                  how many days had a workout
    avg_per_week              sessions per week, averaged over the whole period
    weeks_trained             in how many of the weeks (7-day blocks, starting at
                              period_start) did at least one workout happen
    total_weeks               how many such weeks there are (a short last week counts)
    longest_rest_streak_days  see longest_rest_streak above
    """
    # Keep only dates inside the period, count each day once, and sort them.
    dates = sorted({d for d in workout_dates if period_start <= d <= period_end})

    total_days = (period_end - period_start).days + 1
    weeks_with_training = {(d - period_start).days // 7 for d in dates}

    return {
        "sessions": len(dates),
        "avg_per_week": round(len(dates) / (total_days / 7), 2),
        "weeks_trained": len(weeks_with_training),
        "total_weeks": math.ceil(total_days / 7),
        "longest_rest_streak_days": longest_rest_streak(dates, period_start, period_end),
    }
