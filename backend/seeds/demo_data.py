"""Makes two years of realistic training and body data for a demo user.

This file uses only plain Python. It does not touch the database.
seed_demo_user.py saves what it makes.

The story the data tells (month 0 is two years ago, month 24 is today):
- Months 0 to 14: steady progress, fast at first and then slower.
- Overhead press stalls from month 9 to 17 (a plateau).
- Months 14.5 to 16.5: a rough patch (work stress). Fewer sessions, lighter weights,
  and some weight gain.
- After that: recovery, new records, and a gentle cut at the end.
- One deadlift session near the end is much stronger than normal (a one-off spike).
- Two short holidays with no training.

A fixed random seed means we get the same data every time.
"""

import datetime
import math
import random

DAYS_PER_MONTH = 30.4
MONTHS = 24

# For each exercise:
#   start, target: the strength number at month 0, and where the long-term curve is heading.
#                  For the big lifts this is the one-rep max in kg.
#                  For the small exercises (fraction 1.0) it is just the working weight.
#   sets, reps:    the usual work for one session.
#   fraction:      how much of that number we actually lift in the working sets.
LIFTS = {
    "Barbell Squat": {"start": 90.0, "target": 155.0, "sets": 3, "reps": 5, "fraction": 0.80},
    "Bench Press": {"start": 65.0, "target": 100.0, "sets": 3, "reps": 6, "fraction": 0.76},
    "Overhead Press": {"start": 42.5, "target": 62.0, "sets": 3, "reps": 6, "fraction": 0.75},
    "Triceps Pushdown": {"start": 25.0, "target": 40.0, "sets": 3, "reps": 10, "fraction": 1.0},
    "Deadlift": {"start": 110.0, "target": 185.0, "sets": 2, "reps": 5, "fraction": 0.82},
    "Barbell Row": {"start": 60.0, "target": 95.0, "sets": 3, "reps": 8, "fraction": 0.70},
    "Lat Pulldown": {"start": 45.0, "target": 65.0, "sets": 3, "reps": 10, "fraction": 1.0},
    "Barbell Curl": {"start": 20.0, "target": 32.5, "sets": 3, "reps": 10, "fraction": 1.0},
}

# Two kinds of sessions, done in turn: A, B, A, B ...
SESSION_A = ["Barbell Squat", "Bench Press", "Overhead Press", "Triceps Pushdown"]
SESSION_B = ["Deadlift", "Barbell Row", "Lat Pulldown", "Barbell Curl"]
EXERCISE_NAMES = SESSION_A + SESSION_B

TRAINING_DAYS = (0, 2, 4)  # Monday, Wednesday, Friday
HOLIDAYS = [(6.2, 7.0), (19.5, 20.2)]  # (from month, to month): no training, no weigh-ins
ROUGH_PATCH = (14.5, 16.5)

# Body weight in kg at certain months. In between, we draw a straight line.
WEIGHT_POINTS = [(0, 74.0), (12, 80.0), (14.5, 80.8), (16.5, 82.6), (18, 81.8), (24, 78.5)]


# ---------- small helpers ----------


def interpolate(points, x):
    """Read a value off a list of (x, y) points, drawing straight lines between them."""
    for i in range(len(points) - 1):
        x1, y1 = points[i]
        x2, y2 = points[i + 1]
        if x1 <= x <= x2:
            return y1 + (y2 - y1) * (x - x1) / (x2 - x1)
    return points[-1][1]


def round_to_plate(kg):
    """Round to the nearest 2.5 kg, because that is how plates work."""
    return max(2.5, round(kg / 2.5) * 2.5)


def round_to_half(value):
    """Round to the nearest 0.5, like a tape measure."""
    return round(value * 2) / 2


def clamp(value, low, high):
    return max(low, min(high, value))


def in_rough_patch(month):
    return ROUGH_PATCH[0] <= month <= ROUGH_PATCH[1]


def on_holiday(month):
    for start, end in HOLIDAYS:
        if start <= month <= end:
            return True
    return False


# ---------- how strong the person is ----------


def progress(month):
    """How far along the long-term curve we are, from 0 to 1. Fast at first, then slower."""
    return 1 - math.exp(-month / 10)


def effective_month(name, month):
    """The overhead press stalls for a while. Every other lift just follows the real month."""
    if name != "Overhead Press":
        return month
    if month <= 9:
        return month
    if month <= 17:
        return 9  # the plateau: no progress for 8 months
    return 9 + (month - 17) * 0.6  # slow progress again afterwards


