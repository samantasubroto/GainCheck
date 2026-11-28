"""The page a logged-out user sees: log in or create an account."""

import streamlit as st

from api_client import client
from session import auth_state


def go_after_login():
    """Remember where the user should land after logging in or signing up, then reload the app."""
    try:
        profile = auth_state.call_with_token(client.get_profile)
    except client.ApiError:
        profile = {}  # We could not load it, so treat it as not filled in.

    # A user with an empty profile is sent to the Profile page first (app.py does that).
    if not auth_state.profile_is_complete(profile):
        st.session_state["go_to_profile"] = True

    st.rerun()  # app.py runs again, and now the user is logged in


def show_login_form():
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log in")

    if submitted:
        if not email or not password:
            st.error("Please enter your email and password.")
            return
        try:
            tokens = client.login(email, password)
        except client.ApiError as error:
            st.error(str(error))
            return

        auth_state.save_login(tokens, email)
        go_after_login()


def show_signup_form():
    with st.form("signup_form"):
        email = st.text_input("Email")
        password = st.text_input("Password (at least 6 characters)", type="password")
        password_again = st.text_input("Repeat password", type="password")
        submitted = st.form_submit_button("Create account")

    if submitted:
        if not email or not password:
            st.error("Please enter an email and a password.")
            return
        if password != password_again:
            st.error("The two passwords are not the same.")
            return
        try:
            tokens = client.signup(email, password)
        except client.ApiError as error:
            st.error(str(error))
            return

        # A new account is logged in right away, and a new user has no profile yet.
        auth_state.save_login(tokens, email)
        go_after_login()


st.title("💪 GainCheck")
st.write("Find out whether you are really getting stronger.")

login_tab, signup_tab = st.tabs(["Log in", "Sign up"])
with login_tab:
    show_login_form()
with signup_tab:
    show_signup_form()
