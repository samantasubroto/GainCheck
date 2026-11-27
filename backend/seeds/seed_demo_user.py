"""Creates a demo user with two years of workouts and body measurements.

Run it from the backend folder:

    python -m seeds.seed_demo_user

What it does:
1. Makes sure the demo account exists in Firebase (it signs up, or logs in if it exists).
2. Fills in the demo user's profile.
3. Deletes any workouts and body metrics the DEMO user already has, then saves fresh ones.
   Other users are never touched, so it is safe to run again.

Run "python -m seeds.seed_exercises" first, because the workouts use those exercises.

Log in to the app with the email and password below to see the demo data.
This is a real account in your Firebase project, so delete it in the Firebase
console (Authentication, Users) if you ever put the app online.
"""

import datetime

import app.db.models  # noqa: F401  (loads all the models)
from app.auth import firebase_client
from app.db.models.body_metric import BodyMetric
from app.db.models.exercise import Exercise
from app.db.models.workout import WorkoutSession, WorkoutSet
from app.db.session import SessionLocal
from app.repositories import user_repository
from seeds import demo_data

DEMO_EMAIL = "demo.lifter@example.com"
DEMO_PASSWORD = "Demo1234!"

DEMO_PROFILE = {
    "display_name": "Demo Lifter",
    "sex": "male",
    "birth_year": 1995,
    "height_cm": 178.0,
    "training_years": 3.0,
    "goal": "strength",
}


def get_demo_account():
    """Return the demo account's (uid, email). Create the account if it does not exist."""
    try:
        result = firebase_client.signup(DEMO_EMAIL, DEMO_PASSWORD)
        print("Created the demo account in Firebase.")
    except firebase_client.FirebaseAuthError as error:
        if str(error) != "EMAIL_EXISTS":
            raise
        result = firebase_client.login(DEMO_EMAIL, DEMO_PASSWORD)
        print("The demo account already exists in Firebase.")
    return result["uid"], result["email"]


def seed():
    uid, email = get_demo_account()
    db = SessionLocal()

    # The user row and the profile.
    user = user_repository.get_or_create(db, uid, email)
    user_repository.update(db, user, DEMO_PROFILE)

    # Look up the exercise ids by name.
    exercise_ids = {}
    for name in demo_data.EXERCISE_NAMES:
        exercise = db.query(Exercise).filter(Exercise.name == name).first()
        if exercise is None:
            db.close()
            raise SystemExit(
                "The exercise '" + name + "' is missing. Run: python -m seeds.seed_exercises"
            )
        exercise_ids[name] = exercise.id

    # Remove the demo user's old data (only this user's).
    for old_session in db.query(WorkoutSession).filter(WorkoutSession.user_id == uid).all():
        db.delete(old_session)  # this also deletes the sets of the session
    db.query(BodyMetric).filter(BodyMetric.user_id == uid).delete()
    db.commit()

    workouts, body_metrics = demo_data.build_demo_data(datetime.date.today())

    for workout in workouts:
        session = WorkoutSession(user_id=uid, date=workout["date"], notes=workout["notes"])
        for s in workout["sets"]:
            session.sets.append(
                WorkoutSet(
                    exercise_id=exercise_ids[s["exercise_name"]],
                    set_number=s["set_number"],
                    weight_kg=s["weight_kg"],
                    reps=s["reps"],
                )
            )
        db.add(session)

    for entry in body_metrics:
        db.add(BodyMetric(user_id=uid, **entry))

    db.commit()
    db.close()

    total_sets = sum(len(w["sets"]) for w in workouts)
    print("Saved", len(workouts), "workouts with", total_sets, "sets, and", len(body_metrics), "body entries.")
    print("Log in with:", DEMO_EMAIL, "/", DEMO_PASSWORD)


if __name__ == "__main__":
    seed()
