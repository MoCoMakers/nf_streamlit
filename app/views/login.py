import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from .data import eda
with open('./config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

def loginapp():
    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days'],
        config['preauthorized']
    )
    if 'signup' not in st.session_state:
        st.session_state.signup = False

    def click_button():
        st.session_state.signup = False if st.session_state.signup else True

    if st.session_state.signup:
        try:
            if authenticator.register_user('Sign Up', 'main'):
                st.success('User registered successfully')
            st.button('Log In instead', on_click=click_button)
        except Exception as e:
            st.error(e)
    else:
        name, authentication_status, username = authenticator.login('Login', 'main')
        if not authentication_status:
            st.button('Sign Up instead', on_click=click_button)

    if not st.session_state.signup and "authentication_status" in st.session_state:
        if st.session_state["authentication_status"]:
            authenticator.logout('Logout', 'main')
            st.write(f'Welcome *{name}*')
            eda()
        elif st.session_state["authentication_status"] == False:
            st.error('Username/password is incorrect')
        elif st.session_state["authentication_status"] == None:
            st.warning('Please enter your username and password')