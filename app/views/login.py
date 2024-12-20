import streamlit as st
import streamlit_authenticator as stauth
from .signupform import SignUp
from .signed_in_landing import landing_page

from db import get_credentials, update_user
from time import sleep

def loginapp():
    if "signup" not in st.session_state:
        st.session_state.signup = False

    def toggle_signup_login():
        st.session_state.signup = False if st.session_state.signup else True

    if  st.session_state.signup:

        newauthenticator = SignUp(
            get_credentials(),
            st.secrets["cookie"]["name"],
            st.secrets["cookie"]["key"],
            st.secrets["cookie"]["expiry_days"],
            None,
        )

        try:
            hashed_password, email_of_registered_user, username_of_registered_user, name_of_registered_user = newauthenticator.register_user(
                "main", pre_authorization=False, fields={"Form name": "Sign Up"}
            )

            if email_of_registered_user:
                update_user(hashed_password, email_of_registered_user, username_of_registered_user, name_of_registered_user)
                st.success('User registered successfully')
                sleep(0.5)
                st.session_state.signup = False
                st.switch_page("Home.py")
            else:
                st.button(":blue[Log In instead]", on_click=toggle_signup_login)
        except Exception as e:
            st.error(e)
        
    else:
        authenticator = stauth.Authenticate(
            get_credentials(),
            st.secrets["cookie"]["name"],
            st.secrets["cookie"]["key"],
            st.secrets["cookie"]["expiry_days"],
            None,
        )
        name, authentication_status, username = authenticator.login(
            "main", fields={"Form name": "Login"}
        )
        if not authentication_status:
            st.button(":blue[Sign Up instead]", on_click=toggle_signup_login)

    if not st.session_state.signup and "authentication_status" in st.session_state:
        if st.session_state["authentication_status"]:
            st.session_state.logged_in = True
            st.write(f"Welcome *{name}*")
            st.write("Click any one of the sidebar items to get view the visualizations 😁")
            landing_page()
            authenticator.logout("Log out", "sidebar")
        elif st.session_state["authentication_status"] == False:
            st.error("Username/password is incorrect")
        elif st.session_state["authentication_status"] == None:
            st.warning("Please enter your username and password")
