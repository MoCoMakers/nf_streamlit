# ChEMBL 37 Schema Reference

## Overview

ChEMBL is a manually curated bioactivity database maintained by the European Bioinformatics Institute (EMBL-EBI). It contains binding, functional, and ADMET bioactivity data for drug-like molecules, along with curated drug and target information sourced from the scientific literature, FDA/EMA approvals, and partner databases.

**Version:** ChEMBL 37 (release date 2026-05-01)
**Total tables:** 70
**Schema location:** Foreign schema `chembl` inside the `data_warehouse` PostgreSQL database (accessed via `postgres_fdw`)
**Primary use case for this project:** Enriching NCI-60 compound data with drug names, synonyms, mechanism of action (MOA), ATC drug classes, and therapeutic indications.

---

## Table Index

| Table | Row Count | One-line Summary |
|---|---|---|
| `action_type` | 35 | Lookup: controlled vocabulary for drug action types (e.g., INHIBITOR, AGONIST) |
| `activities` | 24,527,044 | Core bioactivity measurements linking compounds to assays (IC50, Ki, etc.) |
| `activity_properties` | 12,213,211 | Supplementary properties for individual activity records |
| `activity_smid` | 1,732,478 | Maps activities to supplementary measurement groups |
| `activity_stds_lookup` | 151 | Lookup: standard activity types and their units |
| `activity_supp` | 1,776,415 | Supplementary measurement data for activities |
| `activity_supp_map` | 2,010,125 | Maps supplementary measurements to activity records |
| `assay_class_map` | 244,490 | Maps assays to assay classification categories |
| `assay_classification` | 584 | Hierarchical classification of assay types (e.g., panel, kinase) |
| `assay_parameters` | 460,048 | Experimental parameters associated with specific assays |
| `assay_type` | 6 | Lookup: assay type codes (B=Binding, F=Functional, A=ADME, etc.) |
| `assays` | 1,970,438 | Assay metadata including target, organism, and source publication |
| `atc_classification` | 5,579 | WHO ATC drug classification hierarchy (5 levels) |
| `binding_sites` | 4,545 | Named binding sites on targets |
| `bio_component_sequences` | 3,478 | Sequences for components of biotherapeutic molecules |
| `bioassay_ontology` | 311 | BioAssay Ontology (BAO) term lookup |
| `biotherapeutic_components` | 4,415 | Links biotherapeutics to their sequence components |
| `biotherapeutics` | 23,849 | Biotherapeutic molecules with HELM notation |
| `cell_dictionary` | 2,238 | Cell line registry with ontology cross-references |
| `chembl_id_lookup` | 5,478,952 | Global lookup mapping ChEMBL IDs to entity type and internal ID |
| `chembl_release` | 37 | ChEMBL release version history |
| `component_class` | 13,180 | Maps protein components to protein classification hierarchy |
| `component_domains` | 28,547 | Maps protein components to structural domains |
| `component_go` | 153,709 | Maps protein components to Gene Ontology terms |
| `component_sequences` | 12,986 | UniProt protein and nucleic acid sequences for target components |
| `component_synonyms` | 121,157 | Synonyms and identifiers for protein components (gene symbols, etc.) |
| `compound_properties` | 2,901,464 | Calculated physicochemical properties (MW, LogP, HBD, PSA, Ro5 violations) |
| `compound_records` | 3,824,604 | Individual compound-document associations with source identifiers |
| `compound_structural_alerts` | 5,020,133 | SMARTS-based structural alert matches for compounds |
| `compound_structures` | 2,897,819 | Chemical structures: SMILES, InChI, InChIKey, molfile |
| `confidence_score_lookup` | 10 | Lookup: target assignment confidence score definitions (0–9) |
| `data_validity_lookup` | 7 | Lookup: data validity comment codes |
| `defined_daily_dose` | 2,721 | WHO-defined daily doses by ATC code |
| `docs` | 101,100 | Literature references and patent documents |
| `domains` | 3,953 | Protein domain definitions (Pfam, etc.) |
| `drug_indication` | 60,055 | Approved and investigational drug indications with MeSH/EFO terms |
| `drug_mechanism` | 7,561 | Curated mechanism of action per drug-target pair |
| `drug_warning` | 2,304 | Regulatory safety warnings (black box, withdrawn) |
| `formulations` | 53,430 | Links approved products to their active ingredients |
| `go_classification` | 309 | Subset of Gene Ontology terms used for protein classification |
| `indication_refs` | 93,733 | Source references for drug indications (FDA, EMA, ClinicalTrials) |
| `ligand_eff` | 2,223,169 | Ligand efficiency metrics for activity records (LE, BEI, SEI, LLE) |
| `mechanism_refs` | 13,600 | Source references for drug mechanism records |
| `metabolism` | 2,147 | Drug metabolism pathways (substrate-metabolite-enzyme) |
| `metabolism_refs` | 3,296 | Source references for metabolism records |
| `molecule_atc_classification` | 4,567 | Maps molecules to ATC classification level-5 codes |
| `molecule_dictionary` | 2,921,148 | Master compound registry with ChEMBL ID, approval status, and flags |
| `molecule_hierarchy` | 2,828,129 | Parent-child-active molecule relationships for salt/prodrug handling |
| `molecule_synonyms` | 136,061 | Drug names and synonyms (INN, trade, research codes) |
| `organism_class` | 4,280 | Taxonomic organism classification hierarchy |
| `patent_use_codes` | 4,043 | FDA patent use code definitions |
| `pesticide_class_mapping` | 593 | Maps molecules to pesticide classification |
| `pesticide_classification` | 595 | Pesticide classification hierarchy |
| `predicted_binding_domains` | 822,313 | Predicted binding domain for each activity record |
| `product_patents` | 19,705 | Patent information for approved drug products |
| `products` | 45,752 | FDA-approved drug product registry (NDA, trade names) |
| `protein_classification` | 905 | Hierarchical ChEMBL protein family classification tree |
| `relationship_type` | 6 | Lookup: assay-to-target relationship type codes |
| `site_components` | 5,908 | Links binding sites to protein components and domains |
| `source` | 67 | Data source registry (literature, GSK, FDA, etc.) |
| `structural_alert_sets` | 5 | Named sets of structural alerts (e.g., PAINS, Dundee) |
| `structural_alerts` | 936 | SMARTS patterns defining structural alerts |
| `target_components` | 17,284 | Links targets to their protein/nucleic acid components |
| `target_dictionary` | 18,552 | Target registry with type, organism, and ChEMBL ID |
| `target_relations` | 155,208 | Hierarchical relationships between targets (SUBSET OF, SUPERSET OF) |
| `target_type` | 28 | Lookup: target type definitions (SINGLE PROTEIN, CELL-LINE, etc.) |
| `tissue_dictionary` | 791 | Tissue/organ registry with UBERON, BTO, EFO cross-references |
| `usan_stems` | 834 | USAN drug name stem definitions and annotations |
| `variant_sequences` | 2,836 | Mutant/variant protein sequences used in assays |
| `version` | 11 | ChEMBL release version history and component versioning |
| `warning_refs` | 4,946 | Source references for drug warning records |

---

## Detailed Table Sections

---

### `molecule_dictionary` ★ Priority

**Purpose:** The master registry for all compounds in ChEMBL. Every small molecule, biotherapeutic, and other entity has one row here, identified by both an internal `molregno` and a public `chembl_id`. Carries high-level flags for approval status, molecule type, and regulatory annotations.

**Row count:** 2,921,148

