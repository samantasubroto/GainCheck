import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class SetIn(BaseModel):
    """One set that the user sends: which exercise, how heavy, how many reps."""

    exercise_id: int
    # 0 kg is allowed because bodyweight exercises (pull-ups) can have no extra weight.
    weight_kg: float = Field(ge=0, le=1000)
    reps: int = Field(ge=1, le=100)


class WorkoutCreate(BaseModel):
    """A whole workout: the day, a note, and at least one set."""

    date: datetime.date
    notes: Optional[str] = Field(default=None, max_length=500)
    sets: List[SetIn] = Field(min_length=1, max_length=200)


class SetOut(BaseModel):
    id: int
    exercise_id: int
    exercise_name: str
    set_number: int
    weight_kg: float
    reps: int


class WorkoutOut(BaseModel):
    id: int
    date: datetime.date
    notes: Optional[str] = None
    sets: List[SetOut]
