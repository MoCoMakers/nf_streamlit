# Database Schema Reference

## Overview
This document provides a comprehensive reference for all tables in the DepMap data warehouse used by the Delta S Prime application.

## Table Inventory

### 1. **im_dep_raw_secondary_dose_curve** (Primary Drug Response Data)
**Purpose**: Raw drug response data from DepMap secondary screens
**Size**: Large (equivalent to secondary-screen-dose-response-curve-parameters.csv)

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| broad_id | VARCHAR(255) | YES | Broad Institute ID |
| depmap_id | VARCHAR(255) | YES | DepMap ID |
| ccle_name | VARCHAR(1000) | YES | CCLE cell line name |
| screen_id | VARCHAR(50) | YES | Screen identifier |
| upper_limit | INTEGER | YES | Upper limit of dose response |
| lower_limit | DOUBLE PRECISION | YES | Lower limit of dose response |
| slope | DOUBLE PRECISION | YES | Dose response slope |
| r2 | DOUBLE PRECISION | YES | R-squared value |
| auc | DOUBLE PRECISION | YES | Area under curve |
| ec50 | DOUBLE PRECISION | YES | EC50 value |
| ic50 | DOUBLE PRECISION | YES | IC50 value |
| name | VARCHAR(255) | YES | Compound name |
| moa | VARCHAR(1000) | YES | Mechanism of action |
| target | VARCHAR(1000) | YES | Drug target |
| disease_area | VARCHAR(1000) | YES | Disease area |
| indication | VARCHAR(1000) | YES | Indication |
| smiles | VARCHAR(1500) | YES | SMILES structure |
| phase | VARCHAR(255) | YES | Clinical phase |
| passed_str_profiling | BOOLEAN | YES | Passed structure profiling |
| row_name | VARCHAR(255) | YES | Row identifier |

### 2. **im_dep_sprime_damaging_mutations** (Mutation Data)
**Purpose**: Damaging mutation data for cell lines
**Size**: Large (equivalent to OmicsSomaticMutationsMatrixDamaging.csv)

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| cell_line | VARCHAR(255) | YES | Cell line identifier |
| gene_id | INTEGER | YES | Gene identifier |
| mutation_value | INTEGER | YES | Mutation status (0=WT, 2=Mutated) |

### 3. **im_omics_genes** (Gene Reference)
**Purpose**: Gene ontology and reference data
**Size**: Small (equivalent to Manual_ontology.csv)

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | INTEGER | NO | Primary key |
| name | VARCHAR(100) | YES | Gene name |

### 4. **im_sprime_solved_s_prime** (Pre-calculated S' Values)
**Purpose**: Pre-calculated S' values with derived metrics
**Size**: Large (processed from raw data)

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | INTEGER | NO | Primary key |
| broad_id | VARCHAR(255) | YES | Broad Institute ID |
| depmap_id | VARCHAR(255) | YES | DepMap ID |
| ccle_name | VARCHAR(1000) | YES | CCLE cell line name |
| screen_id | VARCHAR(50) | YES | Screen identifier |
| upper_limit | INTEGER | YES | Upper limit of dose response |
| lower_limit | DOUBLE PRECISION | YES | Lower limit of dose response |
| slope | DOUBLE PRECISION | YES | Dose response slope |
| r2 | DOUBLE PRECISION | YES | R-squared value |
| auc | DOUBLE PRECISION | YES | Area under curve |
| ec50 | DOUBLE PRECISION | YES | EC50 value |
| ic50 | DOUBLE PRECISION | YES | IC50 value |
| name | VARCHAR(255) | YES | Compound name |
| moa | VARCHAR(1000) | YES | Mechanism of action |
| target | VARCHAR(1000) | YES | Drug target |
| disease_area | VARCHAR(1000) | YES | Disease area |
| indication | VARCHAR(1000) | YES | Indication |
| smiles | VARCHAR(1500) | YES | SMILES structure |
| phase | VARCHAR(255) | YES | Clinical phase |
| passed_str_profiling | BOOLEAN | YES | Passed structure profiling |
| row_name | VARCHAR(255) | YES | Row identifier |
| eff | DOUBLE PRECISION | YES | EFF = upper_limit - lower_limit |
| eff_100 | DOUBLE PRECISION | YES | EFF*100 |
| eff_ec50 | DOUBLE PRECISION | YES | EFF/EC50 |
| s_prime | DOUBLE PRECISION | YES | S' = ASINH((EFF*100)/EC50) |