| Column | Data Type | Nullable | Description |
|---|---|---|---|
| `molregno` | bigint | NO | Internal primary key for the molecule |
| `pref_name` | varchar | YES | Preferred name (usually INN or USAN); NULL for unapproved compounds |
| `chembl_id` | varchar | NO | Public identifier, e.g., CHEMBL2 |
| `max_phase` | numeric | YES | Highest clinical development phase (4 = approved) |
| `therapeutic_flag` | smallint | NO | 1 if compound has confirmed therapeutic use |
| `dosed_ingredient` | smallint | NO | 1 if used as a dosed ingredient in a drug product |
| `structure_type` | varchar | NO | MOL, SEQ, NONE, etc. |
| `molecule_type` | varchar | YES | Small molecule, Protein, Antibody, Oligonucleotide, etc. |
| `first_approval` | integer | YES | Year of first regulatory approval |
| `oral` | smallint | NO | 1 if administered orally |
| `parenteral` | smallint | NO | 1 if administered parenterally |
| `topical` | smallint | NO | 1 if administered topically |
| `black_box_warning` | smallint | NO | 1 if carries an FDA black box warning |
| `natural_product` | smallint | NO | 1 if derived from a natural product |
| `first_in_class` | smallint | NO | 1 if first-in-class drug |
| `chirality` | smallint | NO | 0=unknown, 1=racemic, 2=single stereoisomer |
| `prodrug` | smallint | NO | 1 if a prodrug |
| `inorganic_flag` | smallint | NO | 1 if inorganic compound |
| `usan_year` | integer | YES | Year the USAN name was assigned |
| `availability_type` | smallint | YES | -1=unknown, 0=discontinued, 1=prescription, 2=OTC |
| `usan_stem` | varchar | YES | USAN stem for this compound |
| `polymer_flag` | smallint | YES | 1 if a polymer |
| `usan_substem` | varchar | YES | USAN substem |
| `usan_stem_definition` | varchar | YES | Definition of the USAN stem |
| `withdrawn_flag` | smallint | NO | 1 if withdrawn from market |
| `chemical_probe` | smallint | NO | 1 if designated as a chemical probe |
| `orphan` | smallint | NO | 1 if orphan drug designation |
| `veterinary` | smallint | YES | 1 if approved for veterinary use |

**Key relationships:**
- `molregno` is the universal join key; referenced by `compound_structures`, `compound_properties`, `molecule_synonyms`, `molecule_hierarchy`, `molecule_atc_classification`, `drug_mechanism`, `drug_indication`, `activities`, `compound_records`, etc.
- Join to `compound_structures` on `molregno` for SMILES/InChI
- Join to `molecule_synonyms` on `molregno` for drug names
- Filter `max_phase = 4` for approved drugs; `max_phase >= 1` for clinical candidates

**Sample data:**

| molregno | chembl_id | pref_name | max_phase | molecule_type | first_approval | withdrawn_flag |
|---|---|---|---|---|---|---|
| 97 | CHEMBL2 | PRAZOSIN | 4 | Small molecule | 1976 | 0 |
| 115 | CHEMBL3 | NICOTINE | 4 | Small molecule | 1984 | 0 |
| 116 | CHEMBL6200 | NORNICOTINE | 1 | Small molecule | NULL | 0 |

---

### `molecule_synonyms` ★ Priority

**Purpose:** Stores all known names and identifiers for each compound, including INN names, trade names, research codes, and CAS numbers. Critical for matching NCI-60 NSC compound names to ChEMBL records.

**Row count:** 136,061

| Column | Data Type | Nullable | Description |
|---|---|---|---|
| `molregno` | bigint | NO | FK to `molecule_dictionary` |
| `syn_type` | varchar | NO | Type of synonym: INN, TRADE_NAME, RESEARCH_CODE, USAN, CAS, FDA, BAN, JAN, etc. |
| `molsyn_id` | bigint | NO | Primary key for this synonym record |
| `synonyms` | varchar | YES | The synonym text |

**Key relationships:**
- Join to `molecule_dictionary` on `molregno`
- Filter by `syn_type` to narrow to specific name types (e.g., `syn_type = 'INN'` for international non-proprietary names)

**Sample data:**

| molregno | molsyn_id | syn_type | synonyms |
|---|---|---|---|
| 463 | 93 | RESEARCH_CODE | Ro-481220 |
| 634 | 119 | RESEARCH_CODE | Ro-151310 |
| 868 | 194 | RESEARCH_CODE | Ro-147437 |

---

### `compound_structures` ★ Priority

**Purpose:** Stores chemical structure representations for each compound: SMILES, InChI, InChIKey, and MDL molfile. The `standard_inchi_key` is useful as a universal structure-based identifier for cross-database matching.

**Row count:** 2,897,819

| Column | Data Type | Nullable | Description |
|---|---|---|---|
| `molregno` | bigint | NO | FK to `molecule_dictionary` (also PK) |
| `molfile` | text | YES | MDL/SDF V2000 structure block |
| `standard_inchi` | varchar | YES | IUPAC Standard InChI string |
| `standard_inchi_key` | varchar | NO | 27-character hashed InChI key (e.g., OWRSAHYFSSNENM-UHFFFAOYSA-N) |
| `canonical_smiles` | varchar | YES | RDKit-canonicalized SMILES string |

**Key relationships:**
- Join to `molecule_dictionary` on `molregno`
- `standard_inchi_key` can be used to match against PubChem, DrugBank, etc.

**Sample data:**

| molregno | standard_inchi_key | canonical_smiles |
|---|---|---|
| 1 | OWRSAHYFSSNENM-UHFFFAOYSA-N | `Cc1cc(-n2ncc(=O)[nH]c2=O)ccc1C(=O)c1ccccc1Cl` |
| 2 | ZJYUMURGSZQFMH-UHFFFAOYSA-N | `Cc1cc(-n2ncc(=O)[nH]c2=O)ccc1C(=O)c1ccc(C#N)cc1` |

---

### `compound_properties` ★ Priority

**Purpose:** Contains calculated physicochemical properties for each compound, including Lipinski Rule-of-Five descriptors, topological polar surface area (PSA), QED drug-likeness score, and natural product likeness.

**Row count:** 2,901,464

| Column | Data Type | Nullable | Description |
|---|---|---|---|
| `molregno` | bigint | NO | FK to `molecule_dictionary` (also PK) |
| `mw_freebase` | numeric | YES | Molecular weight of the freebase form |
| `alogp` | numeric | YES | Calculated ALogP (octanol-water partition coefficient) |
| `hba` | integer | YES | Number of hydrogen bond acceptors |
| `hbd` | integer | YES | Number of hydrogen bond donors |
| `psa` | numeric | YES | Topological polar surface area (Ų) |
| `rtb` | integer | YES | Number of rotatable bonds |
| `ro3_pass` | varchar | YES | Y if passes Ro3 fragment-likeness criteria |
| `num_ro5_violations` | smallint | YES | Number of Lipinski Rule-of-Five violations (0–4) |
| `full_mwt` | numeric | YES | Full molecular weight including salt/counterion |
| `aromatic_rings` | integer | YES | Number of aromatic rings |
| `heavy_atoms` | integer | YES | Number of heavy (non-hydrogen) atoms |
| `qed_weighted` | numeric | YES | Weighted quantitative estimate of drug-likeness (0–1) |
| `full_molformula` | varchar | YES | Molecular formula including salt form |
| `np_likeness_score` | numeric | YES | Natural product likeness score |

**Key relationships:**
- Join to `molecule_dictionary` on `molregno`
- Filter `num_ro5_violations = 0` for drug-like compounds

**Sample data:**

| molregno | mw_freebase | alogp | hba | hbd | psa | num_ro5_violations | qed_weighted | full_molformula |
|---|---|---|---|---|---|---|---|---|
| 1 | 341.75 | 2.11 | 5 | 1 | 84.82 | 0 | 0.74 | C17H12ClN3O3 |
| 2 | 332.32 | 1.33 | 6 | 1 | 108.61 | 0 | 0.73 | C18H12N4O3 |

---

### `drug_mechanism` ★ Priority

**Purpose:** Curated mechanism of action (MOA) for approved drugs and clinical candidates. Describes how a drug acts on its primary target, including the action type (inhibitor, agonist, etc.) and whether the interaction is direct.

**Row count:** 7,561

