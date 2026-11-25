"""Workout logic that uses more than one repository."""

from app.repositories import exercise_repository, workout_repository


def create_workout(db, user_id, data):
    """Check the sets, number them, and save them.

    A user has one workout per day. If there is already a workout for this date,
    the new sets are added to it. Otherwise a new workout is created.

    data is a WorkoutCreate object. Raises ValueError with a message
    the user can read if something is wrong.
    """
    exercises = {}  # exercise_id -> Exercise, so we load each one only once
    set_counts = {}  # exercise_id -> highest set number so far
    sets_data = []

    # Is there already a workout on this day? Then new sets continue its numbering.
    existing = workout_repository.get_for_user_on_date(db, user_id, data.date)
    if existing is not None:
        for old_set in existing.sets:
            highest = set_counts.get(old_set.exercise_id, 0)
            set_counts[old_set.exercise_id] = max(highest, old_set.set_number)

    for new_set in data.sets:
        exercise_id = new_set.exercise_id

        if exercise_id not in exercises:
            exercise = exercise_repository.get_by_id(db, exercise_id)
            if exercise is None:
                raise ValueError("Unknown exercise (id " + str(exercise_id) + ").")
            exercises[exercise_id] = exercise
        exercise = exercises[exercise_id]

        # A bench press with 0 kg is almost certainly a typo.
        if new_set.weight_kg <= 0 and not exercise.is_bodyweight:
            raise ValueError(exercise.name + " needs a weight above 0 kg.")

        # The server numbers the sets: 1, 2, 3 ... for each exercise.
        set_counts[exercise_id] = set_counts.get(exercise_id, 0) + 1
        sets_data.append(
            {
                "exercise_id": exercise_id,
                "set_number": set_counts[exercise_id],
                "weight_kg": new_set.weight_kg,
                "reps": new_set.reps,
            }
        )

    if existing is None:
        return workout_repository.create(db, user_id, data.date, data.notes, sets_data)
    return workout_repository.add_sets(db, existing, data.notes, sets_data)


def workout_to_dict(session):
    """Turn a database workout into a plain dictionary for the response.

    We do this by hand because the response needs the exercise name,
    which lives on the exercise and not on the set.
    """
    # Group the sets by exercise, in the order the exercises were first done.
    first_seen = {}
    for s in session.sets:
        if s.exercise_id not in first_seen:
            first_seen[s.exercise_id] = len(first_seen)
    ordered_sets = sorted(session.sets, key=lambda s: (first_seen[s.exercise_id], s.set_number))

    return {
        "id": session.id,
        "date": session.date,
        "notes": session.notes,
        "sets": [
            {
                "id": s.id,
                "exercise_id": s.exercise_id,
                "exercise_name": s.exercise.name,
                "set_number": s.set_number,
                "weight_kg": s.weight_kg,
                "reps": s.reps,
            }
            for s in ordered_sets
        ],
    }
