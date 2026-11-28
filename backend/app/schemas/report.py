import datetime
from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict, Field


class ReportCreate(BaseModel):
    """What the user sends to generate a report."""

    month: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")  # for example "2026-10"


class VerdictOut(BaseModel):
    exercise: str
    verdict: str
    assessment: str
    reason: str
    reason_source: str  # "model" or "code"


class ReportSummary(BaseModel):
    """What the list of reports shows."""

    # from_attributes lets Pydantic read the values straight from the database object.
    model_config = ConfigDict(from_attributes=True)

    id: int
    month: str
    created_at: datetime.datetime
    model_name: str


class ReportOut(ReportSummary):
    """One whole report."""

    narrative: str
    suggestions: List[str]
    verdicts: List[VerdictOut]
    facts: Dict[str, Any]
