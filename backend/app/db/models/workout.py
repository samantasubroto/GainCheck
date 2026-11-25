from sqlalchemy import Column, Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class WorkoutSession(Base):
    """One visit to the gym on one day. It owns a list of sets."""

    __tablename__ = "workout_sessions"

    id = Column(Integer, primary_key=True)
    # Whose workout this is. We always filter by this when we read data.
    user_id = Column(String, ForeignKey("users.uid"), nullable=False, index=True)
    date = Column(Date, nullable=False)
    notes = Column(String, nullable=True)

    # session.sets gives the list of sets in this session.
    # delete-orphan: if a set is removed from the list, it is deleted from the database too.
    sets = relationship(
        "WorkoutSet",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="WorkoutSet.id",
    )


class WorkoutSet(Base):
    """One set, for example 100 kg for 5 reps on the bench press."""

    __tablename__ = "workout_sets"

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("workout_sessions.id"), nullable=False, index=True)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=False)
    set_number = Column(Integer, nullable=False)  # 1 for the first set of that exercise
    weight_kg = Column(Float, nullable=False)
    reps = Column(Integer, nullable=False)

    # set.session gives the session it belongs to. set.exercise gives the exercise.
    session = relationship("WorkoutSession", back_populates="sets")
    exercise = relationship("Exercise")
