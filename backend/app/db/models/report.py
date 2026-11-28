from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint

from app.db.base import Base


class Report(Base):
    """One monthly report for one user. A user has at most one report per month."""

    __tablename__ = "reports"
    __table_args__ = (UniqueConstraint("user_id", "month", name="uq_reports_user_month"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey("users.uid"), nullable=False, index=True)
    month = Column(String, nullable=False)  # for example "2026-10"

    # The numbers the report was written from, and the judgment for each lift.
    facts = Column(JSON, nullable=False)
    verdicts = Column(JSON, nullable=False)

    narrative = Column(Text, nullable=False)
    suggestions = Column(JSON, nullable=False)  # a list of short texts

    model_name = Column(String, nullable=False)  # for example "ollama:qwen2.5:7b"
    created_at = Column(DateTime, nullable=False)