| Column | Data Type | Nullable | Description |
|---|---|---|---|
| `mec_id` | bigint | NO | Primary key |
| `record_id` | bigint | NO | FK to `compound_records` |
| `molregno` | bigint | YES | FK to `molecule_dictionary` |
| `mechanism_of_action` | varchar | YES | Free-text MOA description, e.g., "Carbonic anhydrase VII inhibitor" |
| `tid` | bigint | YES | FK to `target_dictionary` (the primary target) |
| `site_id` | bigint | YES | FK to `binding_sites` (specific binding site if known) |
| `action_type` | varchar | YES | Controlled vocabulary: INHIBITOR, AGONIST, ANTAGONIST, etc. |
| `direct_interaction` | smallint | YES | 1 if direct drug-target interaction (not downstream) |
| `molecular_mechanism` | smallint | YES | 1 if the MOA is at the molecular level |
| `disease_efficacy` | smallint | YES | 1 if this mechanism underlies therapeutic efficacy |
| `mechanism_comment` | varchar | YES | Free-text annotation or qualification |
| `selectivity_comment` | varchar | YES | Notes on target selectivity |
| `binding_site_comment` | varchar | YES | Notes on the binding site |
| `variant_id` | bigint | YES | FK to `variant_sequences` if MOA is variant-specific |

**Key relationships:**
- Join to `molecule_dictionary` on `molregno` to link compound names
- Join to `target_dictionary` on `tid` to get target names and gene info
- Join to `mechanism_refs` on `mec_id` to get source publications
- Join to `action_type` on `action_type` for descriptions

**Sample data:**

| mec_id | molregno | mechanism_of_action | tid | action_type | direct_interaction | disease_efficacy |
|---|---|---|---|---|---|---|
| 13 | 1124 | Carbonic anhydrase VII inhibitor | 11060 | INHIBITOR | 1 | 1 |
| 14 | 675068 | Carbonic anhydrase I inhibitor | 10193 | INHIBITOR | 1 | 1 |
| 15 | 674765 | Carbonic anhydrase I inhibitor | 10193 | INHIBITOR | 1 | 1 |

---

### `target_dictionary` ★ Priority

**Purpose:** Registry of all biological targets in ChEMBL, including single proteins, protein complexes, cell lines, organisms, and other entity types. Provides the link between bioactivity data and gene/protein information.

**Row count:** 18,552

| Column | Data Type | Nullable | Description |
|---|---|---|---|
| `tid` | bigint | NO | Internal primary key for target |
| `target_type` | varchar | YES | Type of target: SINGLE PROTEIN, PROTEIN COMPLEX, CELL-LINE, etc. |
| `pref_name` | varchar | NO | Preferred name (e.g., "cGMP-specific 3',5'-cyclic phosphodiesterase") |
| `tax_id` | bigint | YES | NCBI Taxonomy ID of the organism |
| `organism` | varchar | YES | Organism name (e.g., "Homo sapiens") |
| `chembl_id` | varchar | NO | Public ChEMBL identifier for this target |
| `species_group_flag` | smallint | NO | 1 if target represents a species group rather than a single species |

**Key relationships:**
- Join to `target_components` on `tid` to link to protein sequences
- Join to `drug_mechanism` on `tid` to get drugs with known MOA at this target
- Join to `assays` on `tid` to get all bioactivity assays for this target
- Join to `protein_classification` via `component_class` for protein family

**Sample data:**

| tid | chembl_id | pref_name | target_type | organism |
|---|---|---|---|---|
| 1 | CHEMBL2074 | Maltase-glucoamylase | SINGLE PROTEIN | Homo sapiens |
| 2 | CHEMBL1971 | ATP-binding cassette sub-family C member 9 | SINGLE PROTEIN | Homo sapiens |
| 3 | CHEMBL1827 | cGMP-specific 3',5'-cyclic phosphodiesterase | SINGLE PROTEIN | Homo sapiens |

---

### `target_components` ★ Priority

**Purpose:** Junction table linking targets to their component protein/nucleic acid sequences. A single-protein target has one component; a protein complex may have multiple.

**Row count:** 17,284

| Column | Data Type | Nullable | Description |
|---|---|---|---|
| `tid` | bigint | NO | FK to `target_dictionary` |
| `component_id` | bigint | NO | FK to `component_sequences` |
| `targcomp_id` | bigint | NO | Primary key for this junction record |
| `homologue` | smallint | NO | 1 if this component is a homologue (not direct match) |

**Key relationships:**
- Join to `target_dictionary` on `tid`
- Join to `component_sequences` on `component_id` for UniProt accession and sequence

---

### `component_sequences` ★ Priority

**Purpose:** Stores protein and nucleic acid sequences for target components, with links to UniProt (SWISS-PROT or TrEMBL). The `accession` field is a UniProt accession number, making this the key bridge to external protein databases.

**Row count:** 12,986

| Column | Data Type | Nullable | Description |
|---|---|---|---|
| `component_id` | bigint | NO | Primary key |
| `component_type` | varchar | YES | PROTEIN or DNA/RNA |
| `accession` | varchar | YES | UniProt accession number (e.g., P02708) |
| `sequence` | text | YES | Full amino acid or nucleotide sequence |
| `sequence_md5sum` | varchar | YES | MD5 hash of the sequence for deduplication |
| `description` | varchar | YES | Protein name/description from UniProt |
| `tax_id` | bigint | YES | NCBI Taxonomy ID |
| `organism` | varchar | YES | Organism name |
| `db_source` | varchar | YES | SWISS-PROT or TREMBL |
| `db_version` | varchar | YES | UniProt release version of the annotation |

**Key relationships:**
- Join to `target_components` on `component_id` to reach targets
- `accession` links to UniProt; also cross-referenced in `component_synonyms` for gene symbols

**Sample data:**

| component_id | accession | component_type | description | organism | db_source |
|---|---|---|---|---|---|
| 1 | O09028 | PROTEIN | Gamma-aminobutyric acid receptor subunit pi | Rattus norvegicus | SWISS-PROT |
| 2 | P02708 | PROTEIN | Acetylcholine receptor subunit alpha | Homo sapiens | SWISS-PROT |
| 3 | P04637 | PROTEIN | Cellular tumor antigen p53 | Homo sapiens | SWISS-PROT |

---

### `atc_classification` ★ Priority

**Purpose:** Contains the complete WHO Anatomical Therapeutic Chemical (ATC) classification hierarchy. ATC codes are organized into 5 levels: anatomical class (L1) → therapeutic subgroup (L2) → pharmacological subgroup (L3) → chemical subgroup (L4) → chemical substance (L5). The level-5 code uniquely identifies a drug substance.

**Row count:** 5,579

| Column | Data Type | Nullable | Description |
|---|---|---|---|
| `who_name` | varchar | YES | WHO INN name for the chemical substance |
| `level1` | varchar | YES | Level-1 ATC code (single letter, e.g., "L") |
| `level2` | varchar | YES | Level-2 ATC code (e.g., "L01") |
| `level3` | varchar | YES | Level-3 ATC code (e.g., "L01E") |
| `level4` | varchar | YES | Level-4 ATC code (e.g., "L01EA") |
| `level5` | varchar | NO | Level-5 ATC code — PK (e.g., "L01EA06") |
| `level1_description` | varchar | YES | Description of level 1 (e.g., "ANTINEOPLASTIC AND IMMUNOMODULATING AGENTS") |
| `level2_description` | varchar | YES | Description of level 2 |
| `level3_description` | varchar | YES | Description of level 3 |
| `level4_description` | varchar | YES | Description of level 4 |

**Key relationships:**
- Join to `molecule_atc_classification` on `level5` to get compounds per ATC code
- Join to `defined_daily_dose` on `atc_code = level5` for DDD data

**Sample data:**

| level5 | who_name | level1 | level1_description | level4_description |
|---|---|---|---|---|
| A01AA01 | sodium fluoride | A | ALIMENTARY TRACT AND METABOLISM | Caries prophylactic agents |
| A01AA02 | sodium monofluorophosphate | A | ALIMENTARY TRACT AND METABOLISM | Caries prophylactic agents |
| A01AA03 | olaflur | A | ALIMENTARY TRACT AND METABOLISM | Caries prophylactic agents |

---

### `molecule_atc_classification` ★ Priority

**Purpose:** Junction table linking compounds in `molecule_dictionary` to their WHO ATC level-5 codes. A single compound may map to multiple ATC codes if it has multiple approved indications.

**Row count:** 4,567

| Column | Data Type | Nullable | Description |
|---|---|---|---|
| `mol_atc_id` | bigint | NO | Primary key |
| `level5` | varchar | NO | FK to `atc_classification.level5` |
| `molregno` | bigint | NO | FK to `molecule_dictionary` |

