import streamlit as st

def landing_page():
    st.write("Choose one of the pages in the sidebar to get started.")
    show_pages(
        [
            Page("visualizations/Delta_S_Prime.py", "Delta S Prime", "📊", use_relative_hash=True),
            Page("visualizations/MIPE_3_0.py", "MIPE 3.0", "📈", use_relative_hash=True),
        ]
    )