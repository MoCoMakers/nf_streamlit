import sys
sys.path.append('..')
from views.data import eda

# Remove authentication - no longer needed
# from views.signed_in_landing import landing_page

# landing_page()

"# MIPE 3.0 Dataset – All S Indices"

# Streamlit automatically provides page navigation in the sidebar

eda()