**Key relationships:**
- Join to `molecule_dictionary` on `molregno`
- Join to `atc_classification` on `level5` to get full ATC hierarchy

**Sample data:**

| mol_atc_id | molregno | level5 |
|---|---|---|
| 100497 | 2286380 | L01EA06 |
| 100498 | 2089491 | L01EX15 |
| 100499 | 608601 | L01EX10 |

---

### `drug_indication` ★ Priority

**Purpose:** Maps drugs to their approved or investigated therapeutic indications, using both MeSH disease terms and EFO (Experimental Factor Ontology) identifiers. Includes the maximum clinical phase reached for each indication.

**Row count:** 60,055

| Column | Data Type | Nullable | Description |
|---|---|---|---|
| `drugind_id` | bigint | NO | Primary key |
| `record_id` | bigint | NO | FK to `compound_records` |
| `molregno` | bigint | YES | FK to `molecule_dictionary` |
| `max_phase_for_ind` | numeric | YES | Maximum clinical phase for this specific indication (4 = approved) |
| `mesh_id` | varchar | NO | MeSH disease identifier (e.g., D001172) |
| `mesh_heading` | varchar | NO | MeSH disease term (e.g., "Arthritis, Rheumatoid") |
| `efo_id` | varchar | YES | EFO ontology identifier (e.g., EFO:0000685) |
| `efo_term` | varchar | YES | EFO disease term |

**Key relationships:**
- Join to `molecule_dictionary` on `molregno`
- Join to `indication_refs` on `drugind_id` for source references (FDA, EMA, ClinicalTrials)

**Sample data:**

| drugind_id | molregno | mesh_heading | efo_term | max_phase_for_ind |
|---|---|---|---|---|
| 22606 | 675774 | Scleroderma, Diffuse | diffuse scleroderma | 2 |
| 22607 | 675774 | Arthritis, Rheumatoid | rheumatoid arthritis | 4 |
| 22609 | 675576 | Myocardial Infarction | myocardial infarction | 3 |

---

### `indication_refs` ★ Priority

**Purpose:** Source references (FDA labels, EMA approvals, ClinicalTrials.gov IDs) that support each drug indication record. Provides traceability for regulatory approval claims.

**Row count:** 93,733

| Column | Data Type | Nullable | Description |
|---|---|---|---|
| `indref_id` | bigint | NO | Primary key |
| `drugind_id` | bigint | NO | FK to `drug_indication` |
| `ref_type` | varchar | NO | Reference type: FDA, EMA, ClinicalTrials, PubMed, etc. |
| `ref_id` | varchar | NO | Reference identifier (label path, EPAR number, NCT IDs, PMID) |
| `ref_url` | varchar | NO | Full URL to the reference |

**Key relationships:**
- Join to `drug_indication` on `drugind_id`

**Sample data:**

| indref_id | drugind_id | ref_type | ref_id |
|---|---|---|---|
| 682606 | 126883 | FDA | label/2015/205739s000lbl.pdf |
| 682608 | 22630 | EMA | EMEA/H/C/002211 |

---

### `activities` ★ Priority

**Purpose:** The primary bioactivity measurements table, containing assay results linking compounds to assays. Includes standardized values (IC50, Ki, EC50, etc.) in nM, along with pChEMBL values (negative log of molar activity). This is the largest table in ChEMBL at ~24.5 million rows.

**Row count:** 24,527,044

| Column | Data Type | Nullable | Description |
|---|---|---|---|
| `activity_id` | bigint | NO | Primary key |
| `assay_id` | bigint | NO | FK to `assays` |
| `doc_id` | bigint | YES | FK to `docs` |
| `record_id` | bigint | NO | FK to `compound_records` |
| `molregno` | bigint | YES | FK to `molecule_dictionary` |
| `standard_relation` | varchar | YES | Relation operator: =, <, >, <=, >= |
| `standard_value` | numeric | YES | Standardized activity value (in standard_units) |
| `standard_units` | varchar | YES | Standardized units (usually nM) |
| `standard_flag` | smallint | YES | 1 if value has been standardized |
| `standard_type` | varchar | YES | Standardized activity type (IC50, Ki, Kd, EC50, etc.) |
| `activity_comment` | varchar | YES | Free-text comments or qualitative result |
| `data_validity_comment` | varchar | YES | Flag for data quality issues |
| `potential_duplicate` | smallint | YES | 1 if flagged as a potential duplicate |
| `pchembl_value` | numeric | YES | -log10(activity in M); comparable across assay types |
| `bao_endpoint` | varchar | YES | BAO ontology endpoint identifier |
| `uo_units` | varchar | YES | Units Ontology identifier |
| `qudt_units` | varchar | YES | QUDT units ontology identifier |
| `toid` | integer | YES | Target ontology ID |
| `upper_value` | numeric | YES | Upper bound for range activity values |
| `standard_upper_value` | numeric | YES | Standardized upper bound |
| `src_id` | integer | YES | FK to `source` |
| `type` | varchar | NO | Original reported activity type |
| `relation` | varchar | YES | Original reported relation operator |
| `value` | numeric | YES | Original reported value |
| `units` | varchar | YES | Original reported units |
| `text_value` | varchar | YES | Text result for qualitative assays |
| `standard_text_value` | varchar | YES | Standardized text result |
| `action_type` | varchar | YES | Action type for the activity |
| `modality` | varchar | YES | Drug modality for the activity |

**Key relationships:**
- Join to `molecule_dictionary` on `molregno` for compound info
- Join to `assays` on `assay_id` for assay metadata and target (`tid`)
- Join to `ligand_eff` on `activity_id` for efficiency metrics
- Join to `activity_properties` on `activity_id` for supplementary measurements
- **Performance note:** Always filter by `molregno`, `assay_id`, or `standard_type` to avoid full table scans

**Sample data:**

| activity_id | assay_id | molregno | standard_type | standard_relation | standard_value | standard_units | pchembl_value |
|---|---|---|---|---|---|---|---|
| 31863 | 54505 | 180094 | IC50 | > | 100000 | nM | NULL |
| 31864 | 83907 | 182268 | IC50 | = | 2500 | nM | 5.60 |

---

### `assays` ★ Priority

**Purpose:** Metadata for each bioactivity assay, including the assay type (binding, functional, ADME, etc.), description, target organism, cell type, and confidence score. The link between `activities` and `target_dictionary`.

**Row count:** 1,970,438

| Column | Data Type | Nullable | Description |
|---|---|---|---|
| `assay_id` | bigint | NO | Primary key |
| `doc_id` | bigint | NO | FK to `docs` (source publication) |
| `description` | varchar | YES | Free-text description of the assay |
| `assay_type` | varchar | YES | B=Binding, F=Functional, A=ADME, P=Physicochemical, T=Toxicity, U=Unassigned |
| `assay_test_type` | varchar | YES | In Vivo, In Vitro, Ex Vivo, etc. |
| `assay_category` | varchar | YES | Screening, confirmatory, panel, etc. |
| `assay_organism` | varchar | YES | Organism in which assay was performed |
| `assay_tax_id` | bigint | YES | NCBI Taxonomy ID of assay organism |
| `assay_strain` | varchar | YES | Strain or variant of assay organism |
| `assay_tissue` | varchar | YES | Tissue type used in assay |
| `assay_cell_type` | varchar | YES | Cell type used in assay |
| `assay_subcellular_fraction` | varchar | YES | Subcellular fraction (e.g., membrane, cytosol) |
| `tid` | bigint | YES | FK to `target_dictionary` |
| `relationship_type` | varchar | YES | Relationship between assay target and `tid` (D, H, M, N, S, U) |
| `confidence_score` | smallint | YES | Target assignment confidence (0–9; see `confidence_score_lookup`) |
| `src_id` | integer | NO | FK to `source` |
| `src_assay_id` | varchar | YES | Source database's own assay identifier |
| `chembl_id` | varchar | NO | Public ChEMBL identifier for this assay |
| `cell_id` | bigint | YES | FK to `cell_dictionary` |
| `bao_format` | varchar | YES | BAO assay format identifier |
| `tissue_id` | bigint | YES | FK to `tissue_dictionary` |
| `variant_id` | bigint | YES | FK to `variant_sequences` if using a mutant target |
| `aidx` | varchar | NO | Internal source index |
| `assay_group` | varchar | YES | Group label for related assays |

