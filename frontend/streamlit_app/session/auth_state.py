"""Keeps track of who is logged in.

Streamlit forgets normal variables every time the page reruns.
st.session_state is a dictionary that survives reruns, so we keep the tokens there.

When the browser page is refreshed, Streamlit starts a brand new session and
st.session_state is empty again. To stay logged in, we also keep the refresh token
in a browser cookie, and use it to log back in when a new session starts.
"""

import re

import streamlit as st

from api_client import client

LOGIN_KEYS = ("id_token", "refresh_token", "uid", "email")

# A profile is complete when all of these fields have a value.
REQUIRED_PROFILE_FIELDS = ("sex", "birth_year", "height_cm", "training_years", "goal")

# The cookie that remembers the login.
COOKIE_NAME = "gaincheck_refresh"
COOKIE_DAYS = 7
# Refresh tokens only contain these characters. We check before putting one into JavaScript.
TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_.\-]+")


def is_logged_in():
    return "id_token" in st.session_state


# ---------- The cookie ----------


def run_javascript(code):
    """Run a small piece of JavaScript in the browser page."""
    st.html("<script>" + code + "</script>", unsafe_allow_javascript=True)


def sync_cookie():
    """Write or delete the cookie in the browser, if a login or logout just happened.

    save_login() and logout() only leave a note in st.session_state ("save" or "delete").
    We act on the note here, at the top of the next run, so the script is sent to the
    browser before any rerun or page switch can interrupt it.
    """
    action = st.session_state.pop("cookie_action", None)

    if action == "save" and is_logged_in():
        token = st.session_state["refresh_token"]
        if TOKEN_PATTERN.fullmatch(token):
            seconds = COOKIE_DAYS * 24 * 60 * 60
            run_javascript(
                "var secure = location.protocol === 'https:' ? '; Secure' : '';"
                "document.cookie = '" + COOKIE_NAME + "=" + token
                + "; max-age=" + str(seconds) + "; path=/; SameSite=Strict' + secure;"
            )

    elif action == "delete":
        run_javascript(
            "document.cookie = '" + COOKIE_NAME + "=; max-age=0; path=/; SameSite=Strict';"
        )


def restore_login():
    """After a page refresh, log the user back in using the cookie.

    st.context.cookies holds the cookies the browser sent when it connected.
    We only try once per session. Without that, logging out would log the user
    straight back in, because that cookie list does not change until the next refresh.
    """
    if is_logged_in() or st.session_state.get("restore_tried"):
        return
    st.session_state["restore_tried"] = True

    refresh_token = st.context.cookies.get(COOKIE_NAME)
    if not refresh_token:
        return

    try:
        tokens = client.refresh(refresh_token)
        profile = client.get_profile(tokens["id_token"])
    except client.ApiError as error:
        # 400 or 401 means the server rejected the token: the cookie is old, or the
        # user logged out somewhere else. Remove it.
        # Any other problem (for example the backend is not running) is temporary,
        # so we keep the cookie and the user can try again after a refresh.
        if error.status_code in (400, 401):
            st.session_state["cookie_action"] = "delete"
        return

    save_login(tokens, profile["email"])


def init():
    """Call this at the top of the main page, and on every page via require_login()."""
    restore_login()
    sync_cookie()


# ---------- Login and logout ----------


def save_login(tokens, email):
    """Remember the user after a successful login or signup."""
    st.session_state["id_token"] = tokens["id_token"]
    st.session_state["refresh_token"] = tokens["refresh_token"]
    st.session_state["uid"] = tokens["uid"]
    st.session_state["email"] = email
    st.session_state["cookie_action"] = "save"


def clear_login():
    """Forget the user on this side only."""
    for key in LOGIN_KEYS:
        st.session_state.pop(key, None)


def logout():
    """Tell the backend, then forget the user here and remove the cookie."""
    try:
        client.logout(st.session_state["id_token"])
    except client.ApiError:
        pass  # For example the token already expired. We log out here anyway.
    clear_login()
    st.session_state["cookie_action"] = "delete"


def require_login():
    """Put this at the top of every page that needs a logged-in user."""
    init()
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
        st.session_state["cookie_action"] = "delete"
        st.rerun()

    st.session_state["id_token"] = tokens["id_token"]
    st.session_state["refresh_token"] = tokens["refresh_token"]
    st.session_state["cookie_action"] = "save"  # keep the cookie in step with the new token
    return api_function(st.session_state["id_token"], *args)


def profile_is_complete(profile):
    """True if the user has filled in every required profile field."""
    for field in REQUIRED_PROFILE_FIELDS:
        if profile.get(field) is None:
            return False
    return True