### 5. **fnl_sprime_pooled_delta_sprime** (Final Aggregated Results)
**Purpose**: Final aggregated delta S' calculations
**Size**: Medium (aggregated by compound and gene)

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| name | VARCHAR(255) | YES | Compound name |
| gene_id | INTEGER | YES | Gene identifier |
| ref_pooled_s_prime | DOUBLE PRECISION | YES | Reference group mean S' |
| ref_median_s_prime | DOUBLE PRECISION | YES | Reference group median S' |
| ref_mad | DOUBLE PRECISION | YES | Reference group MAD |
| ref_pooled_auc | DOUBLE PRECISION | YES | Reference group mean AUC |
| ref_pooled_ec50 | DOUBLE PRECISION | YES | Reference group mean EC50 |
| num_ref_lines | INTEGER | YES | Number of reference cell lines |
| ref_s_prime_variance | DOUBLE PRECISION | YES | Reference group S' variance |
| test_pooled_s_prime | DOUBLE PRECISION | YES | Test group mean S' |
| test_median_s_prime | DOUBLE PRECISION | YES | Test group median S' |
| test_mad | DOUBLE PRECISION | YES | Test group MAD |
| test_pooled_auc | DOUBLE PRECISION | YES | Test group mean AUC |
| test_pooled_ec50 | DOUBLE PRECISION | YES | Test group mean EC50 |
| num_test_lines | INTEGER | YES | Number of test cell lines |
| test_s_prime_variance | DOUBLE PRECISION | YES | Test group S' variance |
| delta_s_prime | DOUBLE PRECISION | YES | Delta S' = ref - test |
| delta_auc | DOUBLE PRECISION | YES | Delta AUC = ref - test |
| delta_ec50 | DOUBLE PRECISION | YES | Delta EC50 = ref - test |
| delta_s_prime_median | DOUBLE PRECISION | YES | Delta S' median = ref - test |
| p_val_median_man_whit | DOUBLE PRECISION | YES | Mann-Whitney U test p-value |
| sensitivity_score | INTEGER | YES | Sensitivity score (-1, 0, 1) |
| sensitivity | VARCHAR(50) | YES | Sensitivity classification |
| moa | VARCHAR(1000) | YES | Mechanism of action |
| target | VARCHAR(1000) | YES | Drug target |
| tissue | VARCHAR(255) | YES | Tissue type |

### 6. **im_sprime_s_prime_with_mutations** (S' with Mutation Status)
**Purpose**: S' values combined with mutation status
**Size**: Large (joined data)

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| s_prime_id | INTEGER | YES | Reference to S' calculation |
| cell_line | VARCHAR(255) | YES | Cell line identifier |
| tissue | VARCHAR(255) | YES | Tissue type |
| gene_id | INTEGER | YES | Gene identifier |
| mutation_value | INTEGER | YES | Mutation status |

### 7. **im_dep_sprime_damaging_mutations_temp** (Temporary Mutation Data)
**Purpose**: Temporary/working mutation data
**Size**: Large

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| cell_line | VARCHAR(255) | YES | Cell line identifier |
| gene_id | INTEGER | YES | Gene identifier |
| mutation_value | INTEGER | YES | Mutation status |

