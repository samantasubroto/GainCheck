"""All database queries for the exercises table live here."""

from app.db.models.exercise import Exercise


def get_all(db):
    """Return every exercise, grouped by category and then sorted by name."""
    return db.query(Exercise).order_by(Exercise.category, Exercise.name).all()


def get_by_id(db, exercise_id):
    """Return one exercise, or None if there is no exercise with this id."""
    return db.query(Exercise).filter(Exercise.id == exercise_id).first()
