"""All database queries for reports live here.

Every query is filtered by user_id, so one user can never read another user's reports.
"""

import datetime

from app.db.models.report import Report


def get_for_month(db, user_id, month):
    """This user's report for one month, or None."""
    return db.query(Report).filter(Report.user_id == user_id, Report.month == month).first()


def list_for_user(db, user_id):
    """All of this user's reports, newest month first."""
    return db.query(Report).filter(Report.user_id == user_id).order_by(Report.month.desc()).all()


def get_for_user(db, user_id, report_id):
    """One report, but only if it belongs to this user. Otherwise None."""
    return db.query(Report).filter(Report.id == report_id, Report.user_id == user_id).first()


def save(db, user_id, month, facts, verdicts, narrative, suggestions, model_name):
    """Save a report. If the user already has one for this month, it is replaced."""
    report = get_for_month(db, user_id, month)
    if report is None:
        report = Report(user_id=user_id, month=month)
        db.add(report)

    report.facts = facts
    report.verdicts = verdicts
    report.narrative = narrative
    report.suggestions = suggestions
    report.model_name = model_name
    report.created_at = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)

    db.commit()
    db.refresh(report)
    return report
