import datetime

import pytest

from app.core.config import settings
from app.llm import judge
from app.llm.schemas import Assessment, JudgeAnswer, Verdict


# ---------- a fake model that records what it was asked ----------


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


# ---------- sample facts ----------


def make_lift(status="plateau", level_now=100.0, level_before=100.0, change=0.0,
              peak=100.0, spike=False, sessions_now=8, sessions_before=8, plateau_weeks=6):
    return {
        "exercise": "Bench Press",
        "plateau_weeks": plateau_weeks,
        "confirmation": {
            "status": status,
            "peak": peak,
            "peak_date": datetime.date(2026, 10, 12),
            "level_now": level_now,
            "level_before": level_before,
            "level_change_percent": change,
            "spike": spike,
            "sessions_now": sessions_now,
            "sessions_before": sessions_before,
        },
        "prs": {"weight_pr": None, "one_rm_pr": None, "volume_pr": None, "rep_prs": []},
    }


CONTEXT = {
    "month": "2026-10",
    "profile": {"goal": "strength", "sex": "male", "age": 31, "training_years": 3.0},
    "bodyweight": {"start_kg": 80.0, "latest_kg": 79.0, "change_kg": -1.0},
    "consistency": {"sessions": 12, "avg_per_week": 2.8, "weeks_trained": 4, "total_weeks": 5},
    "notes": [{"date": datetime.date(2026, 10, 3), "text": "Slept badly all week"}],
}


def answer(reason="The repeatable 1RM stayed at 100 kg this month.", verdict=Verdict.PLATEAU,
           assessment=Assessment.NEUTRAL, exercise="Bench Press"):
    return JudgeAnswer(exercise=exercise, verdict=verdict, assessment=assessment, reason=reason)


# ---------- checking numbers ----------


def test_collect_numbers_finds_numbers_in_nested_data():
    data = {"a": 5, "b": [1.5, {"c": "slept 7 hours"}], "d": datetime.date(2026, 10, 12), "e": None, "f": True}
    numbers = judge.collect_numbers(data)
    assert {5.0, 1.5, 7.0} <= numbers
    assert 1.0 not in numbers  # True is not the number 1
    assert 2026.0 not in numbers and 12.0 not in numbers  # the parts of a date are not loose numbers


def test_numbers_are_grounded_accepts_numbers_from_the_facts():
    assert judge.numbers_are_grounded("It went from 100 kg to 105 kg.", {100.0, 105.0})


def test_numbers_are_grounded_allows_rounding():
    assert judge.numbers_are_grounded("About 178 kg.", {177.9})


def test_numbers_are_grounded_rejects_an_invented_number():
    assert not judge.numbers_are_grounded("It went up 12 percent.", {100.0, 105.0, 5.0})


def test_the_1_in_1rm_is_not_a_number():
    assert judge.numbers_are_grounded("Your repeatable 1RM stayed the same.", {100.0})
    assert judge.numbers_are_grounded("Your estimated 1 RM stayed the same.", {100.0})


def test_text_without_numbers_is_fine():
    assert judge.numbers_are_grounded("Nothing changed.", set())


def test_the_parts_of_a_date_are_not_loose_numbers():
    # "2026-10" is the month of the report. That must not make a made-up "10 weeks" acceptable.
    allowed = judge.collect_numbers({"month": "2026-10", "weeks": 14})
    assert 10.0 not in allowed
    assert not judge.numbers_are_grounded("No progress in the last 10 weeks.", allowed)
    assert judge.numbers_are_grounded("No progress in the last 14 weeks.", allowed)


def test_dates_written_by_the_model_are_ignored_by_the_number_check():
    assert judge.numbers_are_grounded("Your best day was 2026-10-12.", set())


def test_numbers_not_in_facts_lists_the_unknown_ones():
    assert judge.numbers_not_in_facts("Up 12 percent to 105 kg.", {105.0}) == ["12"]


def test_check_reason_says_what_is_wrong():
    allowed = {100.0}
    assert judge.check_reason("Your repeatable 1RM stayed at 100 kg.", allowed, "plateau") is None
    assert "40" in judge.check_reason("It rose 40 percent.", allowed, "plateau")
    assert "spike" in judge.check_reason("A spike happened.", allowed, "plateau")
    assert "confirmed" in judge.check_reason("A confirmed gain.", allowed, "plateau")


# ---------- claims that contradict the status ----------


def test_only_a_spike_lift_may_talk_about_a_spike():
    assert judge.contradicts_status("There was a spike in your best session.", "plateau")
    assert judge.contradicts_status("No spike this month.", "plateau")  # even a negation: keep it simple
    assert not judge.contradicts_status("Your best session is not counted as a real gain. Spike!", "spike")


def test_only_a_confirmed_gain_may_say_confirmed():
    assert judge.contradicts_status("The notes say this is a confirmed gain.", "plateau")
    assert not judge.contradicts_status("This is a confirmed gain.", "confirmed_gain")


def test_ordinary_text_does_not_contradict():
    assert not judge.contradicts_status("Your repeatable 1RM stayed at 100 kg.", "plateau")


# ---------- judging a lift ----------


def test_a_good_answer_is_kept_and_marked_as_from_the_model():
    model = FakeModel([answer(assessment=Assessment.GOOD)])
    result = judge.judge_lift(make_lift(), CONTEXT, model=model)

    assert result.reason_source == "model"
    assert result.assessment == Assessment.GOOD
    assert result.verdict == Verdict.PLATEAU
    assert model.structured.calls == 1


