import streamlit as st

from api_client import client
from session import auth_state

st.set_page_config(page_title="Profile", page_icon="👤")

# Nothing below this line runs for someone who is not logged in.
auth_state.require_login()
auth_state.show_logout_button()

st.title("👤 Your profile")

try:
    profile = auth_state.call_with_token(client.get_profile)
except client.ApiError as error:
    st.error(str(error))
    st.stop()

was_complete = auth_state.profile_is_complete(profile)
if not was_complete:
    st.info(
        "Welcome! Tell us a bit about yourself. We use this to judge your "
        "strength fairly. You can change it later."
    )

SEX_OPTIONS = ["male", "female"]
GOAL_LABELS = {
    "strength": "Get stronger",
    "muscle": "Build muscle",
    "fat_loss": "Lose fat",
    "general": "General fitness",
}
GOAL_OPTIONS = list(GOAL_LABELS.keys())


def saved_or_default(value, default):
    """Use the saved value, or the default if nothing is saved yet.

    We check for None on purpose. "value or default" would wrongly replace a saved 0.
    """
    if value is None:
        return default
    return value


def position_of(options, value):
    """Where is value in the list? Used to pick the saved choice. 0 if not saved yet."""
    if value in options:
        return options.index(value)
    return 0


# Start the form with the saved values. If a field is still empty, use a default.
with st.form("profile_form"):
    display_name = st.text_input("Name (optional)", value=profile.get("display_name") or "")
    sex = st.selectbox(
        "Sex (used for strength standards)",
        SEX_OPTIONS,
        index=position_of(SEX_OPTIONS, profile.get("sex")),
    )
    birth_year = st.number_input(
        "Birth year",
        min_value=1920,
        max_value=2015,
        step=1,
        value=saved_or_default(profile.get("birth_year"), 1995),
    )
    height_cm = st.number_input(
        "Height (cm)",
        min_value=100.0,
        max_value=250.0,
        step=1.0,
        value=saved_or_default(profile.get("height_cm"), 175.0),
    )
    training_years = st.number_input(
        "Years of training",
        min_value=0.0,
        max_value=80.0,
        step=0.5,
        value=saved_or_default(profile.get("training_years"), 1.0),
    )
    goal = st.selectbox(
        "Main goal",
        GOAL_OPTIONS,
        format_func=lambda key: GOAL_LABELS[key],
        index=position_of(GOAL_OPTIONS, profile.get("goal")),
    )
    saved = st.form_submit_button("Save profile")

if saved:
    data = {
        "display_name": display_name.strip() or None,
        "sex": sex,
        "birth_year": int(birth_year),
        "height_cm": float(height_cm),
        "training_years": float(training_years),
        "goal": goal,
    }
    try:
        auth_state.call_with_token(client.update_profile, data)
    except client.ApiError as error:
        st.error(str(error))
        st.stop()

    if was_complete:
        st.success("Profile saved.")
    else:
        # First time: the profile is done, so go to the home page.
        st.switch_page("app.py")
