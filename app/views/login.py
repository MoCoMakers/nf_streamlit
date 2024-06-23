import copy

import streamlit as st
import streamlit_authenticator as stauth
from .signupform import SignUp
from .signed_in_landing import landing_page

from db import get_credentials, update_all_users

credentials_in_database = get_credentials()


def loginapp():
    global credentials_in_database
    authenticator = stauth.Authenticate(
        copy.deepcopy(credentials_in_database),
        st.secrets["cookie"]["name"],
        st.secrets["cookie"]["key"],
        st.secrets["cookie"]["expiry_days"],
        None,
    )
    newauthenticator = SignUp(
        copy.deepcopy(credentials_in_database),
        st.secrets["cookie"]["name"],
        st.secrets["cookie"]["key"],
        st.secrets["cookie"]["expiry_days"],
        None,
    )
    if "signup" not in st.session_state:
        st.session_state.signup = False

    def toggle_signup_login():
        st.session_state.signup = False if st.session_state.signup else True

    if st.session_state.signup:
        try:
            hashed_password, email_of_registered_user, username_of_registered_user, name_of_registered_user = newauthenticator.register_user(
                "main", pre_authorization=False, fields={"Form name": "Sign Up"}
            )

            if email_of_registered_user:
                # TODO: Load data to database
                st.success('User registered successfully')
            else:
                st.button(":blue[Log In instead]", on_click=toggle_signup_login)
        except Exception as e:
            st.error(e)
    else:
        name, authentication_status, username = authenticator.login(
            "main", fields={"Form name": "Login"}
        )
        if not authentication_status:
            st.button(":blue[Sign Up instead]", on_click=toggle_signup_login)

    if not st.session_state.signup and "authentication_status" in st.session_state:
        if st.session_state["authentication_status"]:
            authenticator.logout("Logout", "sidebar")
            st.write(f"Welcome *{name}*")
            landing_page()
        elif st.session_state["authentication_status"] == False:
            st.error("Username/password is incorrect")
        elif st.session_state["authentication_status"] == None:
            st.warning("Please enter your username and password")
