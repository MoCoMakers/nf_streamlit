"""
Database Test Page for DepMap Migration

This page provides a simple interface to test PostgreSQL database connections
and verify that all required tables exist for the DepMap migration.
"""

import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database_test import run_database_test

# Page configuration
st.set_page_config(
    page_title="Database Test - DepMap Migration",
    page_icon="🔍",
    layout="wide"
)

# Run the database test
run_database_test()

# Add navigation
st.sidebar.title("🧪 Database Test")
st.sidebar.write("")
st.sidebar.write("This page tests your PostgreSQL database connection and verifies that all required tables exist for the DepMap migration.")
st.sidebar.write("")
st.sidebar.page_link("Home.py", label="🏠 Home", icon="🏠")
st.sidebar.page_link("pages/Delta_S_Prime.py", label="Delta S Prime", icon="📊")
st.sidebar.page_link("pages/MIPE_3_0.py", label="MIPE 3.0", icon="📈")
st.sidebar.write("")
st.sidebar.write("**Configuration Files:**")
st.sidebar.write("- `app/.streamlit/secrets.toml`")
st.sidebar.write("- `app/.streamlit/config.toml`")
st.sidebar.write("")
st.sidebar.write("**Setup Guide:**")
st.sidebar.write("- `POSTGRESQL_SETUP_GUIDE.md`")
