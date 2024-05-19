from pathlib import Path
import numpy as np
import pandas as pd

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import streamlit as st

from st_aggrid import AgGrid
from st_aggrid import GridOptionsBuilder


import syn5522627 as syn

"# Delta S'"

"""
## Directive 

For the main body, load in ‘secondary-screen-dose-response-curve-parameters.csv’ as called out by Paul the attached document
and calculate delta S’ and display the results as a table st.write(df_depmap) – a new dataframe you need to create
"""

BREWER_9_SET1 = [
    "#e41a1c",
    "#377eb8",
    "#4daf4a",
    "#984ea3",
    "#ff7f00",
    "#ffff33",
    "#a65628",
    "#f781bf",
    "#999999",
]
COLORS = BREWER_9_SET1

def ll4(c, h, inf, zero, ec50):
    """A copy of the LL.4 function from the R drc package with,
    https://doseresponse.github.io/drc/reference/LL.4.html

     - c: concentration
     - h: hill slope
     - inf: asymptote at max concentration
     - zero: asymptote at zero concentration
     - ec50: EC50
    """
    num = zero - inf
    den = 1 + np.exp(h * (np.log(c) - np.log(ec50)))
    response = inf + num / den
    return response    

def get_measured_trace(row, label=None, showlegend=False, color=None):
    cs = row[syn.C_COLS].astype(float).values
    rs = row[syn.R_COLS].astype(float).values
    tr_measured = go.Scatter(
        x=cs,
        y=rs,
        mode="markers",
        name=label,
        showlegend=showlegend,
        marker_color=color,
    )
    return tr_measured

def get_fit_trace(row, label=None, showlegend=False, color=None, line_type="dot"):
    cs = row[syn.C_COLS].astype(float).values
    fit_rs = ll4(
        cs,
        row["HILL"],
        row["INF"],
        row["ZERO"],
        row["AC50"],
    )
    tr_fit = go.Scatter(
        x=cs,
        y=fit_rs,
        mode="lines",
        showlegend=showlegend,
        name=label,
        line_color=color,
        line_dash=line_type
    )
    return tr_fit    
           
def get_ac50_trace(row, label=None, showlegend=False, color=None):
    rs = row[syn.R_COLS].astype(float).values
    tr_ac50 = go.Scatter(
        x=[row["AC50"]] * 2,
        # y=[min(rs), max(rs)],
        y=[row["ZERO"], row["INF"]],
        mode="lines",
        showlegend=showlegend,
        name=label,
        line_color=color,
    )
    return tr_ac50

def build_grid_options(df):
    # https://towardsdatascience.com/make-dataframes-interactive-in-streamlit-c3d0c4f84ccb
    gb = GridOptionsBuilder.from_dataframe(df)
    # gb.configure_pagination(paginationAutoPageSize=True)
    gb.configure_side_bar()
    gb.configure_selection(
        "single",
        use_checkbox=False,
        groupSelectsChildren=True,
    )
    gridOptions = gb.build()
    return gridOptions

data_path = Path("syn5522627")

df_files, df_clines, file_name_to_specimen_id = syn.read_metadata(data_path)
file_show_cols = [col for col in df_files.columns if col not in syn.FILE_HIDE_COLS]

# raw dose-response curve dataframes
dfs_drc_raw = syn.read_raw_drc(df_files, data_path)

# create dose-response curve objects
drcs = {}
for file_name, df_drc_raw in dfs_drc_raw.items():
    file_row = df_files.loc[file_name][file_show_cols]
    drc = syn.DoseResponseCurve(file_row.to_dict(), df_drc_raw)
    drcs[file_name] = drc

dfs_drc = syn.make_mrgd_drc(drcs, file_name_to_specimen_id)

# make one dataframe
df_drc = pd.DataFrame()
for si, df1 in dfs_drc.items():
    df1['cell_line'] = si
    df_drc = pd.concat([df_drc, df1])
df_drc['eff'] = df_drc["ZERO"] - df_drc["INF"]

drcs = {}
for file_name, df_drc_raw in dfs_drc_raw.items():
    file_row = df_files.loc[file_name][file_show_cols]
    drc = syn.DoseResponseCurve(file_row.to_dict(), df_drc_raw)
    drcs[file_name] = drc


