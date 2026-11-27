"""Tells a real gain from a lucky day.

Your best session can be a fluke: a great day, a few loose reps, a spotter's help.
What really counts is the level you can REPEAT. We call it the "repeatable level":
the second-best session in a period. One lucky day cannot raise it, because
it takes two good sessions.

For each lift we compare the repeatable level of a period with the period of the
same length right before it. The result is one of these:

    confirmed_gain     the repeatable level went up by MIN_GAIN or more
    spike              the best session looks like a gain, but the repeatable level did not follow
    plateau            no real change
    regressing         the repeatable level went down by MIN_DROP or more
    insufficient_data  too few sessions to say

The numbers that decide this are named constants below, so they are easy to tune.
"""

import datetime

from app.analytics import one_rm

# Weights go up in 2.5 kg plate steps, which is about 3 to 4 percent of a typical 1RM.
# So a one-plate difference between two sessions is normal and must not count as a spike or a drop.
MIN_GAIN = 0.02  # 2 percent up counts as a real gain
MIN_DROP = 0.05  # 5 percent down counts as going backwards
SPIKE_GAP = 0.05  # a best session 5 percent above the repeatable level is a spike
# On light lifts one plate is a big percentage (2.5 kg is 5 percent of 50 kg).
# So a spike or a drop must ALSO be at least this many kg (about two plate steps).
MIN_KG_CHANGE = 5.0
MIN_SESSIONS = 3  # sessions needed in each period before we judge
LEVEL_WINDOW_DAYS = 28  # for the plateau length: the repeatable level looks back this far


def session_values(sets):
    """One number per training day: the best estimated 1RM of that day.

    Returns a list of (date, value), oldest first. Sets that cannot be used
    (no weight, too many reps) are skipped.
    """
    best_per_day = {}
    for s in sets:
        estimate = one_rm.estimate_one_rm(s["weight_kg"], s["reps"])
        if estimate is None:
            continue
        day = s["date"]
        if day not in best_per_day or estimate > best_per_day[day]:
            best_per_day[day] = estimate
    return sorted(best_per_day.items())


def repeatable_level(values):
    """The second-highest number in the list (or the only one if there is just one).

    Returns None for an empty list.
    """
    if not values:
        return None
    ordered = sorted(values, reverse=True)
    if len(ordered) == 1:
        return ordered[0]
    return ordered[1]


def classify(sets, period_start, period_end):
    """Judge one lift for a period. sets are all the sets ever done for this lift."""
    sessions = session_values(sets)

    period_days = (period_end - period_start).days + 1
    previous_end = period_start - datetime.timedelta(days=1)
    previous_start = previous_end - datetime.timedelta(days=period_days - 1)

    now = [(d, v) for d, v in sessions if period_start <= d <= period_end]
    before = [(d, v) for d, v in sessions if previous_start <= d <= previous_end]

    result = {
        "status": "insufficient_data",
        "peak": None,
        "peak_date": None,
        "level_now": None,
        "level_before": None,
        "level_change_percent": None,
        "spike": False,
        "sessions_now": len(now),
        "sessions_before": len(before),
    }

    if now:
        peak_date, peak = max(now, key=lambda item: item[1])  # the best session
        level_now = repeatable_level([v for d, v in now])
        result["peak"] = round(peak, 1)
        result["peak_date"] = peak_date
        result["level_now"] = round(level_now, 1)
    if before:
        level_before = repeatable_level([v for d, v in before])
        result["level_before"] = round(level_before, 1)

    # With too few sessions, one odd day would decide everything. Do not judge.
    if len(now) < MIN_SESSIONS or len(before) < MIN_SESSIONS:
        return result

    change = level_now / level_before - 1
    spike = peak >= level_now * (1 + SPIKE_GAP) and peak - level_now >= MIN_KG_CHANGE
    dropped = change <= -MIN_DROP and level_before - level_now >= MIN_KG_CHANGE
    result["level_change_percent"] = round(change * 100, 1)
    result["spike"] = spike

    if change >= MIN_GAIN:
        result["status"] = "confirmed_gain"
    elif spike and peak >= level_before * (1 + MIN_GAIN):
        # The best session looks like progress, but the level you repeat did not move.
        result["status"] = "spike"
    elif dropped:
        result["status"] = "regressing"
    else:
        result["status"] = "plateau"

    return result


def plateau_weeks(sets, as_of):
    """How many full weeks since the repeatable level last went up by MIN_GAIN or more.

    We walk through the training days in order. At each day we work out the repeatable
    level over the last LEVEL_WINDOW_DAYS days. Each time it is MIN_GAIN above the best
    level so far, that day is remembered as the last real gain.

    Returns None when there is not enough history to tell.
    """
    sessions = [(d, v) for d, v in session_values(sets) if d <= as_of]
    if len(sessions) < 2:
        return None

    window = datetime.timedelta(days=LEVEL_WINDOW_DAYS)
    best_level = None
    last_gain_day = None

    for i in range(len(sessions)):
        day = sessions[i][0]
        # the training days from the last LEVEL_WINDOW_DAYS days, up to and including this one
        recent = [v for d, v in sessions[: i + 1] if day - d < window]
        if len(recent) < 2:
            continue

        level = repeatable_level(recent)
        if best_level is None or level >= best_level * (1 + MIN_GAIN):
            best_level = level
            last_gain_day = day

    if last_gain_day is None:
        return None
    return (as_of - last_gain_day).days // 7