def rough_patch_factor(month):
    """Strength drops about 10 percent in the rough patch, then comes back over 1.5 months."""
    if month < ROUGH_PATCH[0]:
        return 1.0
    if month <= ROUGH_PATCH[1]:
        return 0.90
    if month < ROUGH_PATCH[1] + 1.5:
        return 0.90 + 0.10 * (month - ROUGH_PATCH[1]) / 1.5
    return 1.0


def lift_strength(name, month):
    """The strength number for one exercise at one point in time."""
    lift = LIFTS[name]
    m = effective_month(name, month)
    value = lift["start"] + (lift["target"] - lift["start"]) * progress(m)
    return value * rough_patch_factor(month)


# ---------- the data ----------


def build_demo_data(today):
    """Return (workouts, body_metrics) for the two years before today.

    Each workout is a dictionary:
        {"date": date, "notes": text or None,
         "sets": [{"exercise_name": ..., "set_number": ..., "weight_kg": ..., "reps": ...}]}
    Each body metric is a dictionary:
        {"date": date, "weight_kg": ..., "waist_cm": ..., "chest_cm": ..., "arm_cm": ..., "notes": ...}
    """
    rng = random.Random(42)
    total_days = round(MONTHS * DAYS_PER_MONTH)
    start = today - datetime.timedelta(days=total_days)

    def month_of(day):
        return (day - start).days / DAYS_PER_MONTH

    # ----- workouts -----
    workouts = []
    session_count = 0
    spike_done = False
    rough_note_done = False
    back_note_done = False

    day = start
    while day <= today:
        month = month_of(day)

        if day.weekday() in TRAINING_DAYS and not on_holiday(month):
            skip_chance = 0.55 if in_rough_patch(month) else 0.12
            if rng.random() >= skip_chance:
                names = SESSION_A if session_count % 2 == 0 else SESSION_B
                session_count += 1

                notes = None
                if in_rough_patch(month) and not rough_note_done:
                    notes = "Work is crazy and I am sleeping badly. Kept it light."
                    rough_note_done = True
                elif month > ROUGH_PATCH[1] and rough_note_done and not back_note_done:
                    notes = "Back on track after a rough patch."
                    back_note_done = True

                # Some days feel a bit better or worse than others.
                day_factor = clamp(rng.gauss(1.0, 0.025), 0.94, 1.05)

                sets = []
                for name in names:
                    factor = day_factor
                    # One great day on the deadlift, which does not repeat.
                    if name == "Deadlift" and month >= 21 and not spike_done:
                        factor = 1.10
                        spike_done = True
                        notes = "Felt unreal today. Everything moved fast."

                    lift = LIFTS[name]
                    weight = round_to_plate(lift_strength(name, month) * lift["fraction"] * factor)

                    for set_number in range(1, lift["sets"] + 1):
                        reps = lift["reps"]
                        # The last set is sometimes one rep short, because of tiredness.
                        if set_number == lift["sets"] and lift["sets"] > 2 and rng.random() < 0.3:
                            reps -= 1
                        sets.append(
                            {
                                "exercise_name": name,
                                "set_number": set_number,
                                "weight_kg": weight,
                                "reps": reps,
                            }
                        )

                workouts.append({"date": day, "notes": notes, "sets": sets})

        day += datetime.timedelta(days=1)

    # ----- body metrics -----
    body_metrics = []
    last_measured = None  # (year, month) of the last time we used the tape measure
    first_entry = True
    cut_note_done = False

    day = start
    while day <= today:
        month = month_of(day)

        # A weigh-in every Monday, sometimes forgotten.
        if day.weekday() == 0 and not on_holiday(month) and rng.random() >= 0.05:
            weight = round(interpolate(WEIGHT_POINTS, month) + rng.gauss(0, 0.35), 1)

            notes = None
            if first_entry:
                notes = "Starting point."
                first_entry = False
            elif month >= 18 and not cut_note_done:
                notes = "Started cutting a little."
                cut_note_done = True

            waist = chest = arm = None
            if (day.year, day.month) != last_measured:  # measure once a month
                last_measured = (day.year, day.month)
                waist = round_to_half(78 + (weight - 74) * 1.1 + rng.gauss(0, 0.4))
                chest = round_to_half(97 + month * 0.12 + (weight - 74) * 0.3 + rng.gauss(0, 0.4))
                arm = round_to_half(33.5 + 0.1 * month - (0.5 if in_rough_patch(month) else 0) + rng.gauss(0, 0.2))

            body_metrics.append(
                {
                    "date": day,
                    "weight_kg": weight,
                    "waist_cm": waist,
                    "chest_cm": chest,
                    "arm_cm": arm,
                    "notes": notes,
                }
            )

        day += datetime.timedelta(days=1)

    return workouts, body_metrics
