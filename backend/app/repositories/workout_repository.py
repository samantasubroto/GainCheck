"""All database queries for workouts live here.

Every query is filtered by user_id, so one user can never read another user's workouts.
"""

from app.db.models.workout import WorkoutSession, WorkoutSet


def create(db, user_id, date, notes, sets_data):
    """Save one workout session together with all its sets.

    sets_data is a list of dictionaries like
    {"exercise_id": 1, "set_number": 1, "weight_kg": 100.0, "reps": 5}
    """
    session = WorkoutSession(user_id=user_id, date=date, notes=notes)
    for set_data in sets_data:
        session.sets.append(WorkoutSet(**set_data))

    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_for_user_on_date(db, user_id, date):
    """Return this user's workout for one day, or None if they have none yet."""
    return (
        db.query(WorkoutSession)
        .filter(WorkoutSession.user_id == user_id, WorkoutSession.date == date)
        .order_by(WorkoutSession.id)
        .first()
    )


def add_sets(db, session, notes, sets_data):
    """Add more sets (and an optional note) to a workout that already exists."""
    for set_data in sets_data:
        session.sets.append(WorkoutSet(**set_data))

    if notes:
        if session.notes:
            session.notes = session.notes + "\n" + notes
        else:
            session.notes = notes

    db.commit()
    db.refresh(session)
    return session


def get_all_for_user(db, user_id, limit):
    """Return this user's newest workouts first."""
    return (
        db.query(WorkoutSession)
        .filter(WorkoutSession.user_id == user_id)
        .order_by(WorkoutSession.date.desc(), WorkoutSession.id.desc())
        .limit(limit)
        .all()
    )


def get_for_user(db, user_id, session_id):
    """Return one workout, but only if it belongs to this user. Otherwise None."""
    return (
        db.query(WorkoutSession)
        .filter(WorkoutSession.id == session_id, WorkoutSession.user_id == user_id)
        .first()
    )
