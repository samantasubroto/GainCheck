"""The home page, shown to a logged-in user."""

import streamlit as st

from api_client import client
from session import auth_state

PROFILE_PAGE = "pages/5_Profile.py"

auth_state.require_login()
auth_state.show_logout_button()

st.title("💪 GainCheck")
st.success("You are logged in as " + st.session_state["email"])

# Remind the user if they skipped the profile.
try:
    profile = auth_state.call_with_token(client.get_profile)
except client.ApiError:
    profile = {}
if not auth_state.profile_is_complete(profile):
    st.warning("Your profile is not complete yet.")
    st.page_link(PROFILE_PAGE, label="Complete your profile")

st.write(
    "Log your workouts and body measurements, then check Progress to see whether "
    "your gains are real, and make a monthly report."
)
