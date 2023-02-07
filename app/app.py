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

# standardized column names for response and concentration
R_COLS = [f"DATA{ii}" for ii in range(11)]
C_COLS = [f"CONC{ii}" for ii in range(11)]

# pairs of files that represent the same cell line
# the top member is from the top level of the synapse dataset
# the bottom member is from the matrix portal raw data folder
SMM_NAME_GROUPS = [
    (
        "NTAP ipNF02.3 2l MIPE qHTS.csv",
        "s-ntap-1PNO-1",
    ),
    (
        "NTAP_ipNF95.11bC_MIPE_qHTS.csv",
        "s-ntap-IPNF95-1bc-1",
    ),
    (
        "NTAP ipNF02.8 MIPE qHTS.csv",
        "s-ntap-ipn02.8-1",
    ),
    (
        "NTAP ipNF05.5 SC MIPE qHTS.csv",
        "s-ntap-IPNF05_5_P31-1",
    ),
    (
        "NTAP ipNF05.5 MC MIPE qHTS.csv",
        "s-ntap-IPNF05_5_P30-1",
    ),
    (
        "NTAP ipNF06.2A MIPE qHTS.csv",
        "s-ntap-IPNF06_2A_P27-1",
    ),
    (
        "NTAP ipNF95.6 MIPE qHTS.csv",
        "s-ntap-IPNF95_6_P53-1",
    ),
    (
        "NTAP ipnNF95.11C MIPE qHTS.csv",
        "s-ntap-ipnNF95_11C_P31-1",
    ),
    (
        "NTAP ipNF95.11b C_T MIPE qHTS.csv",
        "s-ntap-IPNF95_11b_P53-1",
    ),
    (
        "s-ntap-HFF-1.csv",
        "s-ntap-HFF-1",
    ),
    ("s-ntap-MTC-1.csv",),
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


class DoseResponseCurve:
    def __init__(self, smm_hts, df_raw):
        self.smm_hts = smm_hts
        self.df_raw = df_raw

        self.set_concentration_multipliers()
        self.create_df()

    @property
    def raw_col_hill(self):
        for col in ["HILL", "Hill"]:
            if col in self.df_raw.columns:
                return col

    @property
    def raw_col_inf(self):
        for col in ["INF", "Infinity"]:
            if col in self.df_raw.columns:
                return col

    @property
    def raw_col_zero(self):
        for col in ["ZERO", "Zero"]:
            if col in self.df_raw.columns:
                return col

    @property
    def raw_col_name(self):
        for col in ["Name", "name"]:
            if col in self.df_raw.columns:
                return col

    @property
    def raw_col_target(self):
        for col in ["Target", "target"]:
            if col in self.df_raw.columns:
                return col

    @property
    def raw_col_ncgc(self):
        for col in ["NCGC SID", "NCGCID", "SID"]:
            if col in self.df_raw.columns:
                return col

    @property
    def raw_col_smiles(self):
        for col in ["SMILES", "smi"]:
            if col in self.df_raw.columns:
                return col

    @property
    def raw_cols_conc(self):
        if "C1" in self.df_raw.columns:
            c_cols = [col for col in self.df_raw.columns if re.match("C\d+", col)]

        if "CONC1" in self.df_raw.columns:
            c_cols = [col for col in self.df_raw.columns if re.match("CONC\d+", col)]

        assert len(c_cols) == 11
        return c_cols

    @property
    def raw_cols_resp(self):
        if "DATA1" in self.df_raw.columns:
            r_cols = [col for col in self.df_raw.columns if re.match("DATA\d+", col)]

        assert len(r_cols) == 11
        return r_cols

    def create_df(self):

        self.df = pd.DataFrame()
        self.df["NCGC SID"] = self.df_raw[self.raw_col_ncgc]
        self.df["name"] = self.df_raw[self.raw_col_name].values
        self.df["target"] = self.df_raw[self.raw_col_target].values

        if "MoA" in self.df_raw.columns:
            self.df["MoA"] = self.df_raw["MoA"]

        if "R2" in self.df_raw.columns:
            self.df["R2"] = self.df_raw["R2"]

        # set AC50 and LAC50
        if "AC50" in self.df_raw.columns:
            self.df["AC50"] = self.df_raw["AC50"].values * self.ac50_mult

        if "LAC50" in self.df_raw.columns:
            self.df["LAC50"] = self.df_raw["LAC50"].values + np.log10(self.ac50_mult)

        if "AC50" in self.df.columns and "LAC50" not in self.df.columns:
            self.df["LAC50"] = np.log10(self.df["AC50"])

        if "LAC50" in self.df.columns and "AC50" not in self.df.columns:
            self.df["AC50"] = 10 ** self.df["LAC50"]

        assert "AC50" in self.df.columns and "LAC50" in self.df.columns

        self.df["HILL"] = self.df_raw[self.raw_col_hill].values
        self.df["INF"] = self.df_raw[self.raw_col_inf].values
        self.df["ZERO"] = self.df_raw[self.raw_col_zero].values
        self.df["SMILES"] = self.df_raw[self.raw_col_smiles].values

        for ii, col in enumerate(self.raw_cols_conc):
            self.df[C_COLS[ii]] = self.df_raw[col].values * self.c_mult

        for ii, col in enumerate(self.raw_cols_resp):
            self.df[R_COLS[ii]] = self.df_raw[col].values

    def set_concentration_multipliers(self):
        """Set multipliers to turn concentrations into micromolars"""

        # AC50 is in molar units
        # concentration column is in micromolars
        group_1 = [
            "NTAP ipNF02.3 2l MIPE qHTS.csv",
            "NTAP ipNF05.5 MC MIPE qHTS.csv",
            "NTAP ipNF06.2A MIPE qHTS.csv",
            "NTAP ipnNF95.11C MIPE qHTS.csv",
            "NTAP ipNF02.8 MIPE qHTS.csv",
            "NTAP ipNF95.11b C_T MIPE qHTS.csv",
            "NTAP ipNF05.5 SC MIPE qHTS.csv",
            "NTAP ipNF95.6 MIPE qHTS.csv",
            "s-ntap-HFF-1.csv",
            "s-ntap-MTC-1.csv",
        ]

        # AC50 is in micromolars
        # concentration is in molar units
        group_2 = [
            "NTAP_ipNF95.11bC_MIPE_qHTS.csv",
            "s-ntap-IPNF95_11b_P53-1",
            "s-ntap-HFF-1",
            "s-ntap-IPNF06_2A_P27-1",
            "s-ntap-IPNF95-1bc-1",
            "s-ntap-1PNO-1",
            "s-ntap-IPNF95_6_P53-1",
            "s-ntap-IPNF05_5_P30-1",
            "s-ntap-IPNF05_5_P31-1",
            "s-ntap-ipn02.8-1",
            "s-ntap-ipnNF95_11C_P31-1",
        ]

        if self.smm_hts["name"] in group_1:
            self.ac50_mult = 1e6
            self.c_mult = 1.0
        elif self.smm_hts["name"] in group_2:
            self.ac50_mult = 1.0
            self.c_mult = 1e6
        else:
            raise ValueError()

    def get_non_rc_cols(self):
        return [col for col in self.df.columns if col not in C_COLS + R_COLS]

    def get_compound_cols(self):
        return ["NCGC SID", "name", "target", "SMILES"]


def read_metadata(data_path):

    # text file with some variable definitions
    df_qhts_pdh = pd.read_csv(
        data_path / "qhts-protocol-dump-headers.txt",
        header=None,
    )

    # data manifest for matrix portal data
    df_ssm = pd.read_csv(
        data_path / "matrix portal raw data/synapse_storage_manifest.csv",
    )

    # data manifest for all files
    # might only be present when syncing with python client
    # this is the main metadata file we use
    df_smm = pd.read_csv(
        data_path / "SYNAPSE_METADATA_MANIFEST.tsv",
        sep="\t",
    )
    # only keep file descriptions for dose response curves
    df_smm_hts = df_smm[
        df_smm["name"].apply(lambda x: "ntap" in x.lower())
    ].reset_index(drop=True)

    # sort by file pairs
    df_smm_hts = df_smm_hts.set_index("name")
    df_smm_hts = df_smm_hts.loc[funcy.flatten(SMM_NAME_GROUPS)]
    df_smm_hts = df_smm_hts.reset_index()

    # files in the top level synapse directory are labeled "processed"
    # files in the matrix portal raw data folder a labeled "raw"
    proc_indxs = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20]
    raw_indxs = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19]

    smm_name_to_specimen_id = {}
    for pi, ri in zip(proc_indxs, raw_indxs + [20]):
        specimen_id = df_smm_hts.iloc[pi]["specimenID"]
        name_p = df_smm_hts.iloc[pi]["name"]
        name_r = df_smm_hts.iloc[ri]["name"]
        smm_name_to_specimen_id[name_p] = specimen_id
        smm_name_to_specimen_id[name_r] = specimen_id

    # merge the metadata from each file pair
    specimen_ids = df_smm_hts.iloc[proc_indxs]["specimenID"].values

    df_ssm_mrgd = pd.DataFrame(index=specimen_ids)
    df_ssm_mrgd["disease"] = df_smm_hts.iloc[proc_indxs]["disease"].values
    df_ssm_mrgd["nf1Genotype"] = df_smm_hts.iloc[proc_indxs]["nf1Genotype"].values
    df_ssm_mrgd["nf2Genotype"] = df_smm_hts.iloc[proc_indxs]["nf2Genotype"].values
    df_ssm_mrgd["tissue"] = df_smm_hts.iloc[proc_indxs]["tissue"].values
    df_ssm_mrgd["organ"] = df_smm_hts.iloc[proc_indxs]["organ"].values
    df_ssm_mrgd["species"] = df_smm_hts.iloc[proc_indxs]["species"].values
    df_ssm_mrgd["cellType"] = df_smm_hts.iloc[proc_indxs]["cellType"].values

    df_ssm_mrgd["sex"] = list(df_smm_hts.iloc[raw_indxs]["sex"].values) + [None]
    df_ssm_mrgd["tumorType"] = list(df_smm_hts.iloc[raw_indxs]["tumorType"].values) + [
        None
    ]
    df_ssm_mrgd["diagnosis"] = list(df_smm_hts.iloc[raw_indxs]["diagnosis"].values) + [
        None
    ]
    df_ssm_mrgd["modelSystemName"] = list(
        df_smm_hts.iloc[raw_indxs]["modelSystemName"].values
    ) + [None]

    # fixups for NA
    for col in ["tumorType", "diagnosis"]:
        df_ssm_mrgd[col] = df_ssm_mrgd[col].apply(
            lambda x: x if x != "Not Applicable" else None
        )

    # fixups for ipNF95.11bC processes says +/- raw says -/-
    df_ssm_mrgd.loc["ipNF95.11bC", "nf1Genotype"] = "-/-, +/-"
    df_ssm_mrgd.index.name = "specimenID"

    return df_qhts_pdh, df_ssm, df_smm, df_smm_hts, df_ssm_mrgd, smm_name_to_specimen_id


