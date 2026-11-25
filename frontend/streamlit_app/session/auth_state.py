"""Keeps track of who is logged in.

Streamlit forgets normal variables every time the page reruns.
st.session_state is a dictionary that survives reruns, so we keep the tokens there.
"""

import streamlit as st

from api_client import client

LOGIN_KEYS = ("id_token", "refresh_token", "uid", "email")

# A profile is complete when all of these fields have a value.
REQUIRED_PROFILE_FIELDS = ("sex", "birth_year", "height_cm", "training_years", "goal")


def is_logged_in():
    return "id_token" in st.session_state


def save_login(tokens, email):
    """Remember the user after a successful login or signup."""
    st.session_state["id_token"] = tokens["id_token"]
    st.session_state["refresh_token"] = tokens["refresh_token"]
    st.session_state["uid"] = tokens["uid"]
    st.session_state["email"] = email


def clear_login():
    """Forget the user on this side only."""
    for key in LOGIN_KEYS:
        st.session_state.pop(key, None)


def logout():
    """Tell the backend, then forget the user on this side."""
    try:
        client.logout(st.session_state["id_token"])
    except client.ApiError:
        pass  # For example the token already expired. We log out here anyway.
    clear_login()


def require_login():
    """Put this at the top of every page that needs a logged-in user."""
    if not is_logged_in():
        st.warning("Please log in first on the main page.")
        st.stop()  # stops the page here, nothing below it runs


def show_logout_button():
    """A Log out button in the sidebar."""
    if st.sidebar.button("Log out"):
        logout()
        st.rerun()


def call_with_token(api_function, *args):
    """Call a client function that needs the id token, for example:

        profile = call_with_token(client.get_profile)
        call_with_token(client.update_profile, data)

    The id token only lasts about an hour. If the backend says 401 (expired),
    we get a new token with the refresh token and try once more.
    """
    try:
        return api_function(st.session_state["id_token"], *args)
    except client.ApiError as error:
        if error.status_code != 401:
            raise

    # The token was rejected. Ask for a new one.
    try:
        tokens = client.refresh(st.session_state["refresh_token"])
    except client.ApiError:
        # Even the refresh token does not work, so the user must log in again.
        clear_login()
        st.rerun()

    st.session_state["id_token"] = tokens["id_token"]
    st.session_state["refresh_token"] = tokens["refresh_token"]
    return api_function(st.session_state["id_token"], *args)


def profile_is_complete(profile):
    """True if the user has filled in every required profile field."""
    for field in REQUIRED_PROFILE_FIELDS:
        if profile.get(field) is None:
            return False
    return True
