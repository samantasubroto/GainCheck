import datetime

import streamlit as st

from api_client import client
from session import auth_state

st.set_page_config(page_title="Progress", page_icon="📈")

# Nothing below this line runs for someone who is not logged in.
auth_state.require_login()
auth_state.show_logout_button()

st.title("📈 Progress")

PERIODS = {
    "Last 30 days": 30,
    "Last 3 months": 90,
    "Last 6 months": 180,
    "Last year": 365,
}
choice = st.selectbox("Period", list(PERIODS.keys()), index=1)
days = PERIODS[choice]

try:
    progress = auth_state.call_with_token(client.get_progress, days)
except client.ApiError as error:
    st.error(str(error))
    st.stop()

st.caption(
    "From " + progress["period_start"] + " to " + progress["period_end"]
    + ". Changes are compared with the "
    + str(days) + " days before."
)

# ---------- Consistency and bodyweight ----------
st.subheader("Consistency")
c = progress["consistency"]
col1, col2, col3, col4 = st.columns(4)
col1.metric("Workouts", c["sessions"])
col2.metric("Per week", c["avg_per_week"])
col3.metric("Weeks trained", str(c["weeks_trained"]) + " of " + str(c["total_weeks"]))
col4.metric("Longest break", str(c["longest_rest_streak_days"]) + " days")

body = progress["bodyweight"]
if body["latest_kg"] is not None:
    st.metric(
        "Bodyweight",
        str(body["latest_kg"]) + " kg",
        delta=f"{body['change_kg']:+.1f} kg in this period",
        delta_color="off",  # more or less weight is not good or bad by itself
    )

# ---------- One section per lift ----------
st.divider()
st.subheader("Lifts")
st.caption("Strength is shown as the estimated one-rep max (1RM), worked out from your sets.")

lifts = progress["lifts"]
if not lifts:
    st.info(
        "Nothing to show yet. Log workouts with the main lifts: squat, bench press, "
        "deadlift, overhead press or barbell row."
    )
    st.stop()


def records_text(prs):
    """Turn the records of a lift into a list of readable lines."""
    lines = []
    if prs["weight_pr"]:
        lines.append(
            "Heaviest set: " + f"{prs['weight_pr']['value']:g}" + " kg (before: "
            + f"{prs['weight_pr']['previous']:g}" + " kg)"
        )
    if prs["one_rm_pr"]:
        lines.append(
            "Best estimated 1RM: " + f"{prs['one_rm_pr']['value']:g}" + " kg (before: "
            + f"{prs['one_rm_pr']['previous']:g}" + " kg)"
        )
    if prs["volume_pr"]:
        lines.append(
            "Biggest day of work: " + f"{prs['volume_pr']['value']:g}" + " kg lifted in total (before: "
            + f"{prs['volume_pr']['previous']:g}" + ")"
        )
    for rep_pr in prs["rep_prs"]:
        lines.append(
            f"{rep_pr['reps']} reps at {rep_pr['weight_kg']:g} kg (before: {rep_pr['previous_reps']} reps)"
        )
    return lines


for lift in lifts:
    st.markdown("### " + lift["exercise"])

    left, middle, right = st.columns(3)
    if lift["one_rm_now"] is None:
        left.metric("Estimated 1RM", "-")
        left.caption("No usable sets in this period.")
    else:
        delta = None
        if lift["change_kg"] is not None:
            delta = f"{lift['change_kg']:+.1f} kg ({lift['change_percent']:+.1f}%)"
        left.metric("Estimated 1RM", f"{lift['one_rm_now']:g} kg", delta=delta)
    middle.metric("Sessions", lift["sessions_in_period"])
    if lift["all_time_best_one_rm"] is not None:
        right.metric("Best ever", f"{lift['all_time_best_one_rm']:g} kg")

    lines = records_text(lift["prs"])
    if lines:
        st.write("**New records in this period**")
        for line in lines:
            st.write("- " + line)
    else:
        st.caption("No new records in this period.")

    series = lift["monthly_one_rm"]
    if len(series) >= 2:
        st.line_chart(
            {
                "Month": [datetime.date.fromisoformat(point["month"] + "-01") for point in series],
                "Best estimated 1RM (kg)": [point["best_one_rm"] for point in series],
            },
            x="Month",
            y="Best estimated 1RM (kg)",
        )
    st.divider()
