"""The judge: looks at the facts about each lift and says what they mean for this lifter.

Our code decides the verdict (spike, plateau, ...). The model adds two things code cannot:
an assessment (good, neutral or concerning, given the lifter's goal and notes) and a short
reason in plain words. We check the model's work before we keep it:

- the verdict is always the one our code worked out
- every number in the reason must appear in the facts, or we use a sentence written by code
"""

import json
import re
from string import Template

from app.llm import provider
from app.llm.prompts import load_prompt
from app.llm.schemas import Assessment, JudgeAnswer, LiftJudgment, Verdict

JUDGE_ATTEMPTS = 2  # how often we ask when the reason fails our checks
MAX_NOTES = 20
MAX_NOTE_LENGTH = 200

NUMBER_PATTERN = re.compile(r"\d+(?:\.\d+)?")
# A date like 2026-10 or 2026-10-12. Its parts are not loose numbers: a made-up
# "10 weeks" must not be accepted just because "10" is the month of the date.
DATE_PATTERN = re.compile(r"\d{4}-\d{2}(?:-\d{2})?")
NUMBER_TOLERANCE = 0.55  # lets the model write 178 for 177.9


# ---------- turning facts into what the model reads ----------


def build_lift_summary(lift):
    """Pick the facts the model needs about one lift (lift is one entry from the progress facts)."""
    c = lift["confirmation"]
    records = lift["prs"]

    new_records = []
    if records["weight_pr"]:
        new_records.append(
            f"heaviest set {records['weight_pr']['value']:g} kg (before: {records['weight_pr']['previous']:g} kg)"
        )
    if records["one_rm_pr"]:
        new_records.append(
            f"best estimated 1RM {records['one_rm_pr']['value']:g} kg (before: {records['one_rm_pr']['previous']:g} kg)"
        )
    for rep_pr in records["rep_prs"]:
        new_records.append(
            f"{rep_pr['reps']} reps at {rep_pr['weight_kg']:g} kg (before: {rep_pr['previous_reps']} reps)"
        )

    summary = {
        "exercise": lift["exercise"],
        "computed_status": c["status"],
        "repeatable_1rm_now_kg": c["level_now"],
        "repeatable_1rm_before_kg": c["level_before"],
        "change_percent": c["level_change_percent"],
        "sessions_this_month": c["sessions_now"],
        "sessions_previous_month": c["sessions_before"],
        "weeks_without_a_real_gain": lift["plateau_weeks"],
        "new_records": new_records,
    }

    # Only lifts that had a spike get the facts about it. For the others, the model
    # would only be handed something to talk about that does not apply.
    if c["spike"] or c["status"] == "spike":
        summary["best_session_kg"] = c["peak"]
        summary["best_session_date"] = c["peak_date"]
        summary["spike_detected"] = True

    return summary


def format_notes(notes):
    """Turn the notes (a list of {"date": ..., "text": ...}) into lines of text."""
    if not notes:
        return "(no notes)"
    lines = []
    for note in notes[:MAX_NOTES]:
        lines.append("- " + str(note["date"]) + ": " + note["text"][:MAX_NOTE_LENGTH])
    return "\n".join(lines)


def to_json(value):
    return json.dumps(value, indent=2, default=str)  # default=str turns dates into text


# ---------- checking the model's work ----------


