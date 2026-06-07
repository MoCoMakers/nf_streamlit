# Final Data Warehouse Table Documentation

## Table: `fnl_sprime_pooled_delta_sprime`

### Overview

The `fnl_sprime_pooled_delta_sprime` table is the **final aggregated results table** in the cancer drug response data warehouse. It contains comprehensive drug sensitivity analysis comparing cell lines with specific gene mutations against reference (wild-type) cell lines across different tissue types.

### Purpose

This table implements the **Delta S' methodology** for cancer drug response analysis, providing:

- **Drug Sensitivity Classification**: Categorizes drugs as "Sensitive", "Resistant", or "Equivocal" based on statistical analysis
- **Gene-Drug Interactions**: Links specific gene mutations to drug response patterns
- **Tissue-Specific Analysis**: Enables comparison of drug responses across different cancer types
- **Statistical Validation**: Includes Mann-Whitney U test p-values for significance testing

### Scientific Background

#### S' Calculation
The S' metric is calculated using the formula:
```
S' = arcsinh((EFF × 100) / EC50)
```
Where:
- **EFF**: Effectiveness (drug response measure)
- **EC50**: Half-maximal effective concentration
- **arcsinh**: Inverse hyperbolic sine function for normalization

#### Delta S' Analysis
The primary metric for drug sensitivity is Delta S':
```
ΔS' = ref_pooled_s_prime - test_pooled_s_prime
```
Where:
- **ref_pooled_s_prime**: Pooled S' value for reference (wild-type) cell lines
- **test_pooled_s_prime**: Pooled S' value for test (mutated) cell lines

#### Sensitivity Classification Logic
- **Sensitive**: Negative delta S' (test cells more sensitive than reference)
- **Resistant**: Positive delta S' (test cells less sensitive than reference)
- **Equivocal**: Near-zero delta S' (no significant difference)

### Table Schema

#### Primary Identifiers
| Column | Type | Description |
|--------|------|-------------|
| `name` | VARCHAR(255) | Drug name (e.g., "10-deacetylbaccatin") |
| `gene_id` | INTEGER | Unique gene identifier |
| `tissue` | VARCHAR(255) | Tissue type (OVARY, BREAST, KIDNEY, PLEURA, etc.) |

#### Reference Group Metrics (Wild-type cells)
| Column | Type | Description |
|--------|------|-------------|
| `ref_pooled_s_prime` | DOUBLE PRECISION | Pooled S' value for reference cell lines |
| `ref_median_s_prime` | DOUBLE PRECISION | Median S' value for reference group |
| `ref_mad` | DOUBLE PRECISION | Median Absolute Deviation for reference group |
| `ref_pooled_auc` | DOUBLE PRECISION | Pooled Area Under Curve for reference |
| `ref_pooled_ec50` | DOUBLE PRECISION | Pooled EC50 for reference group |
| `num_ref_lines` | INTEGER | Number of reference cell lines |
| `ref_s_prime_variance` | DOUBLE PRECISION | Variance in S' values for reference |

#### Test Group Metrics (Mutated cells)
| Column | Type | Description |
|--------|------|-------------|
| `test_pooled_s_prime` | DOUBLE PRECISION | Pooled S' value for test cell lines |
| `test_median_s_prime` | DOUBLE PRECISION | Median S' value for test group |
| `test_mad` | DOUBLE PRECISION | Median Absolute Deviation for test group |
| `test_pooled_auc` | DOUBLE PRECISION | Pooled AUC for test group |
| `test_pooled_ec50` | DOUBLE PRECISION | Pooled EC50 for test group |
| `num_test_lines` | INTEGER | Number of test cell lines |
| `test_s_prime_variance` | DOUBLE PRECISION | Variance in S' values for test |

