"""Builds a monthly report: facts from the database, then the judge and the writer."""

import datetime
import json
import re

from app.llm import judge, provider, report_writer
from app.repositories import body_metric_repository, report_repository, workout_repository
from app.services import progress_service

MONTH_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
MAX_NOTES = 20


def month_period(month, today):
    """The first and last day of a month like "2026-10". The last day is today for the current month."""
    if not MONTH_PATTERN.match(month):
        raise ValueError("The month must look like 2026-10.")

    year = int(month[:4])
    number = int(month[5:7])
    first_day = datetime.date(year, number, 1)
    if first_day > today:
        raise ValueError("That month is in the future.")

    if number == 12:
        next_month = datetime.date(year + 1, 1, 1)
    else:
        next_month = datetime.date(year, number + 1, 1)
    last_day = min(next_month - datetime.timedelta(days=1), today)
    return first_day, last_day


def to_plain(value):
    """Turn dates and the like into text, so the data can be saved as JSON."""
    return json.loads(json.dumps(value, default=str))


def build_report_facts(db, user, month, today):
    """Everything the judge and the writer need to know about one month."""
    period_start, period_end = month_period(month, today)
    progress = progress_service.get_progress_for_period(db, user.uid, period_start, period_end)

    # The lifter's notes from workouts and from body entries, oldest first.
    notes = workout_repository.get_notes_in_period(db, user.uid, period_start, period_end)
    notes += body_metric_repository.get_notes_in_period(db, user.uid, period_start, period_end)
    notes.sort(key=lambda note: note["date"])
    notes = notes[:MAX_NOTES]

    age = None
    if user.birth_year is not None:
        age = today.year - user.birth_year

    return {
        "month": month,
        "period_start": period_start,
        "period_end": period_end,
        "profile": {
            "goal": user.goal,
            "sex": user.sex,
            "age": age,
            "training_years": user.training_years,
            "height_cm": user.height_cm,
        },
        "bodyweight": progress["bodyweight"],
        "consistency": progress["consistency"],
        "notes": notes,
        "lifts": progress["lifts"],
    }


def generate_report(db, user, month, today=None, model=None):
    """Make the report for one month and save it. A report that already exists is replaced.

    Raises ValueError for a bad month or when there is nothing to report on,
    and LLMError when the language model cannot be used.
    model is only passed in by tests, to use a fake model.
    """
    if today is None:
        today = datetime.date.today()

    facts = build_report_facts(db, user, month, today)
    if not facts["lifts"]:
        raise ValueError("There are no workouts with the main lifts yet, so there is nothing to report on.")

    judgments = judge.judge_all(facts, model=model)
    written = report_writer.write_report(facts, judgments, model=model)

    # What we keep is the same information the model saw, in a compact form.
    kept_facts = to_plain(
        {
            "period_start": facts["period_start"],
            "period_end": facts["period_end"],
            "profile": facts["profile"],
            "bodyweight": facts["bodyweight"],
            "consistency": facts["consistency"],
            "notes": facts["notes"],
            "lifts": [judge.build_lift_summary(lift) for lift in facts["lifts"]],
            "narrative_source": written["source"],
        }
    )

    return report_repository.save(
        db,
        user.uid,
        month,
        facts=kept_facts,
        verdicts=[j.model_dump(mode="json") for j in judgments],
        narrative=written["narrative"],
        suggestions=written["suggestions"],
        model_name=provider.model_name(),
    )
