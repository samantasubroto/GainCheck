"""The report writer: turns the judgments into a short narrative and a few suggestions.

Like the judge, the writer is checked before we keep what it wrote:
- every number in the text must appear in the facts
- it may only talk about a "spike" or a "confirmed" gain when a lift really has that verdict
If the model fails the checks twice, code writes a plain report from the judgments instead.
"""

from string import Template

from app.llm import judge, provider
from app.llm.prompts import load_prompt
from app.llm.schemas import ReportDraft

WRITER_ATTEMPTS = 2

# Suggestions that code uses when the model's text cannot be trusted.
# The most important problems come first.
FALLBACK_SUGGESTIONS = [
    ("spike", "Repeat the weight of your best session a few times before you treat it as progress."),
    ("regressing", "Ease off for a week or two and check your sleep and food, then build back up gradually."),
    ("plateau", "On the lifts that have stalled, try one small increase, such as an extra rep or the smallest plate."),
    ("insufficient_data", "Log at least three sessions a month for each main lift, so we can judge them."),
    ("confirmed_gain", "Keep the same progression on the lifts that are improving."),
]
MAX_FALLBACK_SUGGESTIONS = 4


def unsupported_words_problem(text, statuses):
    """If the text talks about a spike or a confirmed gain that no lift has, say what is wrong. Otherwise None."""
    lowered = text.lower()
    if "spike" in lowered and "spike" not in statuses:
        return "it mentions a spike, but no lift has a spike this month"
    if "confirmed" in lowered and "confirmed_gain" not in statuses:
        return 'it uses the word "confirmed", but no lift has a confirmed gain this month'
    return None


def uses_unsupported_words(text, statuses):
    """True if the text talks about a spike or a confirmed gain that no lift has."""
    return unsupported_words_problem(text, statuses) is not None


def find_problem(texts, allowed_numbers, statuses):
    """Check every text the model wrote. Returns None if all are fine, or a sentence saying what is wrong."""
    for text in texts:
        unknown = judge.numbers_not_in_facts(text, allowed_numbers)
        if unknown:
            return "it contains numbers that are not in the facts: " + ", ".join(unknown)
        problem = unsupported_words_problem(text, statuses)
        if problem:
            return problem
    return None


def fallback_narrative(report_facts, judgments):
    """A plain summary built from the numbers and the reasons of the judgments."""
    c = report_facts["consistency"]
    parts = [
        f"In {report_facts['month']} you trained {c['sessions']} times, about {c['avg_per_week']:g} a week."
    ]
    for j in judgments:
        parts.append(f"{j.exercise}: {j.reason}")
    return " ".join(parts)


def fallback_suggestions(judgments):
    """Pick suggestions for the verdicts that are present, most important first."""
    present = {j.verdict.value for j in judgments}
    chosen = [text for status, text in FALLBACK_SUGGESTIONS if status in present]
    return chosen[:MAX_FALLBACK_SUGGESTIONS]


def write_report(report_facts, judgments, model=None):
    """Write the narrative and suggestions for a month.

    Returns {"narrative": text, "suggestions": [text, ...], "source": "model" or "code"}.
    model is only passed in by tests, to use a fake model.
    """
    summaries = [judge.build_lift_summary(lift) for lift in report_facts["lifts"]]
    judgment_list = [j.model_dump(mode="json") for j in judgments]

    system_prompt = load_prompt("report_system")
    user_prompt = Template(load_prompt("report_user")).substitute(
        month=report_facts["month"],
        profile=judge.to_json(report_facts["profile"]),
        bodyweight=judge.to_json(report_facts["bodyweight"]),
        consistency=judge.to_json(report_facts["consistency"]),
        notes=judge.format_notes(report_facts["notes"]),
        judgments=judge.to_json(judgment_list),
        summaries=judge.to_json(summaries),
    )

    allowed = judge.collect_numbers(
        [summaries, judgment_list, report_facts["profile"], report_facts["bodyweight"],
         report_facts["consistency"], report_facts["notes"], report_facts["month"]]
    )
    statuses = {j.verdict.value for j in judgments}

    feedback = ""  # after a failed try, we tell the model what was wrong
    for _ in range(WRITER_ATTEMPTS):
        draft = provider.ask_structured(ReportDraft, system_prompt, user_prompt + feedback, model=model)

        problem = find_problem([draft.narrative] + list(draft.suggestions), allowed, statuses)
        if problem is None:
            return {"narrative": draft.narrative, "suggestions": list(draft.suggestions), "source": "model"}

        feedback = (
            "\n\nYour previous report was rejected because " + problem
            + ". Write the report again and fix that."
        )

    return {
        "narrative": fallback_narrative(report_facts, judgments),
        "suggestions": fallback_suggestions(judgments),
        "source": "code",
    }