#### Comparative Analysis Metrics
| Column | Type | Description |
|--------|------|-------------|
| `delta_s_prime` | DOUBLE PRECISION | **Primary metric**: Difference in S' between groups |
| `delta_auc` | DOUBLE PRECISION | Difference in Area Under Curve |
| `delta_ec50` | DOUBLE PRECISION | Difference in EC50 values |
| `delta_s_prime_median` | DOUBLE PRECISION | Median delta S' value |
| `p_val_median_man_whit` | DOUBLE PRECISION | **Statistical significance**: Mann-Whitney U test p-value |

#### Classification & Metadata
| Column | Type | Description |
|--------|------|-------------|
| `sensitivity_score` | INTEGER | Numerical sensitivity score (-1, 0, 1) |
| `sensitivity` | VARCHAR(50) | **Categorical classification**: "Sensitive", "Resistant", "Equivocal" |
| `moa` | VARCHAR(1000) | Mechanism of Action (drug target/pathway) |
| `target` | VARCHAR(1000) | Specific molecular target |
| `tissue` | VARCHAR(255) | Tissue type (OVARY, BREAST, KIDNEY, PLEURA, etc.) |

### Sample Data Analysis

#### Example Records
```sql
-- Drug: 10-deacetylbaccatin, Gene ID: 7115, Tissue: OVARY
{
  "name": "10-deacetylbaccatin",
  "gene_id": 7115,
  "tissue": "OVARY",
  "ref_pooled_s_prime": 3.849075485053244,
  "test_pooled_s_prime": 2.7887841515754785,
  "delta_s_prime": 1.0602913334777653,
  "sensitivity": "Resistant",
  "p_val_median_man_whit": 0.0234
}

-- Drug: 10-deacetylbaccatin, Gene ID: 13917, Tissue: OVARY
{
  "name": "10-deacetylbaccatin",
  "gene_id": 13917,
  "tissue": "OVARY",
  "ref_pooled_s_prime": 3.4937578669285494,
  "test_pooled_s_prime": 4.8504056375751485,
  "delta_s_prime": -1.3566477706465991,
  "sensitivity": "Sensitive",
  "p_val_median_man_whit": 0.0156
}
```

#### Data Interpretation
- **Gene ID 7115**: `delta_s_prime = 1.06` → **Resistant** (positive value indicates test cells less sensitive)
- **Gene ID 13917**: `delta_s_prime = -1.36` → **Sensitive** (negative value indicates test cells more sensitive)

### Statistical Methods

#### Mann-Whitney U Test
- **Purpose**: Non-parametric test to compare distributions between reference and test groups
- **Implementation**: `scipy.stats.mannwhitneyu()`
- **Significance**: p-value < 0.05 indicates statistically significant difference
- **Column**: `p_val_median_man_whit`

#### Pooled Analysis
- **Method**: Combines multiple cell lines within each group (reference/test)
- **Advantage**: Increases statistical power and reduces noise
- **Implementation**: Weighted averaging based on cell line counts

#### Robust Statistics
- **Median Absolute Deviation (MAD)**: Robust measure of variability
- **Modified Z-score**: Outlier detection using MAD instead of standard deviation
- **Median-based metrics**: Less sensitive to outliers than mean-based metrics

### Data Quality & Validation

#### Completeness
- **Required Fields**: All core metrics must be present for valid analysis
- **Missing Data**: NULL values indicate insufficient data for reliable analysis
- **Minimum Sample Size**: Requires adequate number of cell lines per group

#### Validation Checks
- **Range Validation**: S' values typically range from -10 to +10
- **Consistency Checks**: Delta S' should equal ref_pooled_s_prime - test_pooled_s_prime
- **Statistical Validation**: P-values should be between 0 and 1

