import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class BodyMetricIn(BaseModel):
    """What the user sends. Only date and weight are required."""

    date: datetime.date
    weight_kg: float = Field(ge=20, le=400)
    waist_cm: Optional[float] = Field(default=None, ge=30, le=250)
    chest_cm: Optional[float] = Field(default=None, ge=30, le=250)
    arm_cm: Optional[float] = Field(default=None, ge=10, le=100)
    notes: Optional[str] = Field(default=None, max_length=500)


class BodyMetricOut(BaseModel):
    # from_attributes lets Pydantic read the values straight from the database object.
    model_config = ConfigDict(from_attributes=True)

    id: int
    date: datetime.date
    weight_kg: float
    waist_cm: Optional[float] = None
    chest_cm: Optional[float] = None
    arm_cm: Optional[float] = None
    notes: Optional[str] = None
