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

column_order = ['name', 'moa', 'target', 'lower_limit', 'upper_limit', 'ec50', 'ccle_name', 'row_name', 'screen_id']

# Load the data
# extracting only columns: 'name', 'moa', 'target', 'lower_limit', 'upper_limit', 'ec50'
data_path = Path("data/DepMap/Prism19Q4/secondary-screen-dose-response-curve-parameters.csv")
df = pd.read_csv(data_path, usecols=['name', 'moa', 'target', 'lower_limit', 'upper_limit', 'ec50', 'ccle_name', 'row_name', 'screen_id'])
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
#st.write(df[df['name'] == 'bortezomib'][(df['EFF*100'] > 97.9788) & (df['EFF*100'] < 97.9790)])

"## S' Table"
# Display the table
gb = GridOptionsBuilder.from_dataframe(df)
gb.configure_pagination()
gb.configure_side_bar()
# Freeze the 1st column for scrolling
column_defs = [{'headerName': col, 'field': col, 'pinned': 'left' if col == 'name' else None} for col in df.columns]
gridOptions = {
    'columnDefs': column_defs,
    'pagination': True,
    'defaultColDef': {
        'groupable': True, 
        'value': True, 
        'enableRowGroup': True, 
        'aggFunc': 'sum', 
        'editable': True,
        'filter': True,
        'sortable': True,
        'resizable': True,
    },
    'statusBar': {
        'statusPanels': [
            { 'statusPanel': 'agTotalRowCountComponent', 'align': 'left' },
            { 'statusPanel': 'agSelectedRowCountComponent' },
            { 'statusPanel': 'agAggregationComponent' }
        ]
    },
}
# TODO: Refactor to not be over size limits
# AgGrid(df, gridOptions=gridOptions)

# Add a filter (dropdown on the column 'name') that updates a dataframe table view.

st.header("Damaging Mutations")

#drop down menu to choose from different genes (columns of damaging mutations)
#drop down menu to choose form different tissue (based on depmap data) (sorted alphabetically) (autocomplete search)

studies = st.multiselect(label='Choose studies included', options=['HTS002', 'MTS005', 'MTS006', 'MTS010'])

df[['ccle', 'tissue']] = df['ccle_name'].str.split('_', n=1, expand=True)

active_gene = None
tissue = None

damaging_mutations = pd.read_csv('data/DepMap/Public24Q2/OmicsSomaticMutationsMatrixDamaging.csv')

active_gene = st.selectbox(label="Active Gene", placeholder="e.g. NF1", options=damaging_mutations.columns.tolist()[1:], index = damaging_mutations.columns.tolist()[1:].index("NF1 (4763)"));

#TODO: not use .head()
tissue = st.selectbox(label= "Tissue", placeholder="e.g. Pancreas", options = df['tissue'].head(100).unique(), index=df['tissue'].head(100).unique().tolist().index("LUNG") )  

st.header("All S' by Mutation and Tissue")

#Unnamed: 0 is the tissue column name in damaging_mutations file
filtered_nf1_values = damaging_mutations[damaging_mutations[active_gene].isin([0, 2])][['Unnamed: 0', active_gene]]

dm_merged = pd.merge(df, filtered_nf1_values, left_on='row_name', right_on='Unnamed: 0', how='inner')

dm_merged = dm_merged.loc[dm_merged['tissue'] == tissue][dm_merged['screen_id'].isin(studies)].drop(columns=['Unnamed: 0', 'ccle_name'])

# for each cmopoumd unique by name:
# name, tissue
# ref_pooled_s_prime: mean of S' for all rows where NF1 is 0
# test_pooled_s_prime: mean of S' for all rows where NF1 is 2
# delta_s_prime: delta S' = mean of S' for NF1 = 0 - mean of S' for NF1 = 2

def format_target(row):
    if isinstance(row, str):  
        return [item.strip() for item in row.split(",")]
    else:
        return [] 
    
dm_merged['target'] = dm_merged['target'].apply(format_target)

st.write(dm_merged)

st.download_button(
            label="Download data as CSV",
            data=dm_merged.to_csv().encode('utf-8'),
            file_name='s_prime.csv',
            mime='text/csv'
        )

