"""Estimate the one-rep max (1RM): the most weight you could lift for a single rep.

Almost nobody tests a true 1RM, so we estimate it from a normal set.
We use the Epley formula:  1RM = weight x (1 + reps / 30)
Example: 100 kg for 5 reps  ->  100 x (1 + 5/30) = 116.7 kg
"""

# The estimate gets unreliable for long sets (a set of 20 mostly measures stamina).
# Sets with more reps than this are ignored.
MAX_REPS_FOR_ESTIMATE = 10


def estimate_one_rm(weight_kg, reps):
    """Estimated 1RM in kg for one set, or None if the set cannot be used.

    A set cannot be used when there is no weight (a bodyweight set with 0 kg),
    no reps, or too many reps.
    """
    if weight_kg <= 0 or reps < 1 or reps > MAX_REPS_FOR_ESTIMATE:
        return None

    if reps == 1:
        return weight_kg  # a single rep already is a 1RM

    return weight_kg * (1 + reps / 30)


def best_one_rm(sets):
    """The highest estimated 1RM among a list of sets, or None if no set can be used.

    Each set is a dictionary like {"weight_kg": 100.0, "reps": 5}.
    """
    best = None
    for s in sets:
        estimate = estimate_one_rm(s["weight_kg"], s["reps"])
        if estimate is None:
            continue
        if best is None or estimate > best:
            best = estimate
    return best
