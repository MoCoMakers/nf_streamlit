"""
Tools for analyzing "Drug Screenging of pNF Cell Lines"
Single Agent Screens
https://www.synapse.org/#!Synapse:syn5522627

files included in the dataset above are,

.
├── aucRecalculatedFromNCATSscreens_nplr.txt
├── ipNF95_11bC_after_correction.png
├── ipNF95_11bC_before_correction.png
├── matrix portal raw data
│   ├── s-ntap-1PNO-1
│   ├── s-ntap-HFF-1
│   ├── s-ntap-ipn02.8-1
│   ├── s-ntap-IPNF05_5_P30-1
│   ├── s-ntap-IPNF05_5_P31-1
│   ├── s-ntap-IPNF06_2A_P27-1
│   ├── s-ntap-IPNF95_11b_P53-1
│   ├── s-ntap-IPNF95-1bc-1
│   ├── s-ntap-IPNF95_6_P53-1
│   ├── s-ntap-ipnNF95_11C_P31-1
│   ├── SYNAPSE_METADATA_MANIFEST.tsv
│   └── synapse_storage_manifest.csv
├── NTAP ipNF02.3 2l MIPE qHTS.csv
├── NTAP ipNF02.8 MIPE qHTS.csv
├── NTAP ipNF05.5 MC MIPE qHTS.csv
├── NTAP ipNF05.5 SC MIPE qHTS.csv
├── NTAP ipNF06.2A MIPE qHTS.csv
├── NTAP_ipNF95.11bC_MIPE_qHTS.csv
├── NTAP ipNF95.11b C_T MIPE qHTS.csv
├── NTAP ipNF95.6 MIPE qHTS.csv
├── NTAP ipnNF95.11C MIPE qHTS.csv
├── qhts-protocol-dump-headers.txt
├── s-ntap-HFF-1.csv
├── s-ntap-MTC-1.csv
└── SYNAPSE_METADATA_MANIFEST.tsv

"""
from pathlib import Path
import re
from typing import Dict, List, Iterable

import funcy
import numpy as np
import pandas as pd

# standardized column names for response and concentration
R_COLS = [f"DATA{ii}" for ii in range(11)]
C_COLS = [f"CONC{ii}" for ii in range(11)]


# pairs of files that represent the same cell line
# the top member is from the top level of the synapse dataset
# the bottom member is from the matrix portal raw data folder
FILE_NAME_GROUPS = [
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

FILE_HIDE_COLS = [
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

    # data manifest for all files
    # might only be present when syncing with python client
    # this is the main metadata file we use
    df_files = pd.read_csv(
        data_path / "SYNAPSE_METADATA_MANIFEST.tsv",
        sep="\t",
    )

    # only keep file descriptions for cell line dose response curves
    df_files = df_files[
        df_files["name"].apply(lambda x: "ntap" in x.lower())
    ].reset_index(drop=True)

    # sort by file pairs
    df_files = df_files.set_index("name")
    df_files = df_files.loc[funcy.flatten(FILE_NAME_GROUPS)]
    df_files = df_files.reset_index()

    # files in the top level synapse directory are labeled "processed"
    # files in the matrix portal raw data folder a labeled "raw"
    proc_indxs = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20]
    raw_indxs = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19]

    file_name_to_specimen_id = {}
    for pi, ri in zip(proc_indxs, raw_indxs + [20]):
        specimen_id = df_files.iloc[pi]["specimenID"]
        name_p = df_files.iloc[pi]["name"]
        name_r = df_files.iloc[ri]["name"]
        file_name_to_specimen_id[name_p] = specimen_id
        file_name_to_specimen_id[name_r] = specimen_id

    # merge the metadata from each file pair
    specimen_ids = df_files.iloc[proc_indxs]["specimenID"].values

    df_clines = pd.DataFrame(index=specimen_ids)
    df_clines["disease"] = df_files.iloc[proc_indxs]["disease"].values
    df_clines["nf1Genotype"] = df_files.iloc[proc_indxs]["nf1Genotype"].values
    df_clines["nf2Genotype"] = df_files.iloc[proc_indxs]["nf2Genotype"].values
    df_clines["tissue"] = df_files.iloc[proc_indxs]["tissue"].values
    df_clines["organ"] = df_files.iloc[proc_indxs]["organ"].values
    df_clines["species"] = df_files.iloc[proc_indxs]["species"].values
    df_clines["cellType"] = df_files.iloc[proc_indxs]["cellType"].values

    df_clines["sex"] = list(df_files.iloc[raw_indxs]["sex"].values) + [None]
    df_clines["tumorType"] = list(df_files.iloc[raw_indxs]["tumorType"].values) + [None]
    df_clines["diagnosis"] = list(df_files.iloc[raw_indxs]["diagnosis"].values) + [None]
    df_clines["modelSystemName"] = list(
        df_files.iloc[raw_indxs]["modelSystemName"].values
    ) + [None]

    # fixups for NA
    for col in ["tumorType", "diagnosis"]:
        df_clines[col] = df_clines[col].apply(
            lambda x: x if x != "Not Applicable" else None
        )

    # fixups for ipNF95.11bC processes says +/- raw says -/-
    df_clines.loc["ipNF95.11bC", "nf1Genotype"] = "-/-, +/-"
    df_clines.index.name = "specimenID"

    df_files = df_files.set_index("name", drop=False, verify_integrity=True)

    # drop cell line with no R2 (ipNF95.11bC)
    drop_fns = ["NTAP_ipNF95.11bC_MIPE_qHTS.csv", "s-ntap-IPNF95-1bc-1"]
    drop_cline = "ipNF95.11bC"
    df_files = df_files[~df_files["name"].isin(drop_fns)]
    df_clines = df_clines.drop(drop_cline)
    file_name_to_specimen_id = {
        fn: si for fn, si in file_name_to_specimen_id.items() if fn not in drop_fns
    }

    # drop mouse line
    drop_fns = ["s-ntap-MTC-1.csv"]
    drop_cline = "MTC"
    df_files = df_files[~df_files["name"].isin(drop_fns)]
    df_clines = df_clines.drop(drop_cline)
    file_name_to_specimen_id = {
        fn: si for fn, si in file_name_to_specimen_id.items() if fn not in drop_fns
    }

    # sort cell lines
    df_clines = df_clines.sort_values(
        by=['disease', 'nf1Genotype'],
        ascending=[True, False],
    )

    # reset index for cell lines
    df_clines = df_clines.reset_index()

    return df_files, df_clines, file_name_to_specimen_id


