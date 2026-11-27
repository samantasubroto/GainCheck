"""All database queries for body metrics live here.

Every query is filtered by user_id, so one user can never read another user's data.
"""

from app.db.models.body_metric import BodyMetric


def get_for_user_on_date(db, user_id, date):
    """Return this user's entry for one day, or None if there is none."""
    return (
        db.query(BodyMetric)
        .filter(BodyMetric.user_id == user_id, BodyMetric.date == date)
        .first()
    )


def get_all_for_user(db, user_id, limit):
    """Return this user's entries, newest first."""
    return (
        db.query(BodyMetric)
        .filter(BodyMetric.user_id == user_id)
        .order_by(BodyMetric.date.desc())
        .limit(limit)
        .all()
    )


def save(db, user_id, data):
    """Save one day's entry.

    data is a dictionary like {"date": ..., "weight_kg": 80.5, "waist_cm": None, ...}

    If there is no entry for that date yet, we create one.
    If there is, we update it, but only with the values that were sent.
    A value that was left empty does not erase what was saved earlier that day.
    """
    entry = get_for_user_on_date(db, user_id, data["date"])

    if entry is None:
        entry = BodyMetric(user_id=user_id, **data)
        db.add(entry)
    else:
        for field, value in data.items():
            if value is not None:
                setattr(entry, field, value)

    db.commit()
    db.refresh(entry)
    return entry
