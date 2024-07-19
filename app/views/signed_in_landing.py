import streamlit as st
from streamlit.runtime.scriptrunner import get_script_run_ctx
from streamlit.source_util import get_pages
from time import sleep

def landing_page():
    with st.sidebar:
        st.title("🧪 Data Visualizations")
        st.write("")
        st.write("")

        if st.session_state.get("logged_in", False):
            st.page_link("pages/Delta_S_Prime.py", label="Delta S Prime", icon="📊")
            st.page_link("pages/MIPE_3_0.py", label="MIPE 3.0", icon="📈")

            st.write("")
            st.write("")

            if get_current_page_name() != "Home":
                if st.button("Log out"):
                    logout()

        elif get_current_page_name() != "Home":
            # If anyone tries to access a secret page without being logged in,
            # redirect them to the login page
            st.switch_page("Home.py")

def get_current_page_name():
    ctx = get_script_run_ctx()
    if ctx is None:
        raise RuntimeError("Couldn't get script context")

    pages = get_pages("")

    return pages[ctx.page_script_hash]["page_name"]

def logout():
    st.session_state.logged_in = False
    st.info("Logged out successfully!")
    sleep(0.5)
    st.switch_page("Home.py")