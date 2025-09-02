from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu
import logging
import sys
import traceback
from datetime import datetime

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import streamlit as st

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('delta_s_prime_debug.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def log_step(step_name, data=None):
    """Helper function to log each step with optional data"""
    logger.info(f"=== STEP: {step_name} ===")
    if data is not None:
        logger.info(f"Data info: {data}")
    st.write(f"🔍 **Debug Log**: {step_name} - {datetime.now().strftime('%H:%M:%S')}")

# Remove authentication - no longer needed
# from views.signed_in_landing import landing_page

#landing_page()

# from views.data import compute_ranked_delta_s_prime, display_ranked_delta_s_prime_for_download

log_step("PAGE_LOAD_START", "Delta S Prime page starting to load")

"# ΔS'"

# Add navigation sidebar
log_step("SIDEBAR_START", "Creating navigation sidebar")
try:
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
    log_step("SIDEBAR_COMPLETE", "Navigation sidebar created successfully")
except Exception as e:
    logger.error(f"SIDEBAR_ERROR: {str(e)}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    st.error(f"Sidebar error: {str(e)}")
    raise


def fetch_df(file, **kwargs):
    log_step(f"FETCH_DF_START", f"Loading file: {file}")
    try:
        data_path = Path(file)
        logger.info(f"File path exists: {data_path.exists()}")
        logger.info(f"File size: {data_path.stat().st_size if data_path.exists() else 'N/A'} bytes")
        
        df = pd.read_csv(data_path, **kwargs)
        logger.info(f"DataFrame loaded - Shape: {df.shape}, Columns: {list(df.columns)}")
        log_step(f"FETCH_DF_COMPLETE", f"Successfully loaded {file}")
        return df
    except Exception as e:
        logger.error(f"FETCH_DF_ERROR: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise


def build_df(*args, **kwargs):
    log_step("BUILD_DF_START", f"Building dataframe with args: {args}")
    try:
        # Load the data
        # extracting only columns: 'name', 'moa', 'target', 'lower_limit', 'upper_limit', 'ec50'
        column_order = ['name', 'moa', 'target', 'lower_limit', 'upper_limit', 'ec50', 'auc', 'ccle_name', 'row_name', 'screen_id']
        logger.info(f"Column order: {column_order}")
        
        df = fetch_df(*args, **kwargs)
        logger.info(f"Raw DataFrame shape: {df.shape}")
        
        # Check if all required columns exist
        missing_cols = [col for col in column_order if col not in df.columns]
        if missing_cols:
            logger.error(f"Missing columns: {missing_cols}")
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        df = df[column_order]
        logger.info(f"Filtered DataFrame shape: {df.shape}")

        # Derive EFF (upper_limit - lower_limit) 
        log_step("CALC_EFF", "Calculating EFF column")
        df['EFF'] = df['upper_limit'] - df['lower_limit']
        logger.info(f"EFF column created - Range: {df['EFF'].min()} to {df['EFF'].max()}")

        # Derive EFF*100
        log_step("CALC_EFF_100", "Calculating EFF*100 column")
        df['EFF*100'] = df['EFF'] * 100
        logger.info(f"EFF*100 column created - Range: {df['EFF*100'].min()} to {df['EFF*100'].max()}")

        # Derive EFF/EC50
        log_step("CALC_EFF_EC50", "Calculating EFF/EC50 column")
        df['EFF/EC50'] = df['EFF'] / df['ec50']
        logger.info(f"EFF/EC50 column created - Range: {df['EFF/EC50'].min()} to {df['EFF/EC50'].max()}")

        # Derive S'
        # ASINH((EFF*100)/EC50)
        log_step("CALC_S_PRIME", "Calculating S' column")
        df["S'"] = np.arcsinh(df['EFF*100'] / df['ec50'])
        logger.info(f"S' column created - Range: {df['S\''].min()} to {df['S\''].max()}")
        
        log_step("BUILD_DF_COMPLETE", f"DataFrame built successfully - Final shape: {df.shape}")
        return df
    except Exception as e:
        logger.error(f"BUILD_DF_ERROR: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise

log_step("MAIN_DATA_LOAD_START", "Starting main data loading")
try:
    df = build_df("data/DepMap/Prism19Q4/secondary-screen-dose-response-curve-parameters.csv", usecols=['name', 'moa', 'target', 'lower_limit', 'upper_limit', 'auc', 'ec50', 'ccle_name', 'row_name', 'screen_id'])
    log_step("MAIN_DATA_LOAD_COMPLETE", f"Main dataframe loaded - Shape: {df.shape}")
except Exception as e:
    logger.error(f"MAIN_DATA_LOAD_ERROR: {str(e)}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    st.error(f"Failed to load main data: {str(e)}")
    st.stop()

# Future: use same calculations as data.py
# df_ranked = compute_ranked_delta_s_prime(df)
# display_ranked_delta_s_prime_for_download(df_ranked, df_ratio=XYZ)

"## Single test value selected from 'bortezomib'"
# as a test only write the rows where 'name' is 'bortezomib' adn the EFF*100 is close to 97.9789
log_step("TEST_VALUE_START", "Processing bortezomib test values")
try:
    def get_single_testvalue():
        return df[df['name'] == 'bortezomib'].query('97.9788 < EFF*100 < 97.9790')
    
    test_df = get_single_testvalue()
    logger.info(f"Test dataframe shape: {test_df.shape}")
    st.dataframe(test_df)
    log_step("TEST_VALUE_COMPLETE", "Bortezomib test values displayed")
except Exception as e:
    logger.error(f"TEST_VALUE_ERROR: {str(e)}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    st.error(f"Error displaying test values: {str(e)}")

"## S' Table"
# Display the table
log_step("S_TABLE_START", f"Displaying S' table - Shape: {df.shape}")
try:
    st.dataframe(df)
    log_step("S_TABLE_DISPLAY_COMPLETE", "S' table displayed successfully")
    
    # Skip download button for large datasets to prevent WebSocket issues
    if len(df) > 100000:
        st.warning("⚠️ **Large Dataset**: Download button disabled for datasets > 100K rows to prevent connection issues.")
        st.info("💡 **Alternative**: Use the data filtering options below to work with smaller subsets.")
    else:
        log_step("DOWNLOAD_BUTTON_START", "Creating download button")
        st.download_button(
                        label="Download data as CSV",
                        data=df.to_csv().encode('utf-8'),
                        file_name='delta_s_prime.csv',
                        mime='text/csv'
                    )
        log_step("DOWNLOAD_BUTTON_COMPLETE", "Download button created")
except Exception as e:
    logger.error(f"S_TABLE_ERROR: {str(e)}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    st.error(f"Error displaying S' table: {str(e)}")

# Add a filter (dropdown on the column 'name') that updates a dataframe table view.

st.header("Damaging Mutations")

log_step("STUDIES_SELECTION_START", "Creating studies multiselect")
try:
    studies = st.multiselect(label='Choose studies included', options=['HTS002', 'MTS005', 'MTS006', 'MTS010',  'HTSwithMTS010_Overlayed'], default=['HTSwithMTS010_Overlayed'])
    log_step("STUDIES_SELECTION_COMPLETE", f"Studies selected: {studies}")
except Exception as e:
    logger.error(f"STUDIES_SELECTION_ERROR: {str(e)}")
    st.error(f"Error creating studies selection: {str(e)}")
    studies = ['HTSwithMTS010_Overlayed']  # Default fallback

log_step("MODIFY_DF_START", "Modifying dataframe to add ccle and tissue columns")
try:
    def modify_df(df):
        df_copy = df.copy()
        df_copy[['ccle', 'tissue']] = df_copy['ccle_name'].str.split('_', n=1, expand=True)
        return df_copy
    
    df = modify_df(df)
    logger.info(f"DataFrame modified - New columns: {list(df.columns)}")
    log_step("MODIFY_DF_COMPLETE", "DataFrame modification completed")
except Exception as e:
    logger.error(f"MODIFY_DF_ERROR: {str(e)}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    st.error(f"Error modifying dataframe: {str(e)}")
    st.stop()

active_gene = 'NF1 (4763)'
tissue = 'LUNG'

log_step("DAMAGING_MUTATIONS_LOAD_START", "Loading damaging mutations data")
try:
    damaging_mutations = fetch_df('data/DepMap/Public24Q2/OmicsSomaticMutationsMatrixDamaging.csv')
    log_step("DAMAGING_MUTATIONS_LOAD_COMPLETE", f"Damaging mutations loaded - Shape: {damaging_mutations.shape}")
except Exception as e:
    logger.error(f"DAMAGING_MUTATIONS_LOAD_ERROR: {str(e)}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    st.error(f"Failed to load damaging mutations: {str(e)}")
    st.stop()


#drop down menu to choose from different genes (columns of damaging mutations)
log_step("GENE_SELECTION_START", "Creating gene selection dropdown")
try:
    gene_options = damaging_mutations.columns.tolist()[1:]
    gene_index = gene_options.index(active_gene) if active_gene in gene_options else 0
    active_gene = st.selectbox(label="Active Gene", placeholder="e.g. NF1", index=gene_index, options=gene_options)
    log_step("GENE_SELECTION_COMPLETE", f"Gene selected: {active_gene}")
except Exception as e:
    logger.error(f"GENE_SELECTION_ERROR: {str(e)}")
    st.error(f"Error creating gene selection: {str(e)}")
    active_gene = 'NF1 (4763)'  # Default fallback

#drop down menu to choose form different tissue (based on depmap data) (sorted alphabetically) (autocomplete search)
log_step("TISSUE_SELECTION_START", "Creating tissue selection dropdown")
try:
    tissue_options = df['tissue'].unique()
    tissue_index = list(tissue_options).index(tissue) if tissue in tissue_options else None
    tissue = st.selectbox(label="Tissue", placeholder="e.g. Pancreas", index=tissue_index, options=tissue_options)
    log_step("TISSUE_SELECTION_COMPLETE", f"Tissue selected: {tissue}")
except Exception as e:
    logger.error(f"TISSUE_SELECTION_ERROR: {str(e)}")
    st.error(f"Error creating tissue selection: {str(e)}")
    tissue = 'LUNG'  # Default fallback   

st.header("All S' by Mutation and Tissue")

log_step("FILTER_DF_START", f"Starting filter_df with gene: {active_gene}, tissue: {tissue}")
def filter_df(active_gene, tissue):
    try:
        logger.info(f"Filtering for gene: {active_gene}, tissue: {tissue}")
        #Unnamed: 0 is the tissue column name in damaging_mutations file
        log_step("FILTER_GENE_VALUES", f"Filtering gene values for {active_gene}")
        filtered_gene_values = damaging_mutations[damaging_mutations[active_gene].isin([0, 2])][['Unnamed: 0', active_gene]]
        logger.info(f"Filtered gene values shape: {filtered_gene_values.shape}")

        log_step("MERGE_DATA", "Merging main df with filtered gene values")
        dm_merged = pd.merge(df, filtered_gene_values, left_on='row_name', right_on='Unnamed: 0', how='inner')
        logger.info(f"After merge shape: {dm_merged.shape}")
        
        log_step("FILTER_STUDIES_TISSUE", f"Filtering by studies: {studies} and tissue: {tissue}")
        dm_merged = dm_merged.loc[dm_merged['screen_id'].isin(studies) & (dm_merged['tissue'] == tissue)].drop(columns=['Unnamed: 0', 'ccle_name'])
        logger.info(f"After filtering shape: {dm_merged.shape}")
    except Exception as e:
        logger.error(f"FILTER_DF_ERROR in initial filtering: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise

        log_step("FORMAT_TARGET", "Formatting target column")
        def format_target(row):
            if isinstance(row, str):  
                return [item.strip() for item in row.split(",")]
            else:
                return [] 
            
        dm_merged['target'] = dm_merged['target'].apply(format_target)
        logger.info(f"Target column formatted, sample: {dm_merged['target'].iloc[0] if len(dm_merged) > 0 else 'Empty'}")

        ########################################################################
        log_step("LOAD_MANUAL_ONTOLOGY", "Loading manual ontology data")
        target = fetch_df('Manual_ontology.csv')
        logger.info(f"Manual ontology loaded - Shape: {target.shape}")
        
        df_reference_ontolgy = pd.DataFrame ( columns = ["Group", "Sub", "Gene"])
        Group = None
        for i in range(len(target)):
            Current_group = str(target.loc[i,'Group']).strip()
            if Current_group != "nan": 
                Group = Current_group 
            df_reference_ontolgy.loc[i] = [Group, target.loc[i,'Sub'], target.loc[i,'Gene']]
        logger.info(f"Reference ontology processed - Shape: {df_reference_ontolgy.shape}")

        log_step("PROCESS_GENE_MAPPING", f"Processing gene mapping for {len(dm_merged)} rows")
        rows_to_append = []
        genes_not_in_manual_ontology = []
        # Add a new column to dm_merged to hold the group and sub strings
        dm_merged['group_sub'] = ''

        # Iterate through dm_merged and update rows_to_append and dm_merged
        for i, row in dm_merged.iterrows():
            group_sub_list = []  # Temporary list to hold group_sub strings for current row
            for gene in row['target']:
                if gene in df_reference_ontolgy['Gene'].values:
                    group = df_reference_ontolgy.loc[df_reference_ontolgy['Gene'] == gene, 'Group'].values[0]
                    sub = df_reference_ontolgy.loc[df_reference_ontolgy['Gene'] == gene, 'Sub'].values[0]
                    group_sub_string = f"{group} | {sub}"
                    if group_sub_string not in group_sub_list:
                        group_sub_list.append(group_sub_string)
                    
                    # Append to rows_to_append
                    rows_to_append.append({
                        'Compound': row['name'],
                        'Group': group,
                        'Sub': sub,
                        'Gene': gene
                    })
                else:
                    if gene not in genes_not_in_manual_ontology:
                        genes_not_in_manual_ontology.append(gene)
        
            # Join all group_sub strings for the current row and update dm_merged
            dm_merged.at[i, 'group_sub'] = group_sub_list

        # Convert rows_to_append to DataFrame
        log_step("CREATE_COMPOUND_TARGET_GROUP", f"Creating compound target group with {len(rows_to_append)} entries")
        cmp_trgt_grp = pd.DataFrame(rows_to_append)
        logger.info(f"Compound target group created - Shape: {cmp_trgt_grp.shape}")
        logger.info(f"Genes not in manual ontology: {len(genes_not_in_manual_ontology)}")

        ##########################################################################
        # dm_merged = pd.merge(df, filtered_gene_values, left_on='row_name', right_on='Unnamed: 0', how='inner');

        log_step("FILTER_DF_FINAL_FILTER", f"Final tissue filter for: {tissue}")
        final_result = dm_merged.loc[dm_merged['tissue'] == tissue]
        logger.info(f"Final result shape: {final_result.shape}")
        
        log_step("FILTER_DF_COMPLETE", "Filter function completed successfully")
        return final_result, cmp_trgt_grp, genes_not_in_manual_ontology
    except Exception as e:
        logger.error(f"FILTER_DF_ERROR: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise

log_step("EXECUTE_FILTER_DF", f"Executing filter_df with gene: {active_gene}, tissue: {tissue}")
try:
    dm_merged, cmp_trgt_grp, genes_not_in_manual_ontology = filter_df(active_gene, tissue)
    log_step("EXECUTE_FILTER_DF_COMPLETE", f"Filter execution completed - dm_merged shape: {dm_merged.shape}")
except Exception as e:
    logger.error(f"EXECUTE_FILTER_DF_ERROR: {str(e)}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    st.error(f"Error executing filter: {str(e)}")
    st.stop()

# for each cmopoumd unique by name:
# name, tissue
# ref_pooled_s_prime: mean of S' for all rows where NF1 is 0
# test_pooled_s_prime: mean of S' for all rows where NF1 is 2
# delta_s_prime: delta S' = mean of S' for NF1 = 0 - mean of S' for NF1 = 2

log_step("DISPLAY_DM_MERGED", f"Displaying dm_merged dataframe - Shape: {dm_merged.shape}")
try:
    st.dataframe(dm_merged)
    log_step("DISPLAY_DM_MERGED_COMPLETE", "dm_merged dataframe displayed successfully")
except Exception as e:
    logger.error(f"DISPLAY_DM_MERGED_ERROR: {str(e)}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    st.error(f"Error displaying merged data: {str(e)}")

if not dm_merged.empty:
    # Skip download button for large filtered datasets
    if len(dm_merged) > 50000:
        st.warning("⚠️ **Large Filtered Dataset**: Download button disabled for datasets > 50K rows.")
        st.info("💡 **Alternative**: Use the compound filtering options below to work with smaller subsets.")
    else:
        st.download_button(
                    label="Download data as CSV",
                    data=dm_merged.to_csv().encode('utf-8'),
                    file_name='s_prime.csv',
                    mime='text/csv'
                )

    st.header("Pooled Delta S' for Selected Values")

    def median_absolute_deviation(data):
        # Calculate the median of the data
        median = np.median(data)
        # Calculate the absolute deviations from the median
        abs_deviation = np.abs(data - median)
        # Compute the median of the absolute deviations
        mad = np.median(abs_deviation)
        return mad

    def calculate_modified_z_score(data: pd.DataFrame, column: str) -> pd.Series:
        """
        Calculate the modified z-scores for a specified column in the DataFrame.

        Parameters:
        data (pd.DataFrame): Input DataFrame.
        column (str): The name of the column for which to calculate the modified z-scores.

        Returns:
        pd.Series: A Series of modified z-scores for the specified column.
        """
        # Compute the median of the column
        median = data[column].median()
        
        # Compute the Median Absolute Deviation (MAD)
        mad = np.median(np.abs(data[column] - median))
        
        # Handle division by zero (if MAD is zero)
        if mad == 0:
            return pd.Series([0] * len(data[column]), index=data.index)
        
        # Compute the modified z-scores
        modified_z_scores = 0.6745 * ((data[column] - median) / mad)
        
        return modified_z_scores

    def compute_compounds_test_agg(active_gene):
        df_ref_group = dm_merged.loc[dm_merged[active_gene] == 0]
        df_test_group = dm_merged.loc[dm_merged[active_gene] == 2]

        # Reference group calculations
        compounds_ref_agg_mean = df_ref_group.groupby('name').agg(
            ref_pooled_s_prime=pd.NamedAgg(column='S\'', aggfunc='mean'),
            ref_median_s_prime=pd.NamedAgg(column='S\'', aggfunc='median'),
            ref_mad=pd.NamedAgg(column='S\'', aggfunc=median_absolute_deviation),
            ref_pooled_auc=pd.NamedAgg(column='auc', aggfunc='mean'),
            ref_pooled_ec50=pd.NamedAgg(column='ec50', aggfunc='mean'),
            num_ref_lines=pd.NamedAgg(column='row_name', aggfunc='count'),
            ref_s_prime_variance=pd.NamedAgg(column='S\'', aggfunc='var')
        ).reset_index()

        # Test group calculations
        compounds_test_agg_mean = df_test_group.groupby('name').agg(
            test_pooled_s_prime=pd.NamedAgg(column='S\'', aggfunc='mean'),
            test_median_s_prime=pd.NamedAgg(column='S\'', aggfunc='median'),
            test_mad=pd.NamedAgg(column='S\'', aggfunc=median_absolute_deviation),
            test_pooled_auc=pd.NamedAgg(column='auc', aggfunc='mean'),
            test_pooled_ec50=pd.NamedAgg(column='ec50', aggfunc='mean'),
            num_test_lines=pd.NamedAgg(column='row_name', aggfunc='count'),
            test_s_prime_variance=pd.NamedAgg(column='S\'', aggfunc='var')
        ).reset_index()

        # Merging reference and test data
        compounds_merge = pd.merge(compounds_ref_agg_mean, compounds_test_agg_mean, on='name', how='inner')

        # Calculating deltas
        compounds_merge['delta_s_prime'] = compounds_merge['ref_pooled_s_prime'] - compounds_merge['test_pooled_s_prime']
        compounds_merge['delta_auc'] = compounds_merge['ref_pooled_auc'] - compounds_merge['test_pooled_auc']
        compounds_merge['delta_ec50'] = compounds_merge['ref_pooled_ec50'] - compounds_merge['test_pooled_ec50']

        # Additional calculations for median differences
        compounds_merge['delta_s_prime_median'] = compounds_merge['ref_median_s_prime'] - compounds_merge['test_median_s_prime']

        # Calculate p-value using Mann-Whitney U test
        p_values = []
        for index, row in compounds_merge.iterrows():
            group1 = df_ref_group[df_ref_group['name'] == row['name']]['S\'']
            group2 = df_test_group[df_test_group['name'] == row['name']]['S\'']
            stat, p_value = mannwhitneyu(group1, group2, alternative='two-sided')
            p_values.append(p_value)

        compounds_merge['p_val_median_man_whit'] = p_values


        # Sensitivity calculations
        compounds_merge['Sensitivity Score'] = np.where(compounds_merge['delta_s_prime'] < -0.5, -1,
                                                        np.where(compounds_merge['delta_s_prime'] > 0.5, 1, 0))

        compounds_merge['Sensitivity'] = np.where(compounds_merge['delta_s_prime'] < -0.5, 'Sensitive',
                                                        np.where(compounds_merge['delta_s_prime'] > 0.5, 'Resistant', 'Equivocal'))

        # Merging drug MOA information
        df_drug_moa = dm_merged[["name", "moa", "target", "group_sub"]]
        df_drug_moa_unique = df_drug_moa.drop_duplicates(subset=['name'])
        compounds_merge = pd.merge(compounds_merge, df_drug_moa_unique, on='name', how='left')

        # Formatting MOA
        def format_to_array(x):
            if isinstance(x, str):
                return x.split(",")
            return [str(x)]

        compounds_merge['moa'] = compounds_merge['moa'].apply(format_to_array)

        return compounds_merge
    
    compounds_merge = compute_compounds_test_agg(active_gene)

    st.write(compounds_merge)

    # Skip download button for large compound datasets
    if len(compounds_merge) > 10000:
        st.warning("⚠️ **Large Compound Dataset**: Download button disabled for datasets > 10K rows.")
        st.info("💡 **Alternative**: Use the filtering options below to work with smaller subsets.")
    else:
        st.download_button(
                    label="Download data as CSV",
                    data=compounds_merge.to_csv().encode('utf-8'),
                    file_name='delta_s_prime.csv',
                    mime='text/csv',
                    key='download-compounds-merged'
                )

    with st.expander("Target Grouping"):
        st.write(cmp_trgt_grp)

    with st.expander("Genes not in Manual Ontology"):
        genes_not_in_manual_ontology = pd.DataFrame(genes_not_in_manual_ontology)
        st.write(genes_not_in_manual_ontology)
        st.markdown("Number of genes not in Manual Ontology: " + str(len(genes_not_in_manual_ontology)))

    st.header("Pooled Delta S' for Compounds By \"Group | Subgroup\" Combination")

    def get_unique_combinations():
        target = fetch_df('Manual_ontology.csv')
        target['Group'] = target['Group'].ffill()
        target['Group_Subgroup'] = target['Group'] + ' | ' + target['Sub']
        unique_combinations = target['Group_Subgroup'].unique()
        return unique_combinations
    unique_combinations = get_unique_combinations()

    selected_combinations = st.multiselect(label='Choose Group | Subgroup combinations', options=unique_combinations)
    st.markdown("Selecting multiple combinations means that the compound must have all the selected values to be included in the result.")

    def filtered_compounds_by_class(selected_combinations):
        return compounds_merge[compounds_merge['group_sub'].apply(lambda x: all(elem in x for elem in selected_combinations))][["name", "delta_s_prime"]]

    if len(filtered_compounds_by_class(selected_combinations)) > 0:
        st.write(filtered_compounds_by_class(selected_combinations))

    st.header("Pooled Delta S' for Compounds By MOA")

    def get_unique_moas(dataframe, column):
        all_moas = set()
        for row in dataframe[column]:
            all_moas.update(row)
        return all_moas

    unique_moas = get_unique_moas(compounds_merge, 'moa')

    selected_moas = st.multiselect(label='Choose MOA\'s', options=unique_moas)
    st.markdown("Selecting multiple MOA\'s means that the compound must have all the selected values to be included in the result.")

    filtered_compounds_by_moa = compounds_merge[compounds_merge['moa'].apply(lambda x: all(elem in x for elem in selected_moas))][["name", "delta_s_prime"]]

    st.write(filtered_compounds_by_moa)

log_step("PAGE_COMPLETE", "Delta S Prime page completed successfully")
