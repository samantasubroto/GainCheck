import datetime
from typing import List, Optional

from pydantic import BaseModel


class MonthPoint(BaseModel):
    month: str  # for example "2026-03"
    best_one_rm: float


class Record(BaseModel):
    value: float
    previous: float


class RepRecord(BaseModel):
    weight_kg: float
    reps: int
    previous_reps: int


class LiftRecords(BaseModel):
    weight_pr: Optional[Record] = None
    one_rm_pr: Optional[Record] = None
    volume_pr: Optional[Record] = None
    rep_prs: List[RepRecord] = []


class ConfirmationOut(BaseModel):
    # confirmed_gain, spike, plateau, regressing or insufficient_data
    status: str
    peak: Optional[float] = None
    peak_date: Optional[datetime.date] = None
    level_now: Optional[float] = None
    level_before: Optional[float] = None
    level_change_percent: Optional[float] = None
    spike: bool
    sessions_now: int
    sessions_before: int


class LiftProgress(BaseModel):
    exercise: str
    sessions_in_period: int
    all_time_best_one_rm: Optional[float] = None
    one_rm_now: Optional[float] = None
    one_rm_before: Optional[float] = None
    change_kg: Optional[float] = None
    change_percent: Optional[float] = None
    prs: LiftRecords
    confirmation: ConfirmationOut
    plateau_weeks: Optional[int] = None
    monthly_one_rm: List[MonthPoint]


class ConsistencyOut(BaseModel):
    sessions: int
    avg_per_week: float
    weeks_trained: int
    total_weeks: int
    longest_rest_streak_days: int


class BodyweightOut(BaseModel):
    start_kg: Optional[float] = None
    latest_kg: Optional[float] = None
    change_kg: Optional[float] = None


class ProgressOut(BaseModel):
    period_start: datetime.date
    period_end: datetime.date
    days: int
    consistency: ConsistencyOut
    bodyweight: BodyweightOut
    lifts: List[LiftProgress]
