import pytest

from app.core.config import settings
from app.llm import report_writer
from app.llm.schemas import Assessment, LiftJudgment, ReportDraft, Verdict


class FakeStructuredModel:
    def __init__(self, answers):
        self.answers = list(answers)
        self.calls = 0
        self.last_messages = None

    def invoke(self, messages):
        self.calls += 1
        self.last_messages = messages
        return self.answers.pop(0)


class FakeModel:
    def __init__(self, answers):
        self.structured = FakeStructuredModel(answers)

    def with_structured_output(self, schema):
        return self.structured


@pytest.fixture(autouse=True)
def no_provider_retries(monkeypatch):
    monkeypatch.setattr(settings, "llm_max_retries", 0)


def make_lift(name, status, level_now=100.0, level_before=100.0):
    return {
        "exercise": name,
        "plateau_weeks": 5,
        "confirmation": {
            "status": status, "peak": level_now, "peak_date": None, "level_now": level_now,
            "level_before": level_before, "level_change_percent": 0.0, "spike": status == "spike",
            "sessions_now": 8, "sessions_before": 8,
        },
        "prs": {"weight_pr": None, "one_rm_pr": None, "volume_pr": None, "rep_prs": []},
    }


def make_judgment(name, verdict, reason="Your repeatable 1RM stayed the same."):
    return LiftJudgment(exercise=name, verdict=verdict, assessment=Assessment.NEUTRAL,
                        reason=reason, reason_source="model")


FACTS = {
    "month": "2026-10",
    "profile": {"goal": "strength", "sex": "male", "age": 31, "training_years": 3.0},
    "bodyweight": {"start_kg": 80.0, "latest_kg": 79.0, "change_kg": -1.0},
    "consistency": {"sessions": 12, "avg_per_week": 2.8, "weeks_trained": 4, "total_weeks": 5,
                    "longest_rest_streak_days": 3},
    "notes": [],
    "lifts": [make_lift("Bench Press", "plateau"), make_lift("Deadlift", "plateau")],
}
JUDGMENTS = [make_judgment("Bench Press", Verdict.PLATEAU), make_judgment("Deadlift", Verdict.PLATEAU)]


def draft(narrative="You trained 12 times and your lifts held steady this month.",
          suggestions=("Try one small increase on the bench press.",)):
    return ReportDraft(narrative=narrative, suggestions=list(suggestions))


# ---------- the model's text ----------


def test_a_good_draft_is_kept():
    model = FakeModel([draft()])
    result = report_writer.write_report(FACTS, JUDGMENTS, model=model)

    assert result["source"] == "model"
    assert "12 times" in result["narrative"]
    assert result["suggestions"] == ["Try one small increase on the bench press."]
    assert model.structured.calls == 1


def test_an_invented_number_causes_a_second_try():
    bad = draft(narrative="You trained 40 times this month and got much stronger overall.")
    model = FakeModel([bad, draft()])

    result = report_writer.write_report(FACTS, JUDGMENTS, model=model)

    assert result["source"] == "model"
    assert "40" not in result["narrative"]
    assert model.structured.calls == 2


def test_the_second_try_is_told_what_was_wrong():
    bad = draft(narrative="Your deadlift was a confirmed spike this month, which is great news.")
    model = FakeModel([bad, draft()])

    report_writer.write_report(FACTS, JUDGMENTS, model=model)

    second_prompt = model.structured.last_messages[1][1]
    assert "rejected because" in second_prompt


def test_a_made_up_number_cannot_hide_behind_the_month():
    # the month is 2026-10, but 10 weeks is not in the facts
    bad = draft(narrative="Your bench press has not moved in 10 weeks, so it is time to change something.")
    model = FakeModel([bad, bad])

    result = report_writer.write_report(FACTS, JUDGMENTS, model=model)

    assert result["source"] == "code"


def test_a_number_in_a_suggestion_is_checked_too():
    bad = draft(suggestions=("Add 15 kg to your bench press next week.",))
    model = FakeModel([bad, bad])

    result = report_writer.write_report(FACTS, JUDGMENTS, model=model)

    assert result["source"] == "code"


def test_talking_about_a_spike_that_did_not_happen_is_rejected():
    bad = draft(narrative="Your deadlift had a big spike this month, so keep going.")
    model = FakeModel([bad, bad])

    result = report_writer.write_report(FACTS, JUDGMENTS, model=model)

    assert result["source"] == "code"


def test_a_spike_may_be_mentioned_when_a_lift_has_one():
    facts = dict(FACTS, lifts=[make_lift("Deadlift", "spike")])
    judgments = [make_judgment("Deadlift", Verdict.SPIKE)]
    model = FakeModel([draft(narrative="Your deadlift had a one-day spike that we do not count as a gain.")])

    result = report_writer.write_report(facts, judgments, model=model)

    assert result["source"] == "model"


def test_the_prompt_contains_the_judgments_and_wraps_the_notes():
    facts = dict(FACTS, notes=[{"date": "2026-10-03", "text": "Slept badly"}])
    model = FakeModel([draft()])
    report_writer.write_report(facts, JUDGMENTS, model=model)

    system_text = model.structured.last_messages[0][1]
    user_text = model.structured.last_messages[1][1]

    assert "Never change a judgment" in system_text
    assert "<notes>" in user_text and "Slept badly" in user_text
    assert "Bench Press" in user_text and "Deadlift" in user_text


# ---------- what code writes when the model fails ----------


def test_fallback_narrative_uses_the_numbers_and_the_reasons():
    text = report_writer.fallback_narrative(FACTS, JUDGMENTS)
    assert "2026-10" in text
    assert "12 times" in text
    assert "Bench Press: Your repeatable 1RM stayed the same." in text


def test_fallback_suggestions_follow_the_verdicts_present():
    judgments = [make_judgment("A", Verdict.PLATEAU), make_judgment("B", Verdict.SPIKE)]
    suggestions = report_writer.fallback_suggestions(judgments)

    assert len(suggestions) == 2
    assert suggestions[0].startswith("Repeat the weight")  # a spike is the most important
    assert "stalled" in suggestions[1]


def test_fallback_suggestions_are_never_more_than_four():
    judgments = [
        make_judgment("A", Verdict.SPIKE), make_judgment("B", Verdict.REGRESSING),
        make_judgment("C", Verdict.PLATEAU), make_judgment("D", Verdict.INSUFFICIENT_DATA),
        make_judgment("E", Verdict.CONFIRMED_GAIN),
    ]
    assert len(report_writer.fallback_suggestions(judgments)) == 4