# all dose response curves have the same compounds so we just take one
one_specimen_id = next(iter(dfs_drc.keys()))
df_compounds = dfs_drc[one_specimen_id]
df_compounds = df_compounds[["NCGC SID", "name", "target", "MoA", "SMILES"]]

# calculate all ratios
df_ratios = syn.calculate_fit_ratios(df_compounds, dfs_drc, syn.den_sis, syn.num_sis)
st.session_state['df_ratios'] = df_ratios


# TODO change this variable name
df_compound_selected = df_compounds.iloc[0:1]

# Compounds
# ==================================

st.header("Selected Compound")
st.dataframe(df_compound_selected)
                             
st_ncgc_sid = df_compound_selected.iloc[0]["NCGC SID"]

# Used Cell Lines
# ----------------------------------
specimen_ids = df_clines.sort_values("disease")['specimenID']

st.header("Available Cell Lines - Dose Response Curves")
# create a checkbox for each category
val = [None] * len(specimen_ids)  # this list will store info about which category is selected
for i, cat in enumerate(specimen_ids):
    # set defaults:
    exclude_list = ["HFF", "ipNF05.5"]
    if cat in exclude_list:
        val[i] = st.sidebar.checkbox(cat, value=False, key='curves_cell_line_selector_' + str(
            i))  # value is the preselect value for first render
    else:
        val[i] = st.sidebar.checkbox(cat, value=True, key='curves_cell_line_selector_' + str(i))

specimen_ids = specimen_ids[specimen_ids.isin(specimen_ids[val])].reset_index(drop=True)

col1, col2 = st.columns([2, 2])

# Dose Response Curves
# ----------------------------------

with col1:

    st.subheader("Dose Response Curves")

    num_cell_lines = len(specimen_ids)

    r2s = {}
    for specimen_id in specimen_ids:
        df = dfs_drc[specimen_id]
        row = df[df["NCGC SID"] == st_ncgc_sid].iloc[0]
        r2s[specimen_id] = row["R2"]

    titles = [f"{si}<br>R2={r2s[si]:.2f}" for si in specimen_ids]

    n_cols = 3
    n_rows = 3
    fig = make_subplots(
        rows=n_rows,
        cols=n_cols,
        shared_xaxes="all",
        shared_yaxes="all",
        vertical_spacing=0.12,
        start_cell="top-left",
        subplot_titles=titles,
    )

    i_row = 1
    i_col = 1
    i_tot = 0

    df_sctr = {
        "cell line": [],
        "ac50": [],
        "eff": [],
        "R2": [],
    }

    for specimen_id in specimen_ids:

        df = dfs_drc[specimen_id]

        row = df[df["NCGC SID"] == st_ncgc_sid].iloc[0]
        df_sctr["cell line"].append(specimen_id)
        df_sctr["ac50"].append(row["AC50"])
        df_sctr["eff"].append(row["ZERO"] - row["INF"])
        df_sctr["R2"].append(row["R2"])

        i_color = i_tot
        tr_measured = get_measured_trace(row, color=COLORS[i_color])
        tr_fit = get_fit_trace(row, color=COLORS[i_color])
        tr_ac50 = get_ac50_trace(row, color=COLORS[i_color])
        for tr in [tr_measured, tr_fit, tr_ac50]:
            fig.add_trace(tr, row=i_row, col=i_col)

        i_tot += 1
        i_col += 1
        if i_col > n_cols:
            i_col = 1
            i_row += 1

    fig.update_xaxes(
        type="log",
        showgrid=True,
    )
    fig.update_yaxes(
        showgrid=True,
        range=[0, 200],
    )
    fig.update_layout(height=700)
    st.plotly_chart(fig, use_container_width=True)

# Thresholds
# ----------------------------------
st.header("Thresholds")

st_min_r2 = st.slider(
    "Min R2",
    min_value=0.5,
    max_value=1.0,
    value=0.80,
    step=0.01,
)

# Effectiveness vs AC50
# ----------------------------------

with col2:

    st.subheader("Effectiveness vs AC50")
    df_sctr = pd.DataFrame(df_sctr)
    df_sctr["color"] = COLORS[: df_sctr.shape[0]]
    df_sctr = df_sctr[df_sctr["R2"] >= st_min_r2].reset_index()
    fig = px.scatter(
        df_sctr,
        x="ac50",
        y="eff",
        color="cell line",
        color_discrete_sequence=df_sctr["color"],
        hover_data=["cell line", "R2"],
        height=700,
    )
    fig.update_xaxes(
        type="log",
        range=[-3.5, 2],
        showgrid=True,
    )
    fig.update_yaxes(
        range=[-100, 250],
        showgrid=True,
    )
    fig.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(
        fig,
        use_container_width=True,
    )

