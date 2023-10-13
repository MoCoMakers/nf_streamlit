import streamlit as st
import streamlit_authenticator as stauth
from streamlit_authenticator.utilities.hasher import Hasher

from typing import Optional

def flatten(data):
    if isinstance(data, tuple):
        for x in data:
            yield from flatten(x)
    else:
        yield data

class SignUp(stauth.Authenticate):
    """
        Create a new instance of "SignUp".

        Parameters
        ----------
        credentials: dict
            Dictionary of usernames, names, passwords, emails, and other user data.
        cookie_name: str
            Name of the re-authentication cookie stored on the client's browser for password-less 
            re-authentication.
        cookie_key: str
            Key to be used to hash the signature of the re-authentication cookie.
        cookie_expiry_days: float
            Number of days before the re-authentication cookie automatically expires on the client's 
            browser.
        pre-authorized: list
            List of emails of unregistered users who are authorized to register.        
        validator: Validator
            Validator object that checks the validity of the username, name, and email fields.
    """
    def __init__(self, *attributes):
        super().__init__(*attributes)

    def register_user(self, location: str='main', pre_authorization: bool=True,
                      domains: Optional[list]=None, fields: dict=None,
                      clear_on_submit: bool=False) -> tuple:
        if location == 'main':
            register_user_form = st.form('Register user', clear_on_submit=clear_on_submit)
        elif location == 'sidebar':
            register_user_form = st.sidebar.form('Register user')

        register_user_form.subheader('Register User' if 'Form name' not in fields
                                     else fields['Form name'])
        new_name = register_user_form.text_input('Name' if 'Name' not in fields
                                                 else fields['Name'])
        new_email = register_user_form.text_input('Email' if 'Email' not in fields
                                                  else fields['Email'])
        new_username = register_user_form.text_input('Username' if 'Username' not in fields
                                                     else fields['Username']).lower()
        new_password = register_user_form.text_input('Password' if 'Password' not in fields
                                                     else fields['Password'], type='password')
        new_password_repeat = register_user_form.text_input('Repeat password'
                                                            if 'Repeat password' not in fields
                                                            else fields['Repeat password'],
                                                            type='password')
        if register_user_form.form_submit_button('Register' if 'Register' not in fields
                                                 else fields['Register']):
            return tuple(flatten((
                            tuple(Hasher([new_password]).generate()) ,
                            self.authentication_handler.register_user(new_password, new_password_repeat,
                                pre_authorization, new_username,
                                new_name, new_email, domains
                            ))
                        )
                    )
        return None, None, None, None