"""Personal records (PRs) for one exercise.

Every function here takes a list of sets that all belong to ONE exercise.
A set is a dictionary like {"date": datetime.date(2026, 3, 2), "weight_kg": 100.0, "reps": 5}.

We look at four kinds of record:
- weight PR:      the heaviest weight lifted in a set
- 1RM PR:         the best estimated one-rep max
- volume PR:      the most total work (weight x reps, added up) in one day
- rep PR:         the most reps at a weight you have used before
"""

from app.analytics.one_rm import best_one_rm


def max_weight(sets):
    """The heaviest weight used in any set, or None if there are no sets."""
    best = None
    for s in sets:
        if best is None or s["weight_kg"] > best:
            best = s["weight_kg"]
    return best


def best_session_volume(sets):
    """The most weight x reps added up on a single day, or None if there are no sets."""
    volume_per_day = {}
    for s in sets:
        day = s["date"]
        volume_per_day[day] = volume_per_day.get(day, 0) + s["weight_kg"] * s["reps"]

    if not volume_per_day:
        return None
    return max(volume_per_day.values())


def max_reps_at_weight(sets, weight_kg):
    """The most reps done in one set at exactly this weight, or None if never used."""
    best = None
    for s in sets:
        if s["weight_kg"] == weight_kg:
            if best is None or s["reps"] > best:
                best = s["reps"]
    return best


def personal_bests(sets):
    """The all-time best of each kind, over every set given."""
    return {
        "max_weight": max_weight(sets),
        "best_one_rm": best_one_rm(sets),
        "best_session_volume": best_session_volume(sets),
    }


def _new_record(new_value, old_value):
    """If new_value beats old_value, return {"value": ..., "previous": ...}. Otherwise None.

    With no old value there is nothing to beat. The first time you do an exercise
    sets the starting point, so that is not counted as a record.
    """
    if new_value is None or old_value is None:
        return None
    if new_value > old_value:
        return {"value": new_value, "previous": old_value}
    return None


def prs_in_period(sets, period_start, period_end):
    """Which records were broken between period_start and period_end (both days included)?

    We compare the best in the period with the best from before the period.
    """
    before = [s for s in sets if s["date"] < period_start]
    inside = [s for s in sets if period_start <= s["date"] <= period_end]

    # Rep PRs: for each weight used in the period, did we do more reps than ever before?
    rep_prs = []
    for weight in sorted({s["weight_kg"] for s in inside}):
        new_reps = max_reps_at_weight(inside, weight)
        old_reps = max_reps_at_weight(before, weight)
        if old_reps is not None and new_reps > old_reps:
            rep_prs.append({"weight_kg": weight, "reps": new_reps, "previous_reps": old_reps})

    return {
        "weight_pr": _new_record(max_weight(inside), max_weight(before)),
        "one_rm_pr": _new_record(best_one_rm(inside), best_one_rm(before)),
        "volume_pr": _new_record(best_session_volume(inside), best_session_volume(before)),
        "rep_prs": rep_prs,
    }