# Trace Combined
st.subheader("Combined Response Curves")
use_full_colors = st.radio("Display lines in full color?", ('No', 'Yes'))

num_cell_lines = len(specimen_ids)

titles = [df_compound_selected['name'][0] + "<br>" + df_compound_selected['NCGC SID'][0]]

EXTENDED_COLORS = COLORS
i_row = 1
i_col = 1
i_tot = 0

r2s = {}
for specimen_id in specimen_ids:
    df = dfs_drc[specimen_id]
    row = df[df["NCGC SID"] == st_ncgc_sid].iloc[0]
    r2s[specimen_id] = row["R2"]

n_cols = 1
n_rows = 1
fig = make_subplots(
    rows=n_rows,
    cols=n_cols,
    shared_xaxes="all",
    shared_yaxes="all",
    vertical_spacing=0.12,
    start_cell="top-left",
    subplot_titles=titles,
)

df_sctr = {
    "cell line": [],
    "ac50": [],
    "eff": [],
    "R2": [],
}

for specimen_id in specimen_ids:

    df = dfs_drc[specimen_id]

    row = df[df["NCGC SID"] == st_ncgc_sid].iloc[0]
    df_sctr["cell line"].append(specimen_id)
    df_sctr["ac50"].append(row["AC50"])
    df_sctr["eff"].append(row["ZERO"] - row["INF"])
    df_sctr["R2"].append(row["R2"])

    if use_full_colors == "Yes":
        i_color = i_tot
        ac50_color = i_tot
    else:
        if specimen_id in syn.den_sis:
            i_color = 8
            ac50_color = 7
        else:
            i_color = 0
            ac50_color = 1
    tr_measured = get_measured_trace(row, color=COLORS[i_color])
    tr_fit = get_fit_trace(row, label=specimen_id, color=EXTENDED_COLORS[i_color], showlegend=True,
                            line_type="solid")
    tr_ac50 = get_ac50_trace(row, color=EXTENDED_COLORS[ac50_color])
    for tr in [tr_fit, tr_ac50]:
        fig.add_trace(tr, row=1, col=1)

    i_tot += 1
    i_col += 1
    if i_col > n_cols:
        i_col = 1
        i_row += 1

fig.update_xaxes(
    type="log",
    showgrid=True,
)
fig.update_yaxes(
    showgrid=True,
    range=[0, 200],
)
fig.update_layout(height=700)
fig.update_layout(hovermode='x unified')
st.plotly_chart(fig, use_container_width=True)

# Cell Lines
# ==================================

# Cell Line selector
# ----------------------------------

st.header("Pick a Cell Line")

cl_grid_response = AgGrid(
    df_clines,
    gridOptions=build_grid_options(df_clines),
    data_return_mode="AS_INPUT",
    update_mode="MODEL_CHANGED",
    # fit_columns_on_grid_load=True,
    width="100%",
)

cl_data = cl_grid_response["data"]
cl_selected = cl_grid_response["selected_rows"]

if cl_selected:
    df_clines_selected = pd.DataFrame(cl_selected)[df_clines.columns]
else:
    df_clines_selected = df_clines.iloc[0:1]

st_specimen_id = df_clines_selected.iloc[0]["specimenID"]

# one cell line
# ---------------------------------
st.header("Selected Cell Line")
st.dataframe(df_clines_selected)

df_sctr = {
    "NCGC SID": [],
    "compound": [],
    "AC50": [],
    "eff": [],
    "target": [],
    "R2": [],
}

df = dfs_drc[st_specimen_id]
for indx, row in df.iterrows():

    if row["R2"] < st_min_r2:
        continue

    df_sctr["NCGC SID"].append(row["NCGC SID"])
    df_sctr["compound"].append(row["name"])
    df_sctr["AC50"].append(row["AC50"])
    df_sctr["eff"].append(row["ZERO"] - row["INF"])
    df_sctr["target"].append(row["target"])
    df_sctr["R2"].append(row["R2"])