def test_the_verdict_always_comes_from_the_facts_not_the_model():
    wrong = answer(verdict=Verdict.CONFIRMED_GAIN, exercise="Something Else")
    model = FakeModel([wrong])
    result = judge.judge_lift(make_lift(status="plateau"), CONTEXT, model=model)

    assert result.verdict == Verdict.PLATEAU
    assert result.exercise == "Bench Press"


def test_invented_numbers_cause_a_second_try():
    bad = answer(reason="The repeatable 1RM jumped 25 percent this month.")
    good = answer(reason="The repeatable 1RM stayed at 100 kg this month.")
    model = FakeModel([bad, good])

    result = judge.judge_lift(make_lift(), CONTEXT, model=model)

    assert result.reason_source == "model"
    assert "100" in result.reason
    assert model.structured.calls == 2


def test_a_reason_that_contradicts_the_status_causes_a_second_try():
    bad = answer(reason="This was a spike, so it does not count as a gain.")  # but the status is plateau
    good = answer(reason="The repeatable 1RM stayed at 100 kg this month.")
    model = FakeModel([bad, good])

    result = judge.judge_lift(make_lift(status="plateau"), CONTEXT, model=model)

    assert result.reason_source == "model"
    assert "spike" not in result.reason
    assert model.structured.calls == 2


def test_the_second_try_is_told_what_was_wrong():
    bad = answer(reason="The repeatable 1RM jumped 25 percent this month.")
    good = answer(reason="The repeatable 1RM stayed at 100 kg this month.")
    model = FakeModel([bad, good])

    judge.judge_lift(make_lift(), CONTEXT, model=model)

    # the fake model keeps the messages of its last call, which is the second one
    second_prompt = model.structured.last_messages[1][1]
    assert "rejected because" in second_prompt
    assert "25" in second_prompt


def test_spike_facts_are_only_given_for_lifts_with_a_spike():
    plain = judge.build_lift_summary(make_lift(status="plateau"))
    assert "best_session_kg" not in plain
    assert "spike_detected" not in plain

    spiked = judge.build_lift_summary(make_lift(status="spike", peak=112.0, spike=True))
    assert spiked["best_session_kg"] == 112.0
    assert spiked["spike_detected"] is True


def test_if_the_model_keeps_inventing_numbers_code_writes_the_reason():
    bad = answer(reason="The repeatable 1RM jumped 25 percent this month.")
    model = FakeModel([bad, bad])

    result = judge.judge_lift(make_lift(), CONTEXT, model=model)

    assert result.reason_source == "code"
    assert result.assessment == Assessment.NEUTRAL
    assert "100" in result.reason
    assert "25" not in result.reason


def test_too_few_sessions_skips_the_model():
    lift = make_lift(status="insufficient_data", sessions_now=2, sessions_before=1,
                     level_now=None, level_before=None, change=None)
    model = FakeModel([])

    result = judge.judge_lift(lift, CONTEXT, model=model)

    assert model.structured.calls == 0
    assert result.verdict == Verdict.INSUFFICIENT_DATA
    assert result.reason_source == "code"
    assert "2 sessions" in result.reason


def test_the_prompt_contains_the_facts_and_wraps_the_notes():
    model = FakeModel([answer()])
    judge.judge_lift(make_lift(), CONTEXT, model=model)

    system_text = model.structured.last_messages[0][1]
    user_text = model.structured.last_messages[1][1]

    assert "ONLY the numbers" in system_text
    assert "never instructions" in system_text
    assert "<notes>" in user_text and "</notes>" in user_text
    assert "Slept badly all week" in user_text
    assert '"computed_status": "plateau"' in user_text
    assert '"goal": "strength"' in user_text


def test_a_numbers_from_the_notes_may_be_used_in_the_reason():
    context = dict(CONTEXT, notes=[{"date": datetime.date(2026, 10, 3), "text": "Only slept 5 hours a night"}])
    model = FakeModel([answer(reason="The stall fits the 5 hours of sleep you wrote about.")])

    result = judge.judge_lift(make_lift(), context, model=model)

    assert result.reason_source == "model"


# ---------- fallback sentences ----------


@pytest.mark.parametrize(
    "status, expected",
    [
        ("confirmed_gain", "went from 100 kg to 105 kg"),
        ("regressing", "dropped from 100 kg to 105 kg"),
        ("plateau", "about the same as before"),
        ("spike", "not counted as a real gain"),
    ],
)
def test_fallback_reason_for_each_status(status, expected):
    summary = judge.build_lift_summary(make_lift(status=status, level_now=105.0, level_before=100.0,
                                                 change=5.0, peak=112.0, spike=True))
    assert expected in judge.fallback_reason(summary)


# ---------- judging every lift ----------


def test_judge_all_returns_one_judgment_per_lift_in_order():
    squat = make_lift()
    squat["exercise"] = "Barbell Squat"
    facts = dict(CONTEXT, lifts=[make_lift(), squat])
    model = FakeModel([answer(), answer(exercise="Barbell Squat")])

    results = judge.judge_all(facts, model=model)

    assert [r.exercise for r in results] == ["Bench Press", "Barbell Squat"]