st.header("Delta S' for Selected Values")

df_ref_group = dm_merged.loc[dm_merged[active_gene] == 0]

df_test_group = dm_merged.loc[dm_merged[active_gene] == 2]

compounds_ref_agg_mean = df_ref_group.groupby('name').agg(ref_pooled_s_prime=pd.NamedAgg(column='S\'', aggfunc='mean')).reset_index()
compounds_ref_agg_sum   = df_ref_group.groupby('name').agg(num_ref_lines=pd.NamedAgg(column='row_name', aggfunc='count')).reset_index()
compounds_ref_var = df_ref_group.groupby('name').agg(ref_s_prime_variance=pd.NamedAgg(column='S\'', aggfunc='var')).reset_index()
compounds_ref_merge = pd.merge(pd.merge(compounds_ref_agg_mean, compounds_ref_var, on='name', how='inner'), compounds_ref_agg_sum, on='name', how='inner')

compounds_test_agg_mean = df_test_group.groupby('name').agg(test_pooled_s_prime=pd.NamedAgg(column='S\'', aggfunc='mean')).reset_index()
compunds_test_agg_sum =  df_test_group.groupby('name').agg(num_test_lines=pd.NamedAgg(column='row_name', aggfunc='count')).reset_index()
compounds_test_agg_var = df_test_group.groupby('name').agg(test_s_prime_variance=pd.NamedAgg(column='S\'', aggfunc='var')).reset_index()
compounds_test_merge = pd.merge(pd.merge(compounds_test_agg_mean, compounds_test_agg_var, on='name', how='inner'), compunds_test_agg_sum, on='name', how='inner')

compounds_merge = pd.merge(compounds_ref_merge, compounds_test_merge, on='name', how='inner')

compounds_merge['delta_s_prime'] = compounds_merge['ref_pooled_s_prime'] - compounds_merge['test_pooled_s_prime']

compounds_merge['Sensitivity Score'] = np.where(compounds_merge['delta_s_prime'] < -0.5, -1,
                                          np.where(compounds_merge['delta_s_prime'] > 0.5, 1, 0))

compounds_merge['Sensitivity'] = np.where(compounds_merge['delta_s_prime'] < -0.5, 'Sensitive',
                                          np.where(compounds_merge['delta_s_prime'] > 0.5, 'Resistent', 'Equivocal'))

df_drug_moa = dm_merged[["name","moa","target"]]
compounds_merge = pd.merge(compounds_merge, df_drug_moa, on='name', how='left')

st.write(compounds_merge)

st.download_button(
            label="Download data as CSV",
            data=compounds_merge.to_csv().encode('utf-8'),
            file_name='delta_s_prime.csv',
            mime='text/csv'
        )

target = pd.read_csv('Manual_ontology.csv')
df_reference_ontolgy = pd.DataFrame ( columns = ["Group", "Sub", "Gene"])
Group = None
for i in range(len(target)):
    Current_group = str(target.loc[i,'Group']).strip()
    if Current_group != "nan": 
        Group = Current_group 
    df_reference_ontolgy.loc[i] = [Group, target.loc[i,'Sub'], target.loc[i,'Gene']]

rows_to_append = []
genes_not_in_manual_ontology = []

for i, row in dm_merged.iterrows():
    for gene in row['target']:
        if gene in df_reference_ontolgy['Gene'].values:
            rows_to_append.append({'Compound': row['name'], 'Group': df_reference_ontolgy.loc[df_reference_ontolgy['Gene'] == gene, 'Group'].values[0], 'Sub': df_reference_ontolgy.loc[df_reference_ontolgy['Gene'] == gene, 'Sub'].values[0], 'Gene': gene})
        else:
            if gene not in genes_not_in_manual_ontology:
                genes_not_in_manual_ontology.append(gene)

st.header("Target Grouping")
cmp_trgt_grp = pd.DataFrame(rows_to_append)
st.write(cmp_trgt_grp)

st.header("Genes not in Manual Ontology")
genes_not_in_manual_ontology = pd.DataFrame(genes_not_in_manual_ontology)
st.write(genes_not_in_manual_ontology)
st.markdown("Number of genes not in Manual Ontology: " + str(len(genes_not_in_manual_ontology)))