def read_raw_hts(df_smm_hts):
    """Read all dose response curve files"""
    dfs_raw = {}
    for indx, row in df_smm_hts.iterrows():
        if row["name"].endswith("csv"):
            path_suffix = Path(row["name"])
        else:
            path_suffix = Path("matrix portal raw data") / row["name"]
        file_path = data_path / path_suffix
        df = pd.read_csv(file_path)
        dfs_raw[row["name"]] = df
    return dfs_raw


def make_mrgd_hts(drcs, smm_name_to_specimen_id):
    """Merge data from pairs of dose response curve files"""
    dfs_mrgd = {}
    for name, drc in drcs.items():
        specimen_id = smm_name_to_specimen_id[name]
        if specimen_id in dfs_mrgd:
            for col in drc.df.columns:
                if not col in dfs_mrgd[specimen_id]:
                    dfs_mrgd[specimen_id][col] = drc.df[col]

        else:
            dfs_mrgd[specimen_id] = drc.df.copy()

    return dfs_mrgd


if check_password():

    data_path = Path("/home/gatlay/syn5522627")

    (
        df_qhts_pdh,
        df_ssm,
        df_smm,
        df_smm_hts,
        df_smm_mrgd,
        smm_name_to_specimen_id,
    ) = read_metadata(data_path)


    smm_hide_cols = [
        "index",
        "path",
        "parent",
        "id",
        "synapseStore",
        "contentType",
        "used",
        "executed",
        "activityName",
        "experimentalTimepoint",
        "timePointUnit",
        "accessType",
        "activityDescription",
        "studyId",
        "fundingAgency",
        "isPrimaryCell",
        "entityId",
        "Resource_id",
        "isCellLine",
        "resourceType",
        "experimentalCondition",
        "reporterGene",
        "accessTeam",
        "cellLineMetadataSynId",
        "specimenMetadataSynId",
        "initiative",
        "isMultiIndividual",
        "fileFormat",
        "assay",
        "individualMetadataSynId",
        "studyName",
        "isMultiSpecimen",
        "eTag",
        "reporterSubstance",
        "dataType",
        "drugScreenType",
    ]
    smm_show_cols = [col for col in df_smm_hts.columns if col not in smm_hide_cols]


    dfs_raw = read_raw_hts(df_smm_hts)


    drcs = {}
    for smm_name, df_raw in dfs_raw.items():
        rows = df_smm_hts[df_smm_hts["name"] == smm_name][smm_show_cols]
        assert rows.shape[0] == 1
        row = rows.iloc[0]
        drc = DoseResponseCurve(row.to_dict(), df_raw)
        drcs[smm_name] = drc

    dfs_mrgd = make_mrgd_hts(drcs, smm_name_to_specimen_id)

    # all df_mrgd have the same compounds
    df_compounds = dfs_mrgd[next(iter(dfs_mrgd.keys()))]
    df_compounds = df_compounds[["NCGC SID", "name", "target", "MoA", "SMILES"]]

    # with st.sidebar:
    #     st.header("Cell Line")
    #     st_specimen_id = st.selectbox("Specimen ID", df_smm_mrgd.index)
    #     st.write(df_smm_mrgd.loc[st_specimen_id].to_dict())

    #     st.header("Compound")
    #     unique_ncgc_sids = set()
    #     for smm_name, drc in drcs.items():
    #         unique_ncgc_sids.update(drc.df["NCGC SID"].unique())
    #     unique_ncgc_sids = sorted(list(unique_ncgc_sids))
    #     st_ncgc_sid = st.selectbox("NCGC SID", unique_ncgc_sids)

    #     tmp_row = dfs_mrgd[st_specimen_id][dfs_mrgd[st_specimen_id]["NCGC SID"] == st_ncgc_sid]
    #     st.write(tmp_row[["NCGC SID", "name", "target", "MoA", "SMILES"]].iloc[0].to_dict())


    tab1, tab2, tab3 = st.tabs(["Raw Data", "Compound Explorer", "Cell Line Explorer"])

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


    with tab1:
        st.header("SYNAPSE_METADATA_MANIFEST.csv")
        st.dataframe(df_smm_hts[smm_show_cols])
        st.header("Merged Cell Line Metadata")
        st.dataframe(df_smm_mrgd)
        AgGrid(df_smm_mrgd.reset_index())
        show_raw_data(drcs)


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
        gb.configure_pagination(paginationAutoPageSize=True)
        gb.configure_side_bar()
        gb.configure_selection(
            'single',
            use_checkbox=True,
            groupSelectsChildren="Group checkbox select children",
        )
        gridOptions = gb.build()
        return gridOptions


    with tab2:

        st.header("All Compounds")
        #st.dataframe(df_compounds)
        #AgGrid(df_compounds)

        cmp_gridOptions = build_grid_options(df_compounds)
        cmp_grid_response = AgGrid(
            df_compounds,
            gridOptions=cmp_gridOptions,
            data_return_mode='AS_INPUT',
            update_mode='MODEL_CHANGED',
            fit_columns_on_grid_load=True,
    #        theme='blue', #Add theme color to the table
    #        enable_enterprise_modules=True,
            height=500,
            width='100%',
    #        reload_data=True
        )

        cmp_data = cmp_grid_response['data']
        cmp_selected = cmp_grid_response['selected_rows']

        st.header("Selected Compound")
        if cmp_selected:
            df_compound_selected = pd.DataFrame(cmp_selected)[df_compounds.columns]
        else:
            df_compound_selected = df_compounds.iloc[0:1]

        st.dataframe(df_compound_selected)
        st_ncgc_sid = df_compound_selected.iloc[0]["NCGC SID"]

        st.header("Dose Response Curves")
        # specimen_ids = list(dfs_mrgd.keys())
        specimen_ids = df_smm_mrgd.sort_values("disease").index
        num_cell_lines = len(specimen_ids)

        n_cols = 4
        n_rows = 3
        fig = make_subplots(
            rows=n_rows,
            cols=n_cols,
            shared_xaxes="all",
            shared_yaxes="all",
            vertical_spacing=0.05,
            start_cell="top-left",
            subplot_titles=specimen_ids,
        )

        i_row = 1
        i_col = 1
        i_tot = 0

        df_sctr = {
            "cell line": [],
            "ac50": [],
            "eff": [],
        }
        for specimen_id in specimen_ids:

            df = dfs_mrgd[specimen_id]

            row = df[df["NCGC SID"] == st_ncgc_sid].iloc[0]
            df_sctr["cell line"].append(specimen_id)
            df_sctr["ac50"].append(row["AC50"])
            df_sctr["eff"].append(row["ZERO"] - row["INF"])

            i_color = i_tot
            tr_measured = get_measured_trace(row, color=BREWER_12_SET3[i_color])
            tr_fit = get_fit_trace(row, color=BREWER_12_SET3[i_color])
            tr_ac50 = get_ac50_trace(row, color=BREWER_12_SET3[i_color])
            for tr in [tr_measured, tr_fit, tr_ac50]:
                fig.add_trace(tr, row=i_row, col=i_col)

            i_tot += 1
            i_col += 1
            if i_col > n_cols:
                i_col = 1
                i_row += 1

        fig.update_xaxes(
            type="log"
        )  # , gridwidth=0.1, gridcolor="white") # , title="Dose")
        fig.update_yaxes(
            showgrid=True
        )  # , gridwidth=0.1, gridcolor="white") # title="Response")
        fig.update_layout(height=800)
        st.plotly_chart(fig, use_container_width=True)

        st.header("Effectiveness vs Potentcy")
        df_sctr = pd.DataFrame(df_sctr)
        fig = px.scatter(
            df_sctr,
            x="ac50",
            y="eff",
            color="cell line",
            hover_data=["cell line"],
            height=600,
        )
        fig.update_xaxes(type="log")
        st.plotly_chart(
            fig,
            use_container_width=True,
        )

    with tab3:

        st.header("Cell Lines")
    #    st.dataframe(df_smm_mrgd)


        cl_gridOptions = build_grid_options(df_smm_mrgd.reset_index())
        cl_grid_response = AgGrid(
            df_smm_mrgd.reset_index(),
            gridOptions=cl_gridOptions,
            data_return_mode='AS_INPUT',
            update_mode='MODEL_CHANGED',
            fit_columns_on_grid_load=True,
            width='100%',
            #reload_data=True
        )

        cl_data = cl_grid_response['data']
        cl_selected = cl_grid_response['selected_rows']

        st.header("Selected Cell Line")
        if cl_selected:
            df_smm_mrgd_selected = pd.DataFrame(cl_selected)[df_smm_mrgd.reset_index().columns]
        else:
            df_smm_mrgd_selected = df_smm_mrgd.reset_index().iloc[0:1]

        st.dataframe(df_smm_mrgd_selected)
        st_specimen_id = df_smm_mrgd_selected.iloc[0]["specimenID"]

        df_sctr = {
            "NCGC SID": [],
            "compound": [],
            "AC50": [],
            "eff": [],
            "target": [],
            #"MoA": [],
        }

        df = dfs_mrgd[st_specimen_id]
        for indx, row in df.iterrows():

            df_sctr["NCGC SID"].append(row["NCGC SID"])
            df_sctr["compound"].append(row["name"])
            df_sctr["AC50"].append(row["AC50"])
            df_sctr["eff"].append(row["ZERO"] - row["INF"])
            df_sctr["target"].append(row["target"])
            #df_sctr["MoA"].append(row["MoA"])

        df_sctr = pd.DataFrame(df_sctr)
        df_sctr = pd.merge(df_sctr, df_compounds[["NCGC SID", "MoA"]], on="NCGC SID")
        fig = px.scatter(
            df_sctr,
            x="AC50",
            y="eff",
            hover_data=["compound", "target", "MoA"],
            height=600,
            #color="MoA",
        )
        fig.update_xaxes(type="log")
        st.plotly_chart(
            fig,
            use_container_width=True,
        )



        st.header(st_specimen_id)
        st.write(dfs_mrgd[st_specimen_id].head(10))




        iloc = st.number_input(
            "sample index",
            min_value=0,
            max_value=dfs_mrgd[specimen_id].shape[0] - 1,
            value=0,
        )

        row = dfs_mrgd[specimen_id].iloc[iloc][
            [col for col in dfs_mrgd[specimen_id].columns if col not in C_COLS + R_COLS]
        ]
        st.write(row.to_dict())
