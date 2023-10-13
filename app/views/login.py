import streamlit as st
import streamlit_authenticator as stauth
from .data import eda
from db import get_credentials, update_all_users
import copy

credentials_in_database = get_credentials()

def loginapp():
    global credentials_in_database
    authenticator = stauth.Authenticate(
        copy.deepcopy(credentials_in_database),
        st.secrets['cookie']['name'],
        st.secrets['cookie']['key'],
        st.secrets['cookie']['expiry_days'],
        None
    )
    if 'signup' not in st.session_state:
        st.session_state.signup = False

    def toggle_signup_login():
        st.session_state.signup = False if st.session_state.signup else True

    if st.session_state.signup:
        try:
            if authenticator.register_user('Sign Up', 'main', False):
                credentials_not_in_database = {
                    'usernames': {username: authenticator.credentials['usernames'][username]}
                    for username in authenticator.credentials['usernames']
                    if username not in credentials_in_database['usernames']
                }
                update_all_users(credentials_not_in_database)
                credentials_in_database = copy.deepcopy(authenticator.credentials)
                st.success('User registered successfully')
            st.button(':blue[Log In instead]', on_click=toggle_signup_login)
        except Exception as e:
            st.error(e)
    else:
        name, authentication_status, username = authenticator.login('Login', 'main')
        if not authentication_status:
            st.button(':blue[Sign Up instead]', on_click=toggle_signup_login)

    if not st.session_state.signup and "authentication_status" in st.session_state:
        if st.session_state["authentication_status"]:
            authenticator.logout('Logout', 'sidebar')
            st.write(f'Welcome *{name}*')
            eda()
        elif st.session_state["authentication_status"] == False:
            st.error('Username/password is incorrect')
        elif st.session_state["authentication_status"] == None:
            st.warning('Please enter your username and password')