#### Data Sources
- **Raw Data**: `im_dep_raw_secondary_dose_curve` (dose-response curves)
- **Gene Information**: `im_omics_genes` (gene ontology)
- **Mutation Data**: `im_dep_sprime_damaging_mutations` (damaging mutations)
- **Processing**: `im_sprime_solved_s_prime` (S' calculations)

### Use Cases & Applications

#### 1. Drug Discovery
- **Target Identification**: Find drugs effective against specific gene mutations
- **Lead Optimization**: Prioritize compounds based on sensitivity profiles
- **Mechanism Studies**: Understand drug-gene interactions

#### 2. Precision Medicine
- **Patient Stratification**: Match patients with gene mutations to effective treatments
- **Biomarker Discovery**: Identify genes that predict drug sensitivity/resistance
- **Clinical Decision Support**: Guide treatment selection based on genetic profile

#### 3. Research Applications
- **Tissue-Specific Analysis**: Compare drug responses across cancer types
- **Pathway Analysis**: Group drugs by mechanism of action
- **Comparative Studies**: Analyze drug response patterns across different studies

#### 4. Data Visualization
- **Interactive Dashboards**: Real-time exploration of drug sensitivity data
- **Statistical Plots**: Scatter plots, distributions, and correlation matrices
- **Export Capabilities**: CSV downloads for further analysis

### API Integration

#### REST Endpoints
```python
# Get pooled delta S' results
GET /api/analysis/pooled_delta_sprime?gene_name={gene}&tissue={tissue}

# Get drug sensitivity data
GET /api/drugs/sensitivity?drug_name={drug}&tissue={tissue}

# Get statistical analysis
GET /api/analysis/statistics?gene_id={gene_id}&tissue={tissue}
```

#### Query Examples
```sql
-- Get all sensitive drugs for NF1 gene in ovarian cancer
SELECT name, delta_s_prime, p_val_median_man_whit
FROM fnl_sprime_pooled_delta_sprime
WHERE gene_id = 4763 AND tissue = 'OVARY' AND sensitivity = 'Sensitive'
ORDER BY delta_s_prime ASC;

-- Get drug resistance patterns by tissue
SELECT tissue, COUNT(*) as resistant_drugs
FROM fnl_sprime_pooled_delta_sprime
WHERE sensitivity = 'Resistant'
GROUP BY tissue
ORDER BY resistant_drugs DESC;
```

### Performance Considerations

#### Indexing Strategy
- **Primary Index**: `(gene_id, tissue, name)` for common query patterns
- **Secondary Index**: `(sensitivity, tissue)` for classification queries
- **Composite Index**: `(delta_s_prime, p_val_median_man_whit)` for statistical analysis

#### Query Optimization
- **Pagination**: Use LIMIT/OFFSET for large result sets
- **Filtering**: Apply WHERE clauses before JOINs
- **Aggregation**: Use GROUP BY for summary statistics

### Maintenance & Updates

#### Data Refresh
- **Frequency**: Updated when new drug response data becomes available
- **Process**: Recalculate S' values and delta S' metrics
- **Validation**: Verify statistical significance and data quality

#### Schema Evolution
- **Version Control**: Track schema changes and data migrations
- **Backward Compatibility**: Maintain API compatibility during updates
- **Documentation**: Update this documentation with schema changes

### Related Tables

#### Dependencies
- **`im_dep_raw_secondary_dose_curve`**: Source dose-response data
- **`im_omics_genes`**: Gene ontology and metadata
- **`im_dep_sprime_damaging_mutations`**: Mutation information
- **`im_sprime_solved_s_prime`**: Intermediate S' calculations

#### Derived Tables
- **`fnl_sprime_pooled_delta_sprime_temp`**: Temporary processing table
- **Summary Tables**: Aggregated statistics by tissue, drug class, etc.

### Security & Access

#### Data Privacy
- **Anonymization**: No patient-identifiable information
- **Access Control**: Role-based permissions for different user types
- **Audit Logging**: Track data access and modifications

#### Compliance
- **HIPAA**: Not applicable (no patient data)
- **Research Ethics**: Follow institutional review board guidelines
- **Data Sharing**: Appropriate data use agreements

---

*This documentation is maintained as part of the cancer drug response data warehouse. For questions or updates, contact the data management team.*

**Last Updated**: January 2025  
**Version**: 1.0  
**Maintained By**: Data Warehouse Team

