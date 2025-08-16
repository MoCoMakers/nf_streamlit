import streamlit as st
import sys
sys.path.append('..')
from views.data import eda

# Remove authentication - no longer needed
# from views.signed_in_landing import landing_page

# landing_page()

"# MIPE 3.0 Dataset – All S Indices"

# Add navigation sidebar
with st.sidebar:
    st.title("🧪 Data Visualizations")
    st.write("")
    st.write("")
    
    # Add Home link back
    st.page_link("Home.py", label="🏠 Home", icon="🏠")
    st.page_link("pages/Delta_S_Prime.py", label="Delta S Prime for DepMap", icon="📊")
    st.page_link("pages/MIPE_3_0.py", label="Delta S on MIPE 3.0 for NF1 Cell Lines", icon="📈")
    
    st.write("")
    st.write("")
    st.write("Navigate between different analysis tools using the links above.")

# Call eda() function outside the sidebar context
eda()