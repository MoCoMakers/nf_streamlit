import streamlit as st


try:
    st.set_page_config(layout="wide", page_title="Hack4NF Drug Response Data Visualization", page_icon="assets/favicon.png")
except st.errors.StreamlitAPIException as e:
    extra_msg = ""
    if "`set_page_config()` can only be called once per app page" in str(e):
        extra_msg = "\n\n...but just keep reloading the page, if it doesn't resolve itself. It should."
    print(f"Error: {e}{extra_msg}")

# Main welcome page without authentication
st.title("🧪 Cancer Drug Response Data Visualization")
st.write("Welcome to the Drug Response Data Visualization platform!")
st.write("Use the sidebar to navigate between different analysis tools.")

st.markdown('''
<a href="https://www.mocomakers.com/wp-content/uploads/2023/06/qHTS-NF1-Drugs-List-PosterV8-Final.pdf" target="_blank">Poster of Our NF1 Work</a>
''', unsafe_allow_html=True)

# Correct HTML link for the group website
st.markdown('''
<a href="https://compbio.dmvpetridish.com/" target="_blank">Find out more about our group on compbio.dmvpetridish.com</a>
''', unsafe_allow_html=True)

# Show navigation in sidebar
with st.sidebar:
    st.title("🧪 Data Visualizations")
    st.write("")
    st.write("")
    
    st.page_link("pages/Delta_S_Prime.py", label="Delta S Prime", icon="📊")
    st.page_link("pages/MIPE_3_0.py", label="MIPE 3.0", icon="📈")
    
    st.write("")
    st.write("")
    st.write("Navigate to any page using the links above to explore the data visualizations.")