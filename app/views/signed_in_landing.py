import streamlit as st

def landing_page():
    col1, col2 = st.columns(2)
    with col1:
        st.button("MIPE 3.0 Dataset - All S Indicies", on_click=lambda: st.switch_page("pages/MIPE_3_0.py"))
    with col2:
        st.button("Delta S Prime - DepMap Dataset", on_click=lambda: st.switch_page("pages/Delta_S_Prime.py"))