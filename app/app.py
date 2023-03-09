from pathlib import Path
import re

import funcy
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from st_aggrid import AgGrid
from st_aggrid import GridOptionsBuilder, GridUpdateMode, DataReturnMode

from syn5522627 import R_COLS, C_COLS, FILE_HIDE_COLS
from syn5522627 import DoseResponseCurve
from syn5522627 import read_metadata, read_raw_drc, make_mrgd_drc, calculate_fit_ratios

st.set_page_config(layout="wide")

def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 Password incorrect")
        return False
    else:
        # Password correct.
        return True

if check_password():

    data_path = Path("syn5522627")

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

    BREWER_12_PAIRED = [
        "#a6cee3",
        "#1f78b4",
        "#b2df8a",
        "#33a02c",
        "#fb9a99",
        "#e31a1c",
        "#fdbf6f",
        "#ff7f00",
        "#cab2d6",
        "#6a3d9a",
        "#ffff99",
        "#b15928",
    ]

    BREWER_12_SET3 = [
        "#8dd3c7",
        "#ffffb3",
        "#bebada",
        "#fb8072",
        "#80b1d3",
        "#fdb462",
        "#b3de69",
        "#fccde5",
        "#d9d9d9",
        "#bc80bd",
        "#ccebc5",
        "#ffed6f",
    ]

    IBM_COLORS = [
        "#648fff",
        "#dc267f",
        "#ffb000",
        "#fe6100",
        "#785ef0",
        "#000000",
        "#ffffff",
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


    df_files, df_clines, file_name_to_specimen_id = read_metadata(data_path)
    file_show_cols = [col for col in df_files.columns if col not in FILE_HIDE_COLS]

    # raw dose-response curve dataframes
    dfs_drc_raw = read_raw_drc(df_files, data_path)

    # create dose-response curve objects
    drcs = {}
    for file_name, df_drc_raw in dfs_drc_raw.items():
        file_row = df_files.loc[file_name][file_show_cols]
        drc = DoseResponseCurve(file_row.to_dict(), df_drc_raw)
        drcs[file_name] = drc

    dfs_drc = make_mrgd_drc(drcs, file_name_to_specimen_id)

    # make one dataframe
    df_drc = pd.DataFrame()
    for si, df1 in dfs_drc.items():
        df1['cell_line'] = si
        df_drc = pd.concat([df_drc, df1])
    df_drc['eff'] = df_drc["ZERO"] - df_drc["INF"]



    # all dose response curves have the same compounds so we just take one
    one_specimen_id = next(iter(dfs_drc.keys()))
    df_compounds = dfs_drc[one_specimen_id]
    df_compounds = df_compounds[["NCGC SID", "name", "target", "MoA", "SMILES"]]

    # calculate all ratios
    df_ratios = calculate_fit_ratios(df_compounds, dfs_drc)


    def get_measured_trace(row, label=None, showlegend=False, color=None):
        cs = row[C_COLS].astype(float).values
        rs = row[R_COLS].astype(float).values
        tr_measured = go.Scatter(
            x=cs,
            y=rs,
            mode="markers",
            name=label,
            showlegend=showlegend,
            marker_color=color,
        )
        return tr_measured


    def get_fit_trace(row, label=None, showlegend=False, color=None):
        cs = row[C_COLS].astype(float).values
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
            line_dash="dot",
        )
        return tr_fit


    def get_ac50_trace(row, label=None, showlegend=False, color=None):
        rs = row[R_COLS].astype(float).values
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
            groupSelectsChildren="Group checkbox select children",
        )
        gridOptions = gb.build()
        return gridOptions


    # Sidebar
    # ==================================

    with st.sidebar:

        # Compound selector
        # ----------------------------------

        st.header("Compounds")

        cmp_grid_response = AgGrid(
            df_compounds,
            gridOptions=build_grid_options(df_compounds),
            data_return_mode="AS_INPUT",
            update_mode="MODEL_CHANGED",
            #        fit_columns_on_grid_load=True,
            height=500,
            #    width='100%',
        )

        cmp_data = cmp_grid_response["data"]
        cmp_selected = cmp_grid_response["selected_rows"]

        if cmp_selected:
            df_compound_selected = pd.DataFrame(cmp_selected)[df_compounds.columns]
        else:
            df_compound_selected = df_compounds.iloc[0:1]

        st_ncgc_sid = df_compound_selected.iloc[0]["NCGC SID"]

        # Cell Line selector
        # ----------------------------------

        st.header("Cell Lines")

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

        # Thresholds
        # ----------------------------------
        st.header("Thresholds")

        fig = px.histogram(
            df_drc,
            x="R2",
            nbins=50,
            log_x=False,
            height=300,
        )
        st.plotly_chart(fig, use_container_width=True)


        st_min_r2 = st.slider(
            "Min R2",
            min_value=0.5,
            max_value=1.0,
            value=0.85,
            step=0.01,
        )
        st_min_lac50_ratio = st.slider(
            "Min Log10(AC50 Ratio)",
            min_value=-4.0,
            max_value=4.0,
            value=0.2,
            step=0.1,
        )
        st_max_lac50_ratio = st.slider(
            "Max Log10(AC50 Ratio)",
            min_value=-4.0,
            max_value=4.0,
            value=4.0,
            step=0.1,
        )
        st_min_num_clines = st.slider(
            "Min Number of Test (tumor) Cell Lines",
            min_value=1,
            max_value=6,
            value=3,
            step=1,
        )

    # Compounds
    # ==================================

    st.header("Selected Compound")
    st.dataframe(df_compound_selected)

    col1, col2 = st.columns([2,2])

    # Dose Response Curves
    # ----------------------------------

    with col1:

        st.subheader("Dose Response Curves")
        specimen_ids = df_clines.sort_values("disease")['specimenID']
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


    # Cell Lines
    # ==================================

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
        df_plt_ratios[df_plt_ratios['score']>0],
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
        return [f"{el:.3f}" for el in list(x)]

    st.header("Compounds ranked by AC50 ratios")

    df_rank_ratios = df_plt_ratios[
        (df_plt_ratios["Log10 (AC50 ratio)"] > st_min_lac50_ratio)
        & (df_plt_ratios["Log10 (AC50 ratio)"] < st_max_lac50_ratio)
    ]

    df_ranked = (
        df_rank_ratios
        .groupby(['den_si', 'NCGC SID'])['Log10 (AC50 ratio)']
        .agg(['size', 'mean', 'var', agg_to_list])
        .reset_index()
    )

    df_ranked = df_ranked[df_ranked['size'] >= st_min_num_clines]
    df_ranked = pd.merge(df_compounds, df_ranked, on='NCGC SID')
    df_ranked = df_ranked.drop(columns='SMILES').sort_values(
        ['mean'], ascending=[False],
    )

    df_ranked = df_ranked.rename(columns={
        'size': 'N Cell Lines',
        'mean': 'mean Log10 AC50 ratios',
        'var': 'variance Log10 AC50 ratios',
        'agg_to_list': 'Log10 AC50 ratios',
    })

    for den_si, df_ranked_den in df_ranked.groupby('den_si'):
        st.subheader(den_si)
        st.write(df_ranked_den)


    st.header("Compounds ranked by (eff ratio) / (AC50 ratio)")

    df_rank_ratios = df_plt_ratios[
        (df_plt_ratios["Log10 (AC50 ratio)"] > st_min_lac50_ratio)
        & (df_plt_ratios["Log10 (AC50 ratio)"] < st_max_lac50_ratio)
    ]

    df_ranked = (
        df_rank_ratios
        .groupby(['den_si', 'NCGC SID'])['Log10 score']
        .agg(['size', 'mean', 'var', agg_to_list])
        .reset_index()
    )

    df_ranked = df_ranked[df_ranked['size'] >= st_min_num_clines]
    df_ranked = pd.merge(df_compounds, df_ranked, on='NCGC SID')
    df_ranked = df_ranked.drop(columns='SMILES').sort_values(
        ['mean'], ascending=[False],
    )

    df_ranked = df_ranked.rename(columns={
        'size': 'N Cell Lines',
        'mean': 'mean Log10 score',
        'var': 'variance Log10 score',
        'agg_to_list': 'Log10 scores',
    })

    for den_si, df_ranked_den in df_ranked.groupby('den_si'):
        st.subheader(den_si)
        st.write(df_ranked_den)





    # Raw Data
    # ==================================


    def show_raw_data(drcs):
        for smm_name_group in SMM_NAME_GROUPS:

            col1, col2 = st.columns(2)

            with col1:
                smm_name = smm_name_group[0]
                drc = drcs[smm_name]

                st.header(smm_name)
                st.write(f"df_raw.shape: {drc.df_raw.shape}")
                st.write(drc.smm_hts)
                st.write(drc.df_raw.head(10))

                fig = px.histogram(drc.df["LAC50"])
                c_min = np.log10(drc.df_raw[drc.raw_cols_conc[0]].min())
                c_max = np.log10(drc.df_raw[drc.raw_cols_conc[-1]].max())

                fig.add_vline(x=c_min, line_color=IBM_COLORS[1])
                fig.add_vline(x=c_max, line_color=IBM_COLORS[1])
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                if len(smm_name_group) > 1:
                    smm_name = smm_name_group[1]
                    drc = drcs[smm_name]

                    st.header(smm_name)
                    st.write(f"df_raw.shape: {drc.df_raw.shape}")
                    st.write(drc.smm_hts)
                    st.write(drc.df_raw.head(10))

                    fig = px.histogram(drc.df["LAC50"])
                    c_min = np.log10(drc.df_raw[drc.raw_cols_conc[0]].min())
                    c_max = np.log10(drc.df_raw[drc.raw_cols_conc[-1]].max())

                    fig.add_vline(x=c_min, line_color=IBM_COLORS[1])
                    fig.add_vline(x=c_max, line_color=IBM_COLORS[1])
                    st.plotly_chart(fig, use_container_width=True)


    show_raw_data_flag = st.checkbox("Show Raw Data", value=False)
    if show_raw_data_flag:
        st.header("SYNAPSE_METADATA_MANIFEST.csv")
        st.dataframe(df_smm_hts[smm_show_cols])
        st.header("Merged Cell Line Metadata")
        AgGrid(df_clines)
        show_raw_data(drcs)