**Key relationships:**
- Join to `activities` on `assay_id` for bioactivity data
- Join to `target_dictionary` on `tid` for target info
- Join to `docs` on `doc_id` for publication details
- Filter `confidence_score >= 8` for direct single-protein target assignments

**Sample data:**

| assay_id | chembl_id | assay_type | tid | confidence_score | description |
|---|---|---|---|---|---|
| 1 | CHEMBL615117 | B | 12052 | 8 | In vitro inhibition of platelet 12-lipoxygenase at 30 uM |
| 2 | CHEMBL615118 | F | 22226 | 0 | Calcium mobilization in 1321NI cells |

---

### `docs` ★ Priority

**Purpose:** Registry of all literature publications and patent documents that are sources of bioactivity data in ChEMBL. Provides PubMed IDs, DOIs, and journal metadata for tracing data provenance.

**Row count:** 101,100

| Column | Data Type | Nullable | Description |
|---|---|---|---|
| `doc_id` | bigint | NO | Primary key |
| `journal` | varchar | YES | Journal name abbreviation |
| `year` | integer | YES | Publication year |
| `volume` | varchar | YES | Journal volume |
| `issue` | varchar | YES | Journal issue |
| `first_page` | varchar | YES | First page number |
| `last_page` | varchar | YES | Last page number |
| `pubmed_id` | bigint | YES | PubMed identifier |
| `doi` | varchar | YES | Digital object identifier |
| `chembl_id` | varchar | NO | Public ChEMBL identifier for this document |
| `title` | varchar | YES | Article title |
| `doc_type` | varchar | NO | PUBLICATION, PATENT, DATASET, BOOK, SYMPOSIUM-ABSTRACT |
| `authors` | varchar | YES | Author list |
| `abstract` | text | YES | Article abstract |
| `patent_id` | varchar | YES | Patent number (for patent documents) |
| `ridx` | varchar | NO | Internal source index |
| `src_id` | integer | NO | FK to `source` |
| `chembl_release_id` | integer | YES | FK to `chembl_release` (version when first included) |
| `contact` | varchar | YES | Submitter contact for deposited datasets |

**Key relationships:**
- Join to `assays` on `doc_id` to get all assays from a publication
- Join to `activities` on `doc_id` to get all bioactivities from a publication

**Sample data:**

| doc_id | chembl_id | doc_type | journal | year | pubmed_id | title |
|---|---|---|---|---|---|---|
| -1 | CHEMBL1158643 | DATASET | NULL | NULL | NULL | Unpublished dataset |
| 1 | CHEMBL1139451 | PUBLICATION | J Med Chem | 2004 | 14695813 | The discovery of ezetimibe... |

---

## Supporting Tables

---

### `compound_records`

**Purpose:** Tracks each time a compound was reported in a specific document/source. A single compound (`molregno`) may appear in many records across publications, with different source IDs and compound keys.

**Row count:** 3,824,604

| Column | Data Type | Nullable | Description |
|---|---|---|---|
| `record_id` | bigint | NO | Primary key |
| `molregno` | bigint | YES | FK to `molecule_dictionary` |
| `doc_id` | bigint | NO | FK to `docs` |
| `compound_key` | varchar | YES | Identifier used in the source document |
| `compound_name` | varchar | YES | Name as reported in the source document |
| `src_id` | integer | NO | FK to `source` |
| `src_compound_id` | varchar | YES | Source database's own compound identifier |
| `cidx` | varchar | NO | Internal source index |

---

### `mechanism_refs`

**Purpose:** Literature and regulatory references supporting each `drug_mechanism` record.

**Row count:** 13,600

| Column | Data Type | Nullable | Description |
|---|---|---|---|
| `mecref_id` | bigint | NO | Primary key |
| `mec_id` | bigint | NO | FK to `drug_mechanism` |
| `ref_type` | varchar | NO | PubMed, DailyMed, FDA, ISBN, etc. |
| `ref_id` | varchar | NO | Identifier in the reference system |
| `ref_url` | varchar | NO | URL to the reference |

---

### `drug_warning`

**Purpose:** Regulatory safety warnings for drugs, including FDA black box warnings, market withdrawals, and EFO-classified warning types.

**Row count:** 2,304

| Column | Data Type | Nullable | Description |
|---|---|---|---|
| `warning_id` | bigint | NO | Primary key |
| `record_id` | bigint | NO | FK to `compound_records` |
| `molregno` | bigint | NO | FK to `molecule_dictionary` |
| `warning_type` | varchar | YES | Black Box Warning, Withdrawal, etc. |
| `warning_class` | varchar | YES | EFO-based warning class (e.g., hepatotoxicity) |
| `warning_description` | varchar | YES | Free-text description |
| `warning_country` | varchar | YES | Country where warning applies |
| `warning_year` | integer | YES | Year warning was issued |
| `efo_term` | varchar | YES | EFO disease term for the adverse event |
| `efo_id` | varchar | YES | EFO identifier |
| `efo_id_for_warning_class` | varchar | YES | EFO identifier for the warning class |

---

### `warning_refs`

**Purpose:** Source references for drug warning records.

**Row count:** 4,946

| Column | Data Type | Nullable | Description |
|---|---|---|---|
| `warnref_id` | bigint | NO | Primary key |
| `warning_id` | bigint | NO | FK to `drug_warning` |
| `ref_type` | varchar | NO | Reference type |
| `ref_id` | varchar | NO | Reference identifier |
| `ref_url` | varchar | NO | URL to the reference |

---

### `molecule_hierarchy`

**Purpose:** Resolves parent-child relationships for salts, prodrugs, and stereoisomers. The `parent_molregno` is the structurally simplest form; `active_molregno` is the pharmacologically active form.

**Row count:** 2,828,129

| Column | Data Type | Nullable | Description |
|---|---|---|---|
| `molregno` | bigint | NO | FK to `molecule_dictionary` — the original recorded molecule |
| `parent_molregno` | bigint | NO | Freebase/parent form of the molecule |
| `active_molregno` | bigint | NO | Active form (often same as parent) |

---

### `action_type`

**Purpose:** Controlled vocabulary lookup for pharmacological action types used in `drug_mechanism`.

**Row count:** 35

| Column | Data Type | Description |
|---|---|---|
| `action_type` | varchar | PK — e.g., INHIBITOR, AGONIST, ANTAGONIST |
| `description` | varchar | Plain-language description of the action |
| `parent_type` | varchar | Parent category: POSITIVE MODULATOR, NEGATIVE MODULATOR, etc. |

**Sample values:** ACTIVATOR (POSITIVE MODULATOR), AGONIST (POSITIVE MODULATOR), ANTAGONIST (NEGATIVE MODULATOR), INHIBITOR (NEGATIVE MODULATOR), FULL AGONIST, PARTIAL AGONIST, INVERSE AGONIST

---

### `assay_type`

**Purpose:** Lookup table for the 6 assay type codes used in `assays.assay_type`.

**Row count:** 6

| Code | Description |
|---|---|
| A | ADME |
| B | Binding |
| F | Functional |
| P | Physicochemical |
| T | Toxicity |
| U | Unassigned |

---

### `confidence_score_lookup`

**Purpose:** Defines the 10-level target assignment confidence scoring system used in `assays.confidence_score`.

**Row count:** 10

| Score | target_mapping | Description |
|---|---|---|
| 0 | Unassigned | Target unknown or not yet assigned |
| 1 | Non-molecular | Non-molecular target |
| 3 | Molecular (non-protein) | Non-protein molecular target |
| 5 | Multiple proteins | Multiple direct protein targets |
| 7 | Protein complex | Direct protein complex |
| 8 | Homologous protein | Homologous single protein |
| 9 | Protein | Direct single protein target |

---

### `target_type`

**Purpose:** Lookup for 28 distinct target type codes used in `target_dictionary.target_type`, defining the nature of the biological target.

**Row count:** 28

