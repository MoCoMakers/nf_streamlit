from pathlib import Path
import numpy as np
import pandas as pd

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import streamlit as st

from st_aggrid import AgGrid
from st_aggrid import GridOptionsBuilder

# from views.data import compute_ranked_delta_s_prime, display_ranked_delta_s_prime_for_download

"# ΔS'"

column_order = ['name', 'moa', 'target', 'lower_limit', 'upper_limit', 'ec50']

# Load the data
# extracting only columns: 'name', 'moa', 'target', 'lower_limit', 'upper_limit', 'ec50'
data_path = Path("data/DepMap/Prism19Q4/secondary-screen-dose-response-curve-parameters.csv")
df = pd.read_csv(data_path, usecols=['name', 'moa', 'target', 'lower_limit', 'upper_limit', 'ec50'])
df = df[column_order]

# Derive EFF (upper_limit - lower_limit) 
df['EFF'] = df['upper_limit'] - df['lower_limit']

# Derive EFF*100
df['EFF*100'] = df['EFF'] * 100

# Derive EFF/EC50
df['EFF/EC50'] = df['EFF'] / df['ec50']

# Derive S'
# ASINH((EFF*100)/EC50)
df["S'"] = np.arcsinh(df['EFF*100'] / df['ec50'])

# Future: use same calculations as data.py
# df_ranked = compute_ranked_delta_s_prime(df)
# display_ranked_delta_s_prime_for_download(df_ranked, df_ratio=XYZ)

"## Single test value selected from 'bortezomib'"
# as a test only write the rows where 'name' is 'bortezomib' adn the EFF*100 is close to 97.9789
st.write(df[df['name'] == 'bortezomib'][(df['EFF*100'] > 97.9788) & (df['EFF*100'] < 97.9790)])

"## ΔS' Table"
# Display the table
gb = GridOptionsBuilder.from_dataframe(df)
gb.configure_pagination()
gb.configure_side_bar()
gb.configure_default_column(groupable=True, value=True, enableRowGroup=True, aggFunc='sum', editable=True)
# Freeze the 1st column for scrolling
column_defs = [{'headerName': col, 'field': col, 'pinned': 'left' if col == 'name' else None} for col in df.columns]
gridOptions = {
    'columnDefs': column_defs,
    'pagination': True,
    'defaultColDef': {'groupable': True, 'value': True, 'enableRowGroup': True, 'aggFunc': 'sum', 'editable': True},
}
AgGrid(df, gridOptions=gridOptions)

# Add a filter (dropdown on the column 'name') that updates a dataframe table view.