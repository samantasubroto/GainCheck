import datetime

import streamlit as st

from api_client import client
from session import auth_state

# Nothing below this line runs for someone who is not logged in.
auth_state.require_login()
auth_state.show_logout_button()

st.title("📝 Monthly Reports")
st.write(
    "Pick a month and we will check whether your lifts really improved, "
    "and write you a short report with suggestions."
)

# After a report was made we rerun the page, then show this message once.
done_message = st.session_state.pop("report_done", None)
if done_message:
    st.success(done_message)


def recent_months(count):
    """The current month and the months before it, as "2026-11", "2026-10", ... newest first."""
    today = datetime.date.today()
    year, month = today.year, today.month
    months = []
    for _ in range(count):
        months.append("%04d-%02d" % (year, month))
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    return months


# ---------- Which month? ----------
months = recent_months(12)
month = st.selectbox("Month", months, index=1)  # index 1: last month, which is a full month

try:
    saved_reports = auth_state.call_with_token(client.get_reports)
except client.ApiError as error:
    st.error(str(error))
    st.stop()

report_id_by_month = {r["month"]: r["id"] for r in saved_reports}
has_report = month in report_id_by_month

# ---------- Generate ----------
if has_report:
    st.caption("A report for this month already exists. Making a new one replaces it.")
button_label = "Make a new report" if has_report else "Make the report"

if st.button(button_label, type="primary"):
    try:
        with st.spinner("The language model is working. This can take a few minutes..."):
            auth_state.call_with_token(client.generate_report, month)
    except client.ApiError as error:
        st.error(str(error))
        st.stop()
    st.session_state["report_done"] = "The report for " + month + " is ready."
    st.rerun()

# ---------- Show the report for the chosen month ----------
if not has_report:
    st.info("There is no report for " + month + " yet.")
    st.stop()

try:
    report = auth_state.call_with_token(client.get_report, report_id_by_month[month])
except client.ApiError as error:
    st.error(str(error))
    st.stop()

st.divider()
st.header("Report for " + report["month"])
st.caption("Written by " + report["model_name"] + " on " + report["created_at"][:10])

# The facts, so the numbers behind the text are easy to check.
facts = report["facts"]
consistency = facts["consistency"]
bodyweight = facts["bodyweight"]
col1, col2, col3 = st.columns(3)
col1.metric("Workouts", consistency["sessions"])
col2.metric("Per week", consistency["avg_per_week"])
if bodyweight["latest_kg"] is not None:
    col3.metric("Bodyweight", str(bodyweight["latest_kg"]) + " kg", delta=f"{bodyweight['change_kg']:+.1f} kg", delta_color="off")

st.subheader("Summary")
st.write(report["narrative"])

# ---------- One card per lift ----------
st.subheader("Your lifts")

STATUS_LABELS = {
    "confirmed_gain": "Confirmed gain",
    "spike": "One-day spike",
    "plateau": "Plateau",
    "regressing": "Going backwards",
    "insufficient_data": "Not enough data",
}
ASSESSMENT_LABELS = {"good": "Good", "neutral": "Neutral", "concerning": "Concerning"}


def show_status(text, status):
    """Show a coloured box that fits the status."""
    if status == "confirmed_gain":
        st.success(text)
    elif status == "spike":
        st.warning(text)
    elif status == "regressing":
        st.error(text)
    else:
        st.info(text)


for verdict in report["verdicts"]:
    label = STATUS_LABELS.get(verdict["verdict"], verdict["verdict"])
    assessment = ASSESSMENT_LABELS.get(verdict["assessment"], verdict["assessment"])
    show_status("**" + verdict["exercise"] + "**: " + label + " (" + assessment + ")\n\n" + verdict["reason"], verdict["verdict"])

# ---------- Suggestions ----------
st.subheader("What to do next")
for suggestion in report["suggestions"]:
    st.write("- " + suggestion)

if facts.get("narrative_source") == "code":
    st.caption(
        "The language model's text did not pass our checks, so this summary was written "
        "from your numbers instead."
    )