### 8. **fnl_sprime_pooled_delta_sprime_temp** (Temporary Aggregated Results)
**Purpose**: Temporary/working aggregated results
**Size**: Medium

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| name | VARCHAR(255) | YES | Compound name |
| gene_id | INTEGER | YES | Gene identifier |
| ref_pooled_s_prime | DOUBLE PRECISION | YES | Reference group mean S' |
| ref_median_s_prime | DOUBLE PRECISION | YES | Reference group median S' |
| ref_mad | DOUBLE PRECISION | YES | Reference group MAD |
| ref_pooled_auc | DOUBLE PRECISION | YES | Reference group mean AUC |
| ref_pooled_ec50 | DOUBLE PRECISION | YES | Reference group mean EC50 |
| num_ref_lines | INTEGER | YES | Number of reference cell lines |
| ref_s_prime_variance | DOUBLE PRECISION | YES | Reference group S' variance |
| test_pooled_s_prime | DOUBLE PRECISION | YES | Test group mean S' |
| test_median_s_prime | DOUBLE PRECISION | YES | Test group median S' |
| test_mad | DOUBLE PRECISION | YES | Test group MAD |
| test_pooled_auc | DOUBLE PRECISION | YES | Test group mean AUC |
| test_pooled_ec50 | DOUBLE PRECISION | YES | Test group mean EC50 |
| num_test_lines | INTEGER | YES | Number of test cell lines |
| test_s_prime_variance | DOUBLE PRECISION | YES | Test group S' variance |
| delta_s_prime | DOUBLE PRECISION | YES | Delta S' = ref - test |
| delta_auc | DOUBLE PRECISION | YES | Delta AUC = ref - test |
| delta_ec50 | DOUBLE PRECISION | YES | Delta EC50 = ref - test |
| delta_s_prime_median | DOUBLE PRECISION | YES | Delta S' median = ref - test |
| p_val_median_man_whit | DOUBLE PRECISION | YES | Mann-Whitney U test p-value |
| sensitivity_score | INTEGER | YES | Sensitivity score (-1, 0, 1) |
| sensitivity | VARCHAR(50) | YES | Sensitivity classification |
| moa | VARCHAR(1000) | YES | Mechanism of action |
| target | VARCHAR(1000) | YES | Drug target |
| tissue | VARCHAR(255) | YES | Tissue type |

## Data Flow Architecture

```
Raw Data → Processed Data → Aggregated Results
    ↓           ↓              ↓
im_dep_raw_secondary_dose_curve → im_sprime_solved_s_prime → fnl_sprime_pooled_delta_sprime
im_dep_sprime_damaging_mutations → im_sprime_s_prime_with_mutations
im_omics_genes (reference data)
```

## Key Relationships

### **Primary Keys**
Based on the schema analysis, the following primary keys are identified:

| Table | Primary Key | Type | Description |
|-------|-------------|------|-------------|
| `im_dep_raw_secondary_dose_curve` | **Composite Key** | Multiple columns | No single PK, likely uses combination of `row_name`, `name`, `screen_id` |
| `im_dep_sprime_damaging_mutations` | **Composite Key** | Multiple columns | No single PK, likely uses combination of `cell_line`, `gene_id` |
| `im_omics_genes` | `id` | INTEGER | Auto-incrementing primary key |
| `im_sprime_solved_s_prime` | `id` | INTEGER | Auto-incrementing primary key |
| `fnl_sprime_pooled_delta_sprime` | **Composite Key** | Multiple columns | No single PK, likely uses combination of `name`, `gene_id`, `tissue` |
| `im_sprime_s_prime_with_mutations` | **Composite Key** | Multiple columns | No single PK, likely uses combination of `s_prime_id`, `cell_line`, `gene_id` |

### **Foreign Key Relationships**
Based on column name patterns and data flow analysis:

| Source Table | Source Column | Target Table | Target Column | Relationship Type |
|--------------|---------------|--------------|---------------|-------------------|
| `im_sprime_solved_s_prime` | `id` | `im_sprime_s_prime_with_mutations` | `s_prime_id` | One-to-Many |
| `im_dep_sprime_damaging_mutations` | `gene_id` | `im_omics_genes` | `id` | Many-to-One |
| `im_dep_sprime_damaging_mutations` | `cell_line` | `im_dep_raw_secondary_dose_curve` | `row_name` | Many-to-One |
| `im_sprime_s_prime_with_mutations` | `gene_id` | `im_omics_genes` | `id` | Many-to-One |
| `fnl_sprime_pooled_delta_sprime` | `gene_id` | `im_omics_genes` | `id` | Many-to-One |