**Sample values:** SINGLE PROTEIN, PROTEIN COMPLEX, CELL-LINE, ORGANISM, TISSUE, ADMET, LIPID, NUCLEIC-ACID, 3D CELL CULTURE

---

### `relationship_type`

**Purpose:** Lookup for the 6 assay-to-target relationship type codes used in `assays.relationship_type`.

**Row count:** 6

| Code | Description |
|---|---|
| D | Direct protein target assigned |
| H | Homologous protein target assigned |
| M | Molecular target other than protein |
| N | Non-molecular target |
| S | Subcellular target |
| U | Uncurated default |

---

### `source`

**Purpose:** Registry of 67 data sources contributing to ChEMBL, including scientific literature, FDA data, partner databases (GSK, Pfizer panels, etc.).

**Row count:** 67

| Column | Data Type | Description |
|---|---|---|
| `src_id` | integer | Primary key |
| `src_description` | varchar | Full description of the source |
| `src_short_name` | varchar | Abbreviated name (e.g., LITERATURE, FDA) |
| `src_comment` | varchar | Additional notes |
| `src_url` | varchar | URL of the source |
| `ddid_pattern` | varchar | Pattern for drug deposit IDs |

---

### `component_synonyms`

**Purpose:** Alternative names and identifiers for protein components, including gene symbols (HGNC), UniProt accessions, and other identifiers.

**Row count:** 121,157

| Column | Data Type | Description |
|---|---|---|
| `compsyn_id` | bigint | Primary key |
| `component_id` | bigint | FK to `component_sequences` |
| `component_synonym` | varchar | The synonym text (e.g., gene symbol "EGFR") |
| `syn_type` | varchar | Type: GENE_SYMBOL, UNIPROT, HGNC, NCBI_GI, etc. |

---

### `protein_classification`

**Purpose:** Hierarchical classification tree for protein families in ChEMBL (up to 8 levels deep), based on the ChEMBL protein family ontology. Used to categorize drug targets by family.

**Row count:** 905

| Column | Data Type | Description |
|---|---|---|
| `protein_class_id` | bigint | Primary key |
| `parent_id` | bigint | FK to parent protein class |
| `pref_name` | varchar | Class name (e.g., Enzyme, Kinase) |
| `short_name` | varchar | Abbreviated name |
| `protein_class_desc` | varchar | Full path description |
| `definition` | varchar | MeSH-style definition |
| `class_level` | bigint | Depth level (0 = root) |

---

### `component_class`

**Purpose:** Maps protein components to the protein classification hierarchy.

**Row count:** 13,180

| Column | Data Type | Description |
|---|---|---|
| `component_id` | bigint | FK to `component_sequences` |
| `protein_class_id` | bigint | FK to `protein_classification` |
| `comp_class_id` | bigint | Primary key |

---

### `go_classification`

**Purpose:** Subset of Gene Ontology terms used for protein annotation in ChEMBL, including molecular function, biological process, and cellular component.

**Row count:** 309

| Column | Data Type | Description |
|---|---|---|
| `go_id` | varchar | GO term identifier (e.g., GO:0000166) |
| `parent_go_id` | varchar | Parent GO term |
| `pref_name` | varchar | GO term name |
| `class_level` | smallint | Depth in the GO hierarchy |
| `aspect` | varchar | F=molecular function, P=biological process, C=cellular component |
| `path` | varchar | Full hierarchical path string |

---

### `component_go`

**Purpose:** Maps protein components to GO terms.

**Row count:** 153,709

| Column | Data Type | Description |
|---|---|---|
| `comp_go_id` | bigint | Primary key |
| `component_id` | bigint | FK to `component_sequences` |
| `go_id` | varchar | FK to `go_classification` |

---

### `component_domains`

**Purpose:** Maps protein components to structural domains (Pfam, etc.).

**Row count:** 28,547

| Column | Data Type | Description |
|---|---|---|
| `compd_id` | bigint | Primary key |
| `domain_id` | bigint | FK to `domains` |
| `component_id` | bigint | FK to `component_sequences` |
| `start_position` | bigint | Amino acid start position of domain |
| `end_position` | bigint | Amino acid end position of domain |

---

### `domains`

**Purpose:** Protein domain definitions from Pfam and other structural databases.

**Row count:** 3,953

| Column | Data Type | Description |
|---|---|---|
| `domain_id` | bigint | Primary key |
| `domain_type` | varchar | Pfam-A, Pfam-B, etc. |
| `source_domain_id` | varchar | Pfam accession |
| `domain_name` | varchar | Domain name |
| `domain_description` | varchar | Description of the domain |

---

### `binding_sites`

**Purpose:** Named binding sites on targets, often corresponding to specific structural domains.

**Row count:** 4,545

| Column | Data Type | Description |
|---|---|---|
| `site_id` | bigint | Primary key |
| `site_name` | varchar | Descriptive site name (e.g., "Pkinase domain") |
| `tid` | bigint | FK to `target_dictionary` |

---

### `site_components`

**Purpose:** Maps binding sites to their constituent protein components and domains.

**Row count:** 5,908

| Column | Data Type | Description |
|---|---|---|
| `sitecomp_id` | bigint | Primary key |
| `site_id` | bigint | FK to `binding_sites` |
| `component_id` | bigint | FK to `component_sequences` |
| `domain_id` | bigint | FK to `domains` |
| `site_residues` | varchar | Key residue positions |

---

### `ligand_eff`

**Purpose:** Ligand efficiency metrics derived from activity data, enabling comparison of activity normalized by molecular size.

**Row count:** 2,223,169

| Column | Data Type | Description |
|---|---|---|
| `activity_id` | bigint | FK to `activities` (also PK) |
| `bei` | numeric | Binding efficiency index |
| `sei` | numeric | Surface efficiency index |
| `le` | numeric | Ligand efficiency (kcal/mol per heavy atom) |
| `lle` | numeric | Lipophilic ligand efficiency (pChEMBL − ALogP) |

---

### `activity_properties`

**Purpose:** Supplementary measurements and parameters associated with individual activity records (e.g., Hill slope, baseline, assay conditions).

**Row count:** 12,213,211

| Column | Data Type | Description |
|---|---|---|
| `ap_id` | bigint | Primary key |
| `activity_id` | bigint | FK to `activities` |
| `type` | varchar | Property type |
| `relation` | varchar | Relation operator |
| `value` | numeric | Numeric value |
| `units` | varchar | Units |
| `text_value` | varchar | Text value |
| `standard_type` | varchar | Standardized property type |
| `standard_value` | numeric | Standardized value |
| `standard_units` | varchar | Standardized units |
| `comments` | varchar | Free-text comments |
| `result_flag` | smallint | 1 if this is a primary result |

---

### `assay_parameters`

**Purpose:** Experimental parameters for assays (e.g., concentration, incubation time, pH), providing assay context for activity data.

**Row count:** 460,048

| Column | Data Type | Description |
|---|---|---|
| `assay_param_id` | bigint | Primary key |
| `assay_id` | bigint | FK to `assays` |
| `type` | varchar | Parameter type |
| `relation` | varchar | Relation operator |
| `value` | numeric | Numeric value |
| `units` | varchar | Units |
| `text_value` | varchar | Text value |
| `standard_type` | varchar | Standardized parameter type |
| `standard_value` | numeric | Standardized value |
| `standard_units` | varchar | Standardized units |
| `comments` | varchar | Comments |

---

### `assay_classification`

**Purpose:** Hierarchical classification of assay types (e.g., kinase panel, GPCR panel) from external sources like BioAssay Ontology.

**Row count:** 584

| Column | Data Type | Description |
|---|---|---|
| `assay_class_id` | bigint | Primary key |
| `l1` | varchar | Level-1 classification |
| `l2` | varchar | Level-2 classification |
| `l3` | varchar | Level-3 classification |
| `class_type` | varchar | Type of classification (e.g., panel) |
| `source` | varchar | Classification source |

---

### `assay_class_map`

**Purpose:** Maps assays to assay classification categories.

**Row count:** 244,490

| Column | Data Type | Description |
|---|---|---|
| `ass_cls_map_id` | bigint | Primary key |
| `assay_id` | bigint | FK to `assays` |
| `assay_class_id` | bigint | FK to `assay_classification` |

---

### `target_relations`

