"""The whole report flow against a temporary database, with a fake language model.

It uses the demo data, so it checks the real path: database -> facts -> judge -> writer -> saved report.
"""

import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.db.models  # noqa: F401  (loads all the models)
from app.db.base import Base
from app.db.models.body_metric import BodyMetric
from app.db.models.exercise import Exercise
from app.db.models.report import Report
from app.db.models.user import User
from app.db.models.workout import WorkoutSession, WorkoutSet
from app.llm.schemas import Assessment, JudgeAnswer, ReportDraft, Verdict
from app.repositories import report_repository
from app.services import report_service
from seeds import demo_data

TODAY = datetime.date(2026, 11, 27)


class FakeStructuredModel:
    def __init__(self, schema):
        self.schema = schema

    def invoke(self, messages):
        if self.schema is JudgeAnswer:
            return JudgeAnswer(
                exercise="whatever", verdict=Verdict.PLATEAU, assessment=Assessment.NEUTRAL,
                reason="Your repeatable 1RM is about the same as before.",
            )
        return ReportDraft(
            narrative="You trained steadily this month and kept your main lifts going.",
            suggestions=["Keep logging every set.", "Repeat your best weights before adding more."],
        )


class FakeModel:
    def with_structured_output(self, schema):
        return FakeStructuredModel(schema)


@pytest.fixture
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()

    exercise_ids = {}
    for name in demo_data.EXERCISE_NAMES:
        exercise = Exercise(name=name, category="test", is_bodyweight=False)
        session.add(exercise)
        session.flush()
        exercise_ids[name] = exercise.id

    session.add(User(uid="u1", email="u1@example.com", sex="male", birth_year=1995,
                     height_cm=178.0, training_years=3.0, goal="strength"))
    session.add(User(uid="u2", email="u2@example.com"))  # a user with no data

    workouts, body_metrics = demo_data.build_demo_data(TODAY)
    for workout in workouts:
        workout_session = WorkoutSession(user_id="u1", date=workout["date"], notes=workout["notes"])
        for s in workout["sets"]:
            workout_session.sets.append(WorkoutSet(
                exercise_id=exercise_ids[s["exercise_name"]], set_number=s["set_number"],
                weight_kg=s["weight_kg"], reps=s["reps"],
            ))
        session.add(workout_session)
    for entry in body_metrics:
        session.add(BodyMetric(user_id="u1", **entry))

    session.commit()
    yield session
    session.close()


def user(db, uid):
    return db.query(User).filter(User.uid == uid).first()


def test_a_report_is_made_and_saved(db):
    report = report_service.generate_report(db, user(db, "u1"), "2026-10", today=TODAY, model=FakeModel())

    assert report.month == "2026-10"
    assert report.user_id == "u1"
    assert report.narrative.startswith("You trained steadily")
    assert len(report.suggestions) == 2
    assert report.model_name.startswith("ollama:") or report.model_name.startswith("openai:")

    verdicts = {v["exercise"]: v["verdict"] for v in report.verdicts}
    assert set(verdicts) == {"Barbell Squat", "Bench Press", "Deadlift", "Overhead Press", "Barbell Row"}
    # the verdicts come from our calculations, whatever the fake model said
    assert verdicts["Deadlift"] == "spike"
    assert verdicts["Overhead Press"] == "plateau"


def test_the_saved_facts_are_plain_json(db):
    report = report_service.generate_report(db, user(db, "u1"), "2026-10", today=TODAY, model=FakeModel())

    assert report.facts["period_start"] == "2026-10-01"
    assert report.facts["period_end"] == "2026-10-31"
    assert report.facts["profile"]["goal"] == "strength"
    assert report.facts["profile"]["age"] == 31
    assert report.facts["consistency"]["sessions"] > 0
    assert len(report.facts["lifts"]) == 5


def test_making_the_report_again_replaces_it(db):
    first = report_service.generate_report(db, user(db, "u1"), "2026-10", today=TODAY, model=FakeModel())
    second = report_service.generate_report(db, user(db, "u1"), "2026-10", today=TODAY, model=FakeModel())

    assert second.id == first.id
    assert db.query(Report).count() == 1


def test_different_months_are_different_reports(db):
    report_service.generate_report(db, user(db, "u1"), "2026-09", today=TODAY, model=FakeModel())
    report_service.generate_report(db, user(db, "u1"), "2026-10", today=TODAY, model=FakeModel())

    months = [r.month for r in report_repository.list_for_user(db, "u1")]
    assert months == ["2026-10", "2026-09"]  # newest first


def test_one_user_cannot_read_another_users_report(db):
    report = report_service.generate_report(db, user(db, "u1"), "2026-10", today=TODAY, model=FakeModel())

    assert report_repository.get_for_user(db, "u1", report.id) is not None
    assert report_repository.get_for_user(db, "u2", report.id) is None
    assert report_repository.list_for_user(db, "u2") == []


def test_a_user_with_no_workouts_gets_a_clear_error(db):
    with pytest.raises(ValueError) as error:
        report_service.generate_report(db, user(db, "u2"), "2026-10", today=TODAY, model=FakeModel())
    assert "nothing to report" in str(error.value)


def test_a_future_month_is_rejected(db):
    with pytest.raises(ValueError):
        report_service.generate_report(db, user(db, "u1"), "2027-01", today=TODAY, model=FakeModel())


def test_workout_notes_reach_the_facts(db):
    # the demo data has a note on 2026-08-31? no, but it has one in February 2026
    report = report_service.generate_report(db, user(db, "u1"), "2026-02", today=TODAY, model=FakeModel())
    texts = " ".join(note["text"] for note in report.facts["notes"])
    assert "sleeping badly" in texts