### **Logical Data Flow Relationships**

1. **Primary Data Flow**:
   - `im_dep_raw_secondary_dose_curve` → `im_sprime_solved_s_prime` (adds calculated fields)
   - `im_sprime_solved_s_prime` + `im_dep_sprime_damaging_mutations` → `im_sprime_s_prime_with_mutations`
   - `im_sprime_s_prime_with_mutations` → `fnl_sprime_pooled_delta_sprime` (aggregated results)

2. **Key Join Fields**:
   - `row_name` (dose curve) ↔ `cell_line` (mutations)
   - `gene_id` (mutations) ↔ `gene_id` (genes reference)
   - `s_prime_id` (solved) ↔ `id` (solved table)

3. **Temporary Tables**:
   - `*_temp` tables appear to be working/processing tables
   - Should use main tables for production queries

### **Relationship Diagram**
```
im_omics_genes (id)
    ↑
    │ gene_id
    │
im_dep_sprime_damaging_mutations (cell_line, gene_id)
    ↑
    │ cell_line
    │
im_dep_raw_secondary_dose_curve (row_name, name, screen_id)
    ↓
    │ (adds calculated fields)
    │
im_sprime_solved_s_prime (id, row_name, name, screen_id)
    ↓
    │ s_prime_id
    │
im_sprime_s_prime_with_mutations (s_prime_id, cell_line, gene_id)
    ↓
    │ (aggregated by name, gene_id, tissue)
    │
fnl_sprime_pooled_delta_sprime (name, gene_id, tissue)
```

## Migration Implications

### Current CSV Files → Database Tables Mapping:
- `secondary-screen-dose-response-curve-parameters.csv` → `im_dep_raw_secondary_dose_curve`
- `OmicsSomaticMutationsMatrixDamaging.csv` → `im_dep_sprime_damaging_mutations`
- `Manual_ontology.csv` → `im_omics_genes`

### Pre-calculated Data Available:
- S' calculations already done in `im_sprime_solved_s_prime`
- Aggregated results available in `fnl_sprime_pooled_delta_sprime`
- This significantly reduces computation needed in the UI

### Performance Benefits:
- No need to recalculate S' values in real-time
- Pre-aggregated results available for common queries
- Proper indexing on large tables
- Reduced memory usage in Streamlit application

## 🔗 **Relationship Implications for Migration**

### **Query Optimization Opportunities**
Based on the identified relationships, the following query patterns can be optimized:

1. **Direct Aggregated Results**: 
   - Use `fnl_sprime_pooled_delta_sprime` for final results instead of real-time calculations
   - Pre-filtered by `gene_id`, `tissue`, and `name` combinations

2. **Efficient Joins**:
   - Join `im_sprime_solved_s_prime` with `im_dep_sprime_damaging_mutations` using `row_name` ↔ `cell_line`
   - Reference `im_omics_genes` for gene name lookups using `gene_id`

3. **Indexed Lookups**:
   - Primary keys (`id` columns) provide fast lookups
   - Composite keys enable efficient filtering on multiple dimensions

### **Migration Strategy Benefits**
The identified relationships enable:

- **Simplified Queries**: Use pre-calculated tables instead of complex joins
- **Reduced Complexity**: Eliminate real-time S' calculations and aggregations
- **Better Performance**: Leverage database indexes and optimized query plans
- **Data Integrity**: Maintain referential integrity through proper relationships

### **Recommended Query Patterns**
```sql
-- Instead of calculating S' values in real-time:
-- Use pre-calculated values from im_sprime_solved_s_prime

-- Instead of aggregating delta S' in real-time:
-- Use pre-aggregated results from fnl_sprime_pooled_delta_sprime

-- For gene name lookups:
-- Join with im_omics_genes using gene_id

-- For mutation status:
-- Join with im_dep_sprime_damaging_mutations using cell_line
```
