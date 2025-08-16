from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import streamlit as st

# Remove authentication - no longer needed
# from views.signed_in_landing import landing_page

#landing_page()

# from views.data import compute_ranked_delta_s_prime, display_ranked_delta_s_prime_for_download

"# ΔS'"

# Streamlit automatically provides page navigation in the sidebar


def fetch_df(file, **kwargs):
    data_path = Path(file)
    return pd.read_csv(data_path, **kwargs)


def build_df(*args, **kwargs):
    # Load the data
    # extracting only columns: 'name', 'moa', 'target', 'lower_limit', 'upper_limit', 'ec50'
    column_order = ['name', 'moa', 'target', 'lower_limit', 'upper_limit', 'ec50', 'auc', 'ccle_name', 'row_name', 'screen_id']
    df = fetch_df(*args, **kwargs)
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
    return df

df = build_df("data/DepMap/Prism19Q4/secondary-screen-dose-response-curve-parameters.csv", usecols=['name', 'moa', 'target', 'lower_limit', 'upper_limit', 'auc', 'ec50', 'ccle_name', 'row_name', 'screen_id'])

# Future: use same calculations as data.py
# df_ranked = compute_ranked_delta_s_prime(df)
# display_ranked_delta_s_prime_for_download(df_ranked, df_ratio=XYZ)

"## Single test value selected from 'bortezomib'"
# as a test only write the rows where 'name' is 'bortezomib' adn the EFF*100 is close to 97.9789
def get_single_testvalue():
    return df[df['name'] == 'bortezomib'].query('97.9788 < EFF*100 < 97.9790')
st.dataframe(get_single_testvalue())

"## S' Table"
# Display the table
st.dataframe(df)
st.download_button(
                label="Download data as CSV",
                data=df.to_csv().encode('utf-8'),
                file_name='delta_s_prime.csv',
                mime='text/csv'
            )

# Add a filter (dropdown on the column 'name') that updates a dataframe table view.

st.header("Damaging Mutations")

studies = st.multiselect(label='Choose studies included', options=['HTS002', 'MTS005', 'MTS006', 'MTS010',  'HTSwithMTS010_Overlayed'], default=['HTSwithMTS010_Overlayed'])

def modify_df(df):
    df[['ccle', 'tissue']] = df['ccle_name'].str.split('_', n=1, expand=True)
    return df
df = modify_df(df)

active_gene = 'NF1 (4763)'
tissue = 'LUNG'

damaging_mutations = fetch_df('data/DepMap/Public24Q2/OmicsSomaticMutationsMatrixDamaging.csv')


#drop down menu to choose from different genes (columns of damaging mutations)
active_gene = st.selectbox(label="Active Gene", placeholder="e.g. NF1", index=damaging_mutations.columns.tolist()[1:].index(active_gene), options=damaging_mutations.columns.tolist()[1:]);

#drop down menu to choose form different tissue (based on depmap data) (sorted alphabetically) (autocomplete search)
tissue = st.selectbox(label= "Tissue", placeholder="e.g. Pancreas", index=None, options = df['tissue'].unique())   

st.header("All S' by Mutation and Tissue")

def filter_df(active_gene, tissue):
    #Unnamed: 0 is the tissue column name in damaging_mutations file
    filtered_gene_values = damaging_mutations[damaging_mutations[active_gene].isin([0, 2])][['Unnamed: 0', active_gene]]

    dm_merged = pd.merge(df, filtered_gene_values, left_on='row_name', right_on='Unnamed: 0', how='inner')
    dm_merged = dm_merged.loc[dm_merged['screen_id'].isin(studies) & (dm_merged['tissue'] == tissue)].drop(columns=['Unnamed: 0', 'ccle_name'])

    def format_target(row):
        if isinstance(row, str):  
            return [item.strip() for item in row.split(",")]
        else:
            return [] 
        
    dm_merged['target'] = dm_merged['target'].apply(format_target)

    ########################################################################
    target = fetch_df('Manual_ontology.csv')
    df_reference_ontolgy = pd.DataFrame ( columns = ["Group", "Sub", "Gene"])
    Group = None
    for i in range(len(target)):
        Current_group = str(target.loc[i,'Group']).strip()
        if Current_group != "nan": 
            Group = Current_group 
        df_reference_ontolgy.loc[i] = [Group, target.loc[i,'Sub'], target.loc[i,'Gene']]

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
    cmp_trgt_grp = pd.DataFrame(rows_to_append)

##########################################################################
    # dm_merged = pd.merge(df, filtered_gene_values, left_on='row_name', right_on='Unnamed: 0', how='inner');

    return dm_merged.loc[dm_merged['tissue'] == tissue], cmp_trgt_grp, genes_not_in_manual_ontology

dm_merged, cmp_trgt_grp, genes_not_in_manual_ontology = filter_df(active_gene, tissue)

# for each cmopoumd unique by name:
# name, tissue
# ref_pooled_s_prime: mean of S' for all rows where NF1 is 0
# test_pooled_s_prime: mean of S' for all rows where NF1 is 2
# delta_s_prime: delta S' = mean of S' for NF1 = 0 - mean of S' for NF1 = 2
st.dataframe(dm_merged)

if not dm_merged.empty:
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