**Purpose:** Hierarchical relationships between targets, such as SUBSET OF or SUPERSET OF, supporting navigation of complex/component targets.

**Row count:** 155,208

| Column | Data Type | Description |
|---|---|---|
| `targrel_id` | bigint | Primary key |
| `tid` | bigint | FK to `target_dictionary` (the subject target) |
| `relationship` | varchar | Relationship type: SUBSET OF, SUPERSET OF, OVERLAPS WITH |
| `related_tid` | bigint | FK to `target_dictionary` (the related target) |

---

### `predicted_binding_domains`

**Purpose:** Predicted protein domain that is the site of binding for an activity, inferred from structural or sequence data.

**Row count:** 822,313

| Column | Data Type | Description |
|---|---|---|
| `predbind_id` | bigint | Primary key |
| `activity_id` | bigint | FK to `activities` |
| `site_id` | bigint | FK to `binding_sites` |
| `prediction_method` | varchar | Method used (e.g., Manual, Multi Pharmacophore) |
| `confidence` | varchar | Confidence level |

---

### `biotherapeutics`

**Purpose:** Biotherapeutic molecules (peptides, antibodies, nucleic acids) with their HELM notation for sequence representation.

**Row count:** 23,849

| Column | Data Type | Description |
|---|---|---|
| `molregno` | bigint | FK to `molecule_dictionary` (PK) |
| `description` | varchar | Description of the biotherapeutic |
| `helm_notation` | varchar | HELM linear notation for the sequence |

---

### `bio_component_sequences`

**Purpose:** Individual sequence components of biotherapeutic molecules.

**Row count:** 3,478

| Column | Data Type | Description |
|---|---|---|
| `component_id` | bigint | Primary key |
| `component_type` | varchar | Peptide, DNA, RNA |
| `description` | varchar | Sequence description |
| `sequence` | text | Amino acid or nucleotide sequence |
| `sequence_md5sum` | varchar | MD5 hash of the sequence |
| `tax_id` | bigint | NCBI Taxonomy ID |
| `organism` | varchar | Source organism |

---

### `biotherapeutic_components`

**Purpose:** Junction table linking biotherapeutic molecules to their sequence components.

**Row count:** 4,415

| Column | Data Type | Description |
|---|---|---|
| `biocomp_id` | bigint | Primary key |
| `molregno` | bigint | FK to `biotherapeutics` |
| `component_id` | bigint | FK to `bio_component_sequences` |

---

### `cell_dictionary`

**Purpose:** Registry of cell lines used in bioactivity assays, with cross-references to Cellosaurus, CLO, and EFO.

**Row count:** 2,238

| Column | Data Type | Description |
|---|---|---|
| `cell_id` | bigint | Primary key |
| `cell_name` | varchar | Cell line name |
| `cell_description` | varchar | Description |
| `cell_source_tissue` | varchar | Tissue of origin |
| `cell_source_organism` | varchar | Source organism |
| `cell_source_tax_id` | bigint | NCBI Taxonomy ID of source organism |
| `clo_id` | varchar | Cell Line Ontology identifier |
| `efo_id` | varchar | EFO identifier |
| `cellosaurus_id` | varchar | Cellosaurus accession (e.g., CVCL_4704) |
| `chembl_id` | varchar | ChEMBL identifier |
| `cell_ontology_id` | varchar | Cell Ontology identifier |

---

### `tissue_dictionary`

**Purpose:** Registry of tissues and organs used in assays, with cross-references to UBERON, BTO, EFO, and CALOHA ontologies.

**Row count:** 791

| Column | Data Type | Description |
|---|---|---|
| `tissue_id` | bigint | Primary key |
| `uberon_id` | varchar | UBERON ontology identifier |
| `pref_name` | varchar | Preferred tissue name |
| `efo_id` | varchar | EFO identifier |
| `chembl_id` | varchar | ChEMBL identifier |
| `bto_id` | varchar | Brenda Tissue Ontology identifier |
| `caloha_id` | varchar | CALOHA identifier |

---

### `products`

**Purpose:** FDA-approved drug products (NDAs/ANDAs), including trade names, dosage forms, routes, and approval dates.

**Row count:** 45,752

| Column | Data Type | Description |
|---|---|---|
| `product_id` | varchar | Primary key (FDA application-based ID) |
| `dosage_form` | varchar | Tablet, Capsule, Solution, etc. |
| `route` | varchar | Oral, Parenteral, Topical, etc. |
| `trade_name` | varchar | Brand name |
| `approval_date` | timestamp | FDA approval date |
| `ad_type` | varchar | Application type (e.g., OTC, RX) |
| `oral` | smallint | 1 if oral |
| `topical` | smallint | 1 if topical |
| `parenteral` | smallint | 1 if parenteral |
| `black_box_warning` | smallint | 1 if black box warning |
| `applicant_full_name` | varchar | Manufacturer/applicant |
| `innovator_company` | smallint | 1 if innovator (not generic) |
| `nda_type` | varchar | NDA type code |

---

### `formulations`

**Purpose:** Links FDA drug products to the active ingredient compounds in ChEMBL.

**Row count:** 53,430

| Column | Data Type | Description |
|---|---|---|
| `formulation_id` | bigint | Primary key |
| `product_id` | varchar | FK to `products` |
| `ingredient` | varchar | Active ingredient name |
| `strength` | varchar | Dosage strength |
| `record_id` | bigint | FK to `compound_records` |
| `molregno` | bigint | FK to `molecule_dictionary` |

---

### `defined_daily_dose`

**Purpose:** WHO-defined daily doses (DDD) for drug substances indexed by ATC level-5 code.

**Row count:** 2,721

| Column | Data Type | Description |
|---|---|---|
| `ddd_id` | bigint | Primary key |
| `atc_code` | varchar | FK to `atc_classification.level5` |
| `ddd_value` | numeric | Defined daily dose amount |
| `ddd_units` | varchar | Units (mg, g, mmol, etc.) |
| `ddd_admr` | varchar | Route of administration (O=oral, P=parenteral, etc.) |
| `ddd_comment` | varchar | Notes on the DDD |

---

### `metabolism`

**Purpose:** Drug metabolism pathway data linking parent drugs to their metabolites via enzymes (e.g., CYP450).

**Row count:** 2,147

| Column | Data Type | Description |
|---|---|---|
| `met_id` | bigint | Primary key |
| `drug_record_id` | bigint | FK to `compound_records` (the parent drug) |
| `substrate_record_id` | bigint | FK to `compound_records` (the substrate) |
| `metabolite_record_id` | bigint | FK to `compound_records` (the metabolite) |
| `pathway_id` | bigint | Pathway group identifier |
| `pathway_key` | varchar | Figure/table reference in source |
| `enzyme_name` | varchar | Enzyme name (e.g., CYP3A4) |
| `enzyme_tid` | bigint | FK to `target_dictionary` (enzyme target) |
| `met_conversion` | varchar | Conversion type (e.g., Glucuronidation) |
| `organism` | varchar | Organism where metabolism occurs |
| `tax_id` | bigint | NCBI Taxonomy ID |
| `met_comment` | varchar | Additional comments |

---

### `metabolism_refs`

**Purpose:** Source references for metabolism records.

**Row count:** 3,296

| Column | Data Type | Description |
|---|---|---|
| `metref_id` | bigint | Primary key |
| `met_id` | bigint | FK to `metabolism` |
| `ref_type` | varchar | Reference type |
| `ref_id` | varchar | Reference identifier |
| `ref_url` | varchar | URL to reference |

---

### `structural_alert_sets`

**Purpose:** Named sets of SMARTS-based structural alerts used for flagging potentially problematic substructures.

**Row count:** 5

| Column | Data Type | Description |
|---|---|---|
| `alert_set_id` | bigint | Primary key |
| `set_name` | varchar | Set name (e.g., PAINS, Dundee, BMS, NIH, MLSMR) |
| `priority` | smallint | Priority order for display |

---

### `structural_alerts`

**Purpose:** SMARTS patterns defining individual structural alerts within each alert set.

**Row count:** 936