def read_raw_drc(df_files, data_path):
    """Read all dose response curve files"""
    dfs = {}
    for file_name, row in df_files.iterrows():
        if file_name.endswith("csv"):
            path_suffix = Path(file_name)
        else:
            path_suffix = Path("matrix portal raw data") / file_name
        file_path = data_path / path_suffix
        df = pd.read_csv(file_path)
        dfs[file_name] = df
    return dfs


def make_mrgd_drc(drcs, file_name_to_specimen_id):
    """Merge data from pairs of dose response curve files"""
    dfs = {}
    for file_name, drc in drcs.items():
        specimen_id = file_name_to_specimen_id[file_name]
        if specimen_id in dfs:
            for col in drc.df.columns:
                if not col in dfs[specimen_id]:
                    dfs[specimen_id][col] = drc.df[col]

        else:
            dfs[specimen_id] = drc.df.copy()

    return dfs


def calculate_fit_ratios(df_compounds, dfs_drc_in):
    dfs_drc = {si: df.set_index("NCGC SID") for si, df in dfs_drc_in.items()}

    den_sis = ["ipn02.3", "ipn02.8", "HFF", "ipnNF95.11c"]
    num_sis = [
        "ipNF05.5",
        "ipNF05.5 (mixed clone)",
        "ipNF06.2A",
        "ipNF95.6",
        "ipNF95.11bC_T",
    ]
    df_ratios = pd.DataFrame()

    for num_si in num_sis:
        for den_si in den_sis:

            df = df_compounds.copy().set_index("NCGC SID")
            df["num_si"] = num_si
            df["den_si"] = den_si
            df["num_R2"] = dfs_drc[num_si]["R2"]
            df["den_R2"] = dfs_drc[den_si]["R2"]

            num_ac50 = dfs_drc[num_si]["AC50"]
            den_ac50 = dfs_drc[den_si]["AC50"]
            df["num_AC50"] = num_ac50
            df["den_AC50"] = den_ac50
            df["AC50 ratio"] = num_ac50 / den_ac50
            df["Log10 (AC50 ratio)"] = np.log10(df["AC50 ratio"])

            num_eff = dfs_drc[num_si]["ZERO"] - dfs_drc[num_si]["INF"]
            den_eff = dfs_drc[den_si]["ZERO"] - dfs_drc[den_si]["INF"]
            df["num_eff"] = num_eff
            df["den_eff"] = den_eff
            df["eff ratio"] = num_eff / den_eff

            # score = (num_eff/den_eff) / (num_AC50/den_AC50)
            df['score'] = df['eff ratio'] / df['AC50 ratio']
            df['Log10 score'] = np.log10(df['score'])

            df_ratios = pd.concat([df_ratios, df])

    df_ratios = df_ratios.reset_index()
    return df_ratios


if __name__ == "__main__":

    data_path = Path("/home/galtay/data/hack4nf-2022/synapse/syn5522627")
    df_files, df_clines, file_name_to_specimen_id = read_metadata(data_path)
    file_show_cols = [col for col in df_files.columns if col not in FILE_HIDE_COLS]

    # raw dose-response curve dataframes
    dfs_drc_raw = read_raw_drc(df_files)

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

    df_ratios = calculate_fit_ratios(df_compounds, dfs_drc)

    st_th_r2 = 0.85
    df_plt_ratios = df_ratios[
        (df_ratios['num_R2'] >= st_th_r2)
        & (df_ratios['den_R2'] >= st_th_r2)
        & (df_ratios['num_eff'] > 0)
        & (df_ratios['den_eff'] > 0)
    ]

    st_th_ac50_ratio = 1.5
    st_th_lac50_ratio = np.log10(st_th_ac50_ratio)
    df_good_ratios = df_plt_ratios[df_plt_ratios["Log10 (AC50 ratio)"] > st_th_lac50_ratio]

    df_ranked = (
        df_good_ratios
        .groupby(['den_si', 'NCGC SID'])['score']
        .agg(['size', 'mean', lambda x: list(x)])
        .reset_index()
    )
    st_th_num_clines = 3
    df_ranked = df_ranked[df_ranked['size']>=st_th_num_clines]
    df_ranked = pd.merge(df_ranked, df_compounds, on='NCGC SID')
    df_ranked = df_ranked.drop(columns='SMILES').sort_values(
        ['size', 'mean'], ascending=[False, False],
    )
