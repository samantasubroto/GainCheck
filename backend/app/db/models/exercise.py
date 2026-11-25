from sqlalchemy import Boolean, Column, Integer, String

from app.db.base import Base


class Exercise(Base):
    """One exercise in the shared list, for example "Barbell Squat".

    Every user picks from the same list.
    """

    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    category = Column(String, nullable=False)  # for example "legs", "push", "pull"
    # Bodyweight exercises (pull-ups, dips) can be logged with 0 kg extra weight.
    is_bodyweight = Column(Boolean, nullable=False, default=False)
