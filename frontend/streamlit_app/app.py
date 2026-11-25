import streamlit as st

from api_client import client
from session import auth_state

st.set_page_config(page_title="GainCheck", page_icon="💪")

PROFILE_PAGE = "pages/5_Profile.py"


def go_after_login():
    """Decide where to send the user right after they log in or sign up."""
    try:
        profile = auth_state.call_with_token(client.get_profile)
    except client.ApiError:
        profile = {}  # We could not load it, so treat it as not filled in.

    if auth_state.profile_is_complete(profile):
        st.rerun()  # run the script again, now it will show the home page
    else:
        st.switch_page(PROFILE_PAGE)


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


def show_login_page():
    st.title("💪 GainCheck")
    st.write("Find out whether you are really getting stronger.")

    login_tab, signup_tab = st.tabs(["Log in", "Sign up"])
    with login_tab:
        show_login_form()
    with signup_tab:
        show_signup_form()


def show_home_page():
    st.title("💪 GainCheck")
    st.success("You are logged in as " + st.session_state["email"])
    auth_state.show_logout_button()

    # Remind the user if they skipped the profile.
    try:
        profile = auth_state.call_with_token(client.get_profile)
    except client.ApiError:
        profile = {}
    if not auth_state.profile_is_complete(profile):
        st.warning("Your profile is not complete yet.")
        st.page_link(PROFILE_PAGE, label="Complete your profile")

    st.write("Welcome! Workouts, body metrics, progress and reports are coming soon.")


# The login gate: logged-in users see the home page, everyone else sees login.
if auth_state.is_logged_in():
    show_home_page()
else:
    show_login_page()