df_sctr = pd.DataFrame(df_sctr)
df_sctr = pd.merge(df_sctr, df_compounds[["NCGC SID", "MoA"]], on="NCGC SID")
fig = px.scatter(
    df_sctr,
    x="AC50",
    y="eff",
    hover_data=["compound", "target", "MoA", "R2"],
    color="R2",
    range_color=(0.5, 1),
    height=600,
)
fig.update_xaxes(type="log")
fig.update_yaxes(range=[-100, 250])
st.plotly_chart(
    fig,
    use_container_width=True,
)

# all cell lines
# ---------------------------------
st.header("All Cell Lines")

df_sctr = {
    "NCGC SID": [],
    "compound": [],
    "AC50": [],
    "eff": [],
    "target": [],
    "cell line": [],
    "R2": [],
}

for specimen_id, df in dfs_drc.items():

    for indx, row in df.iterrows():

        if row["R2"] < st_min_r2:
            continue

        df_sctr["NCGC SID"].append(row["NCGC SID"])
        df_sctr["compound"].append(row["name"])
        df_sctr["AC50"].append(row["AC50"])
        df_sctr["eff"].append(row["ZERO"] - row["INF"])
        df_sctr["target"].append(row["target"])
        df_sctr["cell line"].append(specimen_id)
        df_sctr["R2"].append(row["R2"])

df_sctr = pd.DataFrame(df_sctr)
df_sctr = pd.merge(df_sctr, df_compounds[["NCGC SID", "MoA"]], on="NCGC SID")
fig = px.scatter(
    df_sctr,
    x="AC50",
    y="eff",
    hover_data=["compound", "target", "MoA"],
    height=600,
    color="cell line",
    #    color_discrete_sequence=COLORS,
)
fig.update_xaxes(type="log")
fig.update_yaxes(range=[-100, 250])
st.plotly_chart(
    fig,
    use_container_width=True,
)
   


# Distributions
# ==================================

df_plt_drc = df_drc[df_drc["R2"] >= st_min_r2]

# AC50
# ----------------------------------

st.header("Log10 AC50 Distribution")

col1, col2 = st.columns(2)

