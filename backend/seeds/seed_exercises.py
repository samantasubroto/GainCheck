"""Adds the default list of exercises to the database.

Run it from the backend folder:

    python -m seeds.seed_exercises

It is safe to run more than once. Exercises that already exist are skipped.
"""

import app.db.models  # noqa: F401  (loads all the models)
from app.db.models.exercise import Exercise
from app.db.session import SessionLocal

# (name, category, is_bodyweight)
# Bodyweight exercises can be logged with 0 kg of extra weight.
EXERCISES = [
    # Legs
    ("Barbell Squat", "legs", False),
    ("Front Squat", "legs", False),
    ("Romanian Deadlift", "legs", False),
    ("Leg Press", "legs", False),
    ("Dumbbell Lunge", "legs", False),
    ("Leg Curl", "legs", False),
    ("Leg Extension", "legs", False),
    ("Standing Calf Raise", "legs", False),
    ("Seated Calf Raise", "legs", False),
    ("Bulgarian Split Squat", "legs", False),
    ("Walking Lunge", "legs", False),
    ("Goblet Squat", "legs", False),
    ("Hack Squat", "legs", False),
    ("Hip Thrust", "legs", False),
    ("Glute Bridge", "legs", True),
    ("Sumo Deadlift", "legs", False),
    ("Stiff-Leg Deadlift", "legs", False),
    ("Step-Up", "legs", False),
    ("Hip Abduction Machine", "legs", False),
    ("Hip Adduction Machine", "legs", False),
    ("Good Morning", "legs", False),
    ("Bodyweight Squat", "legs", True),
    ("Pistol Squat", "legs", True),
    ("Nordic Hamstring Curl", "legs", True),

    # Push
    ("Bench Press", "push", False),
    ("Incline Bench Press", "push", False),
    ("Dumbbell Bench Press", "push", False),
    ("Overhead Press", "push", False),
    ("Dips", "push", True),
    ("Push-Up", "push", True),
    ("Triceps Pushdown", "push", False),
    ("Decline Bench Press", "push", False),
    ("Incline Dumbbell Press", "push", False),
    ("Dumbbell Shoulder Press", "push", False),
    ("Arnold Press", "push", False),
    ("Push Press", "push", False),
    ("Dumbbell Fly", "push", False),
    ("Cable Fly", "push", False),
    ("Pec Deck", "push", False),
    ("Chest Press Machine", "push", False),
    ("Lateral Raise", "push", False),
    ("Front Raise", "push", False),
    ("Overhead Triceps Extension", "push", False),
    ("Skull Crusher", "push", False),
    ("Close-Grip Bench Press", "push", False),
    ("Diamond Push-Up", "push", True),
    ("Pike Push-Up", "push", True),
    ("Bench Dips", "push", True),
    ("Landmine Press", "push", False),

    # Pull
    ("Deadlift", "pull", False),
    ("Barbell Row", "pull", False),
    ("Pull-Up", "pull", True),
    ("Chin-Up", "pull", True),
    ("Lat Pulldown", "pull", False),
    ("Seated Cable Row", "pull", False),
    ("Barbell Curl", "pull", False),
    ("Face Pull", "pull", False),
    ("Dumbbell Row", "pull", False),
    ("T-Bar Row", "pull", False),
    ("Pendlay Row", "pull", False),
    ("Chest-Supported Row", "pull", False),
    ("Inverted Row", "pull", True),
    ("Straight-Arm Pulldown", "pull", False),
    ("Rack Pull", "pull", False),
    ("Dumbbell Shrug", "pull", False),
    ("Barbell Shrug", "pull", False),
    ("Rear Delt Fly", "pull", False),
    ("Reverse Pec Deck", "pull", False),
    ("Dumbbell Curl", "pull", False),
    ("Hammer Curl", "pull", False),
    ("Preacher Curl", "pull", False),
    ("Incline Dumbbell Curl", "pull", False),
    ("Cable Curl", "pull", False),
    ("Concentration Curl", "pull", False),
    ("Neutral-Grip Pull-Up", "pull", True),

    # Core
    ("Hanging Leg Raise", "core", True),
    ("Plank", "core", True),
    ("Side Plank", "core", True),
    ("Crunch", "core", True),
    ("Sit-Up", "core", True),
    ("Russian Twist", "core", True),
    ("Bicycle Crunch", "core", True),
    ("Mountain Climber", "core", True),
    ("Dead Bug", "core", True),
    ("Bird Dog", "core", True),
    ("Hollow Body Hold", "core", True),
    ("V-Up", "core", True),
    ("Toes-to-Bar", "core", True),
    ("Ab Wheel Rollout", "core", True),
    ("Cable Crunch", "core", False),
    ("Cable Woodchopper", "core", False),
    ("Pallof Press", "core", False),
    ("Weighted Sit-Up", "core", False),
    ("Decline Sit-Up", "core", False),
    ("Back Extension", "core", True),
]


def seed():
    db = SessionLocal()
    added = 0

    for name, category, is_bodyweight in EXERCISES:
        already_there = db.query(Exercise).filter(Exercise.name == name).first()
        if already_there is None:
            db.add(Exercise(name=name, category=category, is_bodyweight=is_bodyweight))
            added += 1

    db.commit()
    db.close()
    print("Added", added, "exercises. Skipped", len(EXERCISES) - added, "that already existed.")


if __name__ == "__main__":
    seed()
