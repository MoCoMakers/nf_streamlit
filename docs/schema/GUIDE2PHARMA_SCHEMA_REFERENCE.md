# Guide2Pharma Database Schema Reference

## Overview
This document provides a comprehensive reference for all tables in the Guide2Pharma database. The schema aligns with the public [IUPHAR/BPS Guide to PHARMACOLOGY](https://www.guidetopharmacology.org/) (GtoPdb): curated **targets** (`object`), **ligands**, **ligand–target interactions**, and a shared **bibliography** (`reference`), plus satellite tables for families, species, diseases, structures, and portal-specific views (immunopharmacology, malaria, antibacterials). Per-table **Size** figures use live PostgreSQL statistics (`pg_class.reltuples` for row estimates and `pg_total_relation_size` for on-disk bytes, including indexes and TOAST).

## Database Connection
- **Database**: `guide2pharma`
- **Host**: `dmvpetridishdatastore.dev`
- **Port**: `5432`
- **Schema**: `public`
- **Connection**: `guide2pharma-readonly` (read-only account)
- **Total Tables**: 208

## Table Inventory

### 1. **accessory_protein**
**Summary**: Accessory proteins (e.g. RAMPs) that assemble with receptor complexes.
**Purpose**: Stores display names for accessory proteins referenced from target (`object`) records.
**Size**: ~10 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **32 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| object_id | integer | NO | Foreign key to `object.object_id`. |
| full_name | character varying(1000) | YES | Full human-readable name as shown in the UI (e.g. protein or accessory protein name). |

**Primary Keys**: object_id

**Sample Data**:
```json
{
  "full_name": "Receptor activity modifying protein",
  "object_id": 51
}
```
### 2. **allele**
**Summary**: Mouse and other model-organism alleles linked to phenotype ontologies.
**Purpose**: Curates allelic compositions, symbols, and ontology terms (e.g. MP) for genetically modified models.
**Size**: ~12,938 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **2432 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| allele_id | integer | NO | Surrogate primary key. Default: sequence: allele_allele_id_seq |
| accessions | character varying(100) | NO | External database accession (e.g. MGI, Ensembl). |
| species_id | integer | NO | Default: 2 |
| pubmed_ids | character varying(200) | YES | Comma-separated PubMed IDs supporting the row. |
| ontology_id | integer | NO | Default: 1 |
| term_id | character varying(100) | NO | Ontology term identifier (e.g. MP:… phenotype ID). |
| allelic_composition | character varying(300) | YES | Genotype description (hom/het, alleles). |
| allele_symbol | character varying(300) | YES | Standard allele symbol (e.g. gene<sup>allele</sup>). |
| genetic_background | character varying(300) | YES | Inbred strain or mixed background of the model. |

**Primary Keys**: allele_id

**Sample Data**:
```json
{
  "accessions": "MGI:1920904",
  "allele_id": 586988,
  "allele_symbol": "Ccrl2<tm1Ssoz>",
  "allelic_composition": "Ccrl2<tm1Ssoz>/Ccrl2<tm1Ssoz>",
  "genetic_background": "B6.129-Ccrl2<tm1Ssoz>",
  "ontology_id": 1,
  "pubmed_ids": "20606167",
  "species_id": 2,
  "term_id": "MP:0002148"
}
```
### 3. **altered_expression**
**Summary**: Reports where gene/protein expression is altered in disease or knockout models.
**Purpose**: Narrative expression evidence tied to `object_id`, species, tissue, and experimental technique.
**Size**: ~2,074 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **1784 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| altered_expression_id | integer | NO | Surrogate primary key. Default: sequence: altered_expression_altered_expression_id_seq |
| object_id | integer | NO | Foreign key to `object.object_id`. |
| description | character varying(10000) | YES | Free-text description field. |
| species_id | integer | NO | Foreign key to `species.species_id`. |
| tissue | character varying(1000) | YES | Tissue or organ context for expression data. |
| technique | character varying(500) | YES | Experimental method (knockout, qPCR, microarray, …). |
| description_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search on `description`. |
| tissue_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search on `tissue`. |
| technique_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search on `technique`. |

**Primary Keys**: altered_expression_id

**Sample Data**:
```json
{
  "altered_expression_id": 1,
  "description": "5-HT<sub>1A</sub> receptor knockout mice exhibit higher amounts of paradoxical sleep than wild-type mice during both the light and the dark phases.",
  "description_vector": "'5':1 'amount':8 'dark':23 'exhibit':6 'higher':7 'ht1a':2 'knockout':4 'light':20 'mice':5,16 'paradox':10 'phase':24 'receptor':3 'sleep':11 'type':15 'wild':14 'wild-typ':13",
  "object_id": 1,
  "species_id": 2,
  "technique": "Gene targeting in embryonic stem cells.",
  "technique_vector": "'cell':6 'embryon':4 'gene':1 'stem':5 'target':2",
  "tissue": null,
  "tissue_vector": null
}
```
### 4. **altered_expression_refs**
**Summary**: Citations for altered-expression statements.
**Purpose**: Junction linking `altered_expression` rows to `reference` (PubMed-backed bibliography).
**Size**: ~2,739 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **216 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| altered_expression_id | integer | NO | Foreign key to `altered_expression.altered_expression_id`. |
| reference_id | integer | NO | Foreign key to `reference.reference_id`. |

**Primary Keys**: altered_expression_id, reference_id

**Sample Data**:
```json
{
  "altered_expression_id": 1,
  "reference_id": 8
}
```
### 5. **analogue_cluster**
**Summary**: Clusters of structurally related synthetic ligands (analogue series).
**Purpose**: Maps `ligand_id` to a short cluster code used in GtoPdb ligand clustering views.
**Size**: ~884 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **112 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| ligand_id | integer | NO | Foreign key to `ligand.ligand_id`. |
| cluster | character varying(10) | NO | Cluster identifier (short code) for analogue or scaffold grouping. |

**Primary Keys**: ligand_id, cluster

**Sample Data**:
```json
{
  "cluster": "796R",
  "ligand_id": 795
}
```
### 6. **antibiotic_db**
**Summary**: Curated antibacterial compounds from the Antibacterials portal.
**Purpose**: Core antibacterial drug/project metadata (class, phase, institute) with optional `ligand_id` link.
**Size**: ~2,439 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **408 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| adb_id | integer | NO | Foreign key to `antibiotic_db.adb_id`. |
| drug_name | character varying(2000) | NO | Antibacterial resource: compound name, class, or regulatory metadata. |
| drug_class | character varying(1500) | YES | Antibacterial resource: compound name, class, or regulatory metadata. |
| high_dev_phase | character varying(1500) | YES | Curated field in the IUPHAR/BPS Guide to PHARMACOLOGY database ([guidetopharmacology.org](https://www.guidetopharmacology.org/)); see the `antibiotic_db` table and related target/ligand pages for context. |
| institute | character varying(3000) | YES | Antibacterial programme: sponsor, status, mechanism-of-action, or notes. |
| ligand_id | integer | YES | Foreign key to `ligand.ligand_id`. |

**Primary Keys**: adb_id

**Sample Data**:
```json
{
  "adb_id": 1,
  "drug_class": "Acyldepsipeptide",
  "drug_name": "Acyldepsipeptide 4 (ADEP4)",
  "high_dev_phase": "Preclinical",
  "institute": "Antimicrobial Discovery Center, Department of Biology, Northeastern University, Boston, Massachusetts, USA",
  "ligand_id": null
}
```
### 7. **antibiotic_db_full**
**Summary**: Extended antibacterial records with spectrum, MOA, and development status.
**Purpose**: Full antibacterial schema including Gram+/Gram− flags, resistance notes, structures, and literature links.
**Size**: ~2,122 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **872 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| adb_id | integer | NO | Foreign key to `antibiotic_db.adb_id`. |
| drug_name | character varying(2000) | NO | Antibacterial resource: compound name, class, or regulatory metadata. |
| drug_class | character varying(1500) | YES | Antibacterial resource: compound name, class, or regulatory metadata. |
| year_fm | character varying(100) | YES | Antibacterial programme: sponsor, status, mechanism-of-action, or notes. |
| institute | character varying(3000) | YES | Antibacterial programme: sponsor, status, mechanism-of-action, or notes. |
| current_status | character varying(500) | YES | Antibacterial programme: sponsor, status, mechanism-of-action, or notes. |
| high_dev_phase | character varying(1500) | YES | Curated field in the IUPHAR/BPS Guide to PHARMACOLOGY database ([guidetopharmacology.org](https://www.guidetopharmacology.org/)); see the `antibiotic_db_full` table and related target/ligand pages for context. |
| reason_dropped | character varying(1000) | YES | Antibacterial programme: sponsor, status, mechanism-of-action, or notes. |
| moa_target_pathogen | character varying(1500) | YES | Antibacterial programme: sponsor, status, mechanism-of-action, or notes. |
| gram_neg_effect | boolean | YES | Default: false |
| gram_pos_effect | boolean | YES | Default: false |
| combination_therapy | boolean | YES | Default: false |
| prop_select_res_mutants | boolean | YES | Default: false |
| additional_info | character varying(1500) | YES | Antibacterial programme: sponsor, status, mechanism-of-action, or notes. |
| source_hp | character varying(3000) | YES | Antibacterial programme: sponsor, status, mechanism-of-action, or notes. |
| ligand_id | integer | YES | Foreign key to `ligand.ligand_id`. |
| papers_cited_1 | character varying(3000) | YES | Supporting publication URL or external 3D structure link. |
| papers_cited_2 | character varying(3000) | YES | Supporting publication URL or external 3D structure link. |
| papers_cited_3 | character varying(3000) | YES | Supporting publication URL or external 3D structure link. |
| patents | character varying(3000) | YES | Patent reference or assignee (intellectual property). |
| link_to_structure_1 | character varying(3000) | YES | Supporting publication URL or external 3D structure link. |
| link_to_structure_2 | character varying(3000) | YES | Supporting publication URL or external 3D structure link. |

**Primary Keys**: adb_id

**Sample Data**:
```json
{
  "adb_id": 1,
  "additional_info": "",
  "combination_therapy": true,
  "current_status": "A",
  "drug_class": "Acyldepsipeptide",
  "drug_name": "Acyldepsipeptide 4 (ADEP4)",
  "gram_neg_effect": false,
  "gram_pos_effect": true,
  "high_dev_phase": "Preclinical",
  "institute": "Antimicrobial Discovery Center, Department of Biology, Northeastern University, Boston, Massachusetts, USA",
  "ligand_id": null,
  "link_to_structure_1": "",
  "link_to_structure_2": "",
  "moa_target_pathogen": "Staphylococcus aureus\u00a0biofilms (persisters)",
  "papers_cited_1": "https://www.ncbi.nlm.nih.gov/pubmed/24226776",
  "papers_cited_2": "",
  "papers_cited_3": "",
  "patents": "",
  "prop_select_res_mutants": true,
  "reason_dropped": "",
  "source_hp": "",
  "year_fm": "2013"
}
```
### 8. **associated_protein**
**Summary**: Proteins that associate with the target but are not the primary gene product.
**Purpose**: Free-text associated-protein commentary for targets, with citations via `associated_protein_refs`.
**Size**: ~805 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **200 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| associated_protein_id | integer | NO | Surrogate primary key. Default: sequence: associated_protein_associated_protein_id_seq |
| object_id | integer | NO | Foreign key to `object.object_id`. |
| name | character varying(1000) | YES | Primary display name (target, ligand, family, etc.). |
| type | character varying(200) | NO | Controlled type label (ligand class, interaction type, etc.). |
| associated_object_id | integer | YES | Related `object_id` for complexes, partners, or regulated genes. |
| effect | character varying(1000) | YES | Described pharmacological or phenotypic effect. |
| name_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search on `name`. |

**Primary Keys**: associated_protein_id

**Sample Data**:
```json
{
  "associated_object_id": 28,
  "associated_protein_id": 375,
  "effect": null,
  "name": null,
  "name_vector": null,
  "object_id": 28,
  "type": "Interacting Protein"
}
```
### 9. **associated_protein_refs**
**Summary**: References for associated-protein text.
**Purpose**: Links `associated_protein` rows to `reference`.
**Size**: ~1,169 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **152 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| associated_protein_id | integer | NO | Identifier for an associated protein row (internal). |
| reference_id | integer | NO | Foreign key to `reference.reference_id`. |

**Primary Keys**: associated_protein_id, reference_id

**Sample Data**:
```json
{
  "associated_protein_id": 2,
  "reference_id": 7809
}
```
### 10. **binding_partner**
**Summary**: Nuclear receptor and other targets’ protein–protein binding partners.
**Purpose**: Curated binding-partner descriptions for targets (`object_id`).
**Size**: ~143 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **120 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| binding_partner_id | integer | NO | Surrogate primary key. Default: sequence: binding_partner_binding_partner_id_seq |
| object_id | integer | NO | Foreign key to `object.object_id`. |
| name | character varying(300) | NO | Primary display name (target, ligand, family, etc.). |
| interaction | character varying(200) | YES | Curated field in the IUPHAR/BPS Guide to PHARMACOLOGY database ([guidetopharmacology.org](https://www.guidetopharmacology.org/)); see the `binding_partner` table and related target/ligand pages for context. |
| effect | character varying(2000) | YES | Described pharmacological or phenotypic effect. |
| partner_object_id | integer | YES | Related `object_id` for complexes, partners, or regulated genes. |
| name_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search on `name`. |
| effect_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search (see companion text column). |
| interaction_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search (see companion text column). |

**Primary Keys**: binding_partner_id

**Sample Data**:
```json
{
  "binding_partner_id": 28,
  "effect": "",
  "effect_vector": "",
  "interaction": "Physical",
  "interaction_vector": "'physic':1",
  "name": "",
  "name_vector": "",
  "object_id": 601,
  "partner_object_id": 610
}
```
### 11. **binding_partner_refs**
**Summary**: References for binding-partner commentary.
**Purpose**: Links `binding_partner` to `reference`.
**Size**: ~227 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **56 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| binding_partner_id | integer | NO | Foreign key to `binding_partner.binding_partner_id`. |
| reference_id | integer | NO | Foreign key to `reference.reference_id`. |

**Primary Keys**: binding_partner_id, reference_id

**Sample Data**:
```json
{
  "binding_partner_id": 1,
  "reference_id": 10088
}
```
### 12. **catalytic_receptor**
**Summary**: Enzyme-linked receptors (e.g. receptor tyrosine kinases) — class-specific block.
**Purpose**: One row per catalytic-receptor target; holds class-specific narrative fields.
**Size**: ~313 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **56 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| object_id | integer | NO | Foreign key to `object.object_id`. |
| rtk_class | character varying(20) | YES | Receptor tyrosine kinase subclass label. |

**Primary Keys**: object_id

**Sample Data**:
```json
{
  "object_id": 2437,
  "rtk_class": null
}
```
### 13. **celltype_assoc**
**Summary**: Associations between targets and immune / cell-type contexts.
**Purpose**: Links targets to cell-type ontology and Immunopaedia-style cell categories.
**Size**: ~381 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **184 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| celltype_assoc_id | integer | NO | Surrogate primary key. Default: sequence: celltype_assoc_celltype_assoc_id_seq |
| object_id | integer | NO | Foreign key to `object.object_id`. |
| immuno_celltype_id | integer | NO | Foreign key to `immuno_celltype.immuno_celltype_id`. |
| comment | character varying(2000) | YES | Curated field in the IUPHAR/BPS Guide to PHARMACOLOGY database ([guidetopharmacology.org](https://www.guidetopharmacology.org/)); see the `celltype_assoc` table and related target/ligand pages for context. |
| comment_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search (see companion text column). |

**Primary Keys**: celltype_assoc_id

**Sample Data**:
```json
{
  "celltype_assoc_id": 4965,
  "comment": "Orai1 is expressed by NK cells and is involved in degranulation and NK cell-mediated cytotoxicity.",
  "comment_vector": "'cell':6,15 'cell-medi':14 'cytotox':17 'degranul':11 'express':3 'involv':9 'mediat':16 'nk':5,13 'orai1':1",
  "immuno_celltype_id": 7,
  "object_id": 2964
}
```
### 14. **celltype_assoc_colist**
**Summary**: Column lists / layout metadata for cell-type association displays.
**Purpose**: Supports UI ordering and grouping for `celltype_assoc` tables on the portal.
**Size**: ~341 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **64 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| celltype_assoc_id | integer | NO | Foreign key to `celltype_assoc.celltype_assoc_id`. |
| co_celltype_id | integer | NO | Foreign key to `co_celltype.co_celltype_id`. |
| cellonto_id | character varying(50) | YES | Cell Ontology ID |

**Primary Keys**: celltype_assoc_id, co_celltype_id

**Sample Data**:
```json
{
  "cellonto_id": null,
  "celltype_assoc_id": 4693,
  "co_celltype_id": 11800
}
```
### 15. **celltype_assoc_refs**
**Summary**: Citations for cell-type associations.
**Purpose**: Links `celltype_assoc` to `reference`.
**Size**: ~388 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **72 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| celltype_assoc_id | integer | NO | Foreign key to `celltype_assoc.celltype_assoc_id`. |
| reference_id | integer | NO | Foreign key to `reference.reference_id`. |

**Primary Keys**: celltype_assoc_id, reference_id

**Sample Data**:
```json
{
  "celltype_assoc_id": 4835,
  "reference_id": 32536
}
```
### 16. **cellular_location**
**Summary**: Subcellular localisation notes for targets.
**Purpose**: Textual localization for `object_id` (e.g. membrane, nucleus).
**Size**: ~0 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **16 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| cellular_location_id | integer | NO | Surrogate primary key. Default: sequence: cellular_location_cellular_location_id_seq |
| object_id | integer | NO | Foreign key to `object.object_id`. |
| location | character varying(500) | YES | Subcellular, anatomical, or chromosomal location string. |
| technique | character varying(500) | YES | Experimental method (knockout, qPCR, microarray, …). |
| comments | character varying(1000) | YES | Free-text curator comments. |

**Primary Keys**: cellular_location_id

**Sample Data**: *No data available or table is empty*
### 17. **cellular_location_refs**
**Summary**: References for cellular location statements.
**Purpose**: Links `cellular_location` to `reference`.
**Size**: ~0 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **8192 bytes** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| cellular_location_id | integer | NO | Foreign key to `cellular_location.cellular_location_id`. |
| reference_id | integer | NO | Foreign key to `reference.reference_id`. |

**Primary Keys**: cellular_location_id, reference_id

**Sample Data**: *No data available or table is empty*
### 18. **chembl_cluster**
**Summary**: ChEMBL scaffold/cluster identifiers mapped to ligands.
**Purpose**: Associates `ligand_id` with ChEMBL cluster IDs for cheminformatics browsing.
**Size**: ~1,860 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **224 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| object_id | integer | NO | Foreign key to `object.object_id`. |
| chembl_id | character varying(50) | NO | External database identifier for cross-referencing. |
| cluster | character varying(10) | NO | Cluster identifier (short code) for analogue or scaffold grouping. |
| cluster_family | character varying(10) | NO | Short cluster family code for scaffold grouping. |

**Primary Keys**: object_id, chembl_id

**Sample Data**:
```json
{
  "chembl_id": "CHEMBL99954",
  "cluster": "MS9",
  "cluster_family": "11",
  "object_id": 639
}
```
### 19. **cite**
**Summary**: CITE (citation) identifiers used in family-level citation lists.
**Purpose**: Maps cite tokens to contributor/citation metadata for the Concise Guide / family pages.
**Size**: ~156 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **64 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| cite_id | character varying | NO | GtoPdb CITE family token used for formatted citations on family pages. |
| doi | character varying | YES | Digital Object Identifier for the cited publication. |
| issue_volume | integer | YES | Bibliographic metadata for journal articles or books. |
| issue_number | integer | YES | Bibliographic metadata for journal articles or books. |
| edition | integer | NO | Default: 1 |
| year | integer | YES | Bibliographic metadata for journal articles or books. |
| month | character varying | YES | Bibliographic metadata for journal articles or books. |

**Primary Keys**: cite_id

**Sample Data**:
```json
{
  "cite_id": "F76",
  "doi": "10.2218/gtopdb/F76/2023.3",
  "edition": 1,
  "issue_number": 3,
  "issue_volume": 2023,
  "month": "Nov",
  "year": 2023
}
```
### 20. **clinical_trial**
**Summary**: Clinical trials referenced on ligand or disease pages.
**Purpose**: Stores trial identifiers, titles, phases, and narrative summaries.
**Size**: ~3,657 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **2664 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| clinical_trial_id | integer | NO | Surrogate primary key. Default: sequence: clinical_trial_clinical_trial_id_seq |
| accession | character varying(30) | NO | Clinical trial registry accession (e.g. NCT identifier). |
| title | character varying(1000) | YES | Short title or heading for UI display. |
| url | character varying(200) | NO | HTTP(S) link for external resources or Immunopaedia pages. |
| type | character varying(100) | YES | Default: NULL::character varying |
| description | text | YES | Free-text description field. |
| source | character varying(200) | YES | Curated field in the IUPHAR/BPS Guide to PHARMACOLOGY database ([guidetopharmacology.org](https://www.guidetopharmacology.org/)); see the `clinical_trial` table and related target/ligand pages for context. |

**Primary Keys**: clinical_trial_id

**Sample Data**:
```json
{
  "accession": "NCT03852719",
  "clinical_trial_id": 3678,
  "description": "The primary objective of this study is to evaluate the efficacy of bulevirtide for treatment&#xD; of chronic hepatitis delta (CHD) in comparison to delayed treatment.&#xD;",
  "source": "Gilead Sciences",
  "title": "Study to Assess Efficacy and Safety of Bulevirtide in Participants With Chronic Hepatitis Delta (CHD)",
  "type": "Phase 3 Interventional",
  "url": "https://clinicaltrials.gov/show/NCT03852719"
}
```
### 21. **clinical_trial_refs**
**Summary**: Bibliography links for clinical trial records.
**Purpose**: Links `clinical_trial` rows to `reference`.
**Size**: ~12 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **24 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| clinical_trial_id | integer | NO | Foreign key to `clinical_trial.clinical_trial_id`. |
| reference_id | integer | NO | Foreign key to `reference.reference_id`. |

**Primary Keys**: clinical_trial_id, reference_id

**Sample Data**:
```json
{
  "clinical_trial_id": 1892,
  "reference_id": 38734
}
```
### 22. **co_celltype**
**Summary**: Cell Ontology terms used in immunopharmacology cell-type views.
**Purpose**: Cell-type nodes (CL IDs, labels) for immune cell classification.
**Size**: ~2,548 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **1872 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| co_celltype_id | integer | NO | Surrogate primary key. Default: sequence: co_celltype_co_celltype_id_seq |
| name | character varying(1000) | NO | Primary display name (target, ligand, family, etc.). |
| definition | character varying(1500) | NO | Short definition text for the ontology or disease entry. |
| last_modified | date | YES | Last editorial modification date for the row or text block. |
| type | character varying(50) | NO | Controlled type label (ligand class, interaction type, etc.). |
| cellonto_id | character varying(50) | NO | Curated field in the IUPHAR/BPS Guide to PHARMACOLOGY database ([guidetopharmacology.org](https://www.guidetopharmacology.org/)); see the `co_celltype` table and related target/ligand pages for context. |
| name_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search on `name`. |
| definition_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search (see companion text column). |
| cellonto_id_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search (see companion text column). |

**Primary Keys**: co_celltype_id

**Sample Data**:
```json
{
  "cellonto_id": "CL:0000253",
  "cellonto_id_vector": "'0000253':2 'cl':1",
  "co_celltype_id": 11817,
  "definition": "no definition",
  "definition_vector": "'definit':2",
  "last_modified": "2021-11-15",
  "name": "eurydendroid cell",
  "name_vector": "'cell':2 'eurydendroid':1",
  "type": "newcell"
}
```
### 23. **co_celltype_isa**
**Summary**: Parent/child edges in the cell-type ontology.
**Purpose**: Implements `is_a` relationships between `co_celltype` terms.
**Size**: ~32,331 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **1912 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| parent_id | integer | NO | Parent or child node in a hierarchy. |
| child_id | integer | NO | Parent or child node in a hierarchy. |

**Primary Keys**: parent_id, child_id

**Sample Data**:
```json
{
  "child_id": 1,
  "parent_id": 1
}
```
### 24. **co_celltype_relationship**
**Summary**: Non-hierarchical relationships between cell types.
**Purpose**: Additional ontology edges (e.g. develops_from) for cell types.
**Size**: ~530 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **88 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| co_celltype_rel_id | integer | NO | Surrogate primary key. Default: sequence: co_celltype_relationship_co_celltype_rel_id_seq |
| co_celltype_id | integer | NO | Foreign key to `co_celltype.co_celltype_id`. |
| relationship_id | character varying(50) | NO | Identifier for a relationship edge (ontology or graph). |
| type | character varying(100) | YES | Controlled type label (ligand class, interaction type, etc.). |

**Primary Keys**: co_celltype_rel_id

**Sample Data**:
```json
{
  "co_celltype_id": 11570,
  "co_celltype_rel_id": 1726,
  "relationship_id": "GO:0005634",
  "type": "GO"
}
```
### 25. **cofactor**
**Summary**: Cofactors and co-substrates for enzyme targets.
**Purpose**: Curated cofactor text keyed by `object_id` (enzyme).
**Size**: ~96 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **40 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| cofactor_id | integer | NO | Surrogate primary key. Default: sequence: cofactor_cofactor_id_seq |
| object_id | integer | NO | Foreign key to `object.object_id`. |
| species_id | integer | NO | Foreign key to `species.species_id`. |
| ligand_id | integer | YES | Foreign key to `ligand.ligand_id`. |
| name | character varying(1000) | YES | Primary display name (target, ligand, family, etc.). |
| comments | character varying(1000) | YES | Free-text curator comments. |
| in_iuphar | boolean | NO | Default: true |
| in_grac | boolean | NO | Default: false |
| name_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search on `name`. |

**Primary Keys**: cofactor_id

**Sample Data**:
```json
{
  "cofactor_id": 1,
  "comments": null,
  "in_grac": false,
  "in_iuphar": true,
  "ligand_id": 3045,
  "name": null,
  "name_vector": null,
  "object_id": 639,
  "species_id": 1
}
```
### 26. **cofactor_refs**
**Summary**: References for cofactor commentary.
**Purpose**: Links `cofactor` to `reference`.
**Size**: ~40 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **24 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| cofactor_id | integer | NO | Foreign key to `cofactor.cofactor_id`. |
| reference_id | integer | NO | Foreign key to `reference.reference_id`. |

**Primary Keys**: cofactor_id, reference_id

**Sample Data**:
```json
{
  "cofactor_id": 1,
  "reference_id": 13413
}
```
### 27. **committee**
**Summary**: IUPHAR/NC-IUPHAR committees and editorial groups.
**Purpose**: Directory of committees used to group contributors and families.
**Size**: ~19 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **32 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| committee_id | integer | NO | Surrogate primary key. Default: sequence: committee_committee_id_seq |
| name | character varying(1000) | NO | Primary display name (target, ligand, family, etc.). |
| description | character varying(2000) | YES | Free-text description field. |
| family_id | integer | YES | Foreign key to `family.family_id`. |

**Primary Keys**: committee_id

**Sample Data**:
```json
{
  "committee_id": 1,
  "description": null,
  "family_id": 691,
  "name": "Transporters"
}
```
### 28. **conductance**
**Summary**: Ion channel conductance properties.
**Purpose**: Narrative/structured conductance data for ion channel `object_id` rows.
**Size**: ~55 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **32 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| conductance_id | integer | NO | Surrogate primary key. Default: sequence: conductance_conductance_id_seq |
| object_id | integer | NO | Foreign key to `object.object_id`. |
| overall_channel_conductance | character varying(500) | YES | Ion channel biophysical descriptor (conductance / rectification). |
| macroscopic_current_rectification | character varying(100) | YES | Ion channel biophysical descriptor (conductance / rectification). |
| single_channel_current_rectification | character varying(100) | YES | Ion channel biophysical descriptor (conductance / rectification). |
| species_id | integer | NO | Foreign key to `species.species_id`. |

**Primary Keys**: conductance_id

**Sample Data**:
```json
{
  "conductance_id": 1,
  "macroscopic_current_rectification": "Linear",
  "object_id": 378,
  "overall_channel_conductance": "",
  "single_channel_current_rectification": "",
  "species_id": 1
}
```
### 29. **conductance_refs**
**Summary**: Citations for conductance text.
**Purpose**: Links `conductance` to `reference`.
**Size**: ~66 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **24 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| conductance_id | integer | NO | Foreign key to `conductance.conductance_id`. |
| reference_id | integer | NO | Foreign key to `reference.reference_id`. |

**Primary Keys**: conductance_id, reference_id

**Sample Data**:
```json
{
  "conductance_id": 1,
  "reference_id": 7535
}
```
### 30. **conductance_states**
**Summary**: Channel conductance states (e.g. open, closed).
**Purpose**: State-specific conductance annotations for ion channels.
**Size**: ~6 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **24 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| conductance_states_id | integer | NO | Surrogate primary key. Default: sequence: conductance_states_conductance_states_id_seq |
| object_id | integer | NO | Foreign key to `object.object_id`. |
| receptor | character varying(100) | NO | Receptor or target label in the assay/screen row. |
| state1_high | double precision | YES | Gating-state conductance or open probability bound (multi-state channel model). |
| state1_low | double precision | YES | Gating-state conductance or open probability bound (multi-state channel model). |
| state2_high | double precision | YES | Gating-state conductance or open probability bound (multi-state channel model). |
| state2_low | double precision | YES | Gating-state conductance or open probability bound (multi-state channel model). |
| state3_high | double precision | YES | Gating-state conductance or open probability bound (multi-state channel model). |
| state3_low | double precision | YES | Gating-state conductance or open probability bound (multi-state channel model). |
| state4_high | double precision | YES | Gating-state conductance or open probability bound (multi-state channel model). |
| state4_low | double precision | YES | Gating-state conductance or open probability bound (multi-state channel model). |
| state5_high | double precision | YES | Gating-state conductance or open probability bound (multi-state channel model). |
| state5_low | double precision | YES | Gating-state conductance or open probability bound (multi-state channel model). |
| state6_high | double precision | YES | Gating-state conductance or open probability bound (multi-state channel model). |
| state6_low | double precision | YES | Gating-state conductance or open probability bound (multi-state channel model). |
| most_frequent_state | character varying(50) | YES | Dominant gating state under stated conditions. |

**Primary Keys**: conductance_states_id

**Sample Data**:
```json
{
  "conductance_states_id": 1,
  "most_frequent_state": "2",
  "object_id": 428,
  "receptor": "&alpha;1",
  "state1_high": null,
  "state1_low": null,
  "state2_high": 88,
  "state2_low": 75,
  "state3_high": 68,
  "state3_low": 59,
  "state4_high": 49,
  "state4_low": 43,
  "state5_high": 30,
  "state5_low": 25,
  "state6_high": 18,
  "state6_low": 15
}
```
### 31. **conductance_states_refs**
**Summary**: References for conductance state entries.
**Purpose**: Links `conductance_states` to `reference`.
**Size**: ~11 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **24 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| conductance_states_id | integer | NO | Foreign key to `conductance_states.conductance_states_id`. |
| reference_id | integer | NO | Foreign key to `reference.reference_id`. |

**Primary Keys**: conductance_states_id, reference_id

**Sample Data**:
```json
{
  "conductance_states_id": 1,
  "reference_id": 8162
}
```
### 32. **contributor**
**Summary**: Expert contributors and curators of GtoPdb content.
**Purpose**: People records with affiliations used across family and target pages.
**Size**: ~1,035 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **344 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| contributor_id | integer | NO | Surrogate primary key. Default: sequence: contributor_contributor_id_seq |
| address | text | YES | Contributor or contact metadata. |
| email | character varying(500) | YES | Contributor or contact metadata. |
| first_names | character varying(500) | NO | Contributor name parts. |
| surname | character varying(500) | NO | Contributor name parts. |
| suffix | character varying(200) | YES | Contributor name parts. |
| note | character varying(1000) | YES | Free-text note. |
| orcid | character varying(100) | YES | Contributor or contact metadata. |
| country | character varying(50) | YES | Curated field in the IUPHAR/BPS Guide to PHARMACOLOGY database ([guidetopharmacology.org](https://www.guidetopharmacology.org/)); see the `contributor` table and related target/ligand pages for context. |
| description | character varying(1000) | YES | Free-text description field. |
| institution | character varying(1000) | YES | Contributor or contact metadata. |
| name_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search on `name`. |

**Primary Keys**: contributor_id

**Sample Data**:
```json
{
  "address": null,
  "contributor_id": 650,
  "country": "Russia",
  "description": "",
  "email": null,
  "first_names": "Raul R.",
  "institution": "St. Petersburg State University",
  "name_vector": "'gainetdinov':3 'r':2 'raul':1",
  "note": "",
  "orcid": "0000-0003-2951-6038",
  "suffix": "",
  "surname": "Gainetdinov"
}
```
### 33. **contributor2committee**
**Summary**: Membership of contributors in committees.
**Purpose**: Many-to-many linking `contributor` to `committee`.
**Size**: ~158 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **24 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| contributor_id | integer | NO | Foreign key to `contributor.contributor_id`. |
| committee_id | integer | NO | Foreign key to `committee.committee_id`. |
| role | character varying(200) | YES | Functional role label (e.g. agonist, antagonist in context). |
| display_order | integer | YES | Sort order for lists or navigation. |

**Primary Keys**: contributor_id, committee_id

**Sample Data**:
```json
{
  "committee_id": 1,
  "contributor_id": 532,
  "display_order": 1,
  "role": "Chair"
}
```
### 34. **contributor2family**
**Summary**: Contributors credited on target families.
**Purpose**: Assigns contributors to `family_id` for acknowledgement lists.
**Size**: ~1,120 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **168 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| contributor_id | integer | NO | Foreign key to `contributor.contributor_id`. |
| family_id | integer | NO | Foreign key to `family.family_id`. |
| role | character varying(50) | YES | Functional role label (e.g. agonist, antagonist in context). |
| display_order | integer | YES | Sort order for lists or navigation. |
| old_display_order | integer | YES | Sort order for lists or navigation. |

**Primary Keys**: contributor_id, family_id

**Sample Data**:
```json
{
  "contributor_id": 764,
  "display_order": 0,
  "family_id": 30,
  "old_display_order": 1,
  "role": "Past chairperson"
}
```
### 35. **contributor2intro**
**Summary**: Contributors tied to family introduction sections.
**Purpose**: Links contributors to `introduction` blocks.
**Size**: ~221 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **56 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| contributor_id | integer | NO | Foreign key to `contributor.contributor_id`. |
| family_id | integer | NO | Foreign key to `family.family_id`. |
| display_order | integer | NO | Sort order for lists or navigation. |

**Primary Keys**: contributor_id, family_id

**Sample Data**:
```json
{
  "contributor_id": 436,
  "display_order": 0,
  "family_id": 2
}
```
### 36. **contributor2object**
**Summary**: Contributors credited on individual targets.
**Purpose**: Assigns contributors to specific `object_id` pages.
**Size**: ~3,135 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **272 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| contributor_id | integer | NO | Foreign key to `contributor.contributor_id`. |
| object_id | integer | NO | Foreign key to `object.object_id`. |
| display_order | integer | YES | Sort order for lists or navigation. |
| role | character varying | YES | Functional role label (e.g. agonist, antagonist in context). |

**Primary Keys**: contributor_id, object_id

**Sample Data**:
```json
{
  "contributor_id": 548,
  "display_order": 0,
  "object_id": 355,
  "role": null
}
```
### 37. **contributor_copy**
**Summary**: Alternate or historical contributor name strings.
**Purpose**: Supports name variants for matching and display.
**Size**: ~1,802 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **448 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| contributor_id | integer | YES | Foreign key to `contributor.contributor_id`. |
| address | text | YES | Contributor or contact metadata. |
| email | character varying(500) | YES | Contributor or contact metadata. |
| first_names | character varying(500) | YES | Contributor name parts. |
| surname | character varying(500) | YES | Contributor name parts. |
| suffix | character varying(200) | YES | Contributor name parts. |
| note | character varying(1000) | YES | Free-text note. |
| orcid | character varying(100) | YES | Contributor or contact metadata. |
| country | character varying(50) | YES | Curated field in the IUPHAR/BPS Guide to PHARMACOLOGY database ([guidetopharmacology.org](https://www.guidetopharmacology.org/)); see the `contributor_copy` table and related target/ligand pages for context. |
| description | character varying(1000) | YES | Free-text description field. |
| institution | character varying(1000) | YES | Contributor or contact metadata. |

**Primary Keys**: *None identified*

**Sample Data**:
```json
{
  "address": "Department of Molecular and System Pharmacology<br>Graduate School of Pharmaceutical Sciences<br>University of Kyushu<br>Fukuoka<br>Japan<br>",
  "contributor_id": 556,
  "country": null,
  "description": null,
  "email": "inoue@phar.kyushu-u.ac.jp",
  "first_names": "Kazu",
  "institution": null,
  "note": "",
  "orcid": null,
  "suffix": "",
  "surname": "Inoue"
}
```
### 38. **contributor_link**
**Summary**: External profile URLs for contributors.
**Purpose**: Optional links (e.g. institutional pages).
**Size**: ~229 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **88 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| contributor_id | integer | NO | Foreign key to `contributor.contributor_id`. |
| url | character varying(500) | NO | HTTP(S) link for external resources or Immunopaedia pages. |

**Primary Keys**: contributor_id, url

**Sample Data**:
```json
{
  "contributor_id": 662,
  "url": "https://www.researchgate.net/profile/Joanna_Sharman"
}
```
### 39. **coregulator**
**Summary**: Nuclear receptor co-regulators (coactivators/corepressors).
**Purpose**: Co-regulator narrative keyed by `object_id` (NHR targets).
**Size**: ~277 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **160 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| coregulator_id | integer | NO | Surrogate primary key. Default: sequence: coregulator_coregulator_id_seq |
| object_id | integer | NO | Foreign key to `object.object_id`. |
| activity | character varying(500) | YES | Screening assay value, unit, or activity readout. |
| specific | boolean | YES | Curated field in the IUPHAR/BPS Guide to PHARMACOLOGY database ([guidetopharmacology.org](https://www.guidetopharmacology.org/)); see the `coregulator` table and related target/ligand pages for context. |
| ligand_dependent | boolean | NO | Default: false |
| af2_dependent | boolean | YES | Whether AlphaFold-derived structural data is used. |
| comments | character varying(2000) | YES | Free-text curator comments. |
| coregulator_gene_id | integer | YES | Identifier linking a coregulator gene record. |
| activity_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search (see companion text column). |
| comments_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search on `comments`. |

**Primary Keys**: coregulator_id

**Sample Data**:
```json
{
  "activity": "Co-activator",
  "activity_vector": "'activ':3 'co':2 'co-activ':1",
  "af2_dependent": true,
  "comments": "",
  "comments_vector": "",
  "coregulator_gene_id": 45,
  "coregulator_id": 220,
  "ligand_dependent": true,
  "object_id": 625,
  "specific": false
}
```
### 40. **coregulator_gene**
**Summary**: Named co-regulator genes linked to receptors.
**Purpose**: Gene-centric co-regulator detail paired with `coregulator`.
**Size**: ~86 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **144 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| coregulator_gene_id | integer | NO | Surrogate primary key. Default: sequence: coregulator_gene_coregulator_gene_id_seq |
| primary_name | character varying(300) | NO | Primary display name for lists or synonyms. |
| official_gene_id | character varying(100) | YES | External database identifier for cross-referencing. |
| other_names | character varying(1000) | YES | Historical or alternate naming. |
| species_id | integer | NO | Foreign key to `species.species_id`. |
| nursa_id | character varying(100) | YES | External database identifier for cross-referencing. |
| comments | character varying(2000) | YES | Free-text curator comments. |
| gene_long_name | character varying(2000) | YES | Gene or protein naming for display and search. |
| primary_name_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search (see companion text column). |
| other_names_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search (see companion text column). |
| comments_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search on `comments`. |
| gene_long_name_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search (see companion text column). |

**Primary Keys**: coregulator_gene_id

**Sample Data**:
```json
{
  "comments": null,
  "comments_vector": null,
  "coregulator_gene_id": 28,
  "gene_long_name": null,
  "gene_long_name_vector": null,
  "nursa_id": "10.1621/91HWMRZODA",
  "official_gene_id": "23393",
  "other_names": "PRMT4",
  "other_names_vector": "'prmt4':1",
  "primary_name": "CARM1",
  "primary_name_vector": "'carm1':1",
  "species_id": 1
}
```
### 41. **coregulator_refs**
**Summary**: References for co-regulator commentary.
**Purpose**: Links `coregulator` to `reference`.
**Size**: ~404 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **72 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| coregulator_id | integer | NO | Foreign key to `coregulator.coregulator_id`. |
| reference_id | integer | NO | Foreign key to `reference.reference_id`. |

**Primary Keys**: coregulator_id, reference_id

**Sample Data**:
```json
{
  "coregulator_id": 3,
  "reference_id": 10047
}
```
### 42. **covid_ligand**
**Summary**: Ligands highlighted in the Coronavirus (COVID-19) resource.
**Purpose**: Curated COVID-related ligand list with portal-specific flags.
**Size**: ~120 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **128 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| covid_ligand_id | integer | NO | Surrogate primary key. Default: sequence: covid_ligand_id_seq |
| ligand_id | integer | YES | Foreign key to `ligand.ligand_id`. |
| name | character varying(200) | YES | Primary display name (target, ligand, family, etc.). |
| url | character varying(1000) | YES | HTTP(S) link for external resources or Immunopaedia pages. |
| comment | character varying(5000) | YES | Curated field in the IUPHAR/BPS Guide to PHARMACOLOGY database ([guidetopharmacology.org](https://www.guidetopharmacology.org/)); see the `covid_ligand` table and related target/ligand pages for context. |
| curated | boolean | YES | Default: false |
| secondary_ligand_id | integer | YES | Secondary ligand in a multi-ligand assay or pairing. |
| secondary_name | character varying(200) | YES | Secondary catalogue or alternate naming for commercial ligands. |
| secondary_url | character varying(1000) | YES | External URL for `secondary` resources. |
| secondary_curated | boolean | YES | Secondary catalogue or alternate naming for commercial ligands. |
| priority | integer | YES | Sort order for lists or navigation. |

**Primary Keys**: covid_ligand_id

**Sample Data**:
```json
{
  "comment": "A widely used and low-cost anti-inflammatory corticosteroid drug. On June 16th 2020, it was reported that results from the UK RECOVERY trial have shown a clear survival benefit of low-dose dexamethasone in COVID-19 patients with severe respiratory complications. It cut the risk of death by a third for patients on ventilators and by 20% for those on oxygen. Dexamethasone does not appear to help patients with milder symptoms of coronavirus. Results have now been submitted to the medRxiv preprint server: Horby et al. (2020) Effect of Dexamethasone in Hospitalized Patients with COVID-19: Preliminary Report (<a href=\"https://doi.org/10.1101/2020.06.22.20137273\" target=\"_blank\">https://doi.org/10.1101/2020.06.22.20137273</a>). In the UK, dexamethasone was authorised in mid-June 2020 for use within the NHS, as the first coronavirus treatment proven to reduce mortality <a href=\"https://bit.ly/2VPWKuY\" target=\"_blank\">https://bit.ly/2VPWKuY</a>.",
  "covid_ligand_id": 120,
  "curated": true,
  "ligand_id": 2768,
  "name": "dexamethasone",
  "priority": 1,
  "secondary_curated": null,
  "secondary_ligand_id": null,
  "secondary_name": null,
  "secondary_url": null,
  "url": null
}
```
### 43. **covid_target**
**Summary**: Targets highlighted in the Coronavirus (COVID-19) resource.
**Purpose**: COVID-relevant viral/host targets for quick navigation.
**Size**: ~13 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **32 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| covid_target_id | integer | NO | Surrogate primary key. Default: sequence: covid_target_id_seq |
| object_id | integer | YES | Foreign key to `object.object_id`. |
| name | character varying(1000) | YES | Primary display name (target, ligand, family, etc.). |
| url | character varying(1000) | YES | HTTP(S) link for external resources or Immunopaedia pages. |
| comment | character varying(2000) | YES | Curated field in the IUPHAR/BPS Guide to PHARMACOLOGY database ([guidetopharmacology.org](https://www.guidetopharmacology.org/)); see the `covid_target` table and related target/ligand pages for context. |
| curated | boolean | YES | Default: false |
| target_ligand_id | integer | YES | When the ‘target’ is itself a ligand entity (peptide–peptide cases). |

**Primary Keys**: covid_target_id

**Sample Data**:
```json
{
  "comment": "OAS1 is an interferon-induced gene that is part of the innate antiviral defense system within host cells. The protein is an enzyme that generates 2',5'-oligoadenylates (2-5As), and its activity results in the degradation of viral RNAs (via 2-5As-induced activation of RNase L), thus disrupting viral replication. Naturally ocurring variants in human OAS1 have been associated with the risk of developing severe COVID-19/providing a level of protection from SARS-CoV-2 infection PMID: <a href=\"https://pubmed.ncbi.nlm.nih.gov/34336138/\" target=\"_blank\">34336138</a>, PMID: <a href=\"https://pubmed.ncbi.nlm.nih.gov/34402426/\" target=\"_blank\">34402426</a>, PMID: <a href=\"https://pubmed.ncbi.nlm.nih.gov/34557504/\" target=\"_blank\">34557504</a>, PMID: <a href=\"https://pubmed.ncbi.nlm.nih.gov/34282422/\" target=\"_blank\">34282422</a> (preprint). Prenylated (membrane-bound) splice isoform OAS1 p46 is found in the endomembrane system, where it is able to sense RNA generated by viruses, including SARS-CoV-2, that replicate within intracellular organelles that they appropriate from the host cell's endomembrane system PMID: <a href=\"https://pubmed.ncbi.nlm.nih.gov/34342578/\" target=\"_blank\">34342578</a>. Expression of a prenylated OAS1 isoform was found to be associated with protection from severe COVID-19 in patients. In addition, the SNP Rs10774671 was reported to determine an individual's capacity to generate prenylated OAS1 isoforms. Such OAS1 variants are proposed as inherited genetic elements that can influence the severity of COVID-19 PMID: <a href=\"https://pubmed.ncbi.nlm.nih.gov/34581622/\" target=\"_blank\">34581622</a>",
  "covid_target_id": 10,
  "curated": false,
  "name": "OAS1 (<a href=\"https://www.genenames.org/data/gene-symbol-report/#!/hgnc_id/HGNC:8086\" target=\"_blank\">HGNC:8086</a>; UniProt: <a href=\"https://www.uniprot.org/uniprot/P00973\" target=\"_blank\">P00973<a/>)",
  "object_id": null,
  "target_ligand_id": null,
  "url": null
}
```
### 44. **database**
**Summary**: External database registry (ChEMBL, PubChem, etc.).
**Purpose**: Lookup of external resources for cross-links from ligands and diseases.
**Size**: ~57 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **32 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| database_id | integer | NO | Surrogate primary key. Default: sequence: database_database_id_seq |
| name | character varying(100) | NO | Primary display name (target, ligand, family, etc.). |
| url | text | YES | HTTP(S) link for external resources or Immunopaedia pages. |
| specialist | boolean | NO | Default: false |
| prefix | character varying(100) | YES | Contributor name parts. |

**Primary Keys**: database_id

**Sample Data**:
```json
{
  "database_id": 13,
  "name": "Entrez general",
  "prefix": null,
  "specialist": false,
  "url": "http://www.ncbi.nlm.nih.gov/entrez/viewer.fcgi?id=$PLACEHOLDER"
}
```
### 45. **database_link**
**Summary**: Entity-to-external-ID cross-references.
**Purpose**: Maps targets, ligands, or diseases to third-party database accession strings.
**Size**: ~59,261 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **6448 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| database_link_id | integer | NO | Surrogate primary key. Default: sequence: database_link_database_link_id_seq |
| object_id | integer | NO | Foreign key to `object.object_id`. |
| species_id | integer | NO | Default: 9 |
| database_id | integer | NO | Foreign key to `database.database_id`. |
| placeholder | character varying(100) | NO | Internal editorial or QA flag. |

**Primary Keys**: database_link_id

**Sample Data**:
```json
{
  "database_id": 11,
  "database_link_id": 1,
  "object_id": 1,
  "placeholder": "NP_036717",
  "species_id": 3
}
```
### 46. **deleted_family**
**Summary**: Audit of removed or merged family IDs.
**Purpose**: Preserves history when families are deleted or renumbered.
**Size**: ~45 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **32 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| family_id | integer | NO | Foreign key to `family.family_id`. |
| name | character varying(1000) | NO | Primary display name (target, ligand, family, etc.). |
| previous_names | character varying(300) | YES | Historical or alternate naming. |
| type | character varying(25) | NO | Controlled type label (ligand class, interaction type, etc.). |
| old_family_id | integer | YES | Family id after merge or renumbering. |
| new_family_id | integer | YES | Family id after merge or renumbering. |

**Primary Keys**: family_id

**Sample Data**:
```json
{
  "family_id": 32,
  "name": "GPRC5 receptors",
  "new_family_id": 18,
  "old_family_id": 1323,
  "previous_names": null,
  "type": "gpcr"
}
```
### 47. **discoverx**
**Summary**: DiscoverX assay catalog metadata.
**Purpose**: Reference data for commercial DiscoverX binding assays used in mapping tables.
**Size**: ~0 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **16 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| cat_no | character varying(100) | NO | Commercial catalog or product code (DiscoverX, MCE, …). |
| url | character varying(500) | NO | HTTP(S) link for external resources or Immunopaedia pages. |
| name | character varying(500) | NO | Primary display name (target, ligand, family, etc.). |
| description | character varying(1000) | NO | Free-text description field. |
| species_id | integer | NO | Foreign key to `species.species_id`. |

**Primary Keys**: cat_no

**Sample Data**: *No data available or table is empty*
### 48. **disease**
**Summary**: Disease concepts used in disease–target–ligand linking.
**Purpose**: Core disease records (labels, definitions) for GtoPdb disease views.
**Size**: ~1,201 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **592 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| disease_id | integer | NO | Surrogate primary key. Default: sequence: disease_disease_id_seq |
| name | character varying(1000) | NO | Primary display name (target, ligand, family, etc.). |
| description | text | YES | Free-text description field. |
| type | character varying(30) | YES | Default: NULL::character varying |
| name_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search on `name`. |
| description_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search on `description`. |

**Primary Keys**: disease_id

**Sample Data**:
```json
{
  "description": "",
  "description_vector": "",
  "disease_id": 655,
  "name": "Myelofibrosis",
  "name_vector": "'myelofibrosi':1",
  "type": null
}
```
### 49. **disease2category**
**Summary**: Maps diseases to high-level disease categories.
**Purpose**: Many-to-many between `disease` and `disease_category`.
**Size**: ~89 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **32 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| disease_id | integer | NO | Foreign key to `disease.disease_id`. |
| disease_category_id | integer | NO | Foreign key to `disease_category.disease_category_id`. |
| comment | character varying(500) | YES | Curated field in the IUPHAR/BPS Guide to PHARMACOLOGY database ([guidetopharmacology.org](https://www.guidetopharmacology.org/)); see the `disease2category` table and related target/ligand pages for context. |

**Primary Keys**: disease_id, disease_category_id

**Sample Data**:
```json
{
  "comment": null,
  "disease_category_id": 5,
  "disease_id": 583
}
```
### 50. **disease2synonym**
**Summary**: Synonyms and alternate names for diseases.
**Purpose**: Links diseases to rows in `synonym` for search and display.
**Size**: ~1,001 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **336 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| disease2synonym_id | integer | NO | Surrogate primary key. Default: sequence: disease2synonym_disease2synonym_id_seq |
| disease_id | integer | NO | Foreign key to `disease.disease_id`. |
| synonym | character varying(1000) | NO | Curated field in the IUPHAR/BPS Guide to PHARMACOLOGY database ([guidetopharmacology.org](https://www.guidetopharmacology.org/)); see the `disease2synonym` table and related target/ligand pages for context. |
| synonym_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search (see companion text column). |

**Primary Keys**: disease2synonym_id

**Sample Data**:
```json
{
  "disease2synonym_id": 92,
  "disease_id": 812,
  "synonym": "Hereditary papillary renal cell carcinoma",
  "synonym_vector": "'carcinoma':5 'cell':4 'hereditari':1 'papillari':2 'renal':3"
}
```
### 51. **disease_category**
**Summary**: Broad disease buckets (e.g. oncology, immunology).
**Purpose**: Controlled vocabulary for grouping diseases on the portal.
**Size**: ~5 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **32 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| disease_category_id | integer | NO | Surrogate primary key. Default: sequence: disease_category_disease_category_id_seq |
| name | character varying(1000) | NO | Primary display name (target, ligand, family, etc.). |
| description | text | YES | Free-text description field. |

**Primary Keys**: disease_category_id

**Sample Data**:
```json
{
  "description": null,
  "disease_category_id": 1,
  "name": "Allergy"
}
```
### 52. **disease_database_link**
**Summary**: External disease identifiers (OMIM, DOID, etc.).
**Purpose**: Crosswalk from internal `disease` to external ontologies.
**Size**: ~2,390 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **288 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| disease_database_link_id | integer | NO | Surrogate primary key. Default: sequence: disease_database_link_disease_database_link_id_seq |
| disease_id | integer | NO | Foreign key to `disease.disease_id`. |
| database_id | integer | NO | Foreign key to `database.database_id`. |
| placeholder | character varying(100) | NO | Internal editorial or QA flag. |

**Primary Keys**: disease_database_link_id

**Sample Data**:
```json
{
  "database_id": 1,
  "disease_database_link_id": 2536,
  "disease_id": 1287,
  "placeholder": "618093"
}
```
### 53. **disease_synonym2database_link**
**Summary**: External IDs for disease synonym strings.
**Purpose**: Finer-grained linking of synonym text to database IDs.
**Size**: ~918 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **104 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| disease2synonym_id | integer | NO | Foreign key to `disease2synonym.disease2synonym_id`. |
| disease_database_link_id | integer | NO | Foreign key to `disease_database_link.disease_database_link_id`. |

**Primary Keys**: disease2synonym_id, disease_database_link_id

**Sample Data**:
```json
{
  "disease2synonym_id": 9,
  "disease_database_link_id": 223
}
```
### 54. **dna_binding**
**Summary**: Nuclear receptor DNA-binding / response-element commentary.
**Purpose**: Describes HREs and dimerization for NHR `object_id` rows.
**Size**: ~48 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **88 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| dna_binding_id | integer | NO | Surrogate primary key. Default: sequence: dna_binding_dna_binding_id_seq |
| object_id | integer | NO | Foreign key to `object.object_id`. |
| structure | character varying(500) | YES | Structure description or narrative. |
| sequence | character varying(100) | YES | Mutation or sequence representation (variant or protein). |
| response_element | character varying(500) | YES | Curated field in the IUPHAR/BPS Guide to PHARMACOLOGY database ([guidetopharmacology.org](https://www.guidetopharmacology.org/)); see the `dna_binding` table and related target/ligand pages for context. |
| structure_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search (see companion text column). |
| sequence_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search (see companion text column). |
| response_element_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search (see companion text column). |

**Primary Keys**: dna_binding_id

**Sample Data**:
```json
{
  "dna_binding_id": 1,
  "object_id": 588,
  "response_element": "DR4, Palindrome",
  "response_element_vector": "'dr4':1 'palindrom':2",
  "sequence": "AGGTCA",
  "sequence_vector": "'aggtca':1",
  "structure": "Monomer, Heterodimer, RXR partner",
  "structure_vector": "'heterodim':2 'monom':1 'partner':4 'rxr':3"
}
```
### 55. **dna_binding_refs**
**Summary**: References for DNA-binding commentary.
**Purpose**: Links `dna_binding` to `reference`.
**Size**: ~1 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **24 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| dna_binding_id | integer | NO | Foreign key to `dna_binding.dna_binding_id`. |
| reference_id | integer | NO | Foreign key to `reference.reference_id`. |

**Primary Keys**: dna_binding_id, reference_id

**Sample Data**:
```json
{
  "dna_binding_id": 2,
  "reference_id": 10070
}
```
### 56. **do_disease**
**Summary**: Disease Ontology (DO) terms mirrored for queries.
**Purpose**: DOID-aligned disease metadata used alongside `disease`.
**Size**: ~6,624 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **1888 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| do_disease_id | integer | NO | Surrogate primary key. Default: sequence: do_disease_do_disease_id_seq |
| term | character varying(1000) | NO | Ontology or controlled vocabulary term string. |
| definition | character varying(1500) | NO | Short definition text for the ontology or disease entry. |
| last_modified | date | YES | Last editorial modification date for the row or text block. |
| do_id | character varying(50) | NO | Curated field in the IUPHAR/BPS Guide to PHARMACOLOGY database ([guidetopharmacology.org](https://www.guidetopharmacology.org/)); see the `do_disease` table and related target/ligand pages for context. |

**Primary Keys**: do_disease_id

**Sample Data**:
```json
{
  "definition": "A malignant Vascular tumor that results_in rapidly proliferating, extensively infiltrating anaplastic cells derives_from blood vessels and derived_from the lining of irregular blood-filled spaces.",
  "do_disease_id": 1331,
  "do_id": "DOID:0001816",
  "last_modified": "2018-05-04",
  "term": "angiosarcoma"
}
```
### 57. **do_disease_isa**
**Summary**: DO term parent/child relationships.
**Purpose**: Ontology graph edges for `do_disease`.
**Size**: ~0 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **8192 bytes** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| parent_id | integer | NO | Parent or child node in a hierarchy. |
| child_id | integer | NO | Parent or child node in a hierarchy. |

**Primary Keys**: parent_id, child_id

**Sample Data**: *No data available or table is empty*
### 58. **drug2disease**
**Summary**: Legacy or sparse ligand–disease associations.
**Purpose**: Associates drugs/ligands with disease concepts where used.
**Size**: ~0 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **8192 bytes** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| ligand_id | integer | NO | Foreign key to `ligand.ligand_id`. |
| disease_id | integer | NO | Foreign key to `disease.disease_id`. |

**Primary Keys**: ligand_id, disease_id

**Sample Data**: *No data available or table is empty*
### 59. **drug_approvals**
**Summary**: Regulatory approval events (FDA, EMA, etc.).
**Purpose**: Approval history rows referenced from ligand pages and `ligand2drug_approvals`.
**Size**: ~301 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **104 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| drug_approvals_id | integer | NO | Surrogate primary key. Default: sequence: drug_approvals_id_seq |
| inn | character varying(300) | YES | International Nonproprietary Name string (lowercase in data). |
| trade_name | character varying(300) | YES | Commercial trade name. |
| type | character varying(100) | YES | Controlled type label (ligand class, interaction type, etc.). |
| fda_approval_date | character varying | YES | Regulatory approval date (US FDA / EMA). |
| indication | character varying(2000) | YES | Clinical indication, adverse effects, or medical relevance text. |
| ema_approval_date | character varying | YES | Regulatory approval date (US FDA / EMA). |
| primary_target | character varying(300) | YES | Marks the interaction as defining the ligand’s primary target. |
| comment | character varying(5000) | YES | Curated field in the IUPHAR/BPS Guide to PHARMACOLOGY database ([guidetopharmacology.org](https://www.guidetopharmacology.org/)); see the `drug_approvals` table and related target/ligand pages for context. |
| year | character varying | NO | Default: 1900 |

**Primary Keys**: drug_approvals_id

**Sample Data**:
```json
{
  "comment": "",
  "drug_approvals_id": 63,
  "ema_approval_date": null,
  "fda_approval_date": "2023-01-06",
  "indication": "To treat Alzheimer\u2019s disease",
  "inn": "<Ligand id=12202/>",
  "primary_target": "amyloid \u03b2",
  "trade_name": "Leqembi",
  "type": "mAb",
  "year": "2023"
}
```
### 60. **endo_ligand_pairings**
**Summary**: Endogenous ligand pairings to their cognate receptors.
**Purpose**: Curated primary endogenous ligand–receptor pairings (Latest pairings feature).
**Size**: ~3,319 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **336 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| endo_ligand_pairings_id | character varying | NO | Surrogate primary key. Default: sequence: endo_ligand_pairings_id_seq |
| ligand_id | integer | NO | Foreign key to `ligand.ligand_id`. |
| lig_species_id | integer | NO | Species id for ligand vs target in a cross-species pairing. |
| object_id | integer | NO | Foreign key to `object.object_id`. |
| tar_species_id | integer | YES | Species id for ligand vs target in a cross-species pairing. |
| source | character varying | YES | Curated field in the IUPHAR/BPS Guide to PHARMACOLOGY database ([guidetopharmacology.org](https://www.guidetopharmacology.org/)); see the `endo_ligand_pairings` table and related target/ligand pages for context. |

**Primary Keys**: endo_ligand_pairings_id

**Sample Data**:
```json
{
  "endo_ligand_pairings_id": "32080",
  "lig_species_id": 1,
  "ligand_id": 3672,
  "object_id": 229,
  "source": "list",
  "tar_species_id": 1
}
```
### 61. **endo_ligand_pairings_nomatch**
**Summary**: Pairing candidates that could not be auto-matched.
**Purpose**: Staging/QA table for unresolved endogenous pairings.
**Size**: ~427 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **96 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| endo_ligand_pairings_nomatch_id | character varying | NO | Surrogate primary key. Default: sequence: endo_ligand_pairings_id_seq |
| ligand_id | integer | NO | Foreign key to `ligand.ligand_id`. |
| lig_species_id | integer | NO | Species id for ligand vs target in a cross-species pairing. |
| object_id | integer | NO | Foreign key to `object.object_id`. |
| tar_species_id | integer | YES | Species id for ligand vs target in a cross-species pairing. |
| source | character varying | YES | Curated field in the IUPHAR/BPS Guide to PHARMACOLOGY database ([guidetopharmacology.org](https://www.guidetopharmacology.org/)); see the `endo_ligand_pairings_nomatch` table and related target/ligand pages for context. |

**Primary Keys**: endo_ligand_pairings_nomatch_id

**Sample Data**:
```json
{
  "endo_ligand_pairings_nomatch_id": "35399",
  "lig_species_id": 2,
  "ligand_id": 585,
  "object_id": 34,
  "source": "int",
  "tar_species_id": 1
}
```
### 62. **enzyme**
**Summary**: Enzyme-specific commentary block per target.
**Purpose**: Class-specific enzyme text keyed by `object_id`.
**Size**: ~1,321 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **128 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| object_id | integer | NO | Foreign key to `object.object_id`. |

**Primary Keys**: object_id

**Sample Data**:
```json
{
  "object_id": 645
}
```
### 63. **export_refs**
**Summary**: References bundled for export packages.
**Purpose**: Internal export bibliography helper.
**Size**: ~0 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **16 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| reference_id | integer | YES | Foreign key to `reference.reference_id`. |
| type | character varying(50) | YES | Controlled type label (ligand class, interaction type, etc.). |
| title | character varying(2000) | YES | Short title or heading for UI display. |
| article_title | character varying(1000) | YES | Authorship or title fields for citations or Concise Guide content. |
| year | smallint | YES | Bibliographic metadata for journal articles or books. |
| issue | character varying(50) | YES | Bibliographic metadata for journal articles or books. |
| volume | character varying(50) | YES | Bibliographic metadata for journal articles or books. |
| pages | character varying(50) | YES | Bibliographic metadata for journal articles or books. |
| publisher | character varying(500) | YES | Book or report publication metadata. |
| publisher_address | character varying(2000) | YES | Book or report publication metadata. |
| editors | character varying(2000) | YES | Editorial or authorship attribution for publications. |
| pubmed_id | bigint | YES | PubMed identifier (PMID). |
| isbn | character varying(13) | YES | Book or report publication metadata. |
| pub_status | character varying(100) | YES | Publication status (in press, published, …). |
| topics | character varying(250) | YES | Topic tags or keywords. |
| comments | character varying(500) | YES | Free-text curator comments. |
| read | boolean | YES | Editorial teaser or overview text for a topic or contributor. |
| useful | boolean | YES | Internal editorial or QA flag. |
| website | character varying(500) | YES | External website URL. |
| url | character varying(2000) | YES | HTTP(S) link for external resources or Immunopaedia pages. |
| doi | character varying(500) | YES | Digital Object Identifier for the cited publication. |
| accessed | date | YES | Publication, access, or modification date. |
| modified | date | YES | Curated field in the IUPHAR/BPS Guide to PHARMACOLOGY database ([guidetopharmacology.org](https://www.guidetopharmacology.org/)); see the `export_refs` table and related target/ligand pages for context. |
| patent_number | character varying(250) | YES | Patent reference or assignee (intellectual property). |
| priority | date | YES | Sort order for lists or navigation. |
| publication | date | YES | Authorship or title fields for citations or Concise Guide content. |
| authors | text | YES | Authorship or title fields for citations or Concise Guide content. |
| assignee | character varying(500) | YES | Patent reference or assignee (intellectual property). |
| pmc_id | character varying(50) | YES | PubMed Central identifier. |

**Primary Keys**: *None identified*

**Sample Data**:
```json
{
  "accessed": null,
  "article_title": "Carbonic Anhydrase Inhibitors Targeting Metabolism and Tumor Microenvironment.",
  "assignee": null,
  "authors": "Angeli A, Carta F, Nocentini A, Winum JY, Zalubovskis R, Akdemir A, Onnis V, Eldehna WM, Capasso C, Simone G <i>et al.</i>",
  "comments": null,
  "doi": "10.3390/metabo10100412",
  "editors": null,
  "isbn": null,
  "issue": "10",
  "modified": null,
  "pages": "",
  "patent_number": null,
  "pmc_id": null,
  "priority": null,
  "pub_status": "",
  "publication": null,
  "publisher": null,
  "publisher_address": null,
  "pubmed_id": 33066524,
  "read": null,
  "reference_id": 42295,
  "title": "Metabolites",
  "topics": null,
  "type": "Journal",
  "url": null,
  "useful": null,
  "volume": "10",
  "website": null,
  "year": 2020
}
```
### 64. **expression_experiment**
**Summary**: Metadata for expression experiments (datasets).
**Purpose**: High-level experiment records supporting expression tables.
**Size**: ~1 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **32 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| expression_experiment_id | integer | NO | Surrogate primary key. Default: sequence: expression_experiment_expression_experiment_id_seq |
| description | character varying(1000) | YES | Free-text description field. |
| technique | character varying(100) | YES | Experimental method (knockout, qPCR, microarray, …). |
| species_id | integer | NO | Foreign key to `species.species_id`. |
| baseline | double precision | NO | Screening assay value, unit, or activity readout. |

**Primary Keys**: expression_experiment_id

**Sample Data**:
```json
{
  "baseline": 4,
  "description": "Relative transcript abundance in mouse tissues measured by qPCR from Regard, J.B., Sato, I.T., and Coughlin, S.R. (2008). Anatomical profiling of G protein-coupled receptor expression. Cell, 135(3): 561-71. [PMID:18984166]",
  "expression_experiment_id": 1,
  "species_id": 2,
  "technique": "qPCR"
}
```
### 65. **expression_level**
**Summary**: Quantitative or qualitative expression levels by tissue/cell type.
**Purpose**: Granular expression measurements linked to targets and species.
**Size**: ~13,407 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **1152 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| structural_info_id | integer | NO | Foreign key to `structural_info.structural_info_id`. |
| tissue_id | integer | NO | Curated field in the IUPHAR/BPS Guide to PHARMACOLOGY database ([guidetopharmacology.org](https://www.guidetopharmacology.org/)); see the `expression_level` table and related target/ligand pages for context. |
| expression_experiment_id | integer | NO | Foreign key to `expression_experiment.expression_experiment_id`. |
| value | double precision | NO | Numeric or textual property value. |

**Primary Keys**: structural_info_id, tissue_id, expression_experiment_id

**Sample Data**:
```json
{
  "expression_experiment_id": 1,
  "structural_info_id": 3,
  "tissue_id": 1,
  "value": 4
}
```
### 66. **expression_pathophysiology**
**Summary**: Expression changes in pathophysiological states.
**Purpose**: Narrative linking expression to disease context for `object_id`.
**Size**: ~194 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **200 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| expression_pathophysiology_id | integer | NO | Surrogate primary key. Default: sequence: expression_pathophysiology_expression_pathophysiology_id_seq |
| object_id | integer | NO | Foreign key to `object.object_id`. |
| change | text | YES | Narrative of the measured change (expression, phenotype, or assay readout vs baseline). |
| pathophysiology | text | YES | Curated field in the IUPHAR/BPS Guide to PHARMACOLOGY database ([guidetopharmacology.org](https://www.guidetopharmacology.org/)); see the `expression_pathophysiology` table and related target/ligand pages for context. |
| species_id | integer | NO | Foreign key to `species.species_id`. |
| tissue | character varying(1000) | YES | Tissue or organ context for expression data. |
| technique | character varying(500) | YES | Experimental method (knockout, qPCR, microarray, …). |
| change_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search (see companion text column). |
| tissue_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search on `tissue`. |
| pathophysiology_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search (see companion text column). |
| technique_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search on `technique`. |

**Primary Keys**: expression_pathophysiology_id

**Sample Data**:
```json
{
  "change": "Upregulation",
  "change_vector": "'upregul':1",
  "expression_pathophysiology_id": 106,
  "object_id": 478,
  "pathophysiology": "Congestive heart failure",
  "pathophysiology_vector": "'congest':1 'failur':3 'heart':2",
  "species_id": 1,
  "technique": "RT-PCR",
  "technique_vector": "'pcr':3 'rt':2 'rt-pcr':1",
  "tissue": "Heart",
  "tissue_vector": "'heart':1"
}
```
### 67. **expression_pathophysiology_refs**
**Summary**: Citations for pathophysiology expression text.
**Purpose**: Links `expression_pathophysiology` to `reference`.
**Size**: ~265 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **56 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| expression_pathophysiology_id | integer | NO | Foreign key to `expression_pathophysiology.expression_pathophysiology_id`. |
| reference_id | integer | NO | Foreign key to `reference.reference_id`. |

**Primary Keys**: expression_pathophysiology_id, reference_id

**Sample Data**:
```json
{
  "expression_pathophysiology_id": 1,
  "reference_id": 7754
}
```
### 68. **family**
**Summary**: Target families (GPCR families, ion channel families, etc.).
**Purpose**: Central hierarchy node for the Guide to PHARMACOLOGY; groups related `object` targets.
**Size**: ~880 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **392 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| family_id | integer | NO | Surrogate primary key. Default: sequence: family_family_id_seq |
| name | character varying(1000) | NO | Primary display name (target, ligand, family, etc.). |
| last_modified | date | YES | Last editorial modification date for the row or text block. |
| old_family_id | integer | YES | Family id after merge or renumbering. |
| type | character varying(50) | NO | Controlled type label (ligand class, interaction type, etc.). |
| display_order | integer | YES | Sort order for lists or navigation. |
| annotation_status | integer | NO | Default: 5 |
| previous_names | character varying(300) | YES | Historical or alternate naming. |
| only_grac | boolean | YES | Target appears only in GRAC legacy slices. |
| only_iuphar | boolean | YES | Target appears only in IUPHAR views. |
| in_cgtp | boolean | NO | Default: false |
| cite_id | character varying(20) | YES | Used to shows the ID of the GtoPdb CITE family for citation purposes. |
| name_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search on `name`. |
| previous_names_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search (see companion text column). |

**Primary Keys**: family_id

**Sample Data**:
```json
{
  "annotation_status": 5,
  "cite_id": null,
  "display_order": 1,
  "family_id": 950,
  "in_cgtp": false,
  "last_modified": null,
  "name": "Chemokines",
  "name_vector": "'chemokin':1",
  "old_family_id": null,
  "only_grac": null,
  "only_iuphar": null,
  "previous_names": null,
  "previous_names_vector": null,
  "type": "ligand"
}
```
### 69. **functional_assay**
**Summary**: Assays used to validate target function.
**Purpose**: Functional assay descriptions per target with methods and readouts.
**Size**: ~2,045 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **1520 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| functional_assay_id | integer | NO | Surrogate primary key. Default: sequence: functional_assay_functional_assay_id_seq |
| object_id | integer | NO | Foreign key to `object.object_id`. |
| description | character varying(1000) | NO | Free-text description field. |
| response_measured | character varying(1000) | NO | Screening assay value, unit, or activity readout. |
| species_id | integer | NO | Foreign key to `species.species_id`. |
| tissue | character varying(1000) | NO | Tissue or organ context for expression data. |
| description_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search on `description`. |
| tissue_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search on `tissue`. |
| response_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search (see companion text column). |

**Primary Keys**: functional_assay_id

**Sample Data**:
```json
{
  "description": "Not established.",
  "description_vector": "'establish':2",
  "functional_assay_id": 1097,
  "object_id": 395,
  "response_measured": "",
  "response_vector": "",
  "species_id": 9,
  "tissue": "",
  "tissue_vector": ""
}
```
### 70. **functional_assay_refs**
**Summary**: References for functional assay text.
**Purpose**: Links `functional_assay` to `reference`.
**Size**: ~2,884 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **216 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| functional_assay_id | integer | NO | Foreign key to `functional_assay.functional_assay_id`. |
| reference_id | integer | NO | Foreign key to `reference.reference_id`. |

**Primary Keys**: functional_assay_id, reference_id

**Sample Data**:
```json
{
  "functional_assay_id": 2,
  "reference_id": 3
}
```
### 71. **further_reading**
**Summary**: Family-level further reading pointers.
**Purpose**: Short further-reading list items for families.
**Size**: ~0 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **8192 bytes** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| object_id | integer | NO | Foreign key to `object.object_id`. |
| reference_id | integer | NO | Foreign key to `reference.reference_id`. |

**Primary Keys**: object_id, reference_id

**Sample Data**: *No data available or table is empty*
### 72. **go_process**
**Summary**: Gene Ontology biological process terms.
**Purpose**: GO process nodes for annotation of targets.
**Size**: ~2,707 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **2320 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| go_process_id | integer | NO | Surrogate primary key. Default: sequence: go_process_go_process_seq |
| term | character varying(1000) | NO | Ontology or controlled vocabulary term string. |
| definition | character varying(1500) | NO | Short definition text for the ontology or disease entry. |
| last_modified | date | YES | Last editorial modification date for the row or text block. |
| annotation | character varying(200) | NO | Short annotation or note. |
| go_id | character varying(50) | NO | Gene Ontology term label or identifier. |
| term_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search (see companion text column). |
| definition_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search (see companion text column). |
| go_id_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search (see companion text column). |

**Primary Keys**: go_process_id

**Sample Data**:
```json
{
  "annotation": "GOC:curators",
  "definition": "The regrowth of lost or destroyed tissues.",
  "definition_vector": "'destroy':6 'lost':4 'regrowth':2 'tissu':7",
  "go_id": "GO:0042246",
  "go_id_vector": "'0042246':2 'go':1",
  "go_process_id": 19391,
  "last_modified": "2025-06-12",
  "term": "tissue regeneration",
  "term_vector": "'regener':2 'tissu':1"
}
```
### 73. **go_process_rel**
**Summary**: Relationships between GO processes (e.g. part_of).
**Purpose**: Edges connecting `go_process` terms.
**Size**: ~32,852 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **1936 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| parent_id | integer | NO | Parent or child node in a hierarchy. |
| child_id | integer | NO | Parent or child node in a hierarchy. |

**Primary Keys**: parent_id, child_id

**Sample Data**:
```json
{
  "child_id": 19126,
  "parent_id": 17764
}
```
### 74. **gpcr**
**Summary**: GPCR-specific curated fields (e.g. transduction overview).
**Purpose**: One row per G protein-coupled receptor target extending `object`.
**Size**: ~410 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **96 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| object_id | integer | NO | Foreign key to `object.object_id`. |
| class | character varying(200) | YES | High-level class label (ligand class, family class, …). |
| ligand | character varying(500) | YES | Curated field in the IUPHAR/BPS Guide to PHARMACOLOGY database ([guidetopharmacology.org](https://www.guidetopharmacology.org/)); see the `gpcr` table and related target/ligand pages for context. |

**Primary Keys**: object_id

**Sample Data**:
```json
{
  "class": "class A G protein-coupled receptor",
  "ligand": "",
  "object_id": 109
}
```
### 75. **grac_family_text**
**Summary**: Legacy GRAC long-form family text blocks.
**Purpose**: Historical narrative content from the original GRAC publication pipeline.
**Size**: ~574 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **1776 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| family_id | integer | NO | Foreign key to `family.family_id`. |
| overview | text | YES | Editorial teaser or overview text for a topic or contributor. |
| comments | text | YES | Free-text curator comments. |
| last_modified | date | YES | Last editorial modification date for the row or text block. |
| overview_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search (see companion text column). |
| comments_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search on `comments`. |

**Primary Keys**: family_id

**Sample Data**:
```json
{
  "comments": "<b>Adrenoceptors, &alpha;<sub>1</sub></b><br> The three &alpha;1-adrenoceptor subtypes are &alpha;<sub>1A</sub>, &alpha;<sub>1B</sub> and &alpha;<sub>1D</sub>. The previously described &alpha;<sub>1C</sub>-adrenoceptor is a species homologue that corresponds to the pharmacologically defined &alpha;<sub>1A</sub>-adrenoceptor <Reference id=919/>. Some tissues possess &alpha;<sub>1A</sub>-adrenoceptors (termed &alpha;<sub>1L</sub>-adrenoceptors <Reference id=858/><Reference id=13684/>) that display relatively low affinity in functional and binding assays for <Ligand id=503/> indicative of different receptor states or locations. &alpha;<sub>1A</sub>-Adrenoceptor C-terminal splice variants form homo- and heterodimers, and do not generate a functional &alpha;<sub>1L</sub>-adrenoceptor <Reference id=13685/>. Recombinant &alpha;<sub>1D</sub>-adrenoceptors have been shown in some heterologous systems to be mainly located intracellularly but cell-surface localization is encouraged by truncation of the N-terminus, or by co-expression and formation of heterodimers of with &alpha;<sub>1B</sub>-&alpha;<sub>1B</sub>- or &beta;<sub>2</sub>--&beta;<sub>2</sub>-adrenoceptors <Reference id=13687/><Reference id=13686/>. In blood vessels all three &alpha;<sub>1-</sub>-adrenoceptor subtypes are located both at the cell surface and intracellularly <Reference id=22652/><Reference id=20044/>. Signalling is predominantly <i>via</i> G<sub>q/11</sub> but &alpha;<sub>1</sub>-adrenoceptors also couple to G<sub>i/o</sub>, G<sub>s</sub> and G<sub>12/13</sub>. Several &alpha;<sub>1A</sub>-adrenoceptor agonists display ligand directed signalling bias relative to noradrenaline <Reference id=14845/> although some bias appears to relate to off-target activity <Reference id=41742/> . There are also differences between subtypes in coupling efficiency to different pathways. In vascular smooth muscle, the potency of agonists is related to the predominant subtype, &alpha;<sub>1D</sub>- conveying greater agonist sensitivity compared to &alpha;<sub>1A</sub>-adrenoceptors <Reference id=22653/>.   <br><br><b>Adrenoceptors, &alpha;<sub>2</sub></b><br>The three &alpha;<sub>2</sub>-adrenoceptor subtypes are termed &alpha;<sub>2A</sub>, &alpha;<sub>2B</sub> and &alpha;<sub>2C</sub>. <Ligand id=524/> and <Ligand id=503/> show some selectivity for &alpha;<sub>2B</sub>- and &alpha;<sub>2C</sub>-adrenoceptors over &alpha;<sub>2A</sub>-adrenoceptors. <Ligand id=124/> is an imidazoline partial agonist that also binds to non-GPCR binding sites for imidazolines, classified as I<sub>1</sub>, I<sub>2</sub> and I<sub>3 </sub> <Reference id=28438/> at which catecholamines have a low affinity, while rilmenidine and moxonidine are selective ligands with hypotensive effects <i> in vivo</i>. I<sub>1</sub>-imidazoline recognition sites cause central inhibition of sympathetic tone, I<sub>2</sub>-imidazoline sites are an allosteric binding site on monoamine oxidase B, and I<sub>3</sub>-imidazoline sites regulate insulin secretion from pancreatic &beta;-cells. &alpha;<sub>2A</sub>-adrenoceptor stimulation reduces insulin secretion from &beta;-islets <Reference id=22655/>, with a polymorphism in the 5\u2019-UTR of the ADRA2A gene being associated with increased receptor expression in &beta;-islets and heightened susceptibility to diabetes <Reference id=22656/>. The &alpha;<sub>2A</sub>- and &alpha;<sub>2C</sub>-adrenoceptors form homodimers <Reference id=22657/>. Heterodimers between &alpha;<sub>2A</sub>- and either the &alpha;<sub>2c</sub>-adrenoceptor or &mu; opioid peptide receptor exhibit altered signalling and trafficking properties compared to the individual receptors <Reference id=22657/><Reference id=22658/><Reference id=22659/>. Signalling by &alpha;<sub>2</sub>-adrenoceptors is primarily via G<sub>i/o</sub>, although the &alpha;<sub>2A</sub>-adrenoceptor also couples to G<sub>s</sub> <Reference id=22660/>. Imidazoline compounds display bias relative to each other at the &alpha;<sub>2A</sub>-adrenoceptor <Reference id=22661/>. The noradrenaline reuptake inhibitor desipramine acts directly on &alpha;<sub>2A</sub>-adrenoceptors to promote internalisation <i>via</i> recruitment of &beta;-arrestin <Reference id=22662/>. The structure of the &alpha;<sub>2B</sub>-adrenoceptor has recently been determined by cryo-EM in complex with dexmedetomidine and G&alpha;<sub>o</sub> at a resolution of 2.9\u2009\u00c5 providing insights into the structural requirements required for interactions with &alpha;<sub>2</sub>-adrenoceptor agonists <Reference id=41743/>.   <br><br><b>Adrenoceptors, &beta;</b><br> The three &beta;-adrenoceptors are termed &beta;<sub>1</sub>, &beta;<sub>2</sub> and &beta;<sub>3</sub>. <Ligand id=562/> can be used to define either &beta;<sub>1</sub>- or &beta;<sub>2</sub>-adrenoceptors when conducted in the presence of a &beta;<sub>1</sub>- or a &beta;<sub>2</sub>-adrenoceptor-selective antagonist. A fluorescent analogue of <Ligand id=532/> is used to study &beta;-adrenoceptors in living cells <Reference id=14874/>. <Ligand id=562/> at higher (nM) concentrations has been used to label &beta;<sub>3</sub>-adrenoceptors in systems with few if any other &beta;-adrenoceptor subtypes. The &beta;<sub>3</sub>-adrenoceptor has an intron in the coding region, but splice variants have only been described for the mouse <Reference id=1114/>, where the isoforms display different signalling characteristics <Reference id=14871/>. There are three &beta;-adrenoceptors in turkey (termed the t&beta;, t&beta;3c and t&beta;4c) with pharmacology that differs from the human &beta;-adrenoceptors <Reference id=14872/>. Numerous polymorphisms have been described for the &beta;-adrenoceptors; some are associated with altered signalling and trafficking, susceptibility to disease and/or altered responses to pharmacotherapy <Reference id=27997/>. All &beta;-adrenoceptors couple to G<sub>s</sub> (activating adenylyl cyclase and elevating cAMP levels), but the &beta;<sub>2</sub>- and &beta;<sub>3</sub>-adrenoceptors in particular can also activate G<sub>i</sub> and the &beta;<sub>2</sub>-adrenoceptor activates &beta;-arrestin-mediated signalling. Many &beta;<sub>1</sub>- and &beta;<sub>2</sub>-adrenoceptor antagonists are agonists at &beta;<sub>3</sub>-adrenoceptors (<Ligand id=3462/>, <Ligand id=532/> and <Ligand id=569/>). Many \u2018antagonists\u2019 of cAMP accumulation, for example <Ligand id=551/> and bucindolol, weakly activate MAP kinase pathways <Reference id=14865/><Reference id=14866/><Reference id=14867/><Reference id=14868/><Reference id=14861/><Reference id=14849/> and thus display biased agonism. <Ligand id=550/> acts as a neutral antagonist in most systems so far examined. Agonists also display biased signalling at the &beta;<sub>2</sub>-adrenoceptor <i>via</i> G<sub>s</sub> or arrestins <Reference id=22663/>. X-ray crystal structures have been described of the agonist bound <Reference id=14862/> and antagonist bound forms of the &beta;<sub>1</sub>- <Reference id=1117/>, agonist-bound <Reference id=1116/> and antagonist-bound forms of the &beta;<sub>2</sub>-adrenoceptor <Reference id=14864/><Reference id=14863/>, as well as a fully active agonist-bound, G<sub>s</sub> protein-coupled &beta;<sub>2</sub>-adrenoceptor <Reference id=14352/>, as well as providing insights into the structural requirements for agonist, partial agonist, antagonist, G protein and &beta;-arrestin coupling <Reference id=41744/>. Structures have also been described for negative allosteric modulators of the &beta;<sub>2</sub>-adrenoceptor <Reference id=39757/>. Cryo-EM studies have also been recently described that provide a structural framework for agonist mediated signal transduction <Reference id=41745/>.    The agonists <Ligand id=551/> and bucindolol bind to a site on the &beta;<sub>1</sub>-adrenoceptor involving contacts in TM2, 3, and 7 and extracellular loop 2 that may facilitate coupling to arrestins <Reference id=1117/>. Compounds displaying &beta;-arrestin-biased signalling at the &beta;<sub>2</sub>-adrenoceptor have a greater effect on the conformation of TM7, whereas full agonists for G<sub>s</sub> coupling promote movement of TM5 and TM6 <Reference id=22668/>. Recent studies using NMR spectroscopy demonstrate significant conformational flexibility in the &beta;<sub>2</sub>-adrenoceptor that is stabilized by both agonist and G proteins highlighting the dynamic nature of interactions with both ligand and downstream signalling partners <Reference id=27998/><Reference id=27999/><Reference id=28000/>. Such flexibility likely has consequences for our understanding of allosterism and biased agonism, and for the future therapeutic exploitation of these phenomena.",
  "comments_vector": "'2':866 '2.9':475 '3':860 '5':345 '7':862 'accumul':701 'act':435,716 'activ':187,652,670,677,707,778 'adenylyl':653 'adra2a':349 'adrenoceptor':1,7,19,32,38,42,63,81,85,130,137,156,167,223,224,229,246,250,331,371,382,403,412,429,440,456,489,491,497,514,527,540,555,565,570,600,618,628,648,665,676,688,695,736,772,788,823,855,884,919 'affin':47,279 'agon':715,954 'agonist':168,207,217,255,490,691,727,751,761,780,799,801,839,844,896,925 'agonist-bound':760,779 'alloster':309,817,951 'alpha1':2,6,136,155 'alpha1-adrenoceptor':5 'alpha1-adrenoceptors':154 'alpha1a':10,31,37,62,166,222 'alpha1a-adrenoceptor':30,61,165 'alpha1a-adrenoceptors':36,221 'alpha1b':11,124,125 'alpha1b-alpha1b':123 'alpha1c':18 'alpha1c-adrenoceptor':17 'alpha1d':13,84,214 'alpha1d-adrenoceptors':83 'alpha1l':41,80 'alpha1l-adrenoceptor':79 'alpha1l-adrenoceptors':40 'alpha2':228,402,488 'alpha2-adrenoceptor':227,487 'alpha2-adrenoceptors':401 'alpha2a':233,249,330,367,376,411,428,439 'alpha2a-adrenoceptor':329,410,427 'alpha2a-adrenoceptors':248,438 'alpha2b':234,242,455 'alpha2b-adrenoceptor':454 'alpha2c':236,245,370,381 'alpha2c-adrenoceptor':380 'alpha2c-adrenoceptors':244,369 'alpha2the':225 'also':157,190,257,413,669,728,812,829 'alter':389,633,641 'although':177,408 'analogu':532 'and/or':640 'antagonist':529,689,698,720,754,765,802 'antagonist-bound':764 'appear':180 'arrestin':449,680,740,808,872,877 'assay':52 'associ':352,631 'b':315 'beta':327,338,359,448,492,496,539,564,599,617,627,647,679,807,876 'beta-adrenoceptor':495,538,563,598,616,626,646 'beta-arrestin':447,806 'beta-arrestin-bias':875 'beta-arrestin-medi':678 'beta-cel':326 'beta-islet':337,358 'beta1':500,510,522,684,759,854 'beta1-adrenoceptor':853 'beta2':127,129,501,513,526,661,675,687,735,771,787,822,883,918 'beta2-adrenoceptor':674,686,734,770,786,821,882,917 'beta2-adrenoceptor-selective':525 'beta2-adrenoceptors':128,512 'beta3':503,554,569,664,694 'beta3-adrenoceptor':568 'beta3-adrenoceptors':553,663,693 'bias':173,179,420,714,730,878,953 'bind':51,258,263,310,847 'blood':132 'bound':752,755,762,766,781 'bucindolol':705,846 'c':65 'c-termin':64 'camp':657,700 'catecholamin':275 'caus':297 'cell':100,144,328,543 'cell-surfac':99 'central':298 'characterist':594 'classifi':267 'co':115 'co-express':114 'code':576 'compar':219,394 'complex':466 'compound':418,873 'concentr':547 'conduct':516 'conform':891,913 'consequ':946 'contact':857 'convey':215 'correspond':25 'coupl':158,195,414,649,785,809,870,899 'cryo':463,825 'cryo-em':462,824 'crystal':744 'cyclas':654 'defin':29,508 'demonstr':911 'describ':16,584,623,748,814,832 'desipramin':434 'determin':460 'dexmedetomidin':468 'diabet':365 'differ':56,191,198,592,612 'direct':171,436 'diseas':639 'display':44,169,419,591,713,729,874 'downstream':939 'dynam':931 'effect':289,888 'effici':196 'either':378,509 'elev':656 'em':464,826 'encourag':104 'examin':726 'exampl':703 'exhibit':388 'exploit':960 'express':116,356 'extracellular':864 'facilit':869 'far':725 'flexibl':914,943 'fluoresc':531 'form':69,372,756,767 'format':118 'framework':837 'full':895 'fulli':777 'function':49,78 'futur':958 'g':803,927 'g12/13':163 'galphao':470 'gene':350 'generat':76 'gi':671 'gi/o':160,407 'gpcr':262 'gq/11':152 'greater':216,887 'gs':161,416,651,738,782,898 'heighten':362 'heterodim':72,120,374 'heterolog':91 'higher':545 'highlight':929 'homo':70 'homodim':373 'homologu':23 'human':615 'hypotens':288 'i1':269,293 'i1-imidazoline':292 'i2':270,304 'i2-imidazoline':303 'i3':272,318 'i3-imidazoline':317 'imidazolin':253,266,294,305,319,417 'increas':354 'indic':54 'individu':397 'inhibit':299 'inhibitor':433 'insight':478,793 'insulin':322,334 'interact':485,934 'internalis':443 'intracellular':97,147 'intron':573 'involv':856 'islet':339,360 'isoform':590 'kinas':709 'label':552 'level':658 'ligand':170,286,937 'like':944 'live':542 'local':102 'locat':60,96,140 'loop':865 'low':46,278 'main':95 'mani':683,697 'map':708 'may':868 'mediat':681,840 'modul':818 'monoamin':313 'mous':587 'movement':901 'moxonidin':283 'mu':384 'muscl':203 'n':110 'n-terminus':109 'natur':932 'negat':816 'neutral':719 'nm':546 'nmr':909 'non':261 'non-gpcr':260 'noradrenalin':176,431 'numer':619 'off-target':184 'opioid':385 'oxidas':314 'pancreat':325 'partial':254,800 'particular':667 'partner':941 'pathway':199,710 'peptid':386 'pharmacolog':28,610 'pharmacotherapi':644 'phenomena':963 'polymorph':342,620 'possess':35 'potenc':205 'predomin':150,212 'presenc':519 'previous':15 'primarili':405 'promot':442,900 'properti':393 'protein':784,804,928 'protein-coupl':783 'provid':477,792,834 'ray':743 'recent':458,831,906 'receptor':57,355,387,398 'recognit':295 'recombin':82 'recruit':445 'reduc':333 'region':577 'regul':321 'relat':45,174,182,209,421 'requir':482,483,797 'resolut':473 'respons':642 'reuptak':432 'rilmenidin':281 'secret':323,335 'select':240,285,528 'sensit':218 'sever':164 'show':238 'shown':88 'signal':148,172,390,399,593,634,682,731,841,879,940 'signific':912 'site':264,296,306,311,320,850 'smooth':202 'speci':22 'spectroscopi':910 'splice':67,579 'stabil':922 'state':58 'stimul':332 'structur':451,481,745,796,810,836 'studi':537,827,907 'subtyp':8,138,193,213,230,566 'surfac':101,145 'suscept':363,637 'sympathet':301 'system':92,557,723 'target':186 'tbeta':605 'tbeta3c':606 'tbeta4c':608 'term':39,232,499,603 'termin':66 'terminus':111 'therapeut':959 'three':4,135,226,494,597 'thus':712 'tissu':34 'tm2':859 'tm5':903 'tm6':905 'tm7':893 'tone':302 'traffick':392,636 'transduct':842 'truncat':106 'turkey':602 'understand':949 'use':506,535,550,908 'utr':346 'variant':68,580 'vascular':201 'vessel':133 'via':151,406,444,737 'vivo':291 'weak':706 'well':774,790 'wherea':894 'x':742 'x-ray':741 '\u00e5':476",
  "family_id": 4,
  "last_modified": "2023-08-14",
  "overview": "<b>The nomenclature of the Adrenoceptors has been agreed by the <u>NC-IUPHAR</u> Subcommittee on Adrenoceptors <Reference id=1070/><Reference id=919/></b>.<br><br>      <b>Adrenoceptors, &alpha;<sub>1</sub></b><br>  The three &alpha;<sub>1</sub>-adrenoceptor subtypes &alpha;<sub>1A</sub>, &alpha;<sub>1B</sub> and &alpha;<sub>1D</sub> are activated by the endogenous agonists <Ligand id=479/> and <Ligand id=505/>. -(-)<Ligand id=485/>, <Ligand id=483/> and <Ligand id=515/> are agonists and <Ligand id=503/> and <Ligand id=7170/> antagonists considered selective for &alpha;<sub>1</sub>- relative to &alpha;<sub>2</sub>-adrenoceptors. <Ligand id=5385/> and <Ligand id=482/> (BE2254) are relatively selective radioligands. <Ligand id=487/> also has high affinity for L-type Ca<sup>2+</sup> channels. Fluorescent derivatives of <Ligand id=503/> (Bodipy FLprazosin- QAPB) are used to examine cellular localisation of &alpha;<sub>1</sub>-adrenoceptors. &alpha;<sub>1</sub>-Adrenoceptor agonists are used as nasal decongestants; antagonists to treat symptoms of benign prostatic hyperplasia (<Ligand id=7109/>, <Ligand id=7170/>, <Ligand id=7302/>, <Ligand id=488/> and <Ligand id=493/>, with the last two compounds being &alpha;1<sub>A</sub>-adrenoceptor selective and claiming to relax bladder neck tone with less hypotension); and to a lesser extent hypertension (<Ligand id=7170/>, <Ligand id=7302/>). The &alpha;<sub>1</sub>- and &beta;<sub>2</sub>-adrenoceptor antagonist <Ligand id=551/> is used to treat congestive heart failure, although the contribution of &alpha;<sub>1</sub>-adrenoceptor blockade to the therapeutic effect is unclear. Several anti-depressants and anti-psychotic drugs are &alpha;<sub>1</sub>-adrenoceptor antagonists contributing to side effects such as orthostatic hypotension.  <br><br><b>Adrenoceptors, &alpha;<sub>2</sub></b><br>The three &alpha;<sub>2</sub>-adrenoceptor subtypes &alpha;<sub>2A</sub>, &alpha;<sub>2B</sub> and &alpha;<sub>2C</sub> are activated by <Ligand id=479/> and with lower potency by <Ligand id=505/>. <Ligand id=520/> and <Ligand id=5442/> are agonists and <Ligand id=136/> and <Ligand id=102/> antagonists selective for &alpha;<sub>2</sub>- relative to &alpha;<sub>1</sub>-adrenoceptors. <Ligand id=223/>, <Ligand id=5386/> and <Ligand id=528/> are relatively selective radioligands. There are species variations in the pharmacology of the &alpha;<sub>2A</sub>-adrenoceptor. Multiple mutations of &alpha;<sub>2</sub>-adrenoceptors have been described, some associated with alterations in function. Presynaptic &alpha;<sub>2</sub>-adrenoceptors regulate many functions in the nervous system. The &alpha;<sub>2</sub>-adrenoceptor agonists <Ligand id=516/>, <Ligand id=5443/> and <Ligand id=520/> affect central baroreflex control (hypotension and bradycardia), induce hypnotic effects and analgesia, and modulate seizure activity and platelet aggregation. <Ligand id=516/> is an anti-hypertensive (relatively little used) and counteracts opioid withdrawal. <Ligand id=521/> (also <Ligand id=523/>) is increasingly used as a sedative and analgesic in human <Reference id=41738/> and veterinary medicine and has sympatholytic and anxiolytic properties.    The &alpha;<sub>2</sub>-adrenoceptor antagonist <Ligand id=7241/> is used as an anti-depressant. The &alpha;<sub>2B</sub> subtype appears to be involved in neurotransmission in the spinal cord and &alpha;<sub>2C</sub> in regulating catecholamine release from adrenal chromaffin cells. Although subtype-selective antagonists have been developed, none are used clinically and they remain experimental tools.      <br><br><b>Adrenoceptors, &beta;  </b><br>The three &beta;-adrenoceptor subtypes &beta;<sub>1</sub>, &beta;<sub>2</sub> and &beta;<sub>3</sub> are activated by the endogenous agonists <Ligand id=479/> and <Ligand id=505/>. Isoprenaline is selective for &beta;-adrenoceptors relative to &alpha;<sub>1</sub>- and &alpha;<sub>2</sub>-adrenoceptors, while <Ligand id=564/> (p<i>K</i><sub>i</sub> 8.2-9.2) and <Ligand id=132/> (p<i>K</i><sub>i</sub> 10.0-11.0) are relatively selective antagonists for &beta;<sub>1</sub>- and &beta;<sub>2</sub>- relative to &beta;<sub>3</sub>-adrenoceptors.    <Ligand id=505/>, <Ligand id=538/> and <Ligand id=5571/> show selectivity for &beta;<sub>1</sub>- relative to &beta;<sub>2</sub>-adrenoceptors. Pharmacological differences exist between human and mouse &beta;<sub>3</sub>-adrenoceptors, and the 'rodent selective' agonists <Ligand id=567/> and <Ligand id=3462/> have low efficacy at the human &beta;<sub>3</sub>-adrenoceptor whereas   <Ligand id=532/> (low potency) and <Ligand id=3931/> activate human &beta;<sub>3</sub>-adrenoceptors [88]. &beta;<sub>3</sub>-Adrenoceptors are resistant to blockade by <Ligand id=564/>, but can be blocked by high concentrations of <Ligand id=550/>. <Ligand id=547/> has reasonably high affinity at &beta;<sub>3</sub>-adrenoceptors, but does not discriminate between the three &beta;- subtypes <Reference id=41739/> whereas <Ligand id=3932/> is more selective. [<sup>125</sup>I]-<Ligand id=132/>, [<sup>125</sup>I]-hydroxy benzylpindolol and [<sup>3</sup>H]-<Ligand id=563/> are high affinity radioligands that label &beta;<sub>1</sub>- and &beta;<sub>2</sub>- adrenoceptors and &beta;<sub>3</sub>-adrenoceptors can be labelled with higher concentrations (nM) of [<sup>125</sup>I]-<Ligand id=132/> together with &beta;<sub>1</sub>- and &beta;<sub>2</sub>-adrenoceptor antagonists. Fluorescent ligands such as BODIPY-TMR-CGP12177 can be used to track &beta;-adrenoceptors at the cellular level [8]. Somewhat selective &beta;<sub>1</sub>-adrenoceptor agonists (<Ligand id=534/>, <Ligand id=535/>) are used short term to treat cardiogenic shock but, chronically, reduce survival.     &beta;<sub>1</sub>-Adrenoceptor-preferring antagonists are used to treat cardiac arrhythmias (<Ligand id=548/>, <Ligand id=7129/>, <Ligand id=7178/>) and cardiac failure (<Ligand id=553/>, <Ligand id=7246/>) but also in combination with other treatments to treat hypertension (<Ligand id=548/>, <Ligand id=549/>, <Ligand id=7129/>, <Ligand id=553/> and <Ligand id=7246/>) <Reference id=41740/>. Cardiac failure is also treated with carvedilol that blocks &beta;<sub>1</sub>- and &beta;<sub>2</sub>-adrenoceptors, as well as &alpha;<sub>1</sub>-adrenoceptors. Short (<Ligand id=558/>, <Ligand id=560/>) and long (<Ligand id=3465/>, <Ligand id=559/>) acting &beta;<sub>2</sub>-adrenoceptor-selective agonists are powerful bronchodilators used to treat respiratory disorders. Many first generation &beta;-adrenoceptor antagonists (<Ligand id=564/>) block both &beta;<sub>1</sub>- and &beta;<sub>2</sub>-adrenoceptors and there are no &beta;<sub>2</sub>-adrenoceptor-selective antagonists used therapeutically. The &beta;<sub>3</sub>-adrenoceptor agonist <Ligand id=7445/> is used to control overactive bladder syndrome. There is evidence to suggest that &beta;-adrenoceptor antagonists can reduce metastasis in certain types of cancer <Reference id=41741/>.",
  "overview_vector": "'-11.0':402 '-9.2':398 '10.0':401 '125i':498,499,526 '3h':503 '8':555 '8.2':397 '88':460 'act':622 'activ':30,189,274,375,455 'adren':342 'adrenoceptor':5,16,17,23,50,82,85,109,132,147,167,177,182,209,226,232,245,256,313,362,368,387,394,415,425,435,450,459,463,484,513,517,533,550,560,576,612,618,625,641,649,656,664,681 'affect':259 'affin':60,480,506 'aggreg':277 'agonist':34,38,86,198,257,379,440,561,627,665 'agre':8 'alpha1':18,22,45,81,84,128,146,166,208,390,617 'alpha1-adrenoceptor':21,83,145,165 'alpha1-adrenoceptors':80,207,616 'alpha1a':25,108 'alpha1a-adrenoceptor':107 'alpha1b':26 'alpha1d':28 'alpha2':49,181,204,231,244,255,312,393 'alpha2-adrenoceptor':180,254,311 'alpha2-adrenoceptors':48,230,243,392 'alpha2a':184,225 'alpha2a-adrenoceptor':224 'alpha2b':185,323 'alpha2c':187,336 'alpha2the':178 'also':57,290,589,602 'alter':239 'although':141,345 'analges':298 'analgesia':270 'antagonist':41,92,133,168,201,314,349,406,534,578,642,658,682 'anti':157,161,281,320 'anti-depress':156,319 'anti-hypertens':280 'anti-psychot':160 'anxiolyt':308 'appear':325 'arrhythmia':584 'associ':237 'baroreflex':261 'be2254':52 'benign':97 'benzylpindolol':501 'beta':363,367,386,492,549,640,680 'beta-adrenoceptor':366,385,548,639,679 'beta1':370,408,420,510,529,559,575,608,645 'beta1-adrenoceptor':558 'beta1-adrenoceptor-preferring':574 'beta2':131,371,410,424,512,532,611,624,648,655 'beta2-adrenoceptor':130,531 'beta2-adrenoceptor-selective':623,654 'beta2-adrenoceptors':423,610,647 'beta3':373,414,434,449,458,462,483,516,663 'beta3-adrenoceptor':448,662 'beta3-adrenoceptors':413,433,457,461,482,515 'bladder':115,671 'block':472,607,643 'blockad':148,467 'bodipi':70,540 'bodipy-tmr-cgp12177':539 'bradycardia':265 'bronchodil':630 'ca2':65 'cancer':690 'cardiac':583,586,599 'cardiogen':568 'carvedilol':605 'catecholamin':339 'cell':344 'cellular':77,553 'central':260 'certain':687 'cgp12177':542 'channel':66 'chromaffin':343 'chronic':571 'claim':112 'clinic':356 'combin':591 'compound':105 'concentr':475,523 'congest':138 'consid':42 'contribut':143,169 'control':262,669 'cord':334 'counteract':287 'decongest':91 'depress':158,321 'deriv':68 'describ':235 'develop':352 'differ':427 'discrimin':488 'disord':635 'drug':163 'effect':152,172,268 'efficaci':444 'endogen':33,378 'evid':675 'examin':76 'exist':428 'experiment':360 'extent':125 'failur':140,587,600 'first':637 'flprazosin':71 'fluoresc':67,535 'function':241,248 'generat':638 'heart':139 'high':59,474,479,505 'higher':522 'human':300,430,447,456 'hydroxi':500 'hyperplasia':99 'hypertens':126,282,597 'hypnot':267 'hypotens':120,176,263 'increas':292 'induc':266 'involv':328 'isoprenalin':381 'iuphar':13 'l':63 'l-type':62 'label':509,520 'last':103 'less':119 'lesser':124 'level':554 'ligand':536 'littl':284 'localis':78 'long':621 'low':443,452 'lower':193 'mani':247,636 'medicin':303 'metastasi':685 'modul':272 'mous':432 'multipl':227 'mutat':228 'nasal':90 'nc':12 'nc-iuphar':11 'neck':116 'nervous':251 'neurotransmiss':330 'nm':524 'nomenclatur':2 'none':353 'opioid':288 'orthostat':175 'overact':670 'pharmacolog':221,426 'pki':396,400 'platelet':276 'potenc':194,453 'power':629 'prefer':577 'presynapt':242 'properti':309 'prostat':98 'psychot':162 'qapb':72 'radioligand':56,214,507 'reason':478 'reduc':572,684 'regul':246,338 'relat':46,54,205,212,283,388,404,411,421 'relax':114 'releas':340 'remain':359 'resist':465 'respiratori':634 'rodent':438 'sedat':296 'seizur':273 'select':43,55,110,202,213,348,383,405,418,439,497,557,626,657 'sever':155 'shock':569 'short':564,619 'show':417 'side':171 'somewhat':556 'speci':217 'spinal':333 'subcommitte':14 'subtyp':24,183,324,347,369,493 'subtype-select':346 'suggest':677 'surviv':573 'sympatholyt':306 'symptom':95 'syndrom':672 'system':252 'term':565 'therapeut':151,660 'three':20,179,365,491 'tmr':541 'togeth':527 'tone':117 'tool':361 'track':547 'treat':94,137,567,582,596,603,633 'treatment':594 'two':104 'type':64,688 'unclear':154 'use':74,88,135,285,293,316,355,545,563,580,631,659,667 'variat':218 'veterinari':302 'well':614 'wherea':451,494 'withdraw':289"
}
```
### 76. **grac_functional_characteristics**
**Summary**: GRAC functional characteristics snippets.
**Purpose**: Structured legacy characteristics text per family/target.
**Size**: ~158 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **152 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| object_id | integer | NO | Foreign key to `object.object_id`. |
| functional_characteristics | text | NO | GRAC functional characteristics text block. |
| functional_characteristics_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search (see companion text column). |

**Primary Keys**: object_id

**Sample Data**:
```json
{
  "functional_characteristics": "K<sub>V</sub>",
  "functional_characteristics_vector": "'kv':1",
  "object_id": 545
}
```
### 77. **grac_further_reading**
**Summary**: GRAC further reading entries.
**Purpose**: Legacy further-reading references tied to families.
**Size**: ~4,013 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **312 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| family_id | integer | NO | Foreign key to `family.family_id`. |
| reference_id | integer | NO | Foreign key to `reference.reference_id`. |
| key_ref | boolean | NO | Default: false |

**Primary Keys**: family_id, reference_id

**Sample Data**:
```json
{
  "family_id": 1,
  "key_ref": false,
  "reference_id": 403
}
```
### 78. **grac_ligand_rank_potency**
**Summary**: GRAC ligand rank/potency tables.
**Purpose**: Ordered ligand potency rankings within families.
**Size**: ~436 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **176 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| grac_ligand_rank_potency_id | integer | NO | Surrogate primary key. Default: sequence: grac_ligand_rank_potency_grac_ligand_rank_potency_id_seq |
| object_id | integer | NO | Foreign key to `object.object_id`. |
| description | character varying(500) | NO | Free-text description field. |
| rank_potency | character varying(2000) | NO | Ordered potency ranking within a family (GRAC tables). |
| species_id | integer | NO | Foreign key to `species.species_id`. |
| in_iuphar | boolean | NO | Default: true |
| rank_potency_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search (see companion text column). |

**Primary Keys**: grac_ligand_rank_potency_id

**Sample Data**:
```json
{
  "description": "Physical activators",
  "grac_ligand_rank_potency_id": 197,
  "in_iuphar": true,
  "object_id": 494,
  "rank_potency": "Heat ~ 35&deg;C",
  "rank_potency_vector": "'35degc':2 'heat':1",
  "species_id": 1
}
```
### 79. **grac_ligand_rank_potency_refs**
**Summary**: Citations for GRAC potency rankings.
**Purpose**: Links `grac_ligand_rank_potency` to `reference`.
**Size**: ~334 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **56 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| grac_ligand_rank_potency_id | integer | NO | Foreign key to `grac_ligand_rank_potency.grac_ligand_rank_potency_id`. |
| reference_id | integer | NO | Foreign key to `reference.reference_id`. |

**Primary Keys**: grac_ligand_rank_potency_id, reference_id

**Sample Data**:
```json
{
  "grac_ligand_rank_potency_id": 382,
  "reference_id": 22385
}
```
### 80. **grac_transduction**
**Summary**: GRAC transduction mechanism summaries.
**Purpose**: Legacy G protein / signalling coupling text.
**Size**: ~257 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **64 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| object_id | integer | NO | Foreign key to `object.object_id`. |
| transduction | character varying(1000) | NO | Curated field in the IUPHAR/BPS Guide to PHARMACOLOGY database ([guidetopharmacology.org](https://www.guidetopharmacology.org/)); see the `grac_transduction` table and related target/ligand pages for context. |

**Primary Keys**: object_id

**Sample Data**:
```json
{
  "object_id": 281,
  "transduction": "G<sub>q/11</sub> <Reference id=4263/><Reference id=4264/><Reference id=4288/>"
}
```
### 81. **grouping**
**Summary**: Groups of families and higher-level navigation groupings.
**Purpose**: Supports nested navigation (groups of groups) on the website. Database comment: groups of families and groups of groups
**Size**: ~882 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **104 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| group_id | integer | NO | Curated field in the IUPHAR/BPS Guide to PHARMACOLOGY database ([guidetopharmacology.org](https://www.guidetopharmacology.org/)); see the `grouping` table and related target/ligand pages for context. |
| family_id | integer | NO | Foreign key to `family.family_id`. |
| display_order | integer | NO | Default: 1 |

**Primary Keys**: group_id, family_id

**Sample Data**:
```json
{
  "display_order": 1,
  "family_id": 996,
  "group_id": 995
}
```
### 82. **gtip2go_process**
**Summary**: GO processes highlighted in Guide to IMMUNOPHARMACOLOGY.
**Purpose**: Links GTIP process nodes to `go_process` for immune-focused views.
**Size**: ~53 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **32 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| gtip_process_id | integer | NO | Foreign key to `gtip_process.gtip_process_id`. |
| go_process_id | integer | NO | Foreign key to `go_process.go_process_id`. |
| comment | character varying(500) | YES | Curated field in the IUPHAR/BPS Guide to PHARMACOLOGY database ([guidetopharmacology.org](https://www.guidetopharmacology.org/)); see the `gtip2go_process` table and related target/ligand pages for context. |
| go_id | character varying(15) | YES | Gene Ontology term label or identifier. |
| go_term | character varying(500) | YES | Gene Ontology term label or identifier. |

**Primary Keys**: gtip_process_id, go_process_id

**Sample Data**:
```json
{
  "comment": null,
  "go_id": "GO:0001776",
  "go_process_id": 17775,
  "go_term": "leukocyte homeostasis",
  "gtip_process_id": 6
}
```
### 83. **gtip_process**
**Summary**: Immunopharmacology process headings and anchors.
**Purpose**: Short labels and anchors for Guide to Immunopharmacology process pages.
**Size**: ~11 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **48 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| gtip_process_id | integer | NO | Surrogate primary key. Default: sequence: gtip_process_gtip_process_seq |
| term | character varying(1000) | NO | Ontology or controlled vocabulary term string. |
| definition | character varying(1500) | NO | Short definition text for the ontology or disease entry. |
| last_modified | date | YES | Last editorial modification date for the row or text block. |
| short_term | character varying(500) | YES | Short term for wbe display, may contain html |
| anchor | character varying(10) | YES | very short text to use as link anchor on webpages |
| term_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search (see companion text column). |
| definition_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search (see companion text column). |

**Primary Keys**: gtip_process_id

**Sample Data**:
```json
{
  "anchor": "AntiPres",
  "definition": "",
  "definition_vector": "",
  "gtip_process_id": 3,
  "last_modified": "2017-05-11",
  "short_term": "Prod. of signals<br>&amp; mediators",
  "term": "Antigen presentation",
  "term_vector": "'antigen':1 'present':2"
}
```
### 84. **gtopdb_cidmap**
**Summary**: PubChem compound IDs (CID) mapped to ligands.
**Purpose**: Bridge table for PubChem structure integration and downloads.
**Size**: ~12,219 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **864 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| ligand_id | integer | YES | Foreign key to `ligand.ligand_id`. |
| name | character varying(1000) | YES | Primary display name (target, ligand, family, etc.). |
| pubchem_sid | bigint | YES | PubChem Substance ID (when ligand is registered in PubChem). |
| placeholder | character varying(100) | YES | Internal editorial or QA flag. |

**Primary Keys**: *None identified*

**Sample Data**:
```json
{
  "ligand_id": 1,
  "name": "flesinoxan",
  "placeholder": "57347",
  "pubchem_sid": 135650267
}
```
### 85. **hot_topics**
**Summary**: Editorial hot topics (timely review articles).
**Purpose**: Landing pages for themed pharmacology topics on guidetopharmacology.org.
**Size**: ~547 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **512 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| hot_topics_id | integer | NO | Surrogate primary key. Default: sequence: hot_topics_id_seq |
| date | date | NO | Publication, access, or modification date. |
| blog_url | character varying(400) | YES | Link to a related blog post or news article on the Guide to PHARMACOLOGY blog. |
| blog_summary | character varying(2000) | YES | Optional blog / news teaser content for hot topics. |
| has_blog | boolean | NO | Default: false |
| author_name | character varying(100) | YES | Contributor or publication author metadata. |
| author_affiliation | character varying(200) | YES | Contributor or publication author metadata. |
| author_link | character varying(200) | YES | Contributor or publication author metadata. |
| author_twitter | character varying(50) | YES | Contributor or publication author metadata. |
| authorship | character varying(1000) | YES | Editorial or authorship attribution for publications. |
| title | character varying(1000) | YES | Short title or heading for UI display. |
| title_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search on `title`. |
| blog_summary_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search (see companion text column). |
| authorship_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search (see companion text column). |

**Primary Keys**: hot_topics_id

**Sample Data**:
```json
{
  "author_affiliation": null,
  "author_link": null,
  "author_name": null,
  "author_twitter": null,
  "authorship": null,
  "authorship_vector": null,
  "blog_summary": null,
  "blog_summary_vector": null,
  "blog_url": null,
  "date": "2022-06-09",
  "has_blog": false,
  "hot_topics_id": 312,
  "title": "Ketamine exerts its sustained antidepressant effects via cell-type-specific regulation of Kcnq2",
  "title_vector": "'antidepress':5 'cell':9 'cell-type-specif':8 'effect':6 'exert':2 'kcnq2':14 'ketamin':1 'regul':12 'specif':11 'sustain':4 'type':10 'via':7"
}
```
### 86. **hot_topics2family**
**Summary**: Hot topics linked to target families.
**Purpose**: Many-to-many between `hot_topics` and `family`.
**Size**: ~0 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **8192 bytes** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| hot_topics_id | integer | NO | Foreign key to `hot_topics.hot_topics_id`. |
| family_id | integer | NO | Foreign key to `family.family_id`. |

**Primary Keys**: hot_topics_id, family_id

**Sample Data**: *No data available or table is empty*
### 87. **hot_topics2object**
**Summary**: Hot topics linked to individual targets.
**Purpose**: Many-to-many between `hot_topics` and `object`.
**Size**: ~0 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **8192 bytes** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| hot_topics_id | integer | NO | Foreign key to `hot_topics.hot_topics_id`. |
| object_id | integer | NO | Foreign key to `object.object_id`. |

**Primary Keys**: hot_topics_id, object_id

**Sample Data**: *No data available or table is empty*
### 88. **hot_topics_refs**
**Summary**: Bibliography for hot topic pages.
**Purpose**: Links `hot_topics` to `reference`.
**Size**: ~570 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **88 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| hot_topics_id | integer | NO | Foreign key to `hot_topics.hot_topics_id`. |
| reference_id | integer | NO | Foreign key to `reference.reference_id`. |
| is_primary | boolean | NO | Default: false |

**Primary Keys**: hot_topics_id, reference_id

**Sample Data**:
```json
{
  "hot_topics_id": 312,
  "is_primary": false,
  "reference_id": 43788
}
```
### 89. **hottopic_refs**
**Summary**: Alternate hot-topic reference wiring.
**Purpose**: Additional reference joins for topic content.
**Size**: ~10 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **32 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| reference_id | integer | NO | ID of reference from reference table |
| date | date | NO | Publication, access, or modification date. |
| blog_url | character varying(200) | YES | Link to a related blog post or news article on the Guide to PHARMACOLOGY blog. |
| blog_summary | character varying(2000) | YES | Optional blog / news teaser content for hot topics. |
| has_blog | boolean | NO | Default: false |
| author_name | character varying(100) | YES | Contributor or publication author metadata. |
| author_affiliation | character varying(200) | YES | Contributor or publication author metadata. |
| author_link | character varying(200) | YES | Contributor or publication author metadata. |
| author_twitter | character varying(50) | YES | Contributor or publication author metadata. |

**Primary Keys**: reference_id

**Sample Data**:
```json
{
  "author_affiliation": null,
  "author_link": null,
  "author_name": null,
  "author_twitter": null,
  "blog_summary": null,
  "blog_url": null,
  "date": "2018-10-25",
  "has_blog": false,
  "reference_id": 36301
}
```
### 90. **immuno2co_celltype**
**Summary**: Maps immunopharmacology sections to cell ontology terms.
**Purpose**: Connects immune portal structure to `co_celltype`.
**Size**: ~16 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **32 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| immuno_celltype_id | integer | NO | Foreign key to `immuno_celltype.immuno_celltype_id`. |
| cellonto_id | character varying(50) | NO | Curated field in the IUPHAR/BPS Guide to PHARMACOLOGY database ([guidetopharmacology.org](https://www.guidetopharmacology.org/)); see the `immuno2co_celltype` table and related target/ligand pages for context. |
| comment | character varying(500) | YES | Curated field in the IUPHAR/BPS Guide to PHARMACOLOGY database ([guidetopharmacology.org](https://www.guidetopharmacology.org/)); see the `immuno2co_celltype` table and related target/ligand pages for context. |

**Primary Keys**: immuno_celltype_id, cellonto_id

**Sample Data**:
```json
{
  "cellonto_id": "CL:0000945",
  "comment": "lymphocyte of B lineage",
  "immuno_celltype_id": 1
}
```
### 91. **immuno_celltype**
**Summary**: Immunopharmacology cell-type categories.
**Purpose**: Curated immune cell groupings with display names for Guide to IMMUNOPHARMACOLOGY.
**Size**: ~10 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **96 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| immuno_celltype_id | integer | NO | Surrogate primary key. Default: sequence: immuno_celltype_immuno_celltype_id_seq |
| term | character varying(1000) | NO | Ontology or controlled vocabulary term string. |
| definition | character varying(2500) | NO | Short definition text for the ontology or disease entry. |
| last_modified | date | YES | Last editorial modification date for the row or text block. |
| short_term | character varying(500) | YES | Short name for celltype category, may contain html |
| term_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search (see companion text column). |
| definition_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search (see companion text column). |

**Primary Keys**: immuno_celltype_id

**Sample Data**:
```json
{
  "definition": "The <i>Natural killer cells</i> category includes the following Cell Ontology parent terms:<br><br> <b>natural killer cell</b> (<a href=\"https://www.ebi.ac.uk/ols/ontologies/cl/terms?iri=http%3A%2F%2Fpurl.obolibrary.org%2Fobo%2FCL_0000623\" target=\"_blank\" rel=\"noopener noreferrer\">CL:0000623</a>) - A lymphocyte that can spontaneously kill a variety of target cells without prior antigenic activation via germline encoded activation receptors and also regulate immune responses via cytokine release and direct contact with other cells.",
  "definition_vector": "'0000623':17 'activ':32,36 'also':39 'antigen':31 'categori':5 'cell':4,9,15,28,51 'cl':16 'contact':48 'cytokin':44 'direct':47 'encod':35 'follow':8 'germlin':34 'immun':41 'includ':6 'kill':23 'killer':3,14 'lymphocyt':19 'natur':2,13 'ontolog':10 'parent':11 'prior':30 'receptor':37 'regul':40 'releas':45 'respons':42 'spontan':22 'target':27 'term':12 'varieti':25 'via':33,43 'without':29",
  "immuno_celltype_id": 7,
  "last_modified": "2016-08-16",
  "short_term": "NK_cells",
  "term": "Natural killer cells",
  "term_vector": "'cell':3 'killer':2 'natur':1"
}
```
### 92. **immuno_disease2ligand**
**Summary**: Immune-relevant disease–ligand associations.
**Purpose**: Links diseases to ligands in the immunopharmacology context.
**Size**: ~744 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **312 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| immuno_disease2ligand_id | integer | NO | Surrogate primary key. Default: sequence: immuno_disease2ligand_immuno_disease2ligand_id_seq |
| ligand_id | integer | NO | Foreign key to `ligand.ligand_id`. |
| disease_id | integer | YES | Foreign key to `disease.disease_id`. |
| comment | character varying(1000) | YES | Curated field in the IUPHAR/BPS Guide to PHARMACOLOGY database ([guidetopharmacology.org](https://www.guidetopharmacology.org/)); see the `immuno_disease2ligand` table and related target/ligand pages for context. |
| immuno | boolean | YES | Default: true |
| comment_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search (see companion text column). |

**Primary Keys**: immuno_disease2ligand_id

**Sample Data**:
```json
{
  "comment": "In clinical trial in China.",
  "comment_vector": "'china':5 'clinic':2 'trial':3",
  "disease_id": 801,
  "immuno": true,
  "immuno_disease2ligand_id": 273,
  "ligand_id": 9296
}
```
### 93. **immuno_disease2ligand_refs**
**Summary**: Citations for immune disease–ligand links.
**Purpose**: Links `immuno_disease2ligand` rows to `reference`.
**Size**: ~100 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **24 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| immuno_disease2ligand_id | integer | NO | Foreign key to `immuno_disease2ligand.immuno_disease2ligand_id`. |
| reference_id | integer | NO | Foreign key to `reference.reference_id`. |

**Primary Keys**: immuno_disease2ligand_id, reference_id

**Sample Data**:
```json
{
  "immuno_disease2ligand_id": 807,
  "reference_id": 44214
}
```
### 94. **immuno_disease2object**
**Summary**: Immune-relevant disease–target associations.
**Purpose**: Links diseases to `object` for immunopharmacology.
**Size**: ~65 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **80 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| immuno_disease2object_id | integer | NO | Surrogate primary key. Default: sequence: immuno_disease2object_immuno_disease2object_id_seq |
| object_id | integer | NO | Foreign key to `object.object_id`. |
| disease_id | integer | YES | Foreign key to `disease.disease_id`. |
| comment | character varying(500) | YES | Curated field in the IUPHAR/BPS Guide to PHARMACOLOGY database ([guidetopharmacology.org](https://www.guidetopharmacology.org/)); see the `immuno_disease2object` table and related target/ligand pages for context. |
| immuno | boolean | YES | Default: true |
| comment_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search (see companion text column). |

**Primary Keys**: immuno_disease2object_id

**Sample Data**:
```json
{
  "comment": "CD2 is the molecular target of alefacept, a drug that was approved for the treatment of moderate to severe plaque psoriasis.",
  "comment_vector": "'alefacept':7 'approv':12 'cd2':1 'drug':9 'moder':17 'molecular':4 'plaqu':20 'psoriasi':21 'sever':19 'target':5 'treatment':15",
  "disease_id": 801,
  "immuno": true,
  "immuno_disease2object_id": 33,
  "object_id": 2600
}
```
### 95. **immuno_disease2object_refs**
**Summary**: Citations for immune disease–target links.
**Purpose**: Links `immuno_disease2object` to `reference`.
**Size**: ~82 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **24 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| immuno_disease2object_id | integer | NO | Foreign key to `immuno_disease2object.immuno_disease2object_id`. |
| reference_id | integer | NO | Foreign key to `reference.reference_id`. |

**Primary Keys**: immuno_disease2object_id, reference_id

**Sample Data**:
```json
{
  "immuno_disease2object_id": 7,
  "reference_id": 32555
}
```
### 96. **immunopaedia2family**
**Summary**: Immunopaedia clinical cases linked to families.
**Purpose**: Cross-links Immunopaedia content to `family`.
**Size**: ~5 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **32 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| immunopaedia_case_id | integer | NO | Foreign key to `immunopaedia_cases.immunopaedia_case_id`. |
| family_id | integer | NO | Foreign key to `family.family_id`. |
| section | character varying(50) | NO | Section anchor or heading within a long document. |
| url | character varying(150) | YES | HTTP(S) link for external resources or Immunopaedia pages. |
| comment | character varying(500) | YES | Curated field in the IUPHAR/BPS Guide to PHARMACOLOGY database ([guidetopharmacology.org](https://www.guidetopharmacology.org/)); see the `immunopaedia2family` table and related target/ligand pages for context. |

**Primary Keys**: immunopaedia_case_id, family_id

**Sample Data**:
```json
{
  "comment": null,
  "family_id": 2,
  "immunopaedia_case_id": 2,
  "section": "#Discussion-5",
  "url": null
}
```
### 97. **immunopaedia2ligand**
**Summary**: Immunopaedia cases referencing ligands.
**Purpose**: Connects Immunopaedia case studies to `ligand_id`.
**Size**: ~120 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **32 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| immunopaedia_case_id | integer | NO | Foreign key to `immunopaedia_cases.immunopaedia_case_id`. |
| ligand_id | integer | NO | Foreign key to `ligand.ligand_id`. |
| section | character varying(50) | NO | Section anchor or heading within a long document. |
| url | character varying(150) | YES | HTTP(S) link for external resources or Immunopaedia pages. |
| comment | character varying(500) | YES | Curated field in the IUPHAR/BPS Guide to PHARMACOLOGY database ([guidetopharmacology.org](https://www.guidetopharmacology.org/)); see the `immunopaedia2ligand` table and related target/ligand pages for context. |
| placeholder | character varying(100) | YES | Internal editorial or QA flag. |

**Primary Keys**: immunopaedia_case_id, ligand_id

**Sample Data**:
```json
{
  "comment": null,
  "immunopaedia_case_id": 1,
  "ligand_id": 1024,
  "placeholder": "cyclosporin A",
  "section": "#Treatment-6",
  "url": null
}
```
### 98. **immunopaedia2object**
**Summary**: Immunopaedia cases referencing targets.
**Purpose**: Connects Immunopaedia case studies to `object_id`.
**Size**: ~31 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **32 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| immunopaedia_case_id | integer | NO | Foreign key to `immunopaedia_cases.immunopaedia_case_id`. |
| object_id | integer | NO | Foreign key to `object.object_id`. |
| section | character varying(50) | NO | Section anchor or heading within a long document. |
| url | character varying(150) | YES | HTTP(S) link for external resources or Immunopaedia pages. |
| comment | character varying(500) | YES | Curated field in the IUPHAR/BPS Guide to PHARMACOLOGY database ([guidetopharmacology.org](https://www.guidetopharmacology.org/)); see the `immunopaedia2object` table and related target/ligand pages for context. |

**Primary Keys**: immunopaedia_case_id, object_id

**Sample Data**:
```json
{
  "comment": null,
  "immunopaedia_case_id": 1,
  "object_id": 625,
  "section": "#Treatment-6",
  "url": null
}
```
### 99. **immunopaedia_cases**
**Summary**: Immunopaedia.org clinical case metadata.
**Purpose**: Titles and URLs for educational immunology case studies.
**Size**: ~23 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **32 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| immunopaedia_case_id | integer | NO | Surrogate primary key. Default: sequence: immunopaedia_cases_immunopaedia_case_id_seq |
| title | character varying(1000) | NO | Short title or heading for UI display. |
| url | character varying(150) | NO | HTTP(S) link for external resources or Immunopaedia pages. |
| last_modified | date | YES | Last editorial modification date for the row or text block. |
| short_title | character varying(500) | YES | Short name for case study title, may contain html |

**Primary Keys**: immunopaedia_case_id

**Sample Data**:
```json
{
  "immunopaedia_case_id": 1,
  "last_modified": null,
  "short_title": null,
  "title": "Fireworks of autoimmunity from birth",
  "url": "https://www.immunopaedia.org.za/clinical-cases/autoimmune-conditions/fireworks-of-autoimmunity-from-birth/"
}
```
### 100. **inn**
**Summary**: WHO International Nonproprietary Names (INN) with structures.
**Purpose**: INN registry: names, CAS, SMILES/InChI variants for salt handling and searching.
**Size**: ~11,470 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **4720 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| inn_number | integer | NO | Primary key / INN registry number (links to WHO INN). |
| inn | character varying(500) | NO | International Nonproprietary Name string (lowercase in data). |
| cas | character varying(100) | YES | Chemical Abstracts Service registry number. |
| smiles | text | YES | SMILES line notation for the structure (may include salts). |
| smiles_salts_stripped | text | YES | Curated field in the IUPHAR/BPS Guide to PHARMACOLOGY database ([guidetopharmacology.org](https://www.guidetopharmacology.org/)); see the `inn` table and related target/ligand pages for context. |
| inchi_key_salts_stripped | character varying(500) | YES | Curated field in the IUPHAR/BPS Guide to PHARMACOLOGY database ([guidetopharmacology.org](https://www.guidetopharmacology.org/)); see the `inn` table and related target/ligand pages for context. |
| nonisomeric_smiles_salts_stripped | text | YES | Salt-stripped or neutralised structure line for matching. |
| nonisomeric_inchi_key_salts_stripped | character varying(500) | YES | Salt-stripped or neutralised structure line for matching. |
| neutralised_smiles | text | YES | Salt-stripped or neutralised structure line for matching. |
| neutralised_inchi_key | character varying(500) | YES | Salt-stripped or neutralised structure line for matching. |
| neutralised_nonisomeric_smiles | text | YES | Salt-stripped or neutralised structure line for matching. |
| neutralised_nonisomeric_inchi_key | character varying(500) | YES | Salt-stripped or neutralised structure line for matching. |
| inn_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search on `inn`. |

**Primary Keys**: inn_number

**Sample Data**:
```json
{
  "cas": "129639-79-8",
  "inchi_key_salts_stripped": "TYBHXIFFPVFXQW-UHFFFAOYSA-N",
  "inn": "abafungin",
  "inn_number": 7453,
  "inn_vector": "'abafungin':1",
  "neutralised_inchi_key": "TYBHXIFFPVFXQW-UHFFFAOYSA-N",
  "neutralised_nonisomeric_inchi_key": "TYBHXIFFPVFXQW-UHFFFAOYSA-N",
  "neutralised_nonisomeric_smiles": "Cc1ccc(c(c1)C)Oc1ccccc1c1csc(n1)NC1=NCCCN1\t",
  "neutralised_smiles": "Cc1ccc(c(c1)C)Oc1ccccc1c1csc(n1)NC1=NCCCN1",
  "nonisomeric_inchi_key_salts_stripped": "TYBHXIFFPVFXQW-UHFFFAOYSA-N",
  "nonisomeric_smiles_salts_stripped": "Cc1ccc(c(c1)C)Oc1ccccc1c1csc(n1)NC1=NCCCN1",
  "smiles": "C1=C(N=C(S1)NC2=NCCCN2)C3=CC=CC=C3OC4=C(C=C(C=C4)C)C",
  "smiles_salts_stripped": "Cc1ccc(c(c1)C)Oc1ccccc1c1csc(n1)NC1=NCCCN1"
}
```
### 101. **interaction**
**Summary**: Ligand–target interactions (affinity, action, selectivity).
**Purpose**: Core pharmacology table: connects `ligand_id` to `object_id` with potency and assay metadata.
**Size**: ~23,827 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **7264 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| interaction_id | integer | NO | Surrogate primary key. Default: sequence: interaction_interaction_id_seq |
| ligand_id | integer | NO | Foreign key to `ligand.ligand_id`. |
| object_id | integer | YES | Foreign key to `object.object_id`. |
| type | character varying(100) | NO | Controlled type label (ligand class, interaction type, etc.). |
| action | character varying(1000) | NO | Pharmacological action (agonist, antagonist, inhibitor, …). |
| action_comment | character varying(2000) | YES | Curator prose for the `action` section on the portal. |
| species_id | integer | NO | Foreign key to `species.species_id`. |
| endogenous | boolean | NO | Default: false |
| selective | boolean | NO | Default: false |
| use_dependent | boolean | YES | Use-dependent (e.g. channel blocker) binding/activity. |
| voltage_dependent | boolean | YES | Measurement varies with membrane voltage (ion channels). |
| affinity_units | character varying(100) | YES | Default: -::character varying |
| affinity_high | double precision | YES | Upper bound of reported affinity (numeric). |
| affinity_median | double precision | YES | Median or most representative affinity value. |
| affinity_low | double precision | YES | Lower bound of reported affinity (numeric). |
| concentration_range | character varying(200) | YES | Range of concentrations tested in the assay. |
| affinity_voltage_high | real | YES | Affinity at depolarized/hyperpolarized voltage (upper). |
| affinity_voltage_median | real | YES | Affinity at stated voltage (median). |
| affinity_voltage_low | real | YES | Affinity at hyperpolarized/depolarized voltage (lower). |
| affinity_physiological_voltage | boolean | YES | Whether affinity was measured at physiological Vm. |
| rank | integer | YES | Potency or relevance rank within a family or table. |
| selectivity | character varying(100) | YES | Qualitative selectivity class (e.g. non-selective). |
| original_affinity_low_nm | double precision | YES | Original literature affinity (low) in nM space. |
| original_affinity_median_nm | double precision | YES | Original literature affinity (median) in nM space. |
| original_affinity_high_nm | double precision | YES | Original literature affinity (high) converted or in nM. |
| original_affinity_units | character varying(20) | YES | Units as stated in the primary publication. |
| original_affinity_relation | character varying(10) | YES | Inequality relation (<, >, =) for original affinity. |
| assay_description | character varying(1000) | YES | Short assay description (binding, functional, …). |
| assay_conditions | character varying(1000) | YES | Buffer, temperature, co-factors, cell line, etc. |
| from_grac | boolean | NO | Default: false |
| only_grac | boolean | NO | Default: false |
| receptor_site | character varying(300) | YES | Binding site or subpocket annotation (allosteric, orthosteric, …). |
| ligand_context | character varying(300) | YES | Additional ligand context (prodrug, metabolite, formulation). |
| percent_activity | double precision | YES | Functional assay percent activity (e.g. agonist screen). |
| assay_url | character varying(500) | YES | Link to assay protocol or external assay record. |
| primary_target | boolean | YES | Marks the interaction as defining the ligand’s primary target. |
| target_ligand_id | integer | YES | When the ‘target’ is itself a ligand entity (peptide–peptide cases). |
| whole_organism_assay | boolean | YES | Assay performed in vivo / whole organism vs recombinant cells. |
| hide | boolean | NO | Default: false |
| update_status | integer | NO | Default: 0 |
| type_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search on `type`. |

**Primary Keys**: interaction_id

**Sample Data**:
```json
{
  "action": "None",
  "action_comment": null,
  "affinity_high": null,
  "affinity_low": null,
  "affinity_median": null,
  "affinity_physiological_voltage": null,
  "affinity_units": "-",
  "affinity_voltage_high": null,
  "affinity_voltage_low": null,
  "affinity_voltage_median": null,
  "assay_conditions": null,
  "assay_description": null,
  "assay_url": null,
  "concentration_range": null,
  "endogenous": true,
  "from_grac": true,
  "hide": false,
  "interaction_id": 13549,
  "ligand_context": null,
  "ligand_id": 5077,
  "object_id": 1874,
  "only_grac": false,
  "original_affinity_high_nm": null,
  "original_affinity_low_nm": null,
  "original_affinity_median_nm": null,
  "original_affinity_relation": null,
  "original_affinity_units": null,
  "percent_activity": null,
  "primary_target": null,
  "rank": null,
  "receptor_site": null,
  "selective": false,
  "selectivity": "Non-selective",
  "species_id": 1,
  "target_ligand_id": null,
  "type": "None",
  "type_vector": "'none':1",
  "update_status": 0,
  "use_dependent": null,
  "voltage_dependent": null,
  "whole_organism_assay": null
}
```
### 102. **interaction_affinity_refs**
**Summary**: References specifically tied to affinity values.
**Purpose**: Subordinate citations for quantitative interaction data (subset of bibliography).
**Size**: ~26,715 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **1584 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| interaction_id | integer | NO | Foreign key to `interaction.interaction_id`. |
| reference_id | integer | NO | Foreign key to `reference.reference_id`. |

**Primary Keys**: interaction_id, reference_id

**Sample Data**:
```json
{
  "interaction_id": 1,
  "reference_id": 47
}
```
### 103. **introduction**
**Summary**: Per-family introductory narrative (long-form HTML).
**Purpose**: Main family overview text shown at the top of each target family page.
**Size**: ~178 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **1568 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| family_id | integer | NO | Foreign key to `family.family_id`. |
| text | text | NO | Long-form HTML or prose content for display on the portal. |
| last_modified | date | YES | Last editorial modification date for the row or text block. |
| annotation_status | integer | NO | Default: 5 |
| no_contributor_list | boolean | NO | Default: true |
| cite_id | character varying(20) | YES | Used to shows the ID of the GtoPdb CITE family for citation purposes. |
| intro_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search (see companion text column). |

**Primary Keys**: family_id

**Sample Data**:
```json
{
  "annotation_status": 1,
  "cite_id": "F39",
  "family_id": 39,
  "intro_vector": "'1':941 '125i':79,128,142,176,221,302,310,342,373,710 '2':78,127,134,141,168,175,220,301,309,341,355,369,372,709,966,988 '35s':739 '3d':275 '3h':75,305,675 '4p':473,834,837 '4p-adot':836 '4p-pdot':472,833 '549':779 '60':263 '724':781 'aa':272 'abolish':1077 'accumul':738 'acetylserotonin':139,173,188 'acid':271 'activ':59,540,617,679,754,787,1061 'adenyl':495 'adot':838 'affin':192,299,714 'agonist':295,432,469,662,664,691,722,776 'also':27,1023 'amino':270 'amphetamin':929 'analogu':466 'antagonist':297,434,666,693,724,832 'area':821 'arteri':533,567,824,869 'assay':732 'associ':933,957,985 'avail':827 'b':606,905 'base':120,731 'basi':245 'bed':825 'bind':97,130,144,178,223,298,312,344,375,378,383,398,712,741 'bodi':641 'brain':181,322,357,387,820 'c':621,911,1068,1072 'camp':737,794,1117 'carri':453 'case':24 'caudal':532,566,868 'cell':37,727,730,766,772,1013,1040,1106,1124,1137 'cellular':757 'cerebr':530 'certain':522 'cgmp':796 'character':87,160,445,507,574 'characterist':337 'chines':763 'chromosom':251 'circadian':13,47,612,857,863,898 'classif':109,414 'clone':201 'close':152 'code':951 'compar':1129 'consid':411 'constitut':748 'contrast':165 'correspond':151,196,1132 'coupl':64,419 'cyclas':496 'cytoplasm':347 'd':630,918 'defin':102,239 'definit':235 'delet':365,585,875 'demonstr':599,889 'describ':786 'di':1003 'diabet':967,989 'differ':125,397,760 'distinct':104,290 'distinguish':184 'dopamin':676,853,907,920 'downregul':648 'e':638 'e.g':470,525,733 'ec50':1112 'effect':1045,1057 'encod':219 'entiti':242 'equal':191 'evid':548 'exhibit':746 'exist':997 'exon':940,969 'express':558,634,800,815,1006,1009,1125 'extra':32 'extra-pin':31 'fast':960 'fire':603,902 'first':108,1029 'follow':11,592,882 'form':287,1022 'format':797,1099 'forskolin':735 'forskolin-stimul':734 'fraction':348 'frequent':936 'function':57,157,593,845,883,983,1101 'g':61,416,488 'galphai':490 'galphao':492 'gene':950,978 'general':227 'generalth':1 'genet':364,584,874 'gland':10 'glucos':962 'gpcr':330 'gtpgamma':740 'h':257,260,457 'hamster':180,321,764 'hek293':1136 'heterolog':726 'heterom':1025,1065,1103,1127 'heteromer-specif':1064 'heteromersgpcr':992 'heteroreceptor':684 'high':16 'hmt1':278 'hmt2':280 'homolog':264 'homom':1002,1133 'hormon':2 'howev':506,544 'human':254,477,702,789 'hybrid':808 'i.e':557,777 'identif':463,843 'identifi':318,351,437,669,935 'immun':41 'immunohistochemistri':562 'inact':286 'increas':919,959 'inde':356 'indirect':556 'individu':1007 'induc':752 'inform':625 'inhibit':497,601,674,707,793,851,906,912,1115 'inhibitori':487 'innat':40 'inositol':500 'insulin':914 'interf':1096 'intron':946 'invers':468,775 'involv':1060 'iodomelatonin':80,129,135,143,169,177,222,303,311,343,374,711 'islet':917 'iuphar':413 'kb':694 'ki':705 'kidney':359 'kinas':1071 'kinet':122 'ko':619,1080,1083 'lack':370 'lead':493 'led':82,460,840 'leftward':1108 'leptin':645,650 'level':17,273,963 'light':1049 'like':35 'line':728,767,773 'liver':637 'local':85,252 'longer':410 'loss':981 'loss-of-funct':980 'luzindol':471 'main':5 'mammalian':146,207,817 'manner':48 'may':813 'mediat':512,538,1043 'mel1a':210 'mel1b':212 'melatonin':3,25,49,65,76,96,112,136,158,170,194,208,236,255,306,420,430,447,510,534,589,660,673,720,751,791,847,879,1047,1059,1120 'melatonin-induc':750 'membran':182,323,360,388 'mice':362,582,872,1055,1084,1089 'ml1':115,231 'ml2':117,199,308 'model':758 'molecular':248 'monom':1000 'mous':620 'mrna':561 'mt1':215,258,422,458,483,509,542,588,618,993,1014,1079 'mt1/mt2':991,1024,1102,1126 'mt2':217,261,628,656,682,703,743,798,830,846,878,954,995,1016,1082,1093 'mt3':316,340,377,382,406 'mtnr1b':949,977 'multipl':972 'mutant':1094 'n':138,172,187 'n-acetylserotonin':137,171,186 'nativ':89,450,481,515,523 'neuro2a':769 'neuroblastoma':771 'neuroendocrin':56 'neuron':602,901 'new':332 'night':21 'non':46,428,749 'non-circadian':45 'non-select':427 'nonfunct':1092 'nucleus':605,904 'number':93,425,654 'observ':1122 'oligom':1004 'onset':610 'open':403 'origin':325,761 'others.genome':931 'ovari':765 'overexpress':1090 'pancreat':916 'par':149,527,626 'partial':294,663,690 'pathway':1074 'pcr':804 'pdot':474,835 'peak':895 'pharmacolog':105,124,132,167,228,291,336,444,573,687 'phase':607,860,891 'phenotyp':984 'phosphat':501 'phospholipas':1067 'photoperiod':624 'photoreceptor':1039,1053,1105 'physiolog':54 'pi3k':633 'pineal':9,33 'plasma':961 'plc/pkc':1073 'possibl':499 'potenc':716 'presenc':551 'presum':537 'presynapt':683 'produc':6,29 'product':1118 'profil':106,133,292,688 'protein':63,418,489,1070 'protein-coupl':62,417 'putat':95,111 'question':404 'quinon':353,367,391 'rabbit':162,671,909 'radioligand':74 'rare':973 'rat':529,565,867 'recent':652 'receptor':66,113,159,209,237,256,421,423,431,448,459,478,484,511,543,554,577,590,596,629,651,658,661,704,721,744,792,799,812,831,848,880,886,955,996,1017 'receptor-select':657 'recombin':206,456,476,504,701,790 'reduc':926 'reductas':354,368,392 'regul':50,622,631,639 'releas':677,854,908,915 'report':520,580 'respons':535,646 'retin':1038 'retina':147,163,672,818,850,910 'reveal':204,971 'rhythm':14,613,864,899 'risk':968,990 'rod':1052 'rt':803 'rt-pcr':802 'run':615 'select':429,659,819,829 'sensit':927,1050 'sequenc':970 'sheep':526 'shift':608,861,892,1109 'show':190,225,262,685 'shown':1020,1030 'signal':485,513,753 'similar':696 'singl':945 'site':34,98,224,313,333,345,379,384,399,407 'situ':807 'solv':283 'specif':371,560,1066 'still':401 'stimul':502,736 'striatal':923 'structur':249,276 'studi':202,934 'subject':20 'suggest':809 'suprachiasmat':604,903 'synaptosom':924 'synthet':719 'system':42,505,859 'target':68 'term':214,315 'thought':326 'time':858 'tissu':69,90,451,482,516,524,571 'transfect':1135 'tuberali':150,528,627 'two':205,234,756 'type':118,200,232,965,987 'typic':998 'ucm':778,780 'ucsf3384':782 'ucsf7447':783 'uniqu':241 'upstream':938 'uptak':921 'use':71,441,581,729,871 'valu':695,1113 'variant':937,974 'varieti':52 'various':465,718,774 'vasodil':870 'via':486 'vitro':1032 'vivo':1036 'wash':320,386 'weight':642 'well':101,1086 'well-defin':100 'wheel':616 'whether':380 'wide':932 'wih':979 'within':412,943 'work':452",
  "last_modified": "2020-08-21",
  "no_contributor_list": false,
  "text": "<heading>General</heading><p>The hormone melatonin is mainly produced by the pineal gland following a circadian rhythm, with high levels during the subjective night. In some cases melatonin can also be produced by extra-pineal sites like in cells from the innate immune system in a non-circadian manner. Melatonin regulates a variety of physiological and neuroendocrine functions through activation of G protein-coupled melatonin receptors in target tissues <Reference id=15065/><Reference id=11688/><Reference id=24229/><Reference id=25835/><Reference id=25836/>.<BR><BR>The use of the radioligands [<sup>3</sup>H]melatonin and 2-[<sup>125</sup>I]iodomelatonin has led to the localization and characterization in native tissues of a number of putative melatonin binding sites with well-defined and distinct pharmacological profiles <Reference id=15065/>. The first classification of putative melatonin receptors into ML<sub>1</sub> and ML<sub>2</sub> types was based on kinetic and pharmacological differences of 2-[<sup>125</sup>I]iodomelatonin binding <Reference id=4466/>. The pharmacological profile (2-iodomelatonin > melatonin >> N-acetylserotonin) of 2-[<sup>125</sup>I]iodomelatonin binding to mammalian retina and pars tuberalis corresponds closely to that of the functional melatonin receptor characterized in rabbit retina <Reference id=4461/><Reference id=4463/><Reference id=4464/><Reference id=4465/><Reference id=4394/><Reference id=4466/>. By contrast the pharmacology (2-iodomelatonin > melatonin = N-acetylserotonin) of 2-[<sup>125</sup>I]iodomelatonin binding to hamster brain membranes was distinguished by N-acetylserotonin, which showed equal affinity with melatonin <Reference id=4461/><Reference id=4464/><Reference id=4465/><Reference id=4466/> and corresponds to the ML<sub>2</sub> type.   <BR><BR>Cloning studies have revealed two recombinant mammalian melatonin receptors - Mel<sub>1a</sub> and Mel<sub>1b</sub>, now termed MT<sub>1</sub> and MT<sub>2</sub> <Reference id=4394/><Reference id=4395/><Reference id=4448/><Reference id=4467/> both encoding 2-[<sup>125</sup>I]iodomelatonin binding sites showing the general pharmacology of the ML<sub>1</sub> type <Reference id=4394/><Reference id=4443/>. These two definitive melatonin receptors were defined as unique entities on the basis of their molecular structure and chromosomal localization <Reference id=4394/><Reference id=4395/><Reference id=4448/><Reference id=4467/><Reference id=4396/><Reference id=4468/>. The human melatonin receptors, (h MT<sub>1</sub> and h MT<sub>2</sub>) show 60% homology to each other at the amino acid (aa) level. The 3D structure of hMT<sub>1</sub> and hMT<sub>2</sub> have been solved in the inactive form <Reference id=40259/><Reference id=40260/>.   They have distinct pharmacological profiles of partial agonist and antagonist binding affinities for 2-[<sup>125</sup>I]iodomelatonin and [<sup>3</sup>H]melatonin <Reference id=4464/><Reference id=4443/><Reference id=4406/><Reference id=4469/><Reference id=15065/>. The ML<sub>2</sub> 2-[<sup>125</sup>I]iodomelatonin binding site (now termed <i>MT<sub>3</sub></i>), was identified in washed hamster brain membranes and originally thought to be a GPCR <Reference id=4471/><Reference id=4472/><Reference id=4470/><Reference id=4477/><Reference id=4473/>. A new site with the pharmacological characteristics of the <i>MT3</i> 2-[<sup>125</sup>I]-iodomelatonin binding site in cytoplasmic fractions was been identified with quinone reductase 2 <Reference id=4474/>. Indeed, brain and kidney membranes from mice with genetic deletion of quinone reductase 2 lacked specific 2-[<sup>125</sup>I]iodomelatonin binding to <i>MT<sub>3</sub></i> binding sites <Reference id=4475/><Reference id=40261/>.   Whether the <i>MT<sub>3</sub></i> binding sites in washed brain membranes and on quinone reductase are the same or different binding sites is still an open question. The <i>MT<sub>3</sub></i> site is no longer considered within IUPHAR classification of G protein-coupled melatonin receptors.  </p><heading>MT<sub>1</sub> receptors</heading><p>  A number of non-selective melatonin receptor agonists and antagonists have been identified <Reference id=4469/><Reference id=4476/><Reference id=4477/><Reference id=4478/><Reference id=4479/><Reference id=4480/><Reference id=4481/><Reference id=4482/><Reference id=4483/><Reference id=4407/><Reference id=24230/><Reference id=15065/><Reference id=24229/>, which have been useful in the pharmacological characterization of melatonin receptors in native tissues <Reference id=4443/>.      Work carried out with recombinant h MT<sub>1</sub> receptors led to the identification of various analogues as inverse agonists (<i>e.g.</i>, luzindole, 4P-PDOT) on recombinant human receptors <Reference id=4406/><Reference id=4447/><Reference id=38751/> and in native tissues <Reference id=25837/><Reference id=25838/><Reference id=4406/><Reference id=4484/><Reference id=38751/>. <br><br> MT<sub>1</sub> receptors signal <i>via</i> inhibitory G proteins (G&alpha;<sub>i</sub> and G&alpha;<sub>o</sub>) leading to adenylate cyclase inhibition and possibly inositol phosphate stimulation in recombinant systems. However, characterization of MT<sub>1</sub> melatonin receptors mediating signalling in native tissues have not been reported <Reference id=4461/><Reference id=4463/><Reference id=4464/><Reference id=4465/><Reference id=4485/><Reference id=4403/>. In certain native tissues (<i>e.g.</i> sheep pars tuberalis, rat cerebral and caudal arteries) melatonin responses are presumably mediated through activation of MT<sub>1</sub> receptors. However, most of the evidence for the presence of this receptor is indirect (<i>i.e.</i> expression of specific mRNA; immunohistochemistry) <Reference id=4395/><Reference id=4448/><Reference id=4467/><Reference id=4428/><Reference id=4424/><Reference id=4425/><Reference id=4426/><Reference id=4427/>, with the rat caudal artery being the only tissue where pharmacological characterization of this receptor has been reported <Reference id=4412/><Reference id=4413/><Reference id=4414/><Reference id=4486/><Reference id=4415/><Reference id=4445/>. Using mice with genetic deletion of the MT<sub>1</sub> melatonin receptor the following functions for this receptor have been demonstrated a) Inhibition neuronal firing (suprachiasmatic nucleus, <Reference id=4411/>), b) phase shift of onset of circadian rhythm of running wheel activity (MT<sub>1</sub> KO mouse, <Reference id=4404/>); c)   regulation of photoperiodic information (pars tuberalis, <Reference id=25839/>).</p><heading>MT<sub>2</sub> receptors; d) regulation of PI3K expression in the liver <Reference id=40262/>; e) regulation of body weight and the leptin response by downregulating the leptin receptor <Reference id=40263/>.     </heading><p>Recently, a number of MT<sub>2</sub> receptor-selective melatonin receptor agonists, partial agonists and antagonists have been identified <Reference id=4443/><Reference id=4410/><Reference id=4408/><Reference id=4446/><Reference id=4400/><Reference id=4483/><Reference id=24230/><Reference id=15065/><Reference id=24229/>. In rabbit retina melatonin inhibits [<sup>3</sup>H]dopamine release through activation of an MT<sub>2</sub> presynaptic heteroreceptor showing a pharmacological profile of partial agonists and antagonists (<i>K</i><sub>B</sub> values) similar to that of the recombinant human MT<sub>2</sub> receptor (<i>K</i><sub>i</sub> for inhibition of 2-[<sup>125</sup>I]iodomelatonin binding) <Reference id=4443/>. The affinity and potency of various synthetic melatonin receptor agonists and antagonists in heterologous cell lines using cell based assays (<i>e.g</i>., forskolin-stimulated cAMP accumulation; [<sup>35</sup>S]GTP&gamma;S binding). The MT<sub>2</sub> receptors can exhibit a constitutive, non melatonin-induced signaling activity in two cellular models of different origins, the Chinese hamster ovary cell line and Neuro2A, a neuroblastoma cell line <Reference id=25840/>. Various inverse agonists (<i>i.e.</i> UCM 549, UCM 724, UCSF3384, UCSF7447) have been described <Reference id=25840/><Reference id=38751/><Reference id=40264/>.        <BR><BR>Activation of human recombinant melatonin receptors inhibits cAMP and cGMP formation <Reference id=4395/><Reference id=4448/><Reference id=4451/>. MT<sub>2</sub> receptor expression by RT-PCR and <i>in situ</i> hybridization suggests that this receptor may be expressed in mammalian retina, selected brain areas and some arterial beds <Reference id=4448/><Reference id=4414/><Reference id=4411/><Reference id=4447/>. The availability of selective MT<sub>2</sub> receptor antagonists (4P-PDOT, 4P-ADOT) has led to the identification of functional MT<sub>2</sub> melatonin receptors in retina (inhibition of dopamine release) <Reference id=4443/>, in the circadian timing system (phase shifting of circadian rhythms) <Reference id=4411/><Reference id=4404/>, and in rat caudal artery (vasodilation) <Reference id=4415/><Reference id=4416/>. Using mice with genetic deletion of the MT<sub>2</sub> melatonin receptor the following functions for this receptor have been demonstrated: a) phase shift of the peak of the circadian rhythm of neuronal firing (suprachiasmatic nucleus; <Reference id=4411/><Reference id=4404/>); b) inhibition dopamine release (rabbit retina; <Reference id=4443/>); ]);  c) inhibition of insulin release (pancreatic islets; <Reference id=25842/>); d) increased dopamine uptake in striatal synaptosomes and reduced sensitivity to amphetamine <Reference id=40265/> and others.<br><br>Genome-wide association studies identified frequent variants upstream of exon 1 or within the single intron of the <i>MTNR1B</i> gene coding for the MT<sub>2</sub> receptor that associated with increased fasting plasma glucose levels and type 2 diabetes risk <Reference id=25841/>. Exon sequencing revealed multiple rare variants of the <i>MTNR1B</i> gene wih loss-of-function phenotype associated with type 2 diabetes risk <Reference id=26208/><Reference id=40266/>.  </p><heading>MT<sub>1</sub>/MT<sub>2</sub> heteromers</heading><p>GPCRs MT<sub>1</sub> and MT<sub>2</sub> receptors exist typically as monomers and homomers (di-, oligomers) when expressed individually. When expressed in the same cell MT<sub>1</sub> and MT<sub>2</sub> receptors have been shown to form also MT<sub>1</sub>/MT<sub>2</sub> heteromers. This has been first shown <i>in vitro</i> <Reference id=25844/><Reference id=14329/> and then <i>in vivo</i> in retinal photoreceptor cells where they mediated the effect of melatonin on light sensitivity of rod photoreceptors in mice <Reference id=25843/>. This effect of melatonin involved activation of the heteromer-specific phospholipase C and protein kinase C (PLC/PKC) pathway and was abolished in MT<sub>1</sub> KO or MT<sub>2</sub> KO mice, as well as in mice overexpressing a nonfunctional MT<sub>2</sub> mutant that interfered with the formation of functional MT<sub>1</sub>/MT<sub>2</sub> heteromers in photoreceptor cells. A leftward shift of the EC<sub>50</sub> value of inhibition of cAMP production by melatonin was observed in cells expressing MT<sub>1</sub>/MT<sub>2</sub> heteromers as compared to the corresponding homomers in transfected HEK293 cells."
}
```
### 104. **iuphar2discoverx**
**Summary**: Maps GtoPdb targets to DiscoverX catalog numbers.
**Purpose**: Bridge `object_id` to DiscoverX `cat_no` for assay panels.
**Size**: ~0 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **8192 bytes** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| object_id | integer | NO | Foreign key to `object.object_id`. |
| cat_no | character varying(100) | NO | Commercial catalog or product code (DiscoverX, MCE, …). |

**Primary Keys**: object_id, cat_no

**Sample Data**: *No data available or table is empty*
### 105. **iuphar2medchemexpress**
**Summary**: Maps ligands to MedChemExpress catalog SKUs.
**Purpose**: Commercial catalog crosswalk with exactness flags for supplier integration.
**Size**: ~5,227 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **488 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| ligand_id | integer | NO | Foreign key to `ligand.ligand_id`. |
| cat_no | character varying(100) | NO | Commercial catalog or product code (DiscoverX, MCE, …). |
| exact | boolean | YES | Whether supplier structure matches GtoPdb ligand exactly. |
| match | integer | YES | Heuristic match score or match-type code for catalog mapping. |

**Primary Keys**: ligand_id, cat_no

**Sample Data**:
```json
{
  "cat_no": "HY-10045",
  "exact": null,
  "ligand_id": 7643,
  "match": 1
}
```
### 106. **lgic**
**Summary**: Ligand-gated ion channel specific notes.
**Purpose**: LGIC class block per target (e.g. endogenous agonist commentary).
**Size**: ~86 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **32 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| object_id | integer | NO | Foreign key to `object.object_id`. |
| ligand | character varying(500) | YES | Endogenous ligand summary for LGIC targets. |
| selectivity_comments | text | YES | Curator prose for the `selectivity` section on the portal. |

**Primary Keys**: object_id

**Sample Data**:
```json
{
  "ligand": "",
  "object_id": 464,
  "selectivity_comments": null
}
```
### 107. **ligand**
**Summary**: Drugs, tool compounds, peptides, antibodies — all ligand entities.
**Purpose**: Central ligand table: names, types, approvals, clinical/pharmacokinetic text, portal flags.
**Size**: ~13,260 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **26 MB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| ligand_id | integer | NO | Surrogate primary key. Default: sequence: ligand_ligand_id_seq |
| name | character varying(1000) | NO | Primary display name (target, ligand, family, etc.). |
| pubchem_sid | bigint | YES | PubChem Substance ID (when ligand is registered in PubChem). |
| radioactive | boolean | NO | Default: false |
| old_ligand_id | integer | YES | Legacy ligand ID before merges or rekeys. |
| type | character varying(50) | NO | Default: Synthetic organic::character varying |
| approved | boolean | YES | True if the compound has regulatory approval somewhere (per GtoPdb curation). |
| approved_source | character varying(100) | YES | Curated field in the IUPHAR/BPS Guide to PHARMACOLOGY database ([guidetopharmacology.org](https://www.guidetopharmacology.org/)); see the `ligand` table and related target/ligand pages for context. |
| iupac_name | character varying(1000) | YES | IUPAC chemical name where applicable. |
| comments | character varying(4000) | YES | Free-text curator comments. |
| withdrawn_drug | boolean | YES | True if approval was withdrawn or drug discontinued. |
| verified | boolean | YES | Curator verification flag for the ligand record. |
| abbreviation | character varying(300) | YES | Short abbreviation or gene-style shorthand. |
| clinical_use | text | YES | Approved or common clinical indications / usage text. |
| mechanism_of_action | text | YES | Mechanistic class and receptor targets in clinic. |
| absorption_distribution | text | YES | ADME: absorption and distribution notes. |
| metabolism | text | YES | Metabolic routes and enzyme involvement. |
| elimination | text | YES | Excretion pathways and half-life notes. |
| popn_pharmacokinetics | text | YES | Population PK / special populations. |
| organ_function_impairment | text | YES | Dosing in hepatic/renal impairment. |
| emc_url | character varying(1000) | YES | European Medicines Community or national label URL. |
| drugs_url | character varying(1000) | YES | Drugs.com or similar patient-oriented label link. |
| ema_url | character varying(1000) | YES | EMA product information link. |
| bioactivity_comments | text | YES | Miscellaneous bioactivity notes. |
| labelled | boolean | YES | Radiolabelled ligand suitable as tracer. |
| in_gtip | boolean | YES | Target/ligand included in Guide to IMMUNOPHARMACOLOGY. |
| immuno_comments | text | YES | Comments for Guide to IMMUNOPHARMACOLOGY specific to ligand |
| in_gtmp | boolean | YES | Target/ligand included in Guide to MALARIA PHARMACOLOGY. |
| gtmp_comments | text | YES | Comments for Guide to MALARIA PHARMACOLOGY specific to ligand |
| who_essential | boolean | YES | Listed on WHO Essential Medicines List. |
| antibacterial | boolean | YES | Ligand has antibacterial use or antibacterial programme. |
| has_qi_interaction | boolean | YES | Default: false |
| has_chembl_interaction | boolean | YES | Default: false |
| name_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search on `name`. |
| comments_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search on `comments`. |
| abbreviation_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search on `abbreviation`. |
| clinical_use_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search on `clinical_use`. |
| mechanism_of_action_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search on `mechanism_of_action`. |
| absorption_distribution_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search on `absorption_distribution`. |
| metabolism_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search on `metabolism`. |
| elimination_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search on `elimination`. |
| popn_pharmacokinetics_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search on `popn_pharmacokinetics`. |
| organ_function_impairment_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search on `organ_function_impairment`. |
| bioactivity_comments_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search on `bioactivity_comments`. |
| immuno_comments_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search on `immuno_comments`. |
| gtmp_comments_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search on `gtmp_comments`. |

**Primary Keys**: ligand_id

**Sample Data**:
```json
{
  "abbreviation": "",
  "abbreviation_vector": "",
  "absorption_distribution": "",
  "absorption_distribution_vector": "",
  "antibacterial": false,
  "approved": false,
  "approved_source": "",
  "bioactivity_comments": "",
  "bioactivity_comments_vector": "",
  "clinical_use": "",
  "clinical_use_vector": "",
  "comments": "",
  "comments_vector": "",
  "drugs_url": "",
  "elimination": "",
  "elimination_vector": "",
  "ema_url": "",
  "emc_url": "",
  "gtmp_comments": null,
  "gtmp_comments_vector": null,
  "has_chembl_interaction": true,
  "has_qi_interaction": true,
  "immuno_comments": null,
  "immuno_comments_vector": null,
  "in_gtip": null,
  "in_gtmp": null,
  "iupac_name": "",
  "labelled": false,
  "ligand_id": 1517,
  "mechanism_of_action": "",
  "mechanism_of_action_vector": "",
  "metabolism": "",
  "metabolism_vector": "",
  "name": "PYY-(3-36)",
  "name_vector": "'-36':3 '3':2 'pyy':1",
  "old_ligand_id": 3450,
  "organ_function_impairment": "",
  "organ_function_impairment_vector": "",
  "popn_pharmacokinetics": "",
  "popn_pharmacokinetics_vector": "",
  "pubchem_sid": 135651876,
  "radioactive": false,
  "type": "Peptide",
  "verified": false,
  "who_essential": false,
  "withdrawn_drug": false
}
```
### 108. **ligand2adb**
**Summary**: Ligands linked to antibacterial database entries.
**Purpose**: Connects `ligand` to `antibiotic_db` / antibacterial curation.
**Size**: ~428 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **72 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| ligand_id | integer | NO | Foreign key to `ligand.ligand_id`. |
| adb_id | integer | NO | Foreign key to `antibiotic_db.adb_id`. |

**Primary Keys**: ligand_id, adb_id

**Sample Data**:
```json
{
  "adb_id": 4,
  "ligand_id": 10847
}
```
### 109. **ligand2clinical_trial**
**Summary**: Ligands mentioned in specific clinical trials.
**Purpose**: Many-to-many with optional curator comments per pairing.
**Size**: ~3,697 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **352 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| ligand2clinical_trial_id | integer | NO | Surrogate primary key. Default: sequence: ligand2clinical_trial_seq |
| ligand_id | integer | NO | Foreign key to `ligand.ligand_id`. |
| clinical_trial_id | integer | NO | Foreign key to `clinical_trial.clinical_trial_id`. |
| comment | character varying(1000) | YES | Default: NULL::character varying |

**Primary Keys**: ligand2clinical_trial_id

**Sample Data**:
```json
{
  "clinical_trial_id": 1852,
  "comment": "Results from the CANTOS trial (NCT01327846) showed that canakinumab (in high-risk patients; in addition to standard-of-care therapy) reduced the number of recurrent cardiovascular events that were recorded at 3-4 years follow-up",
  "ligand2clinical_trial_id": 1268,
  "ligand_id": 6773
}
```
### 110. **ligand2clinical_trial_refs**
**Summary**: Citations for ligand–trial associations.
**Purpose**: Links `ligand2clinical_trial` rows to `reference`.
**Size**: ~868 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **96 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| ligand2clinical_trial_id | integer | NO | Foreign key to `ligand2clinical_trial.ligand2clinical_trial_id`. |
| reference_id | integer | NO | Foreign key to `reference.reference_id`. |

**Primary Keys**: ligand2clinical_trial_id, reference_id

**Sample Data**:
```json
{
  "ligand2clinical_trial_id": 2088,
  "reference_id": 39590
}
```
### 111. **ligand2drug_approvals**
**Summary**: Ligands tied to regulatory approval records.
**Purpose**: Associates `ligand` rows with `drug_approvals` events.
**Size**: ~323 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **72 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| ligand2drug_approvals_id | integer | NO | Surrogate primary key. Default: sequence: ligand2drug_approvals_ligand2drug_approvals_id_seq |
| drug_approvals_id | integer | NO | Foreign key to `drug_approvals.drug_approvals_id`. |
| ligand_id | integer | YES | Foreign key to `ligand.ligand_id`. |
| ligand_name | character varying(1000) | YES | Ligand name as reported in the source screen or supplier table. |
| curated | boolean | YES | Default: false |

**Primary Keys**: ligand2drug_approvals_id

**Sample Data**:
```json
{
  "curated": false,
  "drug_approvals_id": 16,
  "ligand2drug_approvals_id": 14,
  "ligand_id": null,
  "ligand_name": "nogapendekin alfa inbakicept-pmln"
}
```
### 112. **ligand2family**
**Summary**: Ligand membership in ligand families / classes.
**Purpose**: Many-to-many classification for ligand browsing.
**Size**: ~904 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **104 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| ligand_id | integer | NO | Foreign key to `ligand.ligand_id`. |
| family_id | integer | NO | Foreign key to `family.family_id`. |
| display_order | integer | NO | Sort order for lists or navigation. |

**Primary Keys**: ligand_id, family_id

**Sample Data**:
```json
{
  "display_order": 40,
  "family_id": 999,
  "ligand_id": 11928
}
```
### 113. **ligand2inn**
**Summary**: Ligand ↔ INN mapping (synonyms and salts).
**Purpose**: Links curated ligands to INN records where applicable.
**Size**: ~3,759 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **272 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| ligand_id | integer | NO | Foreign key to `ligand.ligand_id`. |
| inn_number | integer | NO | Primary key / INN registry number (links to WHO INN). |

**Primary Keys**: ligand_id, inn_number

**Sample Data**:
```json
{
  "inn_number": 8204,
  "ligand_id": 4941
}
```
### 114. **ligand2meshpharmacology**
**Summary**: MeSH pharmacology vocabulary links.
**Purpose**: Maps ligands to MeSH terms for literature cross-indexing.
**Size**: ~0 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **16 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| ligand_id | integer | NO | Foreign key to `ligand.ligand_id`. |
| mesh_term | character varying(1000) | NO | Search or synonym expansion for titles, terms, or MeSH. |
| type | character varying(100) | NO | Controlled type label (ligand class, interaction type, etc.). |

**Primary Keys**: ligand_id, mesh_term

**Sample Data**: *No data available or table is empty*
### 115. **ligand2subunit**
**Summary**: Ligands acting at specific receptor subunits.
**Purpose**: Subunit-level specificity for multimeric receptors.
**Size**: ~98 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **24 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| ligand_id | integer | NO | Foreign key to `ligand.ligand_id`. |
| subunit_id | integer | NO | Subunit `object_id` within a multimeric receptor. |

**Primary Keys**: ligand_id, subunit_id

**Sample Data**:
```json
{
  "ligand_id": 1988,
  "subunit_id": 3744
}
```
### 116. **ligand2synonym**
**Summary**: Ligand names, trade names, and code names.
**Purpose**: Large synonym table powering search and display name resolution.
**Size**: ~30,836 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **5720 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| ligand_id | integer | NO | Foreign key to `ligand.ligand_id`. |
| synonym | character varying(2000) | NO | Curated field in the IUPHAR/BPS Guide to PHARMACOLOGY database ([guidetopharmacology.org](https://www.guidetopharmacology.org/)); see the `ligand2synonym` table and related target/ligand pages for context. |
| from_grac | boolean | NO | Default: false |
| ligand2synonym_id | integer | NO | Surrogate primary key. Default: sequence: ligand2synonym_ligand2synonym_id_seq |
| display | boolean | NO | Default: true |
| synonym_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search (see companion text column). |

**Primary Keys**: ligand2synonym_id

**Sample Data**:
```json
{
  "display": true,
  "from_grac": false,
  "ligand2synonym_id": 28147,
  "ligand_id": 9523,
  "synonym": "OF 1",
  "synonym_vector": "'1':2"
}
```
### 117. **ligand2synonym_refs**
**Summary**: References for synonym strings.
**Purpose**: Bibliographic support for alternate ligand names.
**Size**: ~441 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **72 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| ligand2synonym_id | integer | NO | Curated field in the IUPHAR/BPS Guide to PHARMACOLOGY database ([guidetopharmacology.org](https://www.guidetopharmacology.org/)); see the `ligand2synonym_refs` table and related target/ligand pages for context. |
| reference_id | integer | NO | Foreign key to `reference.reference_id`. |

**Primary Keys**: ligand2synonym_id, reference_id

**Sample Data**:
```json
{
  "ligand2synonym_id": 4911,
  "reference_id": 47
}
```
### 118. **ligand2tcp**
**Summary**: Ligands in the Teaching in Clinical Pharmacology (TCP) sets.
**Purpose**: Educational subset cross-reference.
**Size**: ~28 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **40 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| ligand2tcp_id | integer | NO | Surrogate primary key. Default: sequence: ligand2tcp_ligand2tcp_id_seq |
| ligand_id | integer | NO | Foreign key to `ligand.ligand_id`. |
| tcp_id | integer | NO | Teaching in Clinical Pharmacology list identifier. |
| comment | character varying(2000) | NO | Curated field in the IUPHAR/BPS Guide to PHARMACOLOGY database ([guidetopharmacology.org](https://www.guidetopharmacology.org/)); see the `ligand2tcp` table and related target/ligand pages for context. |
| comment_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search (see companion text column). |

**Primary Keys**: ligand2tcp_id

**Sample Data**:
```json
{
  "comment": "",
  "comment_vector": "",
  "ligand2tcp_id": 9,
  "ligand_id": 9721,
  "tcp_id": 1
}
```
### 119. **ligand2tcp_refs**
**Summary**: Citations for TCP ligand inclusions.
**Purpose**: Links `ligand2tcp` to `reference`.
**Size**: ~10 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **24 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| ligand2tcp_id | integer | NO | Curated field in the IUPHAR/BPS Guide to PHARMACOLOGY database ([guidetopharmacology.org](https://www.guidetopharmacology.org/)); see the `ligand2tcp_refs` table and related target/ligand pages for context. |
| reference_id | integer | NO | Foreign key to `reference.reference_id`. |

**Primary Keys**: ligand2tcp_id, reference_id

**Sample Data**:
```json
{
  "ligand2tcp_id": 30,
  "reference_id": 34000
}
```
### 120. **ligand_approval_sources**
**Summary**: Provenance of approval status (FDA label, EMA, etc.).
**Purpose**: Tracks which regulatory source backs `approved` flags on ligands.
**Size**: ~2,685 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **160 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| ligand_id | integer | NO | gtopdb ligand id |
| approval_source | character varying | YES | Curated field in the IUPHAR/BPS Guide to PHARMACOLOGY database ([guidetopharmacology.org](https://www.guidetopharmacology.org/)); see the `ligand_approval_sources` table and related target/ligand pages for context. |
| year | integer | YES | Bibliographic metadata for journal articles or books. |
| comment | character varying | YES | Curated field in the IUPHAR/BPS Guide to PHARMACOLOGY database ([guidetopharmacology.org](https://www.guidetopharmacology.org/)); see the `ligand_approval_sources` table and related target/ligand pages for context. |

**Primary Keys**: *None identified*

**Sample Data**:
```json
{
  "approval_source": "UK MHRA",
  "comment": null,
  "ligand_id": 93,
  "year": 1998
}
```
### 121. **ligand_cluster**
**Summary**: Ligand structural/similarity clusters.
**Purpose**: Cluster IDs for grouping analogues on the website.
**Size**: ~6,859 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **584 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| ligand_id | integer | NO | Foreign key to `ligand.ligand_id`. |
| cluster | character varying(100) | NO | Cluster identifier (short code) for analogue or scaffold grouping. |
| distance | double precision | NO | Distance metric (e.g. sequence or structural distance). |
| cluster_centre | integer | NO | Cluster centroid or representative identifier for ligand clusters. |

**Primary Keys**: ligand_id

**Sample Data**:
```json
{
  "cluster": "776",
  "cluster_centre": 0,
  "distance": 0.154931737,
  "ligand_id": 6159
}
```
### 122. **ligand_cluster_new**
**Summary**: Updated clustering scheme for ligands.
**Purpose**: Newer cluster assignments alongside or replacing `ligand_cluster`.
**Size**: ~10,346 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **712 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| ligand_id | integer | NO | Foreign key to `ligand.ligand_id`. |
| cluster | character varying(100) | NO | Cluster identifier (short code) for analogue or scaffold grouping. |
| distance | double precision | YES | Distance metric (e.g. sequence or structural distance). |
| cluster_centre | integer | YES | Cluster centroid or representative identifier for ligand clusters. |

**Primary Keys**: ligand_id

**Sample Data**:
```json
{
  "cluster": "1",
  "cluster_centre": null,
  "distance": null,
  "ligand_id": 13957
}
```
### 123. **ligand_database_link**
**Summary**: Per-ligand external database identifiers.
**Purpose**: PubChem SID, ChEMBL ID, DrugBank, etc. for each `ligand_id`.
**Size**: ~48,389 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **5344 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| ligand_database_link_id | integer | NO | Surrogate primary key. Default: sequence: ligand_database_link_ligand_database_link_id_seq |
| ligand_id | integer | NO | Foreign key to `ligand.ligand_id`. |
| database_id | integer | NO | Foreign key to `database.database_id`. |
| placeholder | character varying(100) | NO | Internal editorial or QA flag. |
| source | character varying(100) | YES | Curated field in the IUPHAR/BPS Guide to PHARMACOLOGY database ([guidetopharmacology.org](https://www.guidetopharmacology.org/)); see the `ligand_database_link` table and related target/ligand pages for context. |
| commercial | boolean | YES | Default: false |
| species_id | integer | NO | Default: 9 |

**Primary Keys**: ligand_database_link_id

**Sample Data**:
```json
{
  "commercial": false,
  "database_id": 17,
  "ligand_database_link_id": 1,
  "ligand_id": 1,
  "placeholder": "57347",
  "source": null,
  "species_id": 9
}
```
### 124. **ligand_physchem**
**Summary**: Physicochemical properties (logP, MW, TPSA…).
**Purpose**: Calculated or curated descriptors for cheminformatics.
**Size**: ~10,655 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **1088 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| ligand_id | integer | NO | Foreign key to `ligand.ligand_id`. |
| hydrogen_bond_acceptors | integer | NO | Physicochemical descriptor (Lipinski / drug-likeness related). |
| hydrogen_bond_donors | integer | NO | Physicochemical descriptor (Lipinski / drug-likeness related). |
| rotatable_bonds_count | integer | NO | Physicochemical descriptor (Lipinski / drug-likeness related). |
| topological_polar_surface_area | double precision | NO | Physicochemical descriptor (Lipinski / drug-likeness related). |
| molecular_weight | double precision | NO | Physicochemical descriptor (Lipinski / drug-likeness related). |
| xlogp | double precision | NO | Physicochemical descriptor (Lipinski / drug-likeness related). |
| lipinski_s_rule_of_five | integer | NO | Physicochemical descriptor (Lipinski / drug-likeness related). |

**Primary Keys**: ligand_id

**Sample Data**:
```json
{
  "hydrogen_bond_acceptors": 9,
  "hydrogen_bond_donors": 5,
  "ligand_id": 12204,
  "lipinski_s_rule_of_five": 0,
  "molecular_weight": 462.07800982,
  "rotatable_bonds_count": 8,
  "topological_polar_surface_area": 225.13,
  "xlogp": -1.547
}
```
### 125. **ligand_physchem_public**
**Summary**: Public subset of physicochemical properties.
**Purpose**: Redacted or simplified physchem row for open releases.
**Size**: ~0 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **8192 bytes** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| ligand_id | integer | NO | Foreign key to `ligand.ligand_id`. |
| hydrogen_bond_acceptors | integer | NO | Physicochemical descriptor (Lipinski / drug-likeness related). |
| hydrogen_bond_donors | integer | NO | Physicochemical descriptor (Lipinski / drug-likeness related). |
| rotatable_bonds_count | integer | NO | Physicochemical descriptor (Lipinski / drug-likeness related). |
| topological_polar_surface_area | double precision | NO | Physicochemical descriptor (Lipinski / drug-likeness related). |
| molecular_weight | double precision | NO | Physicochemical descriptor (Lipinski / drug-likeness related). |
| xlogp | double precision | NO | Physicochemical descriptor (Lipinski / drug-likeness related). |
| lipinski_s_rule_of_five | integer | NO | Physicochemical descriptor (Lipinski / drug-likeness related). |

**Primary Keys**: ligand_id

**Sample Data**: *No data available or table is empty*
### 126. **ligand_structure**
**Summary**: Structure representations (SMILES, InChI, stereo notes).
**Purpose**: Chemical structure layer for ligands; complements identifiers in `ligand`.
**Size**: ~10,970 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **7120 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| ligand_id | integer | NO | Foreign key to `ligand.ligand_id`. |
| isomeric_smiles | text | NO | Structure representation (SMILES, InChI, HELM) for integration. |
| isomeric_standard_inchi | text | YES | Structure representation (SMILES, InChI, HELM) for integration. |
| isomeric_standard_inchi_key | character varying(300) | NO | Structure representation (SMILES, InChI, HELM) for integration. |
| nonisomeric_smiles | text | NO | Salt-stripped or neutralised structure line for matching. |
| nonisomeric_standard_inchi | text | YES | Structure representation (SMILES, InChI, HELM) for integration. |
| nonisomeric_standard_inchi_key | character varying(300) | YES | Structure representation (SMILES, InChI, HELM) for integration. |
| pubchem_cid | character varying(100) | YES | External database identifier for cross-referencing. |

**Primary Keys**: ligand_id

**Sample Data**:
```json
{
  "isomeric_smiles": "CC12CC3(C)CC(CN)(C1)CC(CO[N+](=O)[O-])(C2)C3",
  "isomeric_standard_inchi": "InChI=1S/C14H24N2O3/c1-11-3-12(2)5-13(4-11,9-15)8-14(6-11,7-12)10-19-16(17)18/h3-10,15H2,1-2H3",
  "isomeric_standard_inchi_key": "SYDDVDMTNCXIDJ-UHFFFAOYSA-N",
  "ligand_id": 12201,
  "nonisomeric_smiles": "NCC12CC3(CO[N+](=O)[O-])CC(C2)(CC(C1)(C3)C)C",
  "nonisomeric_standard_inchi": "InChI=1S/C14H24N2O3/c1-11-3-12(2)5-13(4-11,9-15)8-14(6-11,7-12)10-19-16(17)18/h3-10,15H2,1-2H3",
  "nonisomeric_standard_inchi_key": "SYDDVDMTNCXIDJ-UHFFFAOYSA-N",
  "pubchem_cid": null
}
```
### 127. **lipid_maps**
**Summary**: LIPID MAPS structure/class identifiers for lipid ligands.
**Purpose**: Lipid nomenclature cross-reference for bioactive lipids.
**Size**: ~48,249 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **3744 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | character varying(50) | YES | Curated field in the IUPHAR/BPS Guide to PHARMACOLOGY database ([guidetopharmacology.org](https://www.guidetopharmacology.org/)); see the `lipid_maps` table and related target/ligand pages for context. |
| inchi | character varying(50) | YES | Structure representation (SMILES, InChI, HELM) for integration. |

**Primary Keys**: *None identified*

**Sample Data**:
```json
{
  "id": "LMGP04010069",
  "inchi": "AAABYGXUNQSIIU-IOWSJCHKSA-N"
}
```
### 128. **list_ligand**
**Summary**: Curated ligand lists (e.g. featured sets).
**Purpose**: Ordered list membership for static list pages.
**Size**: ~1,552 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **160 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| object_id | integer | NO | Foreign key to `object.object_id`. |
| ligand_id | integer | NO | Foreign key to `ligand.ligand_id`. |
| display_order | integer | NO | Default: 0 |

**Primary Keys**: object_id, ligand_id

**Sample Data**:
```json
{
  "display_order": 1,
  "ligand_id": 836,
  "object_id": 80
}
```
### 129. **malaria_stage**
**Summary**: Plasmodium life-cycle stages for antimalarial data.
**Purpose**: Stage vocabulary for Guide to MALARIA PHARMACOLOGY.
**Size**: ~5 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **64 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| malaria_stage_id | integer | NO | Surrogate primary key. Default: sequence: malaria_stage_malaria_stage_id_seq |
| name | character varying(300) | NO | Primary display name (target, ligand, family, etc.). |
| description | character varying | YES | Free-text description field. |
| short_name | character varying(20) | YES | Curated field in the IUPHAR/BPS Guide to PHARMACOLOGY database ([guidetopharmacology.org](https://www.guidetopharmacology.org/)); see the `malaria_stage` table and related target/ligand pages for context. |
| name_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search on `name`. |
| description_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search on `description`. |

**Primary Keys**: malaria_stage_id

**Sample Data**:
```json
{
  "description": "During the lifecycle of certain <i>Plasmodium</i> spp., such as <i>P. vivax</i> and <i>P. ovale</i>, a proportion of the liver stage parasites do not achieve maturation immediately and remain in an arrested state of development. This dormant form (<b>hypnozoite</b>) can be reactivated and initiate a cycle of asexual reproduction, causing the clinical symptoms of relapsing malaria.",
  "description_vector": "'achiev':24 'arrest':31 'asexu':47 'caus':49 'certain':5 'clinic':51 'cycl':45 'develop':34 'dormant':36 'form':37 'hypnozoit':38 'immedi':26 'initi':43 'lifecycl':3 'liver':19 'malaria':55 'matur':25 'oval':14 'p':10,13 'parasit':21 'plasmodium':6 'proport':16 'reactiv':41 'relaps':54 'remain':28 'reproduct':48 'spp':7 'stage':20 'state':32 'symptom':52 'vivax':11",
  "malaria_stage_id": 2,
  "name": "Plasmodium dormant liver stage (hypnozoite)",
  "name_vector": "'dormant':2 'hypnozoit':5 'liver':3 'plasmodium':1 'stage':4",
  "short_name": "Dormant liver"
}
```
### 130. **malaria_stage2interaction**
**Summary**: Stage-specific antimalarial interaction annotations.
**Purpose**: Links interactions to `malaria_stage` for parasite stage context.
**Size**: ~494 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **80 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| interaction_id | integer | NO | Foreign key to `interaction.interaction_id`. |
| malaria_stage_id | integer | NO | Foreign key to `malaria_stage.malaria_stage_id`. |

**Primary Keys**: interaction_id, malaria_stage_id

**Sample Data**:
```json
{
  "interaction_id": 86702,
  "malaria_stage_id": 1
}
```
### 131. **medchemexpress**
**Summary**: MedChemExpress product catalog mirror.
**Purpose**: Supplier SKU metadata used with `iuphar2medchemexpress`.
**Size**: ~34,375 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **15 MB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| cat_no | character varying(100) | NO | Commercial catalog or product code (DiscoverX, MCE, …). |
| url | character varying(500) | NO | HTTP(S) link for external resources or Immunopaedia pages. |
| name | character varying(1000) | YES | Primary display name (target, ligand, family, etc.). |
| smiles | character varying(5000) | YES | SMILES line notation for the structure (may include salts). |
| pubchem_cid | character varying(100) | YES | External database identifier for cross-referencing. |
| inchi | character varying(5000) | YES | Structure representation (SMILES, InChI, HELM) for integration. |
| inchikey | character varying(200) | YES | Structure representation (SMILES, InChI, HELM) for integration. |
| cas_number | character varying(200) | YES | Curated field in the IUPHAR/BPS Guide to PHARMACOLOGY database ([guidetopharmacology.org](https://www.guidetopharmacology.org/)); see the `medchemexpress` table and related target/ligand pages for context. |

**Primary Keys**: cat_no

**Sample Data**:
```json
{
  "cas_number": "26049-94-5",
  "cat_no": "HY-100709",
  "inchi": "InChI=1S/C18H18ClNO3/c19-12-17(21)16(11-14-7-3-1-4-8-14)20-18(22)23-13-15-9-5-2-6-10-15/h1-10,16H,11-13H2,(H,20,22)/t16-/m0/s1",
  "inchikey": "OYHLRJGDELITAF-INIZCTEOSA-N",
  "name": "ZPCK",
  "pubchem_cid": "99625",
  "smiles": "O=C(OCC1=CC=CC=C1)N[C@@H](CC2=CC=CC=C2)C(CCl)=O",
  "url": "https://www.medchemexpress.com/zpck.html"
}
```
### 132. **multimer**
**Summary**: Oligomeric assembly notes (dimers, heteromers).
**Purpose**: Short commentary on receptor multimerization per `object_id`.
**Size**: ~3 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **32 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| object_id | integer | NO | Foreign key to `object.object_id`. |
| subunit_specific_agents_comments | text | YES | Curator prose for the `subunit_specific_agents` section on the portal. |

**Primary Keys**: object_id

**Sample Data**:
```json
{
  "object_id": 378,
  "subunit_specific_agents_comments": null
}
```
### 133. **mutation**
**Summary**: Disease- and pharmacology-relevant mutations.
**Purpose**: Mutation descriptions with pathophysiology linkage to targets.
**Size**: ~1,308 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **208 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| mutation_id | integer | NO | Surrogate primary key. Default: sequence: mutation_mutation_id_seq |
| pathophysiology_id | integer | YES | Foreign key to `pathophysiology.pathophysiology_id`. |
| object_id | integer | NO | Foreign key to `object.object_id`. |
| type | character varying(100) | NO | Controlled type label (ligand class, interaction type, etc.). |
| amino_acid_change | character varying(100) | YES | Mutation or sequence representation (variant or protein). |
| species_id | integer | NO | Foreign key to `species.species_id`. |
| description | character varying(1000) | YES | Free-text description field. |
| nucleotide_change | character varying(100) | YES | Mutation or sequence representation (variant or protein). |

**Primary Keys**: mutation_id

**Sample Data**:
```json
{
  "amino_acid_change": "Y129S",
  "description": null,
  "mutation_id": 4,
  "nucleotide_change": null,
  "object_id": 374,
  "pathophysiology_id": 4,
  "species_id": 1,
  "type": "Missense"
}
```
### 134. **mutation_refs**
**Summary**: References for mutation entries.
**Purpose**: Links `mutation` to `reference`.
**Size**: ~1,656 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **152 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| mutation_id | integer | NO | Foreign key to `mutation.mutation_id`. |
| reference_id | integer | NO | Foreign key to `reference.reference_id`. |

**Primary Keys**: mutation_id, reference_id

**Sample Data**:
```json
{
  "mutation_id": 1037,
  "reference_id": 23689
}
```
### 135. **nhr**
**Summary**: Nuclear hormone receptor specific commentary blocks.
**Purpose**: NHR transactivation, DNA binding, co-regulator sections per target.
**Size**: ~49 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **88 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| object_id | integer | NO | Foreign key to `object.object_id`. |
| ligand | character varying(500) | YES | Curated field in the IUPHAR/BPS Guide to PHARMACOLOGY database ([guidetopharmacology.org](https://www.guidetopharmacology.org/)); see the `nhr` table and related target/ligand pages for context. |
| binding_partner_comments | text | YES | Curator prose for the `binding_partner` section on the portal. |
| coregulator_comments | text | YES | Curator prose for the `coregulator` section on the portal. |
| dna_binding_comments | text | YES | Curator prose for the `dna_binding` section on the portal. |
| target_gene_comments | text | YES | Curator prose for the `target_gene` section on the portal. |

**Primary Keys**: object_id

**Sample Data**:
```json
{
  "binding_partner_comments": "MR interacts with other members of the HSP90 complex including, hsp70, p23, the F&kappa;BPs and the cyclopholins <Reference id=29197/><Reference id=11286/><Reference id=29198/>.",
  "coregulator_comments": "A publication describing RHA as a MR co-regulator (Kitagawa <i>et al</i>., 2002) has been retracted <Reference id=29119/><Reference id=29120/>. <br>XRCC6, EEF1A1 and SSRP1 are non-specific, ligand-dependent coregulators that confer tissue specific regulation <Reference id=40665/>.",
  "dna_binding_comments": "MR and GR can heterodimerize.  HRE sequence has variations that contribute to gene-specific regulation.<br><br>Additional response elements are described in Ziera <i>et al.</i>, 2009 <Reference id=29207/>.<br><br>Analysis of the cistromes for the human and rat MRs is reported by Le Billan <i>et al.</i> (2015) <Reference id=37091/> and van Weert <i>et al.</i> (2017) <Reference id=37092/> respectively.",
  "ligand": "",
  "object_id": 626,
  "target_gene_comments": "K-Ras2 gene is activated by MR in Xenopus <Reference id=11274/>.  A small G protein and a proto-oncogene was found to be rapidly induced by aldosterone, enhances Na+ current. Other genes activated include the following: Na+, K+ ATPase &alpha;1 and &beta;1 <Reference id=11277/><Reference id=11277/><Reference id=11278/>.<br><br>In addition to the genes listed above, regulation of L-type Ca2+ channel <Reference id=29229/>, osteogenic genes including alkaline phosphatase (ALP) and bone morphogenetic protein-2 (BMP2) <Reference id=29230/>, the RNA polymerase II elongation factor ELL (eleven-nineteen lysine-rich leukemia; <Reference id=11258/>), the ubiquitin-specific protease Usp2-45 <Reference id=29231/>, and Sgk1, Fkbp5, Rasl12, Tns1 and Tsc22d3 (Gilz) which were validated as direct target genes of MR by quantitative RT-qPCR and ChIP-qPCR in a study using a murine distal convoluted tubular epithelial cell-line <Reference id=29232/>."
}
```
### 136. **nucleic_acid**
**Summary**: Oligonucleotide / siRNA / aptamer ligand details.
**Purpose**: Sequence, HELM, and target mRNA for nucleic-acid therapeutics.
**Size**: ~42 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **32 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| ligand_id | integer | NO | Foreign key to `ligand.ligand_id`. |
| subclass | character varying(2000) | YES | Subclass label (e.g. siRNA, ASO). |
| target | character varying(2000) | YES | Intended mRNA/protein target of a nucleic-acid drug. |
| seq | character varying(2000) | YES | Nucleotide / HELM-style sequence display. |
| helm | character varying(2000) | YES | HELM notation for biopolymers when used. |

**Primary Keys**: ligand_id

**Sample Data**:
```json
{
  "helm": "",
  "ligand_id": 13611,
  "seq": "(3'-5')G-Um-A-A-Cm-Cm-A-A-G-A-G-Um-A-Um-Um-Cm-Cm-A-Um-dT-dT<br>(5'-3')dT-dT-C-A-Um-U-G-G-U-U-C-U-C-A-Um-A-A-G-G-U-A",
  "subclass": "siRNA",
  "target": "transthyretin (TTR) mRNA"
}
```
### 137. **object**
**Summary**: Pharmacological targets — receptors, channels, enzymes, transporters.
**Purpose**: Primary target entity for nearly all GtoPdb content; one row per curated target page.
**Size**: ~3,275 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **1664 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| object_id | integer | NO | Surrogate primary key. Default: sequence: object_object_id_seq |
| name | character varying(1000) | NO | Primary display name (target, ligand, family, etc.). |
| last_modified | date | YES | Last editorial modification date for the row or text block. |
| comments | text | YES | Free-text curator comments. |
| structural_info_comments | text | YES | Summary structure commentary on the target page. |
| old_object_id | integer | YES | Legacy object ID before merges or rekeys. |
| annotation_status | integer | NO | Default: 5 |
| only_iuphar | boolean | YES | Target appears only in IUPHAR views. |
| grac_comments | text | YES | Legacy GRAC-only commentary on targets. |
| only_grac | boolean | YES | Target appears only in GRAC legacy slices. |
| no_contributor_list | boolean | NO | Default: true |
| abbreviation | character varying(100) | YES | Short abbreviation or gene-style shorthand. |
| systematic_name | character varying(100) | YES | Systematic or gene-based name (e.g. HGNC). |
| quaternary_structure_comments | text | YES | Quaternary structure / complex assembly notes. |
| in_cgtp | boolean | NO | Default: false |
| in_gtip | boolean | YES | Default: false |
| gtip_comment | text | YES | Comments fields to capture early curator notes on GtoImmPdb targets |
| in_gtmp | boolean | YES | Default: false |
| gtmp_comment | text | YES | Comments fields to capture curator notes on GtoMPdb targets |
| cite_id | character varying(20) | YES | Used to shows the ID of the GtoPdb CITE family for citation purposes. |

**Primary Keys**: object_id

**Sample Data**:
```json
{
  "abbreviation": "NBCn1",
  "annotation_status": 5,
  "cite_id": null,
  "comments": null,
  "grac_comments": null,
  "gtip_comment": null,
  "gtmp_comment": null,
  "in_cgtp": true,
  "in_gtip": false,
  "in_gtmp": null,
  "last_modified": null,
  "name": "Electroneutral sodium bicarbonate cotransporter 1",
  "no_contributor_list": false,
  "object_id": 910,
  "old_object_id": null,
  "only_grac": true,
  "only_iuphar": false,
  "quaternary_structure_comments": null,
  "structural_info_comments": null,
  "systematic_name": "SLC4A7"
}
```
### 138. **object2go_process**
**Summary**: GO process annotations on targets.
**Purpose**: Many-to-many with evidence codes and optional curator comments.
**Size**: ~4,862 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **592 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| object_id | integer | NO | Foreign key to `object.object_id`. |
| go_process_id | integer | NO | Foreign key to `go_process.go_process_id`. |
| go_evidence | character varying(5) | YES | Gene Ontology evidence code (EXP, ISS, IEA, …). |
| comment | character varying(500) | YES | Curated field in the IUPHAR/BPS Guide to PHARMACOLOGY database ([guidetopharmacology.org](https://www.guidetopharmacology.org/)); see the `object2go_process` table and related target/ligand pages for context. |
| comment_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search (see companion text column). |

**Primary Keys**: object_id, go_process_id

**Sample Data**:
```json
{
  "comment": null,
  "comment_vector": null,
  "go_evidence": "ISS",
  "go_process_id": 19121,
  "object_id": 3018
}
```
### 139. **object2reaction**
**Summary**: Targets participating in curated reaction schemes.
**Purpose**: Links `object` to `reaction` rows (enzymology).
**Size**: ~1,317 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **128 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| object_id | integer | NO | Foreign key to `object.object_id`. |
| reaction_id | integer | NO | Foreign key to `reaction.reaction_id`. |

**Primary Keys**: object_id, reaction_id

**Sample Data**:
```json
{
  "object_id": 644,
  "reaction_id": 2
}
```
### 140. **object_vectors**
**Summary**: Precomputed tsvectors for full-text search across target text fields.
**Purpose**: Search acceleration: aggregates many comment fields into `tsvector` columns per `object_id`.
**Size**: ~3,275 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **7032 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| object_id | integer | NO | Foreign key to `object.object_id`. |
| name | tsvector | YES | Primary display name (target, ligand, family, etc.). |
| abbreviation | tsvector | YES | Short abbreviation or gene-style shorthand. |
| comments | tsvector | YES | Free-text curator comments. |
| grac_comments | tsvector | YES | Legacy GRAC-only commentary on targets. |
| gtip_comments | tsvector | YES | Curator prose for the `gtip` section on the portal. |
| gtmp_comments | tsvector | YES | Malaria-portal-specific ligand commentary. |
| structural_info_comments | tsvector | YES | Summary structure commentary on the target page. |
| associated_proteins_comments | tsvector | YES | Curator prose for the `associated_proteins` section on the portal. |
| functional_assay_comments | tsvector | YES | Curator prose for the `functional_assay` section on the portal. |
| tissue_distribution_comments | tsvector | YES | Curator prose for the `tissue_distribution` section on the portal. |
| functions_comments | tsvector | YES | Curator prose for the `functions` section on the portal. |
| altered_expression_comments | tsvector | YES | Curator prose for the `altered_expression` section on the portal. |
| expression_pathophysiology_comments | tsvector | YES | Curator prose for the `expression_pathophysiology` section on the portal. |
| mutations_pathophysiology_comments | tsvector | YES | Curator prose for the `mutations_pathophysiology` section on the portal. |
| variants_comments | tsvector | YES | Curator prose for the `variants` section on the portal. |
| xenobiotic_expression_comments | tsvector | YES | Curator prose for the `xenobiotic_expression` section on the portal. |
| antibody_comments | tsvector | YES | Curator prose for the `antibody` section on the portal. |
| agonists_comments | tsvector | YES | Curator prose for the `agonists` section on the portal. |
| antagonists_comments | tsvector | YES | Curator prose for the `antagonists` section on the portal. |
| allosteric_modulators_comments | tsvector | YES | Curator prose for the `allosteric_modulators` section on the portal. |
| activators_comments | tsvector | YES | Curator prose for the `activators` section on the portal. |
| inhibitors_comments | tsvector | YES | Curator prose for the `inhibitors` section on the portal. |
| channel_blockers_comments | tsvector | YES | Curator prose for the `channel_blockers` section on the portal. |
| gating_inhibitors_comments | tsvector | YES | Curator prose for the `gating_inhibitors` section on the portal. |
| subunit_specific_agents_comments | tsvector | YES | Curator prose for the `subunit_specific_agents` section on the portal. |
| selectivity_comments | tsvector | YES | Curator prose for the `selectivity` section on the portal. |
| voltage_dependence_comments | tsvector | YES | Curator prose for the `voltage_dependence` section on the portal. |
| target_gene_comments | tsvector | YES | Curator prose for the `target_gene` section on the portal. |
| dna_binding_comments | tsvector | YES | Curator prose for the `dna_binding` section on the portal. |
| coregulator_comments | tsvector | YES | Curator prose for the `coregulator` section on the portal. |
| binding_partner_comments | tsvector | YES | Curator prose for the `binding_partner` section on the portal. |

**Primary Keys**: object_id

**Sample Data**:
```json
{
  "abbreviation": null,
  "activators_comments": "'activ':8 'also':3 'kca1.1':11 'mg2':1 'report':5",
  "agonists_comments": null,
  "allosteric_modulators_comments": null,
  "altered_expression_comments": null,
  "antagonists_comments": null,
  "antibody_comments": null,
  "associated_proteins_comments": null,
  "binding_partner_comments": null,
  "channel_blockers_comments": "'blocker':3 'channel':2 'charybdotoxin':5 'iberiotoxin':6 'includ':4 'tetraethylammonium':8",
  "comments": "'-902':39,61 'applic':5 'approach':48 'associ':56 'asthma':13 'bladder':9,54,75,82 'channel':1 'clinic':42 'crystal':19 'deliv':63 'detrusor':58,76 'develop':43 'direct':72 'effect':80 'either':64 'epilepsi':8 'express':35 'gastric':15 'gate':27 'gene':30 'human':36 'hypermotil':16 'hypertens':14 'inject':73 'instil':69 'intracellular':26 'intraves':68 'kca1.1':37 'limt':79 'may':3 'muscl':77 'novel':46 'open':2 'over-react':10 'overact':53,59 'plasmid':32 'psychos':18 'reactiv':12 'ring':28 'singl':67 'solv':23 'stroke':7 'structur':20 'syndrom':55 'therapeut':47 'therapi':31 'thus':78 'tissu':83 'treament':51 'uro':38,60 'vector':33",
  "coregulator_comments": null,
  "dna_binding_comments": null,
  "expression_pathophysiology_comments": null,
  "functional_assay_comments": null,
  "functions_comments": null,
  "gating_inhibitors_comments": "",
  "grac_comments": null,
  "gtip_comments": null,
  "gtmp_comments": null,
  "inhibitors_comments": null,
  "mutations_pathophysiology_comments": null,
  "name": "'kca1.1':1",
  "object_id": 380,
  "selectivity_comments": "",
  "structural_info_comments": "",
  "subunit_specific_agents_comments": null,
  "target_gene_comments": null,
  "tissue_distribution_comments": null,
  "variants_comments": null,
  "voltage_dependence_comments": "",
  "xenobiotic_expression_comments": null
}
```
### 141. **ontology**
**Summary**: Ontology registry (MP, CL, GO namespaces).
**Purpose**: Metadata about ontologies used in phenotype and cell-type columns.
**Size**: ~1 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **24 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| ontology_id | integer | NO | Surrogate primary key. Default: sequence: ontology_ontology_id_seq |
| name | character varying(100) | NO | Primary display name (target, ligand, family, etc.). |
| short_name | character varying(100) | YES | Curated field in the IUPHAR/BPS Guide to PHARMACOLOGY database ([guidetopharmacology.org](https://www.guidetopharmacology.org/)); see the `ontology` table and related target/ligand pages for context. |

**Primary Keys**: ontology_id

**Sample Data**:
```json
{
  "name": "Mammalian Phenotype Ontology (MP)",
  "ontology_id": 1,
  "short_name": "MP"
}
```
### 142. **ontology_term**
**Summary**: Ontology term cache (IDs and labels).
**Purpose**: Lookup for OBO-style terms used in alleles and phenotypes.
**Size**: ~8,233 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **3216 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| ontology_id | integer | NO | Default: 1 |
| term_id | character varying(100) | NO | Ontology term identifier (e.g. MP:… phenotype ID). |
| term | character varying(1000) | YES | Ontology or controlled vocabulary term string. |
| description | character varying(3000) | YES | Free-text description field. |

**Primary Keys**: ontology_id, term_id

**Sample Data**:
```json
{
  "description": "the observable morphological, physiological, behavioral and other characteristics of mammalian organisms that are manifested through development and lifespan                                                                                                  ",
  "ontology_id": 1,
  "term": "mammalian phenotype",
  "term_id": "MP:0000001"
}
```
### 143. **other_ic**
**Summary**: Miscellaneous ion channel targets not in VGIC/LGIC classes.
**Purpose**: Catch-all ion channel family extension.
**Size**: ~55 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **32 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| object_id | integer | NO | Foreign key to `object.object_id`. |
| selectivity_comments | text | YES | Curator prose for the `selectivity` section on the portal. |

**Primary Keys**: object_id

**Sample Data**:
```json
{
  "object_id": 687,
  "selectivity_comments": null
}
```
### 144. **other_protein**
**Summary**: Other protein targets (non-enzyme, non-receptor categories).
**Purpose**: Class bucket for miscellaneous protein pharmacology.
**Size**: ~329 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **56 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| object_id | integer | NO | Foreign key to `object.object_id`. |

**Primary Keys**: object_id

**Sample Data**:
```json
{
  "object_id": 2529
}
```
### 145. **pathophysiology**
**Summary**: Pathophysiology narrative tied to targets or diseases.
**Purpose**: Clinical mechanism descriptions supporting disease linkage.
**Size**: ~1,467 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **848 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| pathophysiology_id | integer | NO | Surrogate primary key. Default: sequence: pathophysiology_pathophysiology_id_seq |
| object_id | integer | NO | Foreign key to `object.object_id`. |
| disease | character varying(2000) | YES | Disease label or free-text disease name in context. |
| role | character varying(2000) | YES | Functional role label (e.g. agonist, antagonist in context). |
| drugs | character varying(2000) | YES | Curated field in the IUPHAR/BPS Guide to PHARMACOLOGY database ([guidetopharmacology.org](https://www.guidetopharmacology.org/)); see the `pathophysiology` table and related target/ligand pages for context. |
| side_effects | character varying(2000) | YES | Clinical indication, adverse effects, or medical relevance text. |
| use | character varying(2000) | YES | Editorial teaser or overview text for a topic or contributor. |
| omim | character varying(200) | YES | External database identifier for cross-referencing. |
| comments | text | YES | Free-text curator comments. |
| orphanet | character varying(200) | YES | External database identifier for cross-referencing. |
| disease_id | integer | YES | Foreign key to `disease.disease_id`. |
| role_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search (see companion text column). |
| drugs_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search (see companion text column). |
| side_effects_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search (see companion text column). |
| use_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search (see companion text column). |
| comments_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search on `comments`. |

**Primary Keys**: pathophysiology_id

**Sample Data**:
```json
{
  "comments": "",
  "comments_vector": "",
  "disease": null,
  "disease_id": 970,
  "drugs": "",
  "drugs_vector": "",
  "object_id": 875,
  "omim": null,
  "orphanet": null,
  "pathophysiology_id": 1248,
  "role": "",
  "role_vector": "",
  "side_effects": "",
  "side_effects_vector": "",
  "use": "",
  "use_vector": ""
}
```
### 146. **pathophysiology_refs**
**Summary**: References for pathophysiology text.
**Purpose**: Links `pathophysiology` to `reference`.
**Size**: ~1,080 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **104 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| pathophysiology_id | integer | NO | Foreign key to `pathophysiology.pathophysiology_id`. |
| reference_id | integer | NO | Foreign key to `reference.reference_id`. |

**Primary Keys**: pathophysiology_id, reference_id

**Sample Data**:
```json
{
  "pathophysiology_id": 360,
  "reference_id": 12017
}
```
### 147. **pdb_inchi**
**Summary**: InChI keys for PDB ligand instances.
**Purpose**: Maps PDB chemical components to InChI for structure–ligand integration.
**Size**: ~47,414 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **2848 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| inchikey | character varying(50) | YES | Structure representation (SMILES, InChI, HELM) for integration. |
| pdb_id | character varying(50) | YES | External database identifier for cross-referencing. |

**Primary Keys**: *None identified*

**Sample Data**:
```json
{
  "inchikey": "CXHHBNMLPJOKQD-UHFFFAOYSA-N",
  "pdb_id": "000"
}
```
### 148. **pdb_structure**
**Summary**: PDB identifiers and metadata for experimental structures.
**Purpose**: Structure table for target and ligand 3D views.
**Size**: ~1,082 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **584 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| pdb_structure_id | integer | NO | Surrogate primary key. Default: sequence: pdb_structure_pdb_structure_id_seq |
| object_id | integer | NO | Foreign key to `object.object_id`. |
| ligand_id | integer | YES | Foreign key to `ligand.ligand_id`. |
| endogenous | boolean | NO | Default: false |
| pdb_code | character varying(4) | YES | External database identifier for cross-referencing. |
| description | character varying(1000) | YES | Free-text description field. |
| resolution | double precision | YES | Structural resolution (Å) for an experimental structure. |
| species_id | integer | NO | Foreign key to `species.species_id`. |
| description_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search on `description`. |

**Primary Keys**: pdb_structure_id

**Sample Data**:
```json
{
  "description": "HNF4a Ligand Binding Domain",
  "description_vector": "'bind':3 'domain':4 'hnf4a':1 'ligand':2",
  "endogenous": false,
  "ligand_id": null,
  "object_id": 608,
  "pdb_code": "3FS1",
  "pdb_structure_id": 21,
  "resolution": 2.2,
  "species_id": 1
}
```
### 149. **pdb_structure_refs**
**Summary**: Citations for structural entries.
**Purpose**: Links `pdb_structure` to `reference`.
**Size**: ~969 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **104 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| pdb_structure_id | integer | NO | Foreign key to `pdb_structure.pdb_structure_id`. |
| reference_id | integer | NO | Foreign key to `reference.reference_id`. |

**Primary Keys**: pdb_structure_id, reference_id

**Sample Data**:
```json
{
  "pdb_structure_id": 57,
  "reference_id": 13213
}
```
### 150. **peptide**
**Summary**: Peptide ligand sequence and classification.
**Purpose**: One row per peptide-class ligand with sequence features.
**Size**: ~2,816 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **840 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| ligand_id | integer | NO | Foreign key to `ligand.ligand_id`. |
| one_letter_seq | text | YES | Mutation or sequence representation (variant or protein). |
| three_letter_seq | text | YES | Mutation or sequence representation (variant or protein). |
| post_translational_modifications | character varying(1000) | YES | Protein domain or modification notes. |
| chemical_modifications | character varying(1000) | YES | Protein domain or modification notes. |
| medical_relevance | character varying(2000) | YES | Clinical indication, adverse effects, or medical relevance text. |
| helm_notation | character varying(1000) | YES | Structure representation (SMILES, InChI, HELM) for integration. |

**Primary Keys**: ligand_id

**Sample Data**:
```json
{
  "chemical_modifications": "Disulphide bond between Cys3 and Cys7 cyclisizes the peptide.",
  "helm_notation": null,
  "ligand_id": 8723,
  "medical_relevance": "",
  "one_letter_seq": "YWCKGLCK",
  "post_translational_modifications": "",
  "three_letter_seq": "Tyr-Trp-c-[Cys-Lys-Gly-Leu-Cys]-Lys-NH2"
}
```
### 151. **peptide_ligand_cluster**
**Summary**: Clusters of peptide ligands by pharmacophore.
**Purpose**: Grouping for peptide browsing.
**Size**: ~64 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **24 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| ligand_id | integer | NO | Foreign key to `ligand.ligand_id`. |
| cluster | character varying(10) | YES | Cluster identifier (short code) for analogue or scaffold grouping. |

**Primary Keys**: ligand_id

**Sample Data**:
```json
{
  "cluster": "1106P",
  "ligand_id": 1110
}
```
### 152. **peptide_ligand_sequence_cluster**
**Summary**: Sequence similarity clusters for peptides.
**Purpose**: Clusters derived from sequence alignment.
**Size**: ~1,168 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **152 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| ligand_id | integer | NO | Foreign key to `ligand.ligand_id`. |
| cluster | integer | NO | Cluster identifier (short code) for analogue or scaffold grouping. |

**Primary Keys**: ligand_id

**Sample Data**:
```json
{
  "cluster": 1,
  "ligand_id": 7638
}
```
### 153. **physiological_function**
**Summary**: Physiological roles of the target (short narratives).
**Purpose**: Normal physiology text used on target pages.
**Size**: ~2,482 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **1176 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| physiological_function_id | integer | NO | Surrogate primary key. Default: sequence: physiological_function_physiological_function_id_seq |
| object_id | integer | NO | Foreign key to `object.object_id`. |
| description | text | NO | Free-text description field. |
| species_id | integer | NO | Foreign key to `species.species_id`. |
| tissue | text | NO | Tissue or organ context for expression data. |
| description_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search on `description`. |
| tissue_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search on `tissue`. |

**Primary Keys**: physiological_function_id

**Sample Data**:
```json
{
  "description": "Thermoregulation.",
  "description_vector": "'thermoregul':1",
  "object_id": 301,
  "physiological_function_id": 728,
  "species_id": 2,
  "tissue": "Brain.",
  "tissue_vector": "'brain':1"
}
```
### 154. **physiological_function_refs**
**Summary**: References for physiological function text.
**Purpose**: Links `physiological_function` to `reference`.
**Size**: ~3,696 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **272 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| physiological_function_id | integer | NO | Foreign key to `physiological_function.physiological_function_id`. |
| reference_id | integer | NO | Foreign key to `reference.reference_id`. |

**Primary Keys**: physiological_function_id, reference_id

**Sample Data**:
```json
{
  "physiological_function_id": 1,
  "reference_id": 25
}
```
### 155. **precursor**
**Summary**: Peptide hormone precursors (preproproteins).
**Purpose**: Precursor proteins that yield bioactive peptides.
**Size**: ~721 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **424 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| precursor_id | integer | NO | Surrogate primary key. Default: sequence: precursor_precursor_id_seq |
| gene_name | character varying(100) | YES | Gene or protein naming for display and search. |
| official_gene_id | character varying(100) | YES | External database identifier for cross-referencing. |
| protein_name | character varying(200) | YES | Gene or protein naming for display and search. |
| species_id | integer | NO | Foreign key to `species.species_id`. |
| gene_long_name | character varying(2000) | YES | Gene or protein naming for display and search. |
| protein_name_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search (see companion text column). |
| gene_long_name_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search (see companion text column). |

**Primary Keys**: precursor_id

**Sample Data**:
```json
{
  "gene_long_name": "prolactin releasing hormone",
  "gene_long_name_vector": "'hormon':3 'prolactin':1 'releas':2",
  "gene_name": "PRLH",
  "official_gene_id": "17945",
  "precursor_id": 283,
  "protein_name": "prolactin releasing hormone",
  "protein_name_vector": "'hormon':3 'prolactin':1 'releas':2",
  "species_id": 1
}
```
### 156. **precursor2peptide**
**Summary**: Cleavage relationships from precursor to mature peptide ligands.
**Purpose**: Many-to-many linking `precursor` to peptide `ligand` rows.
**Size**: ~1,001 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **104 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| precursor_id | integer | NO | Foreign key to `precursor.precursor_id`. |
| ligand_id | integer | NO | Foreign key to `ligand.ligand_id`. |

**Primary Keys**: precursor_id, ligand_id

**Sample Data**:
```json
{
  "ligand_id": 756,
  "precursor_id": 1
}
```
### 157. **precursor2synonym**
**Summary**: Synonyms for precursor names.
**Purpose**: Alternate names for precursors via `synonym` linkage.
**Size**: ~2,894 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **544 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| precursor2synonym_id | integer | NO | Surrogate primary key. Default: sequence: precursor2synonym_precursor2synonym_id_seq |
| precursor_id | integer | NO | Foreign key to `precursor.precursor_id`. |
| synonym | character varying(2000) | NO | Curated field in the IUPHAR/BPS Guide to PHARMACOLOGY database ([guidetopharmacology.org](https://www.guidetopharmacology.org/)); see the `precursor2synonym` table and related target/ligand pages for context. |
| synonym_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search (see companion text column). |

**Primary Keys**: precursor2synonym_id

**Sample Data**:
```json
{
  "precursor2synonym_id": 367,
  "precursor_id": 205,
  "synonym": "NAP-1",
  "synonym_vector": "'-1':2 'nap':1"
}
```
### 158. **primary_regulator**
**Summary**: Primary transcriptional regulators of the target gene.
**Purpose**: Regulatory relationships for nuclear receptors and signalling genes.
**Size**: ~0 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **16 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| primary_regulator_id | integer | NO | Surrogate primary key. Default: sequence: primary_regulator_primary_regulator_id_seq |
| object_id | integer | NO | Foreign key to `object.object_id`. |
| name | character varying(1000) | YES | Primary display name (target, ligand, family, etc.). |
| regulatory_effect | character varying(2000) | YES | Curated field in the IUPHAR/BPS Guide to PHARMACOLOGY database ([guidetopharmacology.org](https://www.guidetopharmacology.org/)); see the `primary_regulator` table and related target/ligand pages for context. |
| regulator_object_id | integer | YES | Related `object_id` for complexes, partners, or regulated genes. |

**Primary Keys**: primary_regulator_id

**Sample Data**: *No data available or table is empty*
### 159. **primary_regulator_refs**
**Summary**: References for primary regulator commentary.
**Purpose**: Links `primary_regulator` to `reference`.
**Size**: ~0 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **8192 bytes** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| primary_regulator_id | integer | NO | Foreign key to `primary_regulator.primary_regulator_id`. |
| reference_id | integer | NO | Foreign key to `reference.reference_id`. |

**Primary Keys**: primary_regulator_id, reference_id

**Sample Data**: *No data available or table is empty*
### 160. **process_assoc**
**Summary**: Biological process associations beyond GO (curated prose).
**Purpose**: Process linkage with optional GO provenance flags.
**Size**: ~3,586 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **504 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| object_id | integer | NO | Foreign key to `object.object_id`. |
| gtip_process_id | integer | NO | Foreign key to `gtip_process.gtip_process_id`. |
| comment | character varying(500) | YES | Curated field in the IUPHAR/BPS Guide to PHARMACOLOGY database ([guidetopharmacology.org](https://www.guidetopharmacology.org/)); see the `process_assoc` table and related target/ligand pages for context. |
| direct_annotation | boolean | NO | Default: false |
| go_annotation | integer | NO | Default: 0 |
| process_assoc_id | integer | NO | Surrogate primary key. Default: sequence: process_assoc_process_assoc_id_seq |
| comment_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search (see companion text column). |

**Primary Keys**: process_assoc_id

**Sample Data**:
```json
{
  "comment": "",
  "comment_vector": "",
  "direct_annotation": false,
  "go_annotation": 1,
  "gtip_process_id": 3,
  "object_id": 2935,
  "process_assoc_id": 19999
}
```
### 161. **process_assoc_refs**
**Summary**: References for process association text.
**Purpose**: Links `process_assoc` to `reference`.
**Size**: ~20 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **24 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| process_assoc_id | integer | NO | Foreign key to `process_assoc.process_assoc_id`. |
| reference_id | integer | NO | Foreign key to `reference.reference_id`. |

**Primary Keys**: process_assoc_id, reference_id

**Sample Data**:
```json
{
  "process_assoc_id": 19996,
  "reference_id": 29579
}
```
### 162. **prodrug**
**Summary**: Prodrug relationships (inactive parent → active metabolite).
**Purpose**: Maps prodrug ligands to active forms.
**Size**: ~136 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **24 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| prodrug_ligand_id | integer | NO | Active metabolite or parent ligand id in prodrug relationships. |
| drug_ligand_id | integer | NO | Antibacterial resource: compound name, class, or regulatory metadata. |

**Primary Keys**: prodrug_ligand_id, drug_ligand_id

**Sample Data**:
```json
{
  "drug_ligand_id": 6373,
  "prodrug_ligand_id": 6367
}
```
### 163. **product**
**Summary**: Formulation / product-level information for ligands.
**Purpose**: Trade products and formulation notes where distinct from ligand entity.
**Size**: ~49 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **40 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| product_id | integer | NO | Surrogate primary key. Default: sequence: product_product_id_seq |
| object_id | integer | NO | Foreign key to `object.object_id`. |
| species_id | integer | NO | Foreign key to `species.species_id`. |
| ligand_id | integer | YES | Foreign key to `ligand.ligand_id`. |
| name | character varying(1000) | YES | Primary display name (target, ligand, family, etc.). |
| endogenous | boolean | NO | Default: true |
| in_iuphar | boolean | NO | Default: true |
| in_grac | boolean | NO | Default: false |
| name_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search on `name`. |

**Primary Keys**: product_id

**Sample Data**:
```json
{
  "endogenous": true,
  "in_grac": true,
  "in_iuphar": false,
  "ligand_id": 5110,
  "name": null,
  "name_vector": null,
  "object_id": 1230,
  "product_id": 3,
  "species_id": 1
}
```
### 164. **product_refs**
**Summary**: References for product information.
**Purpose**: Links `product` to `reference`.
**Size**: ~3 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **24 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| product_id | integer | NO | Foreign key to `product.product_id`. |
| reference_id | integer | NO | Foreign key to `reference.reference_id`. |

**Primary Keys**: product_id, reference_id

**Sample Data**:
```json
{
  "product_id": 23,
  "reference_id": 17887
}
```
### 165. **reaction**
**Summary**: Biochemical reaction schemes (substrates/products).
**Purpose**: Reaction nodes for enzyme targets and pathway context.
**Size**: ~464 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **128 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| reaction_id | integer | NO | Surrogate primary key. Default: sequence: reaction_reaction_id_seq |
| ec_number | character varying(50) | NO | Enzyme Commission (EC) number. |
| reaction | character varying(3000) | YES | Reaction label or narrative (enzymology). |

**Primary Keys**: reaction_id

**Sample Data**:
```json
{
  "ec_number": "3.4.21.71",
  "reaction": "",
  "reaction_id": 452
}
```
### 166. **receptor2family**
**Summary**: Target-to-family membership (many targets per family).
**Purpose**: Core graph edge placing each `object` in a `family` hierarchy.
**Size**: ~3,339 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **336 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| object_id | integer | NO | Foreign key to `object.object_id`. |
| family_id | integer | NO | Foreign key to `family.family_id`. |
| display_order | integer | NO | Sort order for lists or navigation. |

**Primary Keys**: object_id, family_id

**Sample Data**:
```json
{
  "display_order": 1,
  "family_id": 151,
  "object_id": 756
}
```
### 167. **receptor2subunit**
**Summary**: Subunit composition of heteromeric receptors.
**Purpose**: Which gene products form the channel/receptor complex.
**Size**: ~189 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **56 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| receptor_id | integer | NO | Target id (`object_id` of the receptor) in screening or pairing data. |
| subunit_id | integer | NO | Subunit `object_id` within a multimeric receptor. |
| type | character varying(200) | YES | Controlled type label (ligand class, interaction type, etc.). |

**Primary Keys**: receptor_id, subunit_id

**Sample Data**:
```json
{
  "receptor_id": 44,
  "subunit_id": 43,
  "type": null
}
```
### 168. **receptor_basic**
**Summary**: Compact ‘basic information’ block per target.
**Purpose**: Gene names, HGNC, localization snippets — summary card data.
**Size**: ~3,265 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **912 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| object_id | integer | NO | Foreign key to `object.object_id`. |
| list_comments | character varying(1000) | YES | Curator prose for the `list` section on the portal. |
| associated_proteins_comments | text | YES | Curator prose for the `associated_proteins` section on the portal. |
| functional_assay_comments | text | YES | Curator prose for the `functional_assay` section on the portal. |
| tissue_distribution_comments | text | YES | Curator prose for the `tissue_distribution` section on the portal. |
| functions_comments | text | YES | Curator prose for the `functions` section on the portal. |
| altered_expression_comments | text | YES | Curator prose for the `altered_expression` section on the portal. |
| expression_pathophysiology_comments | text | YES | Curator prose for the `expression_pathophysiology` section on the portal. |
| mutations_pathophysiology_comments | text | YES | Curator prose for the `mutations_pathophysiology` section on the portal. |
| variants_comments | text | YES | Curator prose for the `variants` section on the portal. |
| xenobiotic_expression_comments | text | YES | Curator prose for the `xenobiotic_expression` section on the portal. |
| antibody_comments | text | YES | Curator prose for the `antibody` section on the portal. |
| agonists_comments | text | YES | Curator prose for the `agonists` section on the portal. |
| antagonists_comments | text | YES | Curator prose for the `antagonists` section on the portal. |
| allosteric_modulators_comments | text | YES | Curator prose for the `allosteric_modulators` section on the portal. |
| activators_comments | text | YES | Curator prose for the `activators` section on the portal. |
| inhibitors_comments | text | YES | Curator prose for the `inhibitors` section on the portal. |
| channel_blockers_comments | text | YES | Curator prose for the `channel_blockers` section on the portal. |
| gating_inhibitors_comments | text | YES | Curator prose for the `gating_inhibitors` section on the portal. |

**Primary Keys**: object_id

**Sample Data**:
```json
{
  "activators_comments": "NS309, riluzole, DC-EBIO and EBIO increase Ca<sup>2+</sup> sensitivity of K<sub>Ca</sub>2.2 <Reference id=7844/><Reference id=7824/>. A detailed review of K<sub>Ca</sub>2 channel pharmacology can be found in <Reference id=7825/>. For shorter more recent reviews see <Reference id=31646/><Reference id=31647/>.",
  "agonists_comments": null,
  "allosteric_modulators_comments": null,
  "altered_expression_comments": "",
  "antagonists_comments": null,
  "antibody_comments": null,
  "associated_proteins_comments": "Casein kinase 2 (CK2) and protein phosphatase 2A (PPA) phosphorylate and dephosphorylate Thr<sup>80</sup> in calmodulin changing K<sub>Ca</sub>2.2 Ca<sup>2+</sup> sensitivity <Reference id=31649/><Reference id=31650/>. ",
  "channel_blockers_comments": "Tamapin, apamin and leiurotoxin I block K<sub>Ca</sub>2.2 at picomolar concentrations and K<sub>Ca</sub>2.1 and K<sub>Ca</sub>2.3 at low nanomolar concentrations.<Br> <br> A detailed review of K<sub>Ca</sub>2 channel pharmacology can be found in <Reference id=7825/>. For shorter more recent reviews see <Reference id=31646/><Reference id=31647/>.",
  "expression_pathophysiology_comments": "",
  "functional_assay_comments": "",
  "functions_comments": "",
  "gating_inhibitors_comments": "NS5893 is an inhibitory gating modulator that decreases the Ca<sup>2+</sup> sensitivity of K<sub>Ca</sub>2 channels <Reference id=7826/>. ",
  "inhibitors_comments": "",
  "list_comments": "",
  "mutations_pathophysiology_comments": "",
  "object_id": 382,
  "tissue_distribution_comments": "",
  "variants_comments": "",
  "xenobiotic_expression_comments": ""
}
```
### 169. **reference**
**Summary**: Bibliography — PubMed and full citations.
**Purpose**: Central publications table cited across the entire database via `*_refs` tables.
**Size**: ~47,380 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **38 MB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| reference_id | integer | NO | Surrogate primary key. Default: sequence: reference_reference_id_seq |
| type | character varying(50) | NO | Controlled type label (ligand class, interaction type, etc.). |
| title | character varying(2000) | YES | Short title or heading for UI display. |
| article_title | character varying(1000) | NO | Authorship or title fields for citations or Concise Guide content. |
| year | smallint | YES | Bibliographic metadata for journal articles or books. |
| issue | character varying(50) | YES | Bibliographic metadata for journal articles or books. |
| volume | character varying(50) | YES | Bibliographic metadata for journal articles or books. |
| pages | character varying(50) | YES | Bibliographic metadata for journal articles or books. |
| publisher | character varying(500) | YES | Book or report publication metadata. |
| publisher_address | character varying(2000) | YES | Book or report publication metadata. |
| editors | character varying(2000) | YES | Editorial or authorship attribution for publications. |
| pubmed_id | bigint | YES | PubMed identifier (PMID). |
| isbn | character varying(13) | YES | Book or report publication metadata. |
| pub_status | character varying(100) | YES | Publication status (in press, published, …). |
| topics | character varying(250) | YES | Topic tags or keywords. |
| comments | character varying(500) | YES | Free-text curator comments. |
| read | boolean | YES | Editorial teaser or overview text for a topic or contributor. |
| useful | boolean | YES | Internal editorial or QA flag. |
| website | character varying(500) | YES | External website URL. |
| url | character varying(2000) | YES | HTTP(S) link for external resources or Immunopaedia pages. |
| doi | character varying(500) | YES | Digital Object Identifier for the cited publication. |
| accessed | date | YES | Publication, access, or modification date. |
| modified | date | YES | Curated field in the IUPHAR/BPS Guide to PHARMACOLOGY database ([guidetopharmacology.org](https://www.guidetopharmacology.org/)); see the `reference` table and related target/ligand pages for context. |
| patent_number | character varying(250) | YES | Patent reference or assignee (intellectual property). |
| priority | date | YES | Sort order for lists or navigation. |
| publication | date | YES | Authorship or title fields for citations or Concise Guide content. |
| authors | text | YES | Authorship or title fields for citations or Concise Guide content. |
| assignee | character varying(500) | YES | Patent reference or assignee (intellectual property). |
| pmc_id | character varying(50) | YES | PubMed Central identifier. |
| authors_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search (see companion text column). |
| article_title_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search (see companion text column). |

**Primary Keys**: reference_id

**Sample Data**:
```json
{
  "accessed": null,
  "article_title": "A next-generation human genome sequence.",
  "article_title_vector": "'generat':4 'genom':6 'human':5 'next':3 'next-gener':2 'sequenc':7",
  "assignee": null,
  "authors": "Church DM",
  "authors_vector": "'church':1 'dm':2",
  "comments": null,
  "doi": "",
  "editors": null,
  "isbn": null,
  "issue": "6588",
  "modified": null,
  "pages": "34-35",
  "patent_number": null,
  "pmc_id": null,
  "priority": null,
  "pub_status": "",
  "publication": null,
  "publisher": null,
  "publisher_address": null,
  "pubmed_id": 35357937,
  "read": null,
  "reference_id": 43602,
  "title": "Science",
  "topics": null,
  "type": "Journal",
  "url": null,
  "useful": null,
  "volume": "376",
  "website": null,
  "year": 2022
}
```
### 170. **reference2immuno**
**Summary**: References flagged for immunopharmacology relevance.
**Purpose**: Subset tagging for immune portal bibliography.
**Size**: ~83 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **24 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| reference_id | integer | NO | ID of reference from reference table |
| type | character varying(50) | NO | Controlled type label (ligand class, interaction type, etc.). |

**Primary Keys**: reference_id, type

**Sample Data**:
```json
{
  "reference_id": 33004,
  "type": "review"
}
```
### 171. **reference2ligand**
**Summary**: Direct ligand–reference associations (non-interaction).
**Purpose**: General citations attached to ligands (reviews, discovery papers).
**Size**: ~14,978 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **912 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| reference_id | integer | NO | Foreign key to `reference.reference_id`. |
| ligand_id | integer | NO | Foreign key to `ligand.ligand_id`. |

**Primary Keys**: reference_id, ligand_id

**Sample Data**:
```json
{
  "ligand_id": 753,
  "reference_id": 10967
}
```
### 172. **screen**
**Summary**: High-throughput screening campaign metadata.
**Purpose**: Screening project headers for large bioactivity dumps.
**Size**: ~3 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **32 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| screen_id | integer | NO | Surrogate primary key. Default: sequence: screen_screen_id_seq |
| name | character varying(500) | NO | Primary display name (target, ligand, family, etc.). |
| description | text | YES | Free-text description field. |
| url | character varying(1000) | YES | HTTP(S) link for external resources or Immunopaedia pages. |
| affinity_cut_off_nm | integer | YES | Affinity cutoff used when filtering screening hits (nM). |
| company_logo_filename | character varying(250) | YES | Image asset filename for sponsor or technology logo. |
| technology_logo_filename | character varying(250) | YES | Image asset filename for sponsor or technology logo. |

**Primary Keys**: screen_id

**Sample Data**:
```json
{
  "affinity_cut_off_nm": 3000,
  "company_logo_filename": "DRx_logo_hrsmall_90x16.png",
  "description": "A screen of 72 inhibitors against 456 human kinases. Quantitative data were derived using DiscoveRx KINOME<i>scan</i><sup>&reg;</sup> platform.",
  "name": "DiscoveRx KINOME<i>scan</i><sup>&reg;</sup> screen",
  "screen_id": 2,
  "technology_logo_filename": "KINOMEscan_90x63.png",
  "url": "http://www.discoverx.com/services/drug-discovery-development-services/kinase-profiling/kinomescan"
}
```
### 173. **screen_interaction**
**Summary**: Screen-derived bioactivity measurements at scale.
**Purpose**: Very large fact table of assay results linking ligands and targets from screens.
**Size**: ~158,551 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **45 MB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| screen_interaction_id | integer | NO | Surrogate primary key. Default: sequence: screen_interaction_screen_interaction_id_seq |
| screen_id | integer | NO | Foreign key to `screen.screen_id`. |
| ligand_id | integer | NO | Foreign key to `ligand.ligand_id`. |
| object_id | integer | NO | Foreign key to `object.object_id`. |
| type | character varying(100) | NO | Controlled type label (ligand class, interaction type, etc.). |
| action | character varying(1000) | NO | Pharmacological action (agonist, antagonist, inhibitor, …). |
| action_comment | character varying(2000) | NO | Curator prose for the `action` section on the portal. |
| species_id | integer | NO | Foreign key to `species.species_id`. |
| endogenous | boolean | NO | Default: false |
| affinity_units | character varying(100) | NO | Default: -::character varying |
| affinity_high | double precision | YES | Upper bound of reported affinity (numeric). |
| affinity_median | double precision | YES | Median or most representative affinity value. |
| affinity_low | double precision | YES | Lower bound of reported affinity (numeric). |
| concentration_range | character varying(200) | YES | Range of concentrations tested in the assay. |
| original_affinity_low_nm | double precision | YES | Original literature affinity (low) in nM space. |
| original_affinity_median_nm | double precision | YES | Original literature affinity (median) in nM space. |
| original_affinity_high_nm | double precision | YES | Original literature affinity (high) converted or in nM. |
| original_affinity_units | character varying(20) | YES | Units as stated in the primary publication. |
| original_affinity_relation | character varying(10) | YES | Inequality relation (<, >, =) for original affinity. |
| assay_description | character varying(1000) | YES | Short assay description (binding, functional, …). |
| percent_activity | double precision | YES | Functional assay percent activity (e.g. agonist screen). |
| assay_url | character varying(500) | YES | Link to assay protocol or external assay record. |

**Primary Keys**: screen_interaction_id

**Sample Data**:
```json
{
  "action": "Inhibition",
  "action_comment": "TRPM6",
  "affinity_high": null,
  "affinity_low": null,
  "affinity_median": 8.1,
  "affinity_units": "pKd",
  "assay_description": "DiscoveRx KINOMEscan platform",
  "assay_url": "http://www.discoverx.com/kinase-data-sheets/TRPM6",
  "concentration_range": null,
  "endogenous": false,
  "ligand_id": 5715,
  "object_id": 498,
  "original_affinity_high_nm": null,
  "original_affinity_low_nm": null,
  "original_affinity_median_nm": 7.9,
  "original_affinity_relation": "=",
  "original_affinity_units": "Kd",
  "percent_activity": null,
  "screen_id": 2,
  "screen_interaction_id": 1,
  "species_id": 1,
  "type": "Inhibitor"
}
```
### 174. **screen_refs**
**Summary**: Publications for screening datasets.
**Purpose**: Links `screen` to `reference`.
**Size**: ~4 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **24 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| screen_id | integer | NO | Foreign key to `screen.screen_id`. |
| reference_id | integer | NO | Foreign key to `reference.reference_id`. |

**Primary Keys**: screen_id, reference_id

**Sample Data**:
```json
{
  "reference_id": 19282,
  "screen_id": 2
}
```
### 175. **selectivity**
**Summary**: Ligand selectivity profiles across targets.
**Purpose**: Selectivity commentary and rankings for ligands.
**Size**: ~303 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **64 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| selectivity_id | integer | NO | Surrogate primary key. Default: sequence: selectivity_selectivity_id_seq |
| object_id | integer | NO | Foreign key to `object.object_id`. |
| ion | character varying(20) | NO | Permeant ion species for channel conductance. |
| conductance_high | real | YES | Channel conductance parameter (numeric or descriptive). |
| conductance_low | real | YES | Channel conductance parameter (numeric or descriptive). |
| conductance_median | real | YES | Channel conductance parameter (numeric or descriptive). |
| hide_conductance | boolean | YES | Suppress conductance block from the default target view. |
| species_id | integer | NO | Foreign key to `species.species_id`. |

**Primary Keys**: selectivity_id

**Sample Data**:
```json
{
  "conductance_high": null,
  "conductance_low": null,
  "conductance_median": 1,
  "hide_conductance": true,
  "ion": "Cs+",
  "object_id": 378,
  "selectivity_id": 1,
  "species_id": 1
}
```
### 176. **selectivity_refs**
**Summary**: References for selectivity statements.
**Purpose**: Links `selectivity` to `reference`.
**Size**: ~291 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **56 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| selectivity_id | integer | NO | Foreign key to `selectivity.selectivity_id`. |
| reference_id | integer | NO | Foreign key to `reference.reference_id`. |

**Primary Keys**: selectivity_id, reference_id

**Sample Data**:
```json
{
  "reference_id": 7535,
  "selectivity_id": 1
}
```
### 177. **species**
**Summary**: Species taxonomy for orthologs and assay species.
**Purpose**: Species list (human, mouse, rat, …) used in interactions and expression.
**Size**: ~118 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **128 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| species_id | integer | NO | Surrogate primary key. Default: sequence: species_species_id_seq |
| name | character varying(100) | NO | Primary display name (target, ligand, family, etc.). |
| short_name | character varying(15) | NO | Curated field in the IUPHAR/BPS Guide to PHARMACOLOGY database ([guidetopharmacology.org](https://www.guidetopharmacology.org/)); see the `species` table and related target/ligand pages for context. |
| scientific_name | character varying(200) | YES | Taxonomic classification for species rows. |
| ncbi_taxonomy_id | integer | YES | Taxonomic classification for species rows. |
| comments | text | YES | Free-text curator comments. |
| description | text | YES | Detailed description of the species for display on species page - added for MMV |
| name_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search on `name`. |
| short_name_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search (see companion text column). |

**Primary Keys**: species_id

**Sample Data**:
```json
{
  "comments": null,
  "description": null,
  "name": "Monkey",
  "name_vector": "'monkey':1",
  "ncbi_taxonomy_id": null,
  "scientific_name": "",
  "short_name": "Monkey",
  "short_name_vector": "'monkey':1",
  "species_id": 20
}
```
### 178. **specific_reaction**
**Summary**: Fine-grained enzyme reactions (substrate-specific EC variants).
**Purpose**: Specific catalytic forms as described in PostgreSQL comment on this table. Database comment: provides a place to enter specific forms of reactions described by EC numbers, e.g. with different chemical substrates/products
**Size**: ~79 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **64 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| specific_reaction_id | integer | NO | Surrogate primary key. Default: sequence: specific_reaction_specific_reaction_id_seq |
| object_id | integer | NO | Foreign key to `object.object_id`. |
| reaction_id | integer | NO | Foreign key to `reaction.reaction_id`. |
| description | character varying(1000) | YES | Free-text description field. |
| reaction | character varying(3000) | NO | Reaction label or narrative (enzymology). |

**Primary Keys**: specific_reaction_id

**Sample Data**:
```json
{
  "description": "",
  "object_id": 2912,
  "reaction": "ATP + H(2)O &lt;=&gt; ADP + phosphate",
  "reaction_id": 389,
  "specific_reaction_id": 43
}
```
### 179. **specific_reaction_refs**
**Summary**: References for specific reaction entries.
**Purpose**: Links `specific_reaction` to `reference`.
**Size**: ~8 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **24 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| specific_reaction_id | integer | NO | Foreign key to `specific_reaction.specific_reaction_id`. |
| reference_id | integer | NO | Foreign key to `reference.reference_id`. |

**Primary Keys**: specific_reaction_id, reference_id

**Sample Data**:
```json
{
  "reference_id": 13426,
  "specific_reaction_id": 3
}
```
### 180. **structural_info**
**Summary**: Structural biology commentary (domains, folds, PDB overview).
**Purpose**: Long-form structure section for targets.
**Size**: ~9,047 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **3400 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| structural_info_id | integer | NO | Surrogate primary key. Default: sequence: structural_info_structural_info_id_seq |
| object_id | integer | NO | Foreign key to `object.object_id`. |
| species_id | integer | NO | Foreign key to `species.species_id`. |
| transmembrane_domains | integer | YES | Protein domain or modification notes. |
| amino_acids | integer | YES | Mutation or sequence representation (variant or protein). |
| pore_loops | integer | YES | Protein domain or modification notes. |
| genomic_location | character varying(50) | YES | Curated field in the IUPHAR/BPS Guide to PHARMACOLOGY database ([guidetopharmacology.org](https://www.guidetopharmacology.org/)); see the `structural_info` table and related target/ligand pages for context. |
| gene_name | character varying(100) | YES | Gene or protein naming for display and search. |
| official_gene_id | character varying(100) | YES | External database identifier for cross-referencing. |
| molecular_weight | integer | YES | Physicochemical descriptor (Lipinski / drug-likeness related). |
| gene_long_name | character varying(2000) | YES | Gene or protein naming for display and search. |
| gene_long_name_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search (see companion text column). |

**Primary Keys**: structural_info_id

**Sample Data**:
```json
{
  "amino_acids": 306,
  "gene_long_name": "",
  "gene_long_name_vector": "",
  "gene_name": "",
  "genomic_location": "",
  "molecular_weight": null,
  "object_id": 3111,
  "official_gene_id": "",
  "pore_loops": 0,
  "species_id": 125,
  "structural_info_id": 9911,
  "transmembrane_domains": 0
}
```
### 181. **structural_info_refs**
**Summary**: References for structural information text.
**Purpose**: Links `structural_info` to `reference`.
**Size**: ~1,996 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **168 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| structural_info_id | integer | NO | Foreign key to `structural_info.structural_info_id`. |
| reference_id | integer | NO | Foreign key to `reference.reference_id`. |

**Primary Keys**: structural_info_id, reference_id

**Sample Data**:
```json
{
  "reference_id": 1,
  "structural_info_id": 1
}
```
### 182. **subcommittee**
**Summary**: Subcommittees under NC-IUPHAR committees.
**Purpose**: Finer editorial structure for contributor assignment.
**Size**: ~603 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **88 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| contributor_id | integer | NO | Foreign key to `contributor.contributor_id`. |
| family_id | integer | NO | Foreign key to `family.family_id`. |
| role | character varying(50) | YES | Functional role label (e.g. agonist, antagonist in context). |
| display_order | integer | NO | Sort order for lists or navigation. |

**Primary Keys**: contributor_id, family_id

**Sample Data**:
```json
{
  "contributor_id": 1055,
  "display_order": 0,
  "family_id": 61,
  "role": null
}
```
### 183. **substrate**
**Summary**: Enzyme substrate commentary.
**Purpose**: Substrate specificity and reaction context for enzymes.
**Size**: ~1,015 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **312 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| substrate_id | integer | NO | Surrogate primary key. Default: sequence: substrate_substrate_id_seq |
| object_id | integer | NO | Foreign key to `object.object_id`. |
| species_id | integer | NO | Foreign key to `species.species_id`. |
| ligand_id | integer | YES | Foreign key to `ligand.ligand_id`. |
| property | character varying(20) | NO | Default: -::character varying |
| value | double precision | YES | Numeric or textual property value. |
| units | character varying(100) | YES | Screening assay value, unit, or activity readout. |
| assay_description | character varying(1000) | YES | Short assay description (binding, functional, …). |
| assay_conditions | character varying(1000) | YES | Buffer, temperature, co-factors, cell line, etc. |
| comments | character varying(1000) | YES | Free-text curator comments. |
| name | character varying(1000) | YES | Primary display name (target, ligand, family, etc.). |
| endogenous | boolean | NO | Default: true |
| in_iuphar | boolean | NO | Default: true |
| in_grac | boolean | NO | Default: false |
| standard_property | character varying(100) | YES | Default: -::character varying |
| standard_value | double precision | YES | Screening assay value, unit, or activity readout. |
| name_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search on `name`. |

**Primary Keys**: substrate_id

**Sample Data**:
```json
{
  "assay_conditions": null,
  "assay_description": null,
  "comments": null,
  "endogenous": false,
  "in_grac": true,
  "in_iuphar": false,
  "ligand_id": 4833,
  "name": null,
  "name_vector": null,
  "object_id": 1119,
  "property": "-",
  "species_id": 1,
  "standard_property": null,
  "standard_value": null,
  "substrate_id": 941,
  "units": null,
  "value": null
}
```
### 184. **substrate_refs**
**Summary**: References for substrate commentary.
**Purpose**: Links `substrate` to `reference`.
**Size**: ~627 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **80 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| substrate_id | integer | NO | Foreign key to `substrate.substrate_id`. |
| reference_id | integer | NO | Foreign key to `reference.reference_id`. |

**Primary Keys**: substrate_id, reference_id

**Sample Data**:
```json
{
  "reference_id": 13399,
  "substrate_id": 73
}
```
### 185. **synonym**
**Summary**: General synonym strings for targets, ligands, and diseases.
**Purpose**: Large vocabulary table for alternate spellings and names.
**Size**: ~31,019 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **7456 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| synonym_id | integer | NO | Surrogate primary key. Default: sequence: synonym_synonym_id_seq |
| object_id | integer | NO | Foreign key to `object.object_id`. |
| synonym | character varying(2000) | NO | Curated field in the IUPHAR/BPS Guide to PHARMACOLOGY database ([guidetopharmacology.org](https://www.guidetopharmacology.org/)); see the `synonym` table and related target/ligand pages for context. |
| display | boolean | NO | Default: true |
| from_grac | boolean | NO | Default: false |
| display_order | integer | NO | Default: 0 |
| synonym_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search (see companion text column). |

**Primary Keys**: synonym_id

**Sample Data**:
```json
{
  "display": false,
  "display_order": 0,
  "from_grac": false,
  "object_id": 220,
  "synonym": "s",
  "synonym_id": 21462,
  "synonym_vector": ""
}
```
### 186. **synonym_refs**
**Summary**: References for synonym entries.
**Purpose**: Links `synonym` to `reference`.
**Size**: ~162 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **24 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| synonym_id | integer | NO | Foreign key to `synonym.synonym_id`. |
| reference_id | integer | NO | Foreign key to `reference.reference_id`. |

**Primary Keys**: synonym_id, reference_id

**Sample Data**:
```json
{
  "reference_id": 86,
  "synonym_id": 2
}
```
### 187. **target_candidate_profile**
**Summary**: Candidate therapeutic target profiles (industry-style summaries).
**Purpose**: Brief profiles for prioritised targets.
**Size**: ~5 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **56 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| tcp_id | integer | NO | Surrogate primary key. Default: sequence: target_candidate_profile_tcp_id_seq |
| profile | character varying(50) | NO | Editorial teaser or overview text for a topic or contributor. |
| intended_use | character varying(500) | NO | Educational or editorial intended use statement. |
| target_stage | character varying(500) | NO | Curated field in the IUPHAR/BPS Guide to PHARMACOLOGY database ([guidetopharmacology.org](https://www.guidetopharmacology.org/)); see the `target_candidate_profile` table and related target/ligand pages for context. |
| profile_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search (see companion text column). |
| intended_use_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search (see companion text column). |
| target_stage_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search (see companion text column). |

**Primary Keys**: tcp_id

**Sample Data**:
```json
{
  "intended_use": "reduce parasite burden",
  "intended_use_vector": "'burden':3 'parasit':2 'reduc':1",
  "profile": "TCP-1",
  "profile_vector": "'-1':2 'tcp':1",
  "target_stage": "asexual blood stages",
  "target_stage_vector": "'asexu':1 'blood':2 'stage':3",
  "tcp_id": 1
}
```
### 188. **target_gene**
**Summary**: Gene-level targets and regulation for NHRs/signalling.
**Purpose**: Downstream genes regulated by the target (esp. nuclear receptors).
**Size**: ~259 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **232 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| target_gene_id | integer | NO | Surrogate primary key. Default: sequence: target_gene_target_gene_id_seq |
| object_id | integer | NO | Foreign key to `object.object_id`. |
| species_id | integer | NO | Foreign key to `species.species_id`. |
| description | character varying(1000) | YES | Free-text description field. |
| official_gene_id | character varying(100) | YES | External database identifier for cross-referencing. |
| effect | character varying(300) | YES | Described pharmacological or phenotypic effect. |
| technique | character varying(500) | YES | Experimental method (knockout, qPCR, microarray, …). |
| comments | character varying(2000) | YES | Free-text curator comments. |
| description_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search on `description`. |
| effect_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search (see companion text column). |
| technique_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search on `technique`. |
| comments_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search on `comments`. |

**Primary Keys**: target_gene_id

**Sample Data**:
```json
{
  "comments": "Angiogenesis and neovascularization",
  "comments_vector": "'angiogenesi':1 'neovascular':3",
  "description": "VEGFA",
  "description_vector": "'vegfa':1",
  "effect": "Activated",
  "effect_vector": "'activ':1",
  "object_id": 601,
  "official_gene_id": "12680",
  "species_id": 1,
  "target_gene_id": 107,
  "technique": "",
  "technique_vector": ""
}
```
### 189. **target_gene_refs**
**Summary**: References for target gene commentary.
**Purpose**: Links `target_gene` to `reference`.
**Size**: ~349 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **56 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| target_gene_id | integer | NO | Foreign key to `target_gene.target_gene_id`. |
| reference_id | integer | NO | Foreign key to `reference.reference_id`. |

**Primary Keys**: target_gene_id, reference_id

**Sample Data**:
```json
{
  "reference_id": 10198,
  "target_gene_id": 23
}
```
### 190. **target_ligand_same_entity**
**Summary**: Cases where target and ligand denote the same biological entity.
**Purpose**: Edge-case linking (e.g. peptide hormone as both).
**Size**: ~14 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **24 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| object_id | integer | NO | Foreign key to `object.object_id`. |
| ligand_id | integer | NO | Foreign key to `ligand.ligand_id`. |

**Primary Keys**: object_id, ligand_id

**Sample Data**:
```json
{
  "ligand_id": 3572,
  "object_id": 2348
}
```
### 191. **tissue**
**Summary**: Controlled tissue / organ vocabulary.
**Purpose**: Tissue terms for expression and localization.
**Size**: ~41 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **24 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| tissue_id | integer | NO | Surrogate primary key. Default: sequence: tissue_tissue_id_seq |
| name | character varying(100) | NO | Primary display name (target, ligand, family, etc.). |

**Primary Keys**: tissue_id

**Sample Data**:
```json
{
  "name": "Olfactory epithelium",
  "tissue_id": 1
}
```
### 192. **tissue_distribution**
**Summary**: Where targets are expressed (tissue-level narratives).
**Purpose**: Tissue distribution text per `object_id` and species.
**Size**: ~3,813 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **1944 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| tissue_distribution_id | integer | NO | Surrogate primary key. Default: sequence: tissue_distribution_tissue_distribution_id_seq |
| object_id | integer | NO | Foreign key to `object.object_id`. |
| tissues | character varying(10000) | NO | Tissue list or narrative for expression. |
| species_id | integer | NO | Foreign key to `species.species_id`. |
| technique | character varying(1000) | YES | Experimental method (knockout, qPCR, microarray, …). |
| expression_level | integer | YES | Curated field in the IUPHAR/BPS Guide to PHARMACOLOGY database ([guidetopharmacology.org](https://www.guidetopharmacology.org/)); see the `tissue_distribution` table and related target/ligand pages for context. |
| tissues_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search (see companion text column). |
| technique_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search on `technique`. |

**Primary Keys**: tissue_distribution_id

**Sample Data**:
```json
{
  "expression_level": 0,
  "object_id": 292,
  "species_id": 1,
  "technique": "RT-PCR.",
  "technique_vector": "'pcr':3 'rt':2 'rt-pcr':1",
  "tissue_distribution_id": 940,
  "tissues": "Testes.",
  "tissues_vector": "'test':1"
}
```
### 193. **tissue_distribution_refs**
**Summary**: References for tissue distribution statements.
**Purpose**: Links `tissue_distribution` to `reference`.
**Size**: ~5,140 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **352 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| tissue_distribution_id | integer | NO | Foreign key to `tissue_distribution.tissue_distribution_id`. |
| reference_id | integer | NO | Foreign key to `reference.reference_id`. |

**Primary Keys**: tissue_distribution_id, reference_id

**Sample Data**:
```json
{
  "reference_id": 2,
  "tissue_distribution_id": 1
}
```
### 194. **tocris_update**
**Summary**: Tocris (Bio-Techne) catalog update snapshots.
**Purpose**: Supplier batch updates for commercial ligand tooling.
**Size**: ~4,073 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **1016 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| cat_no | character varying(100) | YES | Commercial catalog or product code (DiscoverX, MCE, …). |
| url | character varying(500) | YES | HTTP(S) link for external resources or Immunopaedia pages. |
| name | character varying(1000) | YES | Primary display name (target, ligand, family, etc.). |
| smiles | character varying(2000) | YES | SMILES line notation for the structure (may include salts). |
| pubchem_cid | character varying(100) | YES | External database identifier for cross-referencing. |
| inchi | character varying(200) | YES | Structure representation (SMILES, InChI, HELM) for integration. |
| cas | character varying(100) | YES | Chemical Abstracts Service registry number. |

**Primary Keys**: *None identified*

**Sample Data**:
```json
{
  "cas": "6323-99-5",
  "cat_no": "0101",
  "inchi": "DDOQBQRIEWHWBT-UHFFFAOYSA-N",
  "name": "DL-AP4",
  "pubchem_cid": "2207",
  "smiles": "O=C(C(N)CCP(O)(O)=O)O",
  "url": "https://www.tocris.com/products/dl-ap4_0101"
}
```
### 195. **transduction**
**Summary**: Signal transduction mechanisms (G proteins, β-arrestin, etc.).
**Purpose**: Downstream signalling text for receptors.
**Size**: ~418 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **480 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| transduction_id | integer | NO | Surrogate primary key. Default: sequence: transduction_transduction_id_seq |
| object_id | integer | NO | Foreign key to `object.object_id`. |
| secondary | boolean | NO | Secondary catalogue or alternate naming for commercial ligands. |
| t01 | boolean | NO | Default: false |
| t02 | boolean | NO | Default: false |
| t03 | boolean | NO | Default: false |
| t04 | boolean | NO | Default: false |
| t05 | boolean | NO | Default: false |
| t06 | boolean | NO | Default: false |
| e01 | boolean | NO | Default: false |
| e02 | boolean | NO | Default: false |
| e03 | boolean | NO | Default: false |
| e04 | boolean | NO | Default: false |
| e05 | boolean | NO | Default: false |
| e06 | boolean | NO | Default: false |
| e07 | boolean | NO | Default: false |
| e08 | boolean | NO | Default: false |
| e09 | boolean | NO | Default: false |
| comments | character varying(10000) | YES | Free-text curator comments. |
| comments_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search on `comments`. |

**Primary Keys**: transduction_id

**Sample Data**:
```json
{
  "comments": null,
  "comments_vector": null,
  "e01": true,
  "e02": false,
  "e03": false,
  "e04": false,
  "e05": false,
  "e06": false,
  "e07": false,
  "e08": false,
  "e09": false,
  "object_id": 327,
  "secondary": true,
  "t01": true,
  "t02": false,
  "t03": false,
  "t04": false,
  "t05": false,
  "t06": false,
  "transduction_id": 237
}
```
### 196. **transduction_refs**
**Summary**: References for transduction commentary.
**Purpose**: Links `transduction` to `reference`.
**Size**: ~973 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **104 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| transduction_id | integer | NO | Foreign key to `transduction.transduction_id`. |
| reference_id | integer | NO | Foreign key to `reference.reference_id`. |

**Primary Keys**: transduction_id, reference_id

**Sample Data**:
```json
{
  "reference_id": 3,
  "transduction_id": 1
}
```
### 197. **transporter**
**Summary**: Transporter-class specific commentary.
**Purpose**: SLC/ABC transporter blocks per `object_id`.
**Size**: ~557 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **128 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| object_id | integer | NO | Foreign key to `object.object_id`. |
| grac_stoichiometry | character varying(1000) | YES | GRAC stoichiometry narrative for receptor complexes. |
| grac_stoichiometry_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search (see companion text column). |

**Primary Keys**: object_id

**Sample Data**:
```json
{
  "grac_stoichiometry": null,
  "grac_stoichiometry_vector": null,
  "object_id": 758
}
```
### 198. **variant**
**Summary**: Genetic variants affecting drug response or protein function.
**Purpose**: Variant annotations with clinical/pharmacogenomic notes.
**Size**: ~977 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **848 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| variant_id | integer | NO | Surrogate primary key. Default: sequence: variant_variant_id_seq |
| object_id | integer | NO | Foreign key to `object.object_id`. |
| description | character varying(2000) | YES | Free-text description field. |
| type | character varying(100) | YES | Controlled type label (ligand class, interaction type, etc.). |
| species_id | integer | NO | Foreign key to `species.species_id`. |
| amino_acids | integer | YES | Mutation or sequence representation (variant or protein). |
| amino_acid_change | character varying(500) | YES | Mutation or sequence representation (variant or protein). |
| validation | character varying(1000) | YES | Validation status for a mapping or submission. |
| global_maf | character varying(100) | YES | Population allele frequency metadata (variant tables). |
| subpop_maf | character varying(1000) | YES | Population allele frequency metadata (variant tables). |
| minor_allele_count | character varying(500) | YES | Population allele frequency metadata (variant tables). |
| frequency_comment | character varying(1000) | YES | Curator prose for the `frequency` section on the portal. |
| nucleotide_change | character varying(500) | YES | Mutation or sequence representation (variant or protein). |
| description_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search on `description`. |

**Primary Keys**: variant_id

**Sample Data**:
```json
{
  "amino_acid_change": "",
  "amino_acids": 372,
  "description": "",
  "description_vector": "",
  "frequency_comment": "",
  "global_maf": "",
  "minor_allele_count": "",
  "nucleotide_change": null,
  "object_id": 429,
  "species_id": 3,
  "subpop_maf": "",
  "type": "Splice variant",
  "validation": "",
  "variant_id": 1018
}
```
### 199. **variant2database_link**
**Summary**: External variant IDs (ClinVar, dbSNP…).
**Purpose**: Cross-references for `variant` rows.
**Size**: ~921 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **112 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| variant_id | integer | NO | Foreign key to `variant.variant_id`. |
| database_link_id | integer | NO | Foreign key to `database_link.database_link_id`. |
| type | character varying(50) | NO | Controlled type label (ligand class, interaction type, etc.). |

**Primary Keys**: variant_id, database_link_id

**Sample Data**:
```json
{
  "database_link_id": 6697,
  "type": "protein",
  "variant_id": 273
}
```
### 200. **variant_refs**
**Summary**: References for variant entries.
**Purpose**: Links `variant` to `reference`.
**Size**: ~1,232 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **152 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| variant_id | integer | NO | Foreign key to `variant.variant_id`. |
| reference_id | integer | NO | Foreign key to `reference.reference_id`. |

**Primary Keys**: variant_id, reference_id

**Sample Data**:
```json
{
  "reference_id": 1548,
  "variant_id": 45
}
```
### 201. **version**
**Summary**: Database release version metadata.
**Purpose**: Tracks GtoPdb release numbers (e.g. 2026.1) for reproducibility.
**Size**: ~1 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **24 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| version_number | character varying(100) | NO | Software or content version number. |
| publish_date | date | YES | Publication, access, or modification date. |

**Primary Keys**: version_number

**Sample Data**:
```json
{
  "publish_date": "2025-06-18",
  "version_number": "2025.2"
}
```
### 202. **vgic**
**Summary**: Voltage-gated ion channel specific fields.
**Purpose**: VGIC gating and auxiliary subunit commentary per target.
**Size**: ~145 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **80 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| object_id | integer | NO | Foreign key to `object.object_id`. |
| physiological_ion | character varying(100) | YES | Permeant ion species for channel conductance. |
| selectivity_comments | text | YES | Curator prose for the `selectivity` section on the portal. |
| voltage_dependence_comments | text | YES | Curator prose for the `voltage_dependence` section on the portal. |

**Primary Keys**: object_id

**Sample Data**:
```json
{
  "object_id": 397,
  "physiological_ion": "See comments below",
  "selectivity_comments": "",
  "voltage_dependence_comments": ""
}
```
### 203. **voltage_dep_activation_refs**
**Summary**: References for voltage-dependent activation curves.
**Purpose**: Citations for activation gating data.
**Size**: ~224 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **24 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| voltage_dependence_id | integer | NO | Foreign key to `voltage_dependence.voltage_dependence_id`. |
| reference_id | integer | NO | Foreign key to `reference.reference_id`. |

**Primary Keys**: voltage_dependence_id, reference_id

**Sample Data**:
```json
{
  "reference_id": 7968,
  "voltage_dependence_id": 3
}
```
### 204. **voltage_dep_deactivation_refs**
**Summary**: References for voltage-dependent deactivation.
**Purpose**: Citations for deactivation gating data.
**Size**: ~10 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **24 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| voltage_dependence_id | integer | NO | Foreign key to `voltage_dependence.voltage_dependence_id`. |
| reference_id | integer | NO | Foreign key to `reference.reference_id`. |

**Primary Keys**: voltage_dependence_id, reference_id

**Sample Data**:
```json
{
  "reference_id": 9802,
  "voltage_dependence_id": 116
}
```
### 205. **voltage_dep_inactivation_refs**
**Summary**: References for voltage-dependent inactivation.
**Purpose**: Citations for inactivation gating data.
**Size**: ~132 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **24 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| voltage_dependence_id | integer | NO | Foreign key to `voltage_dependence.voltage_dependence_id`. |
| reference_id | integer | NO | Foreign key to `reference.reference_id`. |

**Primary Keys**: voltage_dependence_id, reference_id

**Sample Data**:
```json
{
  "reference_id": 8582,
  "voltage_dependence_id": 18
}
```
### 206. **voltage_dependence**
**Summary**: Voltage-dependence parameters for ion channels.
**Purpose**: V½, slope factors, and narrative for channel gating.
**Size**: ~172 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **136 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| voltage_dependence_id | integer | NO | Surrogate primary key. Default: sequence: voltage_dependence_voltage_dependence_id_seq |
| object_id | integer | NO | Foreign key to `object.object_id`. |
| cell_type | character varying(500) | NO | Cell type label (expression or immunology context). |
| comments | text | YES | Free-text curator comments. |
| activation_v_high | double precision | YES | Ion channel gating parameter (voltage V or time/temperature T dependence). |
| activation_v_median | double precision | YES | Ion channel gating parameter (voltage V or time/temperature T dependence). |
| activation_v_low | double precision | YES | Ion channel gating parameter (voltage V or time/temperature T dependence). |
| activation_t_high | double precision | YES | Ion channel gating parameter (voltage V or time/temperature T dependence). |
| activation_t_low | double precision | YES | Ion channel gating parameter (voltage V or time/temperature T dependence). |
| inactivation_v_high | double precision | YES | Ion channel gating parameter (voltage V or time/temperature T dependence). |
| inactivation_v_median | double precision | YES | Ion channel gating parameter (voltage V or time/temperature T dependence). |
| inactivation_v_low | double precision | YES | Ion channel gating parameter (voltage V or time/temperature T dependence). |
| inactivation_t_high | double precision | YES | Ion channel gating parameter (voltage V or time/temperature T dependence). |
| inactivation_t_low | double precision | YES | Ion channel gating parameter (voltage V or time/temperature T dependence). |
| deactivation_v_high | double precision | YES | Ion channel gating parameter (voltage V or time/temperature T dependence). |
| deactivation_v_median | double precision | YES | Ion channel gating parameter (voltage V or time/temperature T dependence). |
| deactivation_v_low | double precision | YES | Ion channel gating parameter (voltage V or time/temperature T dependence). |
| deactivation_t_high | double precision | YES | Ion channel gating parameter (voltage V or time/temperature T dependence). |
| deactivation_t_low | double precision | YES | Ion channel gating parameter (voltage V or time/temperature T dependence). |
| species_id | integer | NO | Foreign key to `species.species_id`. |
| cell_type_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search (see companion text column). |
| comments_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search on `comments`. |

**Primary Keys**: voltage_dependence_id

**Sample Data**:
```json
{
  "activation_t_high": null,
  "activation_t_low": null,
  "activation_v_high": -46,
  "activation_v_low": -48,
  "activation_v_median": null,
  "cell_type": "DRG neurons",
  "cell_type_vector": "'drg':1 'neuron':2",
  "comments": "",
  "comments_vector": "",
  "deactivation_t_high": null,
  "deactivation_t_low": null,
  "deactivation_v_high": null,
  "deactivation_v_low": null,
  "deactivation_v_median": null,
  "inactivation_t_high": 47,
  "inactivation_t_low": 39,
  "inactivation_v_high": -43,
  "inactivation_v_low": -45,
  "inactivation_v_median": null,
  "object_id": 586,
  "species_id": 2,
  "voltage_dependence_id": 174
}
```
### 207. **xenobiotic_expression**
**Summary**: Expression changes induced by drugs or xenobiotics.
**Purpose**: Contrasts with `altered_expression`; focuses on chemical induction.
**Size**: ~78 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **120 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| xenobiotic_expression_id | integer | NO | Surrogate primary key. Default: sequence: xenobiotic_expression_xenobiotic_expression_id_seq |
| object_id | integer | NO | Foreign key to `object.object_id`. |
| change | character varying(2000) | YES | Narrative of the measured change (expression, phenotype, or assay readout vs baseline). |
| technique | character varying(500) | YES | Experimental method (knockout, qPCR, microarray, …). |
| tissue | character varying(1000) | YES | Tissue or organ context for expression data. |
| species_id | integer | NO | Foreign key to `species.species_id`. |
| change_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search (see companion text column). |
| tissue_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search on `tissue`. |
| technique_vector | tsvector | YES | PostgreSQL `tsvector` for full-text search on `technique`. |

**Primary Keys**: xenobiotic_expression_id

**Sample Data**:
```json
{
  "change": "~ 2 fold increase of transcription upon treatment with cycloleucin, an inhibitor of methionine adenosyltransferase",
  "change_vector": "'2':1 'adenosyltransferas':14 'cycloleucin':9 'fold':2 'increas':3 'inhibitor':11 'methionin':13 'transcript':5 'treatment':7 'upon':6",
  "object_id": 189,
  "species_id": 1,
  "technique": "Microarray",
  "technique_vector": "'microarray':1",
  "tissue": "Lymphoblasts",
  "tissue_vector": "'lymphoblast':1",
  "xenobiotic_expression_id": 5
}
```
### 208. **xenobiotic_expression_refs**
**Summary**: References for xenobiotic expression statements.
**Purpose**: Links `xenobiotic_expression` to `reference`.
**Size**: ~90 rows (PostgreSQL `pg_class.reltuples` estimate); total on-disk **24 kB** (`pg_total_relation_size`, includes heap, indexes, and TOAST).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| xenobiotic_expression_id | integer | NO | Foreign key to `xenobiotic_expression.xenobiotic_expression_id`. |
| reference_id | integer | NO | Foreign key to `reference.reference_id`. |

**Primary Keys**: xenobiotic_expression_id, reference_id

**Sample Data**:
```json
{
  "reference_id": 19601,
  "xenobiotic_expression_id": 5
}
```

## Primary Keys Summary

*Primary keys have been identified for each table in the individual table sections above.*

## Foreign Key Relationships

Foreign key relationships in this database appear to be primarily logical (based on column naming patterns) rather than formally defined constraints. Common relationship patterns observed:

- **Reference tables**: Many tables have `*_refs` companion tables linking to a `reference` table via `reference_id`
- **Object relationships**: Many tables reference the main `object` table via `object_id`
- **Ligand relationships**: Tables link to `ligand` table via `ligand_id`
- **Family relationships**: Tables link to `family` table via `family_id`

## Data Flow Architecture

The Guide2Pharma database follows a hub-and-spoke architecture:

```
Core Entities:
├── object (receptors, proteins, etc.)
├── ligand (drugs, compounds)
├── family (protein families)
├── reference (citations, publications)
└── species (biological species)

Relationship Tables:
├── *_refs tables (link entities to references)
├── *2* tables (many-to-many relationships)
└── *_isa tables (hierarchical relationships)
```

## Key Relationships

### Core Entity Relationships
- **object**: Central table for receptors, proteins, and other molecular entities
- **ligand**: Central table for drugs, compounds, and ligands
- **family**: Protein family classifications
- **reference**: Citations and publications
- **species**: Biological species information

### Common Relationship Patterns
1. **Reference Linking**: Most entity tables have companion `*_refs` tables for citations
2. **Many-to-Many**: `*2*` tables connect entities (e.g., `ligand2family`, `drug2disease`)
3. **Hierarchical**: `*_isa` tables represent parent-child relationships
4. **Clustering**: Tables like `analogue_cluster`, `chembl_cluster` group related entities

## Validation Methodology & Results Summary

### Validation Approach
This schema reference was generated using the MCP Toolbox with the `guide2pharma-readonly` connection. Schema information was extracted using:
- `pg_tables` for table enumeration
- `pg_catalog.pg_attribute` for column information
- `pg_index` for primary key identification

### Key Validation Results
| Validation Type | Status | Details |
|----------------|--------|---------|
| **Primary Keys** | ✅ **Identified** | Primary keys found for all documented tables |
| **Foreign Key Constraints** | ⚠️ **Not formally defined** | Relationships appear to be logical based on column names |
| **Data Volume** | ✅ **Populated** | Row estimates from `pg_class.reltuples` and on-disk sizes from `pg_total_relation_size` (see per-table **Size**) |
| **Join Relationships** | ✅ **Logical patterns identified** | Common relationship patterns documented |

### Critical Findings
1. **Well-structured schema**: Clear naming conventions and relationship patterns
2. **Reference system**: Comprehensive citation system via `*_refs` tables
3. **Flexible relationships**: Many-to-many relationships well-supported
4. **Hierarchical data**: ISA relationships for taxonomies and classifications

## Validation Date
*Schema doc text generated April 5, 2026; sizes queried live from PostgreSQL (`pg_class`, `pg_total_relation_size`).*

---

**Note**: This document was automatically generated. Column descriptions and table purposes should be reviewed and enhanced with domain knowledge from the Guide2Pharma project.