def collect_numbers(value):
    """Every number found anywhere inside value (numbers, text, lists, dictionaries)."""
    numbers = set()

    if value is None or isinstance(value, bool):
        return numbers

    if isinstance(value, (int, float)):
        numbers.add(abs(float(value)))
    elif isinstance(value, str):
        for text in NUMBER_PATTERN.findall(DATE_PATTERN.sub(" ", value)):
            numbers.add(float(text))
    elif isinstance(value, dict):
        for item in value.values():
            numbers |= collect_numbers(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            numbers |= collect_numbers(item)
    else:
        numbers |= collect_numbers(str(value))  # for example a date

    return numbers


def numbers_not_in_facts(text, allowed_numbers):
    """The numbers written in text that are not among the allowed numbers.

    Dates are ignored, and so is the "1" in "1RM", because that is a name and not a number.
    """
    text = DATE_PATTERN.sub(" ", text)
    text = re.sub(r"\b1\s?RM\b", "", text, flags=re.IGNORECASE)

    unknown = []
    for found in NUMBER_PATTERN.findall(text):
        number = float(found)
        if not any(abs(number - allowed) <= NUMBER_TOLERANCE for allowed in allowed_numbers):
            unknown.append(found)
    return unknown


def numbers_are_grounded(text, allowed_numbers):
    """True if every number written in text is one of the allowed numbers."""
    return not numbers_not_in_facts(text, allowed_numbers)


def check_reason(text, allowed_numbers, status):
    """Check a reason written by the model. Returns None if it is fine, or a sentence saying what is wrong."""
    unknown = numbers_not_in_facts(text, allowed_numbers)
    if unknown:
        return "it contains numbers that are not in the facts: " + ", ".join(unknown)
    return contradiction_problem(text, status)


def contradiction_problem(text, status):
    """If the text talks about something the computed status says did not happen, say what.

    - Only a spike lift may mention a spike.
    - Only a confirmed gain may say "confirmed".
    This also catches odd wording that came from the lifter's notes.
    Returns None when there is no problem.
    """
    lowered = text.lower()
    if "spike" in lowered and status != "spike":
        return "it mentions a spike, but this lift is not a spike (its status is " + status + ")"
    if "confirmed" in lowered and status != "confirmed_gain":
        return 'it uses the word "confirmed", but this lift is not a confirmed gain (its status is ' + status + ")"
    return None


def contradicts_status(text, status):
    """True if the text talks about something the computed status says did not happen."""
    return contradiction_problem(text, status) is not None


# ---------- sentences that code writes itself ----------


def fallback_reason(summary):
    """A plain sentence built from the facts, used when we cannot trust the model's wording."""
    now = summary["repeatable_1rm_now_kg"]
    before = summary["repeatable_1rm_before_kg"]
    change = summary["change_percent"]
    status = summary["computed_status"]

    if status == "confirmed_gain":
        return f"The repeatable 1RM went from {before:g} kg to {now:g} kg ({change:+.1f}%)."
    if status == "spike":
        return (
            f"The best session of {summary['best_session_kg']:g} kg is above the repeatable 1RM "
            f"of {now:g} kg, so it is not counted as a real gain."
        )
    if status == "regressing":
        return f"The repeatable 1RM dropped from {before:g} kg to {now:g} kg ({change:+.1f}%)."
    if status == "plateau":
        return f"The repeatable 1RM is {now:g} kg, about the same as before ({before:g} kg)."

    return (
        f"Only {summary['sessions_this_month']} sessions this month and "
        f"{summary['sessions_previous_month']} the month before. We need at least 3 in each to judge."
    )


# ---------- the judge ----------


def judge_lift(lift, context, model=None):
    """Judge one lift. context holds the month, profile, bodyweight, consistency and notes.

    model is only passed in by tests, to use a fake model.
    """
    summary = build_lift_summary(lift)
    verdict = Verdict(summary["computed_status"])

    # Too few sessions: there is nothing to explain, so we do not ask the model.
    if verdict == Verdict.INSUFFICIENT_DATA:
        return LiftJudgment(
            exercise=summary["exercise"],
            verdict=verdict,
            assessment=Assessment.NEUTRAL,
            reason=fallback_reason(summary),
            reason_source="code",
        )

    system_prompt = load_prompt("judge_system")
    user_prompt = Template(load_prompt("judge_user")).substitute(
        month=context["month"],
        profile=to_json(context["profile"]),
        bodyweight=to_json(context["bodyweight"]),
        consistency=to_json(context["consistency"]),
        notes=format_notes(context["notes"]),
        exercise=summary["exercise"],
        lift=to_json(summary),
    )

    # The numbers the model may use: those in the facts, the profile and the notes.
    allowed = collect_numbers([summary, context["profile"], context["bodyweight"],
                               context["consistency"], context["notes"], context["month"]])

    feedback = ""  # after a failed try, we tell the model what was wrong
    for _ in range(JUDGE_ATTEMPTS):
        answer = provider.ask_structured(JudgeAnswer, system_prompt, user_prompt + feedback, model=model)
        problem = check_reason(answer.reason, allowed, summary["computed_status"])
        if problem is None:
            return LiftJudgment(
                exercise=summary["exercise"],  # always our values, whatever the model wrote
                verdict=verdict,
                assessment=answer.assessment,
                reason=answer.reason,
                reason_source="model",
            )
        feedback = (
            "\n\nYour previous answer was rejected because " + problem
            + ". Write the answer again and fix that."
        )

    # The model failed our checks twice. We write the reason ourselves.
    return LiftJudgment(
        exercise=summary["exercise"],
        verdict=verdict,
        assessment=Assessment.NEUTRAL,
        reason=fallback_reason(summary),
        reason_source="code",
    )


def judge_all(report_facts, model=None):
    """Judge every lift in the report facts. Returns a list of LiftJudgment, in the same order."""
    context = {
        "month": report_facts["month"],
        "profile": report_facts["profile"],
        "bodyweight": report_facts["bodyweight"],
        "consistency": report_facts["consistency"],
        "notes": report_facts["notes"],
    }
    return [judge_lift(lift, context, model=model) for lift in report_facts["lifts"]]
