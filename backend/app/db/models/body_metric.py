from sqlalchemy import Column, Date, Float, ForeignKey, Integer, String, UniqueConstraint

from app.db.base import Base


class BodyMetric(Base):
    """One day's body measurements for one user. Only the weight is required."""

    __tablename__ = "body_metrics"

    # A user can have only one entry per date. The database enforces this.
    __table_args__ = (UniqueConstraint("user_id", "date", name="uq_body_metrics_user_date"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey("users.uid"), nullable=False, index=True)
    date = Column(Date, nullable=False)
    weight_kg = Column(Float, nullable=False)
    waist_cm = Column(Float, nullable=True)
    chest_cm = Column(Float, nullable=True)
    arm_cm = Column(Float, nullable=True)
    notes = Column(String, nullable=True)
