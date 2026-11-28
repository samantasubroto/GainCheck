"""The shapes of the things the language model reads and writes."""

from enum import Enum
from typing import Annotated, List

from pydantic import BaseModel, Field


class Verdict(str, Enum):
    """The state of one lift. Our code works this out. The model never decides it."""

    CONFIRMED_GAIN = "confirmed_gain"
    SPIKE = "spike"
    PLATEAU = "plateau"
    REGRESSING = "regressing"
    INSUFFICIENT_DATA = "insufficient_data"


class Assessment(str, Enum):
    """How the month looks for this lift once the lifter's situation is taken into account."""

    GOOD = "good"
    NEUTRAL = "neutral"
    CONCERNING = "concerning"


class JudgeAnswer(BaseModel):
    """What the model must fill in for one lift. Any other shape is rejected."""

    exercise: str
    verdict: Verdict
    assessment: Assessment
    reason: str = Field(min_length=10, max_length=300)


class ReportDraft(BaseModel):
    """What the model must fill in when it writes the monthly report."""

    narrative: str = Field(min_length=20, max_length=800)
    suggestions: List[Annotated[str, Field(min_length=5, max_length=160)]] = Field(min_length=1, max_length=4)


class LiftJudgment(BaseModel):
    """The final judgment we keep for one lift."""

    exercise: str
    verdict: Verdict
    assessment: Assessment
    reason: str
    # "model" if the model wrote the reason, "code" if we wrote it from the facts instead.
    reason_source: str
