"""Builds the "facts" about someone's progress.

The progress page shows these facts, and later the monthly report is written from them.
Plain Python only: no database, no web code. The service passes the data in.

A set is a dictionary like {"date": datetime.date(2026, 3, 2), "weight_kg": 100.0, "reps": 5}.
"""

import datetime

from app.analytics import confirmation, one_rm, prs


def monthly_best_one_rm(sets):
    """The best estimated 1RM in each calendar month, oldest month first.

    Returns a list like [{"month": "2026-01", "best_one_rm": 112.5}, ...].
    Months without a usable set are left out.
    """
    best = {}
    for s in sets:
        estimate = one_rm.estimate_one_rm(s["weight_kg"], s["reps"])
        if estimate is None:
            continue
        month = s["date"].strftime("%Y-%m")
        if month not in best or estimate > best[month]:
            best[month] = estimate

    return [{"month": month, "best_one_rm": round(best[month], 1)} for month in sorted(best)]


def _round_record(record):
    """Round the numbers of a record like {"value": 122.5, "previous": 116.666} to 1 decimal."""
    if record is None:
        return None
    return {"value": round(record["value"], 1), "previous": round(record["previous"], 1)}


def lift_facts(exercise_name, sets, period_start, period_end):
    """All the facts about one lift for a period.

    We compare the period with the period of the same length right before it,
    for example the last 90 days against the 90 days before that.
    sets are all the sets ever done for this one exercise.
    """
    period_days = (period_end - period_start).days + 1
    previous_end = period_start - datetime.timedelta(days=1)
    previous_start = previous_end - datetime.timedelta(days=period_days - 1)

    in_period = [s for s in sets if period_start <= s["date"] <= period_end]
    in_previous = [s for s in sets if previous_start <= s["date"] <= previous_end]

    now = one_rm.best_one_rm(in_period)
    before = one_rm.best_one_rm(in_previous)

    change_kg = None
    change_percent = None
    if now is not None and before is not None:
        change_kg = round(now - before, 1)
        change_percent = round((now - before) / before * 100, 1)

    records = prs.prs_in_period(sets, period_start, period_end)
    all_time = one_rm.best_one_rm(sets)

    return {
        "exercise": exercise_name,
        "sessions_in_period": len({s["date"] for s in in_period}),
        "all_time_best_one_rm": round(all_time, 1) if all_time is not None else None,
        "one_rm_now": round(now, 1) if now is not None else None,
        "one_rm_before": round(before, 1) if before is not None else None,
        "change_kg": change_kg,
        "change_percent": change_percent,
        "prs": {
            "weight_pr": _round_record(records["weight_pr"]),
            "one_rm_pr": _round_record(records["one_rm_pr"]),
            "volume_pr": _round_record(records["volume_pr"]),
            "rep_prs": records["rep_prs"],
        },
        "confirmation": confirmation.classify(sets, period_start, period_end),
        "plateau_weeks": confirmation.plateau_weeks(sets, period_end),
        "monthly_one_rm": monthly_best_one_rm(sets),
    }


def bodyweight_summary(entries, period_start, period_end):
    """First weight, latest weight and the change, for the entries inside the period.

    An entry is a dictionary like {"date": datetime.date(2026, 3, 2), "weight_kg": 80.5}.
    """
    inside = [e for e in entries if period_start <= e["date"] <= period_end]
    inside.sort(key=lambda e: e["date"])  # oldest first

    if not inside:
        return {"start_kg": None, "latest_kg": None, "change_kg": None}

    start_kg = inside[0]["weight_kg"]
    latest_kg = inside[-1]["weight_kg"]
    return {
        "start_kg": start_kg,
        "latest_kg": latest_kg,
        "change_kg": round(latest_kg - start_kg, 1),
    }
