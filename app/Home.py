import streamlit as st


try:
    st.set_page_config(layout="wide", page_title="Hack4NF Drug Response Data Visualization", page_icon="assets/favicon.png")
except st.errors.StreamlitAPIException as e:
    extra_msg = ""
    if "`set_page_config()` can only be called once per app page" in str(e):
        extra_msg = "\n\n...but just keep reloading the page, if it doesn't resolve itself. It should."
    print(f"Error: {e}{extra_msg}")

from views import login
login.loginapp()