| Column | Data Type | Description |
|---|---|---|
| `alert_id` | bigint | Primary key |
| `alert_set_id` | bigint | FK to `structural_alert_sets` |
| `alert_name` | varchar | Name of the alert |
| `smarts` | varchar | SMARTS pattern for the alert |

---

### `compound_structural_alerts`

**Purpose:** Records which structural alerts are matched by which compounds.

**Row count:** 5,020,133

| Column | Data Type | Description |
|---|---|---|
| `cpd_str_alert_id` | bigint | Primary key |
| `molregno` | bigint | FK to `molecule_dictionary` |
| `alert_id` | bigint | FK to `structural_alerts` |

---

### `chembl_id_lookup`

**Purpose:** Global index mapping every public ChEMBL ID to its entity type (COMPOUND, TARGET, ASSAY, DOCUMENT, CELL, TISSUE) and internal primary key.

**Row count:** 5,478,952

| Column | Data Type | Description |
|---|---|---|
| `chembl_id` | varchar | Public ChEMBL ID (PK) |
| `entity_type` | varchar | COMPOUND, TARGET, ASSAY, DOCUMENT, CELL, TISSUE |
| `entity_id` | bigint | Internal primary key in the respective entity table |
| `status` | varchar | ACTIVE or INACTIVE |
| `last_active` | integer | ChEMBL release version when last active |

---

### `organism_class`

**Purpose:** NCBI-based taxonomic organism classification hierarchy.

**Row count:** 4,280

| Column | Data Type | Description |
|---|---|---|
| `oc_id` | bigint | Primary key |
| `tax_id` | bigint | NCBI Taxonomy ID |
| `l1` | varchar | Domain/kingdom level |
| `l2` | varchar | Phylum level |
| `l3` | varchar | Class level |

---

### `usan_stems`

**Purpose:** USAN (United States Adopted Name) drug name stem definitions used to identify pharmacological class from a drug's suffix or prefix.

**Row count:** 834

| Column | Data Type | Description |
|---|---|---|
| `usan_stem_id` | bigint | Primary key |
| `stem` | varchar | The stem string (e.g., "-mab", "-statin") |
| `subgroup` | varchar | More specific subgroup of the stem |
| `annotation` | varchar | Pharmacological class annotation |
| `stem_class` | varchar | prefix, suffix, or infix |

---

### `variant_sequences`

**Purpose:** Protein variant/mutant sequences used in specific bioactivity assays, enabling activity to be annotated to a specific clinically relevant mutation.

**Row count:** 2,836

| Column | Data Type | Description |
|---|---|---|
| `variant_id` | bigint | Primary key |
| `mutation` | varchar | Mutation description (e.g., T790M) |
| `accession` | varchar | UniProt accession of the wild-type protein |
| `version` | bigint | UniProt sequence version |
| `isoform` | bigint | Isoform number |
| `sequence` | text | Full variant protein sequence |
| `organism` | varchar | Organism name |
| `tax_id` | bigint | NCBI Taxonomy ID |

---

### `activity_smid` / `activity_supp` / `activity_supp_map`

**Purpose:** These three tables together store supplementary measured values for activities that have multiple associated measurements (e.g., dose-response curves with full data). `activity_smid` groups supplementary measurements; `activity_supp` stores the values; `activity_supp_map` links activities to their supplementary groups.

| Table | Row Count | Description |
|---|---|---|
| `activity_smid` | 1,732,478 | Supplementary measurement group IDs |
| `activity_supp` | 1,776,415 | Individual supplementary measurement values |
| `activity_supp_map` | 2,010,125 | Maps `activity_id` to `smid` groups |

---

### `bioassay_ontology`

**Purpose:** BioAssay Ontology (BAO) term lookup used to annotate assay formats and endpoints.

**Row count:** 311

| Column | Data Type | Description |
|---|---|---|
| `bao_id` | varchar | BAO ontology identifier |
| `label` | varchar | Human-readable term label |

---

### `chembl_release`

**Purpose:** Historical release log of ChEMBL database versions.

**Row count:** 37

| Column | Data Type | Description |
|---|---|---|
| `chembl_release_id` | integer | Primary key |
| `chembl_release` | varchar | Release name (e.g., ChEMBL_37) |
| `creation_date` | timestamp | Release creation date |

---

### `version`

**Purpose:** Component version tracking for ChEMBL and related ontologies bundled with each release.

**Row count:** 11

**Sample values:** ChEMBL_37 (2026-05-01), Bioassay Ontology 2.0, COCONUT 2025-07

---

### `pesticide_classification` / `pesticide_class_mapping`

**Purpose:** Pesticide classification hierarchy and mapping of molecules to pesticide classes (IUPAC/PPDB).

| Table | Row Count |
|---|---|
| `pesticide_classification` | 595 |
| `pesticide_class_mapping` | 593 |

---

### `product_patents` / `patent_use_codes`

**Purpose:** FDA patent and exclusivity data for drug products. `product_patents` lists patents by product; `patent_use_codes` defines the approved use codes.

| Table | Row Count |
|---|---|
| `product_patents` | 19,705 |
| `patent_use_codes` | 4,043 |

---

### `data_validity_lookup`

**Purpose:** Lookup for 7 data validity comment codes used in `activities.data_validity_comment` to flag potential data quality issues.

**Row count:** 7

---

## Common Join Patterns for NCI-60 Compound Enrichment

### Pattern 1: Match NSC compound name to ChEMBL → get preferred name and approval status
```sql
SELECT md.molregno, md.chembl_id, md.pref_name, md.max_phase, md.first_approval
FROM chembl.molecule_synonyms ms
JOIN chembl.molecule_dictionary md ON ms.molregno = md.molregno
WHERE upper(ms.synonyms) = upper('<NSC_COMPOUND_NAME>')
```

### Pattern 2: Get MOA for a compound
```sql
SELECT md.pref_name, dm.mechanism_of_action, dm.action_type, td.pref_name AS target_name, td.organism
FROM chembl.drug_mechanism dm
JOIN chembl.molecule_dictionary md ON dm.molregno = md.molregno
JOIN chembl.target_dictionary td ON dm.tid = td.tid
WHERE dm.molregno = <molregno>
```

### Pattern 3: Get ATC class for a compound
```sql
SELECT md.pref_name, atc.level1_description, atc.level2_description, atc.level3_description, atc.level4_description, atc.level5, atc.who_name
FROM chembl.molecule_atc_classification mac
JOIN chembl.molecule_dictionary md ON mac.molregno = md.molregno
JOIN chembl.atc_classification atc ON mac.level5 = atc.level5
WHERE mac.molregno = <molregno>
```

### Pattern 4: Get therapeutic indications for a compound
```sql
SELECT md.pref_name, di.mesh_heading, di.efo_term, di.max_phase_for_ind
FROM chembl.drug_indication di
JOIN chembl.molecule_dictionary md ON di.molregno = md.molregno
WHERE di.molregno = <molregno>
ORDER BY di.max_phase_for_ind DESC
```

### Pattern 5: Get all synonyms for a compound
```sql
SELECT ms.syn_type, ms.synonyms
FROM chembl.molecule_synonyms ms
WHERE ms.molregno = <molregno>
ORDER BY ms.syn_type
```

### Pattern 6: Get structure and properties together
```sql
SELECT md.chembl_id, md.pref_name, cs.canonical_smiles, cs.standard_inchi_key,
       cp.mw_freebase, cp.alogp, cp.num_ro5_violations, cp.qed_weighted
FROM chembl.molecule_dictionary md
JOIN chembl.compound_structures cs ON md.molregno = cs.molregno
JOIN chembl.compound_properties cp ON md.molregno = cp.molregno
WHERE md.molregno = <molregno>
```

### Pattern 7: Get UniProt accession for a drug target (MOA pathway)
```sql
SELECT md.pref_name, dm.mechanism_of_action, cs_seq.accession AS uniprot_acc, cs_seq.description AS protein_name
FROM chembl.drug_mechanism dm
JOIN chembl.molecule_dictionary md ON dm.molregno = md.molregno
JOIN chembl.target_components tc ON dm.tid = tc.tid
JOIN chembl.component_sequences cs_seq ON tc.component_id = cs_seq.component_id
WHERE dm.molregno = <molregno>
  AND cs_seq.organism = 'Homo sapiens'
```
