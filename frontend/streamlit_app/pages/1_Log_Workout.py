import datetime

import streamlit as st

from api_client import client
from session import auth_state

st.set_page_config(page_title="Log Workout", page_icon="🏋️")

# Nothing below this line runs for someone who is not logged in.
auth_state.require_login()
auth_state.show_logout_button()

st.title("🏋️ Log Workout")

# After a successful save we rerun the page. This runs first on that rerun, before
# the widgets exist, so it is allowed to clear the notes box.
saved_message = st.session_state.pop("workout_saved", None)
if saved_message:
    st.session_state.pop("workout_notes", None)
    st.success(saved_message)

# The sets of the workout we are building. They live here until we press Save.
if "draft_sets" not in st.session_state:
    st.session_state["draft_sets"] = []


def remove_last_set():
    if st.session_state["draft_sets"]:
        st.session_state["draft_sets"].pop()


def clear_sets():
    st.session_state["draft_sets"] = []


# ---------- Load the exercise list (once per login session) ----------
if "exercises" not in st.session_state:
    try:
        st.session_state["exercises"] = auth_state.call_with_token(client.get_exercises)
    except client.ApiError as error:
        st.error(str(error))
        st.stop()

exercises = st.session_state["exercises"]
exercise_by_id = {e["id"]: e for e in exercises}

# ---------- Step 1: the day and a note ----------
today = datetime.date.today()
workout_date = st.date_input("Date", value=today, max_value=today)
notes = st.text_area("Notes (optional)", key="workout_notes", placeholder="For example: slept badly, elbow sore")

# ---------- Step 2: add sets ----------
st.subheader("Add a set")

categories = ["all"] + sorted({e["category"] for e in exercises})
category = st.selectbox("Muscle group", categories)

if category == "all":
    visible = exercises
else:
    visible = [e for e in exercises if e["category"] == category]

exercise_id = st.selectbox(
    "Exercise",
    [e["id"] for e in visible],
    format_func=lambda eid: exercise_by_id[eid]["name"],
)
chosen = exercise_by_id[exercise_id]

if chosen["is_bodyweight"]:
    st.caption("Bodyweight exercise. Use 0 kg, or the extra weight you added (belt, vest).")

weight_col, reps_col = st.columns(2)
weight_kg = weight_col.number_input("Weight (kg)", min_value=0.0, max_value=1000.0, value=20.0, step=2.5)
reps = reps_col.number_input("Reps", min_value=1, max_value=100, value=8, step=1)

if st.button("Add set"):
    if weight_kg <= 0 and not chosen["is_bodyweight"]:
        st.error(chosen["name"] + " needs a weight above 0 kg.")
    else:
        st.session_state["draft_sets"].append(
            {
                "exercise_id": chosen["id"],
                "exercise_name": chosen["name"],
                "weight_kg": float(weight_kg),
                "reps": int(reps),
            }
        )

# ---------- Step 3: review the sets and save ----------
st.subheader("This workout")
draft_sets = st.session_state["draft_sets"]

if not draft_sets:
    st.info("No sets yet. Add your first set above.")
else:
    # Number the sets for each exercise: 1, 2, 3 ... (the server does the same).
    rows = []
    counts = {}
    for s in draft_sets:
        counts[s["exercise_id"]] = counts.get(s["exercise_id"], 0) + 1
        rows.append(
            {
                "Exercise": s["exercise_name"],
                "Set": counts[s["exercise_id"]],
                "Weight (kg)": s["weight_kg"],
                "Reps": s["reps"],
            }
        )
    st.table(rows)

    left, right = st.columns(2)
    left.button("Remove last set", on_click=remove_last_set)
    right.button("Clear all sets", on_click=clear_sets)

    if st.button("Save workout", type="primary"):
        data = {
            "date": workout_date.isoformat(),
            "notes": notes.strip() or None,
            "sets": [
                {"exercise_id": s["exercise_id"], "weight_kg": s["weight_kg"], "reps": s["reps"]}
                for s in draft_sets
            ],
        }
        try:
            result = auth_state.call_with_token(client.create_workout, data)
        except client.ApiError as error:
            st.error(str(error))
        else:
            # If the workout has more sets than we sent, it already existed for this day.
            if len(result["sets"]) > len(draft_sets):
                message = "Added to your workout for " + result["date"] + "."
            else:
                message = "Workout saved!"
            st.session_state["draft_sets"] = []
            st.session_state["workout_saved"] = message
            st.rerun()

# ---------- Past workouts ----------
st.divider()
st.subheader("Recent workouts")

try:
    workouts = auth_state.call_with_token(client.get_workouts)
except client.ApiError as error:
    st.error(str(error))
    st.stop()

if not workouts:
    st.write("Nothing logged yet.")

def count_text(number, word):
    """3, "set" -> "3 sets".  1, "set" -> "1 set"."""
    if number == 1:
        return str(number) + " " + word
    return str(number) + " " + word + "s"


def group_by_exercise(sets):
    """Turn a flat list of sets into {exercise name: [its sets]}.

    A dictionary keeps the order we put things in, so the exercises stay
    in the order they were done.
    """
    groups = {}
    for s in sets:
        groups.setdefault(s["exercise_name"], []).append(s)
    return groups


for workout in workouts:
    groups = group_by_exercise(workout["sets"])

    # The header shows the totals, so you do not need to open it.
    label = (
        workout["date"]
        + "  ·  "
        + count_text(len(groups), "exercise")
        + "  ·  "
        + count_text(len(workout["sets"]), "set")
    )

    with st.expander(label):
        if workout["notes"]:
            st.write("Notes: " + workout["notes"])

        # One small table per exercise.
        for exercise_name, exercise_sets in groups.items():
            st.markdown("**" + exercise_name + "**")
            st.table(
                [
                    {
                        "Set": s["set_number"],
                        "Weight (kg)": s["weight_kg"],
                        "Reps": s["reps"],
                    }
                    for s in exercise_sets
                ]
            )