with col1:
    fig = px.histogram(
        df_plt_drc,
        x="LAC50",
        nbins=50,
        log_x=False,
        height=600,
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig = px.histogram(
        df_plt_drc,
        x="LAC50",
        nbins=50,
        log_x=False,
        facet_col='cell_line',
        facet_col_wrap=3,
        height=600,
    )
    st.plotly_chart(fig, use_container_width=True)

# eff
# ----------------------------------

st.header("eff = Effectiveness = (ZERO - INF) Distribution")

col1, col2 = st.columns(2)

with col1:
    fig = px.histogram(
        df_plt_drc,
        x="eff",
        nbins=50,
        log_x=False,
        height=600,
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig = px.histogram(
        df_plt_drc,
        x="eff",
        nbins=50,
        log_x=False,
        facet_col='cell_line',
        facet_col_wrap=3,
        height=600,
    )
    st.plotly_chart(fig, use_container_width=True)

# AC50 ratios
# ----------------------------------

df_ratios = st.session_state['df_ratios']

df_plt_ratios = df_ratios[
    (df_ratios['num_R2'] >= st_min_r2)
    & (df_ratios['den_R2'] >= st_min_r2)
    ]

st.header("Log10 (AC50_num / AC50_den) Distribution")

fig = px.histogram(
    df_plt_ratios,
    x="Log10 (AC50 ratio)",
    nbins=50,
    facet_row='den_si',
    facet_col='num_si',
    log_x=False,
    height=800,
)

st.plotly_chart(fig, use_container_width=True)

# Eff ratios
# ----------------------------------

st.header("(eff_num / eff_den) Distribution")

fig = px.histogram(
    df_plt_ratios,
    x="eff ratio",
    nbins=50,
    facet_row='den_si',
    facet_col='num_si',
    log_x=False,
    height=800,
)

st.plotly_chart(fig, use_container_width=True)

# Scores
# ----------------------------------

st.header("eff ratio / AC50 ratio Distribution")

fig = px.histogram(
    df_plt_ratios[df_plt_ratios['score'] > 0],
    x="Log10 score",
    nbins=50,
    facet_row='den_si',
    facet_col='num_si',
    log_x=False,
    height=800,
)

st.plotly_chart(fig, use_container_width=True)

# Scores
# ==================================

def agg_to_list(x):
    # print(x.to_markdown())
    # raise
    return [f"{el:.3f}" for el in list(x)]

st.header("Compounds ranked by AC50 ratios")

df_rank_ratios = df_plt_ratios
# df_rank_ratios = df_plt_ratios[
#     (df_plt_ratios["Log10 (AC50 ratio)"] >= st_min_lac50_ratio)
#     & (df_plt_ratios["Log10 (AC50 ratio)"] <= st_max_lac50_ratio)
#     ]

df_ranked = (
    df_rank_ratios
    .groupby(['den_si', 'NCGC SID', 'num_si'])['Log10 (AC50 ratio)']
    .agg([('Log10 (AC50 ratio)', lambda x: x)])
    .reset_index()
)

df_ranked = df_ranked.loc[df_ranked.den_si.isin(syn.den_sis)]
df_ranked = df_ranked.loc[df_ranked.num_si.isin(syn.num_sis)]

df_ranked = pd.merge(df_compounds, df_ranked, on='NCGC SID')
df_ranked = df_ranked.drop(columns='SMILES')
df_ranked_original = df_ranked.copy()

for num_si in syn.num_sis:
    df_ranked_by_num_si = df_ranked_original.loc[df_ranked_original.num_si == num_si]

    df_ranked_by_num_si = df_ranked_by_num_si.rename(columns={
        'Log10 (AC50 ratio)': num_si,
    })

    merged_columns = ['NCGC SID', 'name', 'target', 'MoA', 'den_si', 'num_si']

    df_ranked = pd.merge(df_ranked, df_ranked_by_num_si, how='left',
                            on=merged_columns)

df_ranked_final = (
    df_ranked
    .groupby(['den_si', 'NCGC SID'])['Log10 (AC50 ratio)']
    .agg(['size', 'mean', 'var', agg_to_list])
    .reset_index()
)

df_ranked.drop(columns=['num_si'])
merge_columns = ['NCGC SID', 'den_si']
df_ranked = pd.merge(df_ranked_final, df_ranked, how='left', on=merge_columns)

df_ranked = df_ranked.sort_values(
    ['mean'], ascending=[False],
)
df_ranked = df_ranked.rename(columns={
    'size': 'N Cell Lines',
    'mean': 'mean Log10 AC50 ratios',
    'var': 'variance Log10 AC50 ratios',
    'agg_to_list': 'Log10 AC50 ratios',
})

st_min_num_clines = st.slider(
    "Min Number of Test (tumor) Cell Lines To Appear in Score List",
    min_value=1,
    max_value=6,
    value=4,
    step=1,
)

df_ranked = df_ranked[df_ranked['N Cell Lines'] >= st_min_num_clines]

count = 0
for den_si in syn.den_sis:
    df_ranked_den = df_ranked.loc[df_ranked.den_si == den_si].groupby('NCGC SID').max()
    st.subheader("Reference Line: " + den_si)
    st.write(df_ranked_den)
    st.download_button(
        label="Download data as CSV",
        data=df_ranked_den.to_csv().encode('utf-8'),
        file_name='log_ac50_ratio_mean.csv',
        mime='text/csv',
        key='den_sis_count'+str(count)
    )
    count = count + 1

st.header("Compounds ranked by delta S")

df_rank_ratios = df_plt_ratios
# df_rank_ratios = df_plt_ratios[
#     (df_plt_ratios["Log10 (AC50 ratio)"] > st_min_lac50_ratio)
#     & (df_plt_ratios["Log10 (AC50 ratio)"] < st_max_lac50_ratio)
#     ]

df_ranked = (
    df_rank_ratios
    .groupby(['den_si', 'NCGC SID', 'num_si'])['Log10 score']
    .agg([('Log10 score', lambda x: x)])
    .reset_index()
)

df_ranked = df_ranked.loc[df_ranked.den_si.isin(syn.den_sis)]
df_ranked = df_ranked.loc[df_ranked.num_si.isin(syn.num_sis)]

df_ranked = pd.merge(df_compounds, df_ranked, on='NCGC SID')
df_ranked = df_ranked.drop(columns='SMILES')
df_ranked_original = df_ranked.copy()

for num_si in syn.num_sis:
    # Merge sequence for delta_S
    df_ranked_by_num_si = df_ranked_original.loc[df_ranked_original.num_si == num_si]
    df_ranked_by_num_si = df_ranked_by_num_si.rename(columns={
        'Log10 score': num_si,
    })

    merged_columns = ['NCGC SID', 'name', 'target', 'MoA', 'den_si', 'num_si']

    df_ranked = pd.merge(df_ranked, df_ranked_by_num_si, how='left',
                            on=merged_columns)

df_ranked_delta_s = (
    df_ranked
    .groupby(['den_si', 'NCGC SID'])['Log10 score']
    .agg(['size', 'mean', 'var', agg_to_list])
    .reset_index()
)
df_ranked.drop(columns=['num_si'])
merge_columns = ['NCGC SID', 'den_si']
df_ranked = pd.merge(df_ranked_delta_s, df_ranked, how='left', on=merge_columns)


df_ranked = df_ranked.sort_values(
    ['mean'], ascending=[False],
)
df_ranked = df_ranked.rename(columns={
    'size': 'N Cell Lines',
    'mean': 'mean delta_S',
    'var': 'variance delta_S',
    'agg_to_list': 'delta_S Scores (Log10)',
})

df_ranked = df_ranked[df_ranked['N Cell Lines'] >= st_min_num_clines]

count = 0
for den_si in syn.den_sis:
    df_ranked_den = df_ranked.loc[df_ranked.den_si == den_si].groupby('NCGC SID').max()
    st.subheader("Reference Line: " + den_si)
    st.write(df_ranked_den)
    st.download_button(
        label="Download data as CSV",
        data=df_ranked_den.to_csv().encode('utf-8'),
        file_name='large_df.csv',
        mime='text/csv',
        key='df_count_' + str(count)
    )
    count = count + 1

# Start of S Prime Diplay
st.header("Compounds ranked by delta S prime")
# Reset the context of df_rank_ratios
df_rank_ratios = df_plt_ratios

df_ranked = (
    df_rank_ratios
    .groupby(['den_si', 'NCGC SID', 'num_si'])['delta_s_prime']
    .agg([('Delta S_prime', lambda x: x)])
    .reset_index()
)

df_ranked = df_ranked.loc[df_ranked.den_si.isin(syn.den_sis)]
df_ranked = df_ranked.loc[df_ranked.num_si.isin(syn.num_sis)]

df_ranked = pd.merge(df_compounds, df_ranked, on='NCGC SID')
df_ranked = df_ranked.drop(columns='SMILES')
df_ranked_s_prime_original = df_ranked.copy()

for num_si in syn.num_sis:
    # Merge sequence for delta_s_prime
    df_ranked_by_num_si = df_ranked_s_prime_original.loc[df_ranked_s_prime_original.num_si == num_si]
    df_ranked_by_num_si = df_ranked_by_num_si.rename(columns={
        'Delta S_prime': num_si,
    })

    merged_columns = ['NCGC SID', 'name', 'target', 'MoA', 'den_si', 'num_si']

    df_ranked = pd.merge(df_ranked, df_ranked_by_num_si, how='left',
                            on=merged_columns)

df_ranked_delta_s_prime = (
    df_ranked
    .groupby(['den_si', 'NCGC SID'])['Delta S_prime']
    .agg(['size', 'mean', 'var', agg_to_list])
    .reset_index()
)

df_ranked.drop(columns=['num_si'])
merge_columns = ['NCGC SID', 'den_si']
df_ranked = pd.merge(df_ranked_delta_s_prime, df_ranked, how='left', on=merge_columns)

df_ranked = df_ranked.sort_values(
    ['mean'], ascending=[False],
)
df_ranked = df_ranked.rename(columns={
    'size': 'N Cell Lines',
    'mean': 'mean delta_S_prime',
    'var': 'variance delta_S_prime',
    'agg_to_list': 'delta_S_prime values',
})

# TODO: Should this filter be also applied to S_prime? Currently it is.
df_ranked = df_ranked[df_ranked['N Cell Lines'] >= st_min_num_clines]

count = 0
for den_si in syn.den_sis:
    df_ranked_den = df_ranked.loc[df_ranked.den_si == den_si].groupby('NCGC SID').max()
    st.subheader("Reference Line: " + den_si)
    st.write(df_ranked_den)
    st.download_button(
        label="Download data as CSV",
        data=df_ranked_den.to_csv().encode('utf-8'),
        file_name='large_df.csv',
        mime='text/csv',
        key='df_s_prime_count_' + str(count)
    )
    count = count + 1