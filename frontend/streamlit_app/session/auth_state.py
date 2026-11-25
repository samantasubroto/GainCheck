"""Keeps track of who is logged in.

Streamlit forgets normal variables every time the page reruns.
st.session_state is a dictionary that survives reruns, so we keep the tokens there.
"""

import streamlit as st

from api_client import client


def is_logged_in():
    return "id_token" in st.session_state


def save_login(tokens, email):
    """Remember the user after a successful login or signup."""
    st.session_state["id_token"] = tokens["id_token"]
    st.session_state["refresh_token"] = tokens["refresh_token"]
    st.session_state["uid"] = tokens["uid"]
    st.session_state["email"] = email


def logout():
    """Tell the backend, then forget the user on this side."""
    try:
        client.logout(st.session_state["id_token"])
    except client.ApiError:
        pass  # For example the token already expired. We log out here anyway.

    for key in ("id_token", "refresh_token", "uid", "email"):
        st.session_state.pop(key, None)


def require_login():
    """Put this at the top of every page that needs a logged-in user."""
    if not is_logged_in():
        st.warning("Please log in first on the main page.")
        st.stop()  # stops the page here, nothing below it runs
