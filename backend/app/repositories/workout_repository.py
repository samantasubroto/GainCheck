"""All database queries for workouts live here.

Every query is filtered by user_id, so one user can never read another user's workouts.
"""

from app.db.models.exercise import Exercise
from app.db.models.workout import WorkoutSession, WorkoutSet


def get_sets_for_user(db, user_id, exercise_names):
    """Every set this user did for the given exercises, as plain dictionaries.

    Each one looks like {"date": ..., "exercise_name": "Bench Press", "weight_kg": 80.0, "reps": 5}.
    """
    rows = (
        db.query(WorkoutSession.date, Exercise.name, WorkoutSet.weight_kg, WorkoutSet.reps)
        .join(WorkoutSet, WorkoutSet.session_id == WorkoutSession.id)
        .join(Exercise, Exercise.id == WorkoutSet.exercise_id)
        .filter(WorkoutSession.user_id == user_id, Exercise.name.in_(exercise_names))
        .all()
    )
    return [
        {"date": row[0], "exercise_name": row[1], "weight_kg": row[2], "reps": row[3]}
        for row in rows
    ]


def get_workout_dates(db, user_id):
    """The date of every workout this user has done."""
    rows = db.query(WorkoutSession.date).filter(WorkoutSession.user_id == user_id).all()
    return [row[0] for row in rows]


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
