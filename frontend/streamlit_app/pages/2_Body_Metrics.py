import datetime

import streamlit as st

from api_client import client
from session import auth_state

st.set_page_config(page_title="Body Metrics", page_icon="📏")

# Nothing below this line runs for someone who is not logged in.
auth_state.require_login()
auth_state.show_logout_button()

st.title("📏 Body Metrics")

# After a successful save we rerun the page. This runs first on that rerun, before
# the widgets exist, so it is allowed to clear the notes box.
if st.session_state.pop("metric_saved", False):
    st.session_state.pop("metric_notes", None)
    st.success("Saved!")

# ---------- Load the saved entries (newest first) ----------
try:
    entries = auth_state.call_with_token(client.get_body_metrics)
except client.ApiError as error:
    st.error(str(error))
    st.stop()

# Start the weight box at your latest weight, so you only have to change a little.
if entries:
    default_weight = entries[0]["weight_kg"]
else:
    default_weight = 70.0

# ---------- The form ----------
st.subheader("Log your measurements")
st.caption("Only the weight is required. Leave a measurement at 0 if you did not measure it.")

today = datetime.date.today()
with st.form("body_form"):
    entry_date = st.date_input("Date", value=today, max_value=today)
    weight_kg = st.number_input("Weight (kg)", min_value=20.0, max_value=400.0, value=float(default_weight), step=0.1)

    waist_col, chest_col, arm_col = st.columns(3)
    waist_cm = waist_col.number_input("Waist (cm)", min_value=0.0, max_value=250.0, value=0.0, step=0.5)
    chest_cm = chest_col.number_input("Chest (cm)", min_value=0.0, max_value=250.0, value=0.0, step=0.5)
    arm_cm = arm_col.number_input("Arm (cm)", min_value=0.0, max_value=100.0, value=0.0, step=0.5)

    notes = st.text_area("Notes (optional)", key="metric_notes", placeholder="For example: started a cut, fasted")
    submitted = st.form_submit_button("Save")

if submitted:
    # A measurement left at 0 means "not measured", so we send nothing for it.
    data = {
        "date": entry_date.isoformat(),
        "weight_kg": float(weight_kg),
        "waist_cm": float(waist_cm) if waist_cm > 0 else None,
        "chest_cm": float(chest_cm) if chest_cm > 0 else None,
        "arm_cm": float(arm_cm) if arm_cm > 0 else None,
        "notes": notes.strip() or None,
    }
    try:
        auth_state.call_with_token(client.save_body_metric, data)
    except client.ApiError as error:
        st.error(str(error))
    else:
        st.session_state["metric_saved"] = True
        st.rerun()

# ---------- Chart ----------
st.divider()
st.subheader("Progress")

if not entries:
    st.info("No entries yet. Log your first measurements above.")
    st.stop()

MEASURES = {
    "Weight (kg)": "weight_kg",
    "Waist (cm)": "waist_cm",
    "Chest (cm)": "chest_cm",
    "Arm (cm)": "arm_cm",
}
chosen_label = st.selectbox("Show", list(MEASURES.keys()))
chosen_field = MEASURES[chosen_label]

# Keep only the days where this measurement exists, oldest first.
points = [e for e in reversed(entries) if e[chosen_field] is not None]

if len(points) < 2:
    st.caption("Log at least two days of " + chosen_label.lower() + " to see a chart.")
else:
    st.line_chart(
        {
            "Date": [datetime.date.fromisoformat(p["date"]) for p in points],
            chosen_label: [p[chosen_field] for p in points],
        },
        x="Date",
        y=chosen_label,
    )

# ---------- History ----------
st.subheader("Recent entries")


def show(value):
    """Print a number without extra zeros (80.0 -> 80, 80.5 -> 80.5). Empty -> a dash."""
    if value is None:
        return "-"
    return f"{value:g}"


st.table(
    [
        {
            "Date": e["date"],
            "Weight (kg)": show(e["weight_kg"]),
            "Waist (cm)": show(e["waist_cm"]),
            "Chest (cm)": show(e["chest_cm"]),
            "Arm (cm)": show(e["arm_cm"]),
            "Notes": e["notes"] or "-",
        }
        for e in entries[:14]
    ]
)
if len(entries) > 14:
    st.caption("Showing the latest 14 of " + str(len(entries)) + " entries.")
