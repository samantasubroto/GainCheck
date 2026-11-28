"""The entry point. It decides which pages exist, depending on whether the user is logged in.

A logged-out user only gets the login page, and no menu. A logged-in user gets all the pages.
"""

import streamlit as st

from session import auth_state

st.set_page_config(page_title="GainCheck", page_icon="💪")

# After a browser refresh this logs the user back in from the cookie.
auth_state.init()

if auth_state.is_logged_in():
    profile_page = st.Page("pages/5_Profile.py", title="Profile", icon="👤")
    navigation = st.navigation(
        [
            st.Page("views/home.py", title="Home", icon="🏠", default=True),
            st.Page("pages/1_Log_Workout.py", title="Log Workout", icon="🏋️"),
            st.Page("pages/2_Body_Metrics.py", title="Body Metrics", icon="📏"),
            st.Page("pages/3_Progress.py", title="Progress", icon="📈"),
            st.Page("pages/4_Reports.py", title="Reports", icon="📝"),
            profile_page,
        ]
    )

    # A user who has just signed up has an empty profile, so they start there.
    if st.session_state.pop("go_to_profile", False):
        st.switch_page(profile_page)
else:
    # position="hidden" hides the menu, so there is nothing to click except the login form.
    navigation = st.navigation(
        [st.Page("views/login.py", title="Log in", icon="💪")],
        position="hidden",
    )

navigation.run()
