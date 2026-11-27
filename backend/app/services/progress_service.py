"""Reads a user's data from the database and hands it to the analytics functions."""

import datetime

from app.analytics import consistency, progress_facts
from app.repositories import body_metric_repository, workout_repository

# The lifts we track progress for. They are the ones with meaningful strength numbers.
MAIN_LIFTS = ["Barbell Squat", "Bench Press", "Deadlift", "Overhead Press", "Barbell Row"]


def get_progress(db, user_id, days, today=None):
    """Progress facts for the last `days` days, ending today."""
    if today is None:
        today = datetime.date.today()
    period_end = today
    period_start = today - datetime.timedelta(days=days - 1)

    # Read everything we need from the database.
    all_sets = workout_repository.get_sets_for_user(db, user_id, MAIN_LIFTS)
    workout_dates = workout_repository.get_workout_dates(db, user_id)
    body_entries = body_metric_repository.get_all_for_user(db, user_id, 500)
    body_weights = [{"date": e.date, "weight_kg": e.weight_kg} for e in body_entries]

    # Work out the facts for each lift the user has ever done.
    lifts = []
    for name in MAIN_LIFTS:
        lift_sets = [s for s in all_sets if s["exercise_name"] == name]
        if lift_sets:
            lifts.append(progress_facts.lift_facts(name, lift_sets, period_start, period_end))

    return {
        "period_start": period_start,
        "period_end": period_end,
        "days": days,
        "consistency": consistency.summarize(workout_dates, period_start, period_end),
        "bodyweight": progress_facts.bodyweight_summary(body_weights, period_start, period_end),
        "lifts": lifts,
    }
