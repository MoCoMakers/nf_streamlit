# DepMap Data Migration Strategy: Files → PostgreSQL + MCP

## 🎯 **Objective**
Migrate the Delta S Prime page from file-based data loading to PostgreSQL database with MCP (Model Context Protocol) integration, while maintaining the exact same UI/UX.

## 📊 **Current State Analysis**

### **Current File-Based Architecture**
- **Primary Data**: `data/DepMap/Prism19Q4/secondary-screen-dose-response-curve-parameters.csv` (1.3M rows, 499MB)
- **Secondary Data**: `data/DepMap/Public24Q2/OmicsSomaticMutationsMatrixDamaging.csv`
- **Reference Data**: `Manual_ontology.csv`
- **Performance Issues**: 
  - 2+ minute load times for large CSV files
  - WebSocket timeouts during data loading
  - Memory pressure from loading multiple large datasets
  - UI freezing during synchronous data operations

### **Identified Bottlenecks**
1. **Synchronous CSV Loading**: Blocks UI thread for 2+ minutes
2. **Memory Overhead**: Multiple large DataFrames in memory simultaneously
3. **WebSocket Limits**: Large data transfers exceed connection limits
4. **No Caching**: Data reloaded on every page refresh

## 🔍 **Database Schema Discovery**

### **Available Tables in Data Warehouse**
The data warehouse already contains optimized, pre-processed tables that can replace the current CSV-based approach:

1. **`im_dep_raw_secondary_dose_curve`** - Raw drug response data (equivalent to secondary-screen-dose-response-curve-parameters.csv)
2. **`im_dep_sprime_damaging_mutations`** - Mutation data (equivalent to OmicsSomaticMutationsMatrixDamaging.csv)
3. **`im_omics_genes`** - Gene reference data (equivalent to Manual_ontology.csv)
4. **`im_sprime_solved_s_prime`** - Pre-calculated S' values with derived metrics
5. **`fnl_sprime_pooled_delta_sprime`** - Pre-aggregated delta S' results
6. **`im_sprime_s_prime_with_mutations`** - S' values combined with mutation status

### **Key Advantages of Existing Database Structure**
- **Pre-calculated Metrics**: S' values, EFF, EFF*100, EFF/EC50 already computed
- **Pre-aggregated Results**: Delta S' calculations already performed
- **Optimized Schema**: Proper indexing and data types
- **Reduced Computation**: No need for real-time calculations in UI
- **Better Performance**: Database queries vs. CSV file processing

### **Data Mapping Analysis**
| Current CSV File | Database Table | Status |
|------------------|----------------|---------|
| `secondary-screen-dose-response-curve-parameters.csv` | `im_dep_raw_secondary_dose_curve` | ✅ Direct mapping |
| `OmicsSomaticMutationsMatrixDamaging.csv` | `im_dep_sprime_damaging_mutations` | ✅ Serialized format |
| `Manual_ontology.csv` | `im_omics_genes` | ✅ Direct mapping |
| **Calculated Fields** | `im_sprime_solved_s_prime` | ✅ Pre-calculated |
| **Aggregated Results** | `fnl_sprime_pooled_delta_sprime` | ✅ Pre-aggregated |

## 🏗️ **Target Architecture**

### **PostgreSQL + MCP Integration**
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Streamlit UI  │    │   MCP Toolbox    │    │   PostgreSQL    │
│                 │◄──►│   (Docker)       │◄──►│   Database      │
│ - Same UI/UX    │    │ - Tool Registry  │    │ - Optimized     │
│ - Cached Data   │    │ - Query Engine   │    │ - Indexed       │
│ - Fast Loading  │    │ - Connection Pool│    │ - Partitioned   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### **Data Flow Transformation**
```
BEFORE: File → Pandas → Streamlit UI
AFTER:  PostgreSQL → MCP Toolbox → Streamlit UI
```

## 📋 **Migration Plan**

### **Phase 1: MCP Toolbox Configuration & Tool Creation**
1. **MCP Toolbox Setup**
   - Deploy MCP Toolbox Docker container
   - Configure `tools.yaml` with database connections
   - Create exploration tools for data inspection

2. **Tool Definitions for Data Access**
   - Create limited exploration tools (LIMIT 100) for initial inspection
   - Define tools for each data access pattern
   - Implement caching and pagination strategies

3. **Data Validation & Mapping**
   - Validate existing database tables match CSV structure
   - Test data integrity and completeness
   - Verify pre-calculated values match current calculations

### **Phase 2: Code Migration**
1. **Replace File Loading Functions**
   ```python
   # BEFORE
   def fetch_df(file, **kwargs):
       return pd.read_csv(file, **kwargs)
   
   # AFTER
   def fetch_data_via_mcp(tool_name, params=None):
       return mcp_client.call_tool(tool_name, params)
   ```

2. **Implement Caching Strategy**
   - Use Streamlit's `@st.cache_data` for MCP results
   - Implement smart cache invalidation
   - Add progress indicators for long-running queries

3. **Error Handling & Fallbacks**
   - Graceful degradation if MCP unavailable
   - Connection retry logic
   - User-friendly error messages

## 🔄 **Key Functions & DataFrames Migration Analysis**

### **Critical Functions Requiring Backend Migration**

#### **1. Data Loading Functions** ⚠️ **HIGH PRIORITY**
| Function | Current Implementation | Database Migration | Performance Impact |
|----------|----------------------|-------------------|-------------------|
| `fetch_df(file, **kwargs)` | `pd.read_csv(data_path, **kwargs)` | MCP tool calls to database | **95%+ load time reduction** |
| `build_df(*args, **kwargs)` | CSV loading + real-time calculations | Use `im_sprime_solved_s_prime` table | **Eliminate 2+ minute calculations** |

**Migration Strategy:**
```python
# BEFORE (Current - 2+ minutes)
def fetch_df(file, **kwargs):
    data_path = Path(file)
    return pd.read_csv(data_path, **kwargs)

def build_df(*args, **kwargs):
    df = fetch_df(*args, **kwargs)
    # Real-time calculations (EFF, EFF*100, EFF/EC50, S')
    df['EFF'] = df['upper_limit'] - df['lower_limit']
    df['EFF*100'] = df['EFF'] * 100
    df['EFF/EC50'] = df['EFF'] / df['ec50']
    df["S'"] = np.arcsinh(df['EFF*100'] / df['ec50'])
    return df

# AFTER (Database - <5 seconds)
@st.cache_data(ttl=300)
def get_s_prime_data_via_mcp(studies=None, tissue=None):
    """Get pre-calculated S' data with all derived metrics"""
    client = MCPClient("http://localhost:5000")
    params = {"studies": studies, "tissue": tissue}
    result = client.call_tool("get-s-prime-with-metrics", params)
    return pd.DataFrame(result)
```

#### **2. Data Processing Functions** ⚠️ **HIGH PRIORITY**
| Function | Current Implementation | Database Migration | Performance Impact |
|----------|----------------------|-------------------|-------------------|
| `modify_df(df)` | String splitting for tissue extraction | Use pre-computed tissue column | **Eliminate pandas operations** |
| `filter_df(active_gene, tissue)` | Complex pandas merges + filtering | Single SQL query with JOINs | **90%+ processing time reduction** |
| `get_single_testvalue()` | DataFrame filtering | Parameterized SQL query | **Instant results vs seconds** |

**Migration Strategy:**
```python
# BEFORE (Current - Complex pandas operations)
def modify_df(df):
    df[['ccle', 'tissue']] = df['ccle_name'].str.split('_', n=1, expand=True)
    return df

def filter_df(active_gene, tissue):
    filtered_gene_values = damaging_mutations[damaging_mutations[active_gene].isin([0, 2])]
    dm_merged = pd.merge(df, filtered_gene_values, left_on='row_name', right_on='Unnamed: 0', how='inner')
    # Complex filtering and processing...
    return dm_merged, cmp_trgt_grp, genes_not_in_manual_ontology

# AFTER (Database - Single optimized query)
@st.cache_data(ttl=300)
def get_filtered_data_via_mcp(active_gene, tissue, studies):
    """Get filtered data with mutations and tissue in single query"""
    client = MCPClient("http://localhost:5000")
    params = {
        "gene_name": active_gene,
        "tissue": tissue,
        "studies": studies
    }
    result = client.call_tool("get-filtered-s-prime-data", params)
    return pd.DataFrame(result)
```

#### **3. Aggregation Functions** ⚠️ **CRITICAL PRIORITY**
| Function | Current Implementation | Database Migration | Performance Impact |
|----------|----------------------|-------------------|-------------------|
| `compute_compounds_test_agg(active_gene)` | Complex pandas groupby + aggregations | Use `fnl_sprime_pooled_delta_sprime` | **99%+ computation elimination** |
| `median_absolute_deviation(data)` | Real-time MAD calculations | Pre-calculated in database | **Eliminate statistical computations** |
| `calculate_modified_z_score()` | Real-time z-score calculations | Pre-calculated sensitivity scores | **Eliminate statistical computations** |

**Migration Strategy:**
```python
# BEFORE (Current - 30+ seconds of complex aggregations)
def compute_compounds_test_agg(active_gene):
    df_ref_group = dm_merged.loc[dm_merged[active_gene] == 0]
    df_test_group = dm_merged.loc[dm_merged[active_gene] == 2]
    
    # Complex groupby operations with multiple aggregations
    compounds_ref_agg_mean = df_ref_group.groupby('name').agg(
        ref_pooled_s_prime=pd.NamedAgg(column='S\'', aggfunc='mean'),
        ref_median_s_prime=pd.NamedAgg(column='S\'', aggfunc='median'),
        ref_mad=pd.NamedAgg(column='S\'', aggfunc=median_absolute_deviation),
        # ... many more aggregations
    )
    # Complex merging and delta calculations...
    return compounds_merge

# AFTER (Database - Pre-aggregated results)
@st.cache_data(ttl=600)
def get_aggregated_results_via_mcp(active_gene, tissue):
    """Get pre-calculated aggregated results"""
    client = MCPClient("http://localhost:5000")
    params = {
        "gene_name": active_gene,
        "tissue": tissue
    }
    result = client.call_tool("get-pooled-delta-s-prime", params)
    return pd.DataFrame(result)
```

#### **4. Reference Data Functions** ⚠️ **MEDIUM PRIORITY**
| Function | Current Implementation | Database Migration | Performance Impact |
|----------|----------------------|-------------------|-------------------|
| `get_unique_combinations()` | CSV loading + processing | Direct database query | **Eliminate file I/O** |
| `get_unique_moas(dataframe, column)` | DataFrame processing | Database DISTINCT query | **Eliminate pandas operations** |

**Migration Strategy:**
```python
# BEFORE (Current - File I/O + processing)
def get_unique_combinations():
    target = fetch_df('Manual_ontology.csv')
    target['Group'] = target['Group'].ffill()
    target['Group_Subgroup'] = target['Group'] + ' | ' + target['Sub']
    return target['Group_Subgroup'].unique()

# AFTER (Database - Direct query)
@st.cache_data(ttl=3600)
def get_unique_combinations_via_mcp():
    """Get unique group-subgroup combinations from database"""
    client = MCPClient("http://localhost:5000")
    result = client.call_tool("get-unique-group-combinations")
    return result
```

### **Critical DataFrames Requiring Migration**

#### **1. Primary DataFrames** ⚠️ **CRITICAL**
| DataFrame | Current Source | Database Table | Size Impact | Migration Priority |
|-----------|---------------|----------------|-------------|-------------------|
| `df` (main S' data) | `secondary-screen-dose-response-curve-parameters.csv` | `im_sprime_solved_s_prime` | 1.3M rows → Pre-calculated | **CRITICAL** |
| `damaging_mutations` | `OmicsSomaticMutationsMatrixDamaging.csv` | `im_dep_sprime_damaging_mutations` | 33.8M rows → Optimized | **CRITICAL** |
| `target` (ontology) | `Manual_ontology.csv` | `im_omics_genes` | 18.9K rows → Indexed | **HIGH** |

#### **2. Derived DataFrames** ⚠️ **HIGH PRIORITY**
| DataFrame | Current Generation | Database Alternative | Performance Impact |
|-----------|-------------------|---------------------|-------------------|
| `dm_merged` | Complex pandas merge + filtering | Single SQL JOIN query | **90%+ processing time reduction** |
| `compounds_merge` | Complex groupby + aggregations | `fnl_sprime_pooled_delta_sprime` table | **99%+ computation elimination** |
| `cmp_trgt_grp` | Iterative DataFrame building | Pre-computed target groupings | **Eliminate loops and processing** |

#### **3. Filtered DataFrames** ⚠️ **MEDIUM PRIORITY**
| DataFrame | Current Generation | Database Alternative | Performance Impact |
|-----------|-------------------|---------------------|-------------------|
| `filtered_compounds_by_class()` | DataFrame filtering with lambda functions | SQL WHERE clauses | **Eliminate pandas operations** |
| `filtered_compounds_by_moa()` | DataFrame filtering with lambda functions | SQL WHERE clauses | **Eliminate pandas operations** |

### **Required MCP Tool Definitions for Migration**

#### **1. Core Data Access Tools**
```yaml
tools:
  get-s-prime-with-metrics:
    kind: postgres-sql
    source: postgres-readonly
    description: Get S' data with all pre-calculated metrics
    parameters:
      - name: studies
        type: array
        description: List of study IDs to filter by
      - name: tissue
        type: string
        description: Tissue type to filter by
    statement: |
      SELECT name, moa, target, lower_limit, upper_limit, ec50, auc, 
             ccle_name, row_name, screen_id, tissue, eff, eff_100, eff_ec50, s_prime
      FROM im_sprime_solved_s_prime 
      WHERE ($1 IS NULL OR screen_id = ANY($1))
        AND ($2 IS NULL OR tissue = $2)
      ORDER BY name;

  get-filtered-s-prime-data:
    kind: postgres-sql
    source: postgres-readonly
    description: Get filtered S' data with mutation status
    parameters:
      - name: gene_name
        type: string
        description: Gene name to filter by
      - name: tissue
        type: string
        description: Tissue type to filter by
      - name: studies
        type: array
        description: List of study IDs
    statement: |
      SELECT s.name, s.moa, s.target, s.s_prime, s.tissue, s.screen_id,
             m.mutation_value, g.name as gene_name
      FROM im_sprime_solved_s_prime s
      JOIN im_dep_sprime_damaging_mutations m ON s.row_name = m.cell_line
      JOIN im_omics_genes g ON m.gene_id = g.id
      WHERE g.name = $1 
        AND s.tissue = $2 
        AND s.screen_id = ANY($3)
        AND m.mutation_value IN (0, 2);

  get-pooled-delta-s-prime:
    kind: postgres-sql
    source: postgres-readonly
    description: Get pre-aggregated delta S' results
    parameters:
      - name: gene_name
        type: string
        description: Gene name to filter by
      - name: tissue
        type: string
        description: Tissue type to filter by
    statement: |
      SELECT f.name, f.gene_id, f.delta_s_prime, f.sensitivity, f.tissue,
             f.ref_pooled_s_prime, f.test_pooled_s_prime, f.p_val_median_man_whit,
             f.num_ref_lines, f.num_test_lines, f.moa, f.target
      FROM fnl_sprime_pooled_delta_sprime f
      JOIN im_omics_genes g ON f.gene_id = g.id
      WHERE g.name = $1 AND f.tissue = $2
      ORDER BY f.delta_s_prime DESC;
```

#### **2. Reference Data Tools**
```yaml
  get-unique-group-combinations:
    kind: postgres-sql
    source: postgres-readonly
    description: Get unique group-subgroup combinations
    statement: |
      SELECT DISTINCT CONCAT(g.name, ' | ', g.name) as group_subgroup
      FROM im_omics_genes g
      ORDER BY group_subgroup;

  get-unique-moas:
    kind: postgres-sql
    source: postgres-readonly
    description: Get unique mechanisms of action
    statement: |
      SELECT DISTINCT unnest(string_to_array(moa, ',')) as moa
      FROM im_sprime_solved_s_prime
      WHERE moa IS NOT NULL
      ORDER BY moa;
```

### **Migration Performance Impact Summary**

#### **Before Migration (Current State)**
- **Initial Load Time**: 2+ minutes (CSV loading + calculations)
- **Memory Usage**: 2-4GB (multiple large DataFrames)
- **Processing Time**: 30+ seconds for aggregations
- **UI Responsiveness**: Freezes during data operations
- **Computation**: Real-time S' calculations, EFF derivations, aggregations

#### **After Migration (Database + MCP)**
- **Initial Load Time**: <5 seconds (pre-calculated data)
- **Memory Usage**: <200MB (cached results)
- **Processing Time**: <2 seconds (database queries)
- **UI Responsiveness**: Instant, no freezing
- **Computation**: Pre-calculated values, direct database queries

#### **Key Performance Improvements**
- **95%+ reduction in load time** (2+ minutes → <5 seconds)
- **90%+ reduction in memory usage** (2-4GB → <200MB)
- **99%+ elimination of real-time calculations**
- **100% elimination of UI freezing**
- **Massive reduction in pandas operations**

### **Migration Implementation Priority**

#### **Phase 2A: Critical Functions (Week 1)**
1. ✅ **COMPLETED**: Database schema analysis
2. **NEXT**: Replace `fetch_df()` and `build_df()` with MCP calls
3. **NEXT**: Migrate `compute_compounds_test_agg()` to use pre-aggregated data
4. **NEXT**: Replace `filter_df()` with optimized SQL queries

#### **Phase 2B: Data Processing (Week 2)**
1. Migrate `modify_df()` to use pre-computed tissue data
2. Replace `get_unique_combinations()` with database queries
3. Migrate filtering functions to SQL WHERE clauses
4. Implement caching strategy for all MCP calls

#### **Phase 2C: Optimization (Week 3)**
1. Fine-tune MCP tool parameters
2. Optimize database queries
3. Implement progressive loading for large datasets
4. Add error handling and fallbacks

## 📊 **Static Files vs Derivative Calculations Analysis**

### **Static File Dependencies in Current UI**

#### **1. Direct Static File Usage** ⚠️ **REPLACE WITH DATABASE**
| UI Element | Static File | Current Usage | Database Alternative | Migration Impact |
|------------|-------------|---------------|---------------------|------------------|
| **Main S' Table Display** | `secondary-screen-dose-response-curve-parameters.csv` | Lines 62, 76: `df = build_df(...)` | `im_sprime_solved_s_prime` | **CRITICAL** - Eliminate 2+ minute load |
| **Gene Selection Dropdown** | `OmicsSomaticMutationsMatrixDamaging.csv` | Line 98: `damaging_mutations = fetch_df(...)` | `im_dep_sprime_damaging_mutations` | **HIGH** - Eliminate 33.8M row processing |
| **Tissue Selection Dropdown** | Derived from `ccle_name` splitting | Line 91-93: `modify_df()` | Pre-computed `tissue` column | **MEDIUM** - Eliminate string operations |
| **Target Grouping Reference** | `Manual_ontology.csv` | Line 125: `target = fetch_df(...)` | `im_omics_genes` | **MEDIUM** - Eliminate file I/O |
| **Group/Subgroup Combinations** | `Manual_ontology.csv` | Line 319: `get_unique_combinations()` | Database DISTINCT query | **LOW** - Eliminate pandas processing |

#### **2. Derivative Calculations from Static Files** ⚠️ **REPLACE WITH PRE-CALCULATED DATA**
| UI Element | Current Calculation | Database Alternative | Performance Impact |
|------------|-------------------|---------------------|-------------------|
| **EFF Values** | `df['EFF'] = df['upper_limit'] - df['lower_limit']` | `im_sprime_solved_s_prime.eff` | **Eliminate 1.3M calculations** |
| **EFF*100 Values** | `df['EFF*100'] = df['EFF'] * 100` | `im_sprime_solved_s_prime.eff_100` | **Eliminate 1.3M calculations** |
| **EFF/EC50 Values** | `df['EFF/EC50'] = df['EFF'] / df['ec50']` | `im_sprime_solved_s_prime.eff_ec50` | **Eliminate 1.3M calculations** |
| **S' Values** | `df["S'"] = np.arcsinh(df['EFF*100'] / df['ec50'])` | `im_sprime_solved_s_prime.s_prime` | **Eliminate 1.3M complex calculations** |
| **Tissue Extraction** | `df[['ccle', 'tissue']] = df['ccle_name'].str.split('_', n=1, expand=True)` | Pre-computed `tissue` column | **Eliminate string operations** |

#### **3. Complex Derivative Aggregations** ⚠️ **REPLACE WITH PRE-AGGREGATED DATA**
| UI Element | Current Calculation | Database Alternative | Performance Impact |
|------------|-------------------|---------------------|-------------------|
| **Pooled Delta S' Results** | `compute_compounds_test_agg()` - 30+ seconds of groupby operations | `fnl_sprime_pooled_delta_sprime` | **99%+ computation elimination** |
| **Reference Group Statistics** | Real-time mean, median, MAD calculations | Pre-calculated `ref_pooled_s_prime`, `ref_median_s_prime`, `ref_mad` | **Eliminate statistical computations** |
| **Test Group Statistics** | Real-time mean, median, MAD calculations | Pre-calculated `test_pooled_s_prime`, `test_median_s_prime`, `test_mad` | **Eliminate statistical computations** |
| **Delta Calculations** | `delta_s_prime = ref_pooled_s_prime - test_pooled_s_prime` | Pre-calculated `delta_s_prime` | **Eliminate arithmetic operations** |
| **Sensitivity Classification** | `np.where(delta_s_prime < -0.5, 'Sensitive', ...)` | Pre-calculated `sensitivity` column | **Eliminate conditional logic** |
| **Mann-Whitney U Test** | Real-time `mannwhitneyu()` calculations | Pre-calculated `p_val_median_man_whit` | **Eliminate statistical tests** |

### **Proposed UI Element to Database Table Mapping**

#### **Direct Static File Replacements**
```python
# BEFORE: Static file loading (2+ minutes)
df = build_df("data/DepMap/Prism19Q4/secondary-screen-dose-response-curve-parameters.csv")
damaging_mutations = fetch_df('data/DepMap/Public24Q2/OmicsSomaticMutationsMatrixDamaging.csv')
target = fetch_df('Manual_ontology.csv')

# AFTER: Database queries (<5 seconds)
@st.cache_data(ttl=300)
def get_s_prime_data():
    return mcp_client.call_tool("get-s-prime-with-metrics")

@st.cache_data(ttl=600) 
def get_damaging_mutations():
    return mcp_client.call_tool("get-damaging-mutations")

@st.cache_data(ttl=3600)
def get_gene_ontology():
    return mcp_client.call_tool("get-gene-ontology")
```

#### **Derivative Calculation Replacements**
```python
# BEFORE: Real-time calculations (30+ seconds)
def compute_compounds_test_agg(active_gene):
    df_ref_group = dm_merged.loc[dm_merged[active_gene] == 0]
    df_test_group = dm_merged.loc[dm_merged[active_gene] == 2]
    # Complex groupby operations with multiple aggregations...
    return compounds_merge

# AFTER: Pre-calculated results (<2 seconds)
@st.cache_data(ttl=300)
def get_aggregated_results(active_gene, tissue):
    return mcp_client.call_tool("get-pooled-delta-s-prime", {
        "gene_name": active_gene,
        "tissue": tissue
    })
```

### **UI Element Migration Priority Matrix**

#### **CRITICAL PRIORITY** (Week 1)
| UI Element | Current Implementation | Database Alternative | Expected Performance Gain |
|------------|----------------------|---------------------|---------------------------|
| **Main S' Table** | CSV loading + real-time calculations | `im_sprime_solved_s_prime` | **95%+ load time reduction** |
| **Pooled Delta S' Results** | Complex pandas aggregations | `fnl_sprime_pooled_delta_sprime` | **99%+ computation elimination** |
| **Gene Selection** | CSV loading + column processing | `im_dep_sprime_damaging_mutations` | **90%+ processing time reduction** |

#### **HIGH PRIORITY** (Week 2)
| UI Element | Current Implementation | Database Alternative | Expected Performance Gain |
|------------|----------------------|---------------------|---------------------------|
| **Tissue Selection** | String splitting operations | Pre-computed `tissue` column | **Eliminate pandas operations** |
| **Target Grouping** | CSV loading + processing | `im_omics_genes` | **Eliminate file I/O** |
| **Filtered Results** | Complex pandas merges | Single SQL JOIN query | **90%+ processing time reduction** |

#### **MEDIUM PRIORITY** (Week 3)
| UI Element | Current Implementation | Database Alternative | Expected Performance Gain |
|------------|----------------------|---------------------|---------------------------|
| **Group/Subgroup Combinations** | CSV processing + unique operations | Database DISTINCT query | **Eliminate pandas operations** |
| **MOA Filtering** | DataFrame processing | SQL WHERE clauses | **Eliminate pandas operations** |
| **Download Functions** | DataFrame to CSV conversion | Direct database export | **Eliminate memory operations** |

### **Database Schema Utilization Strategy**

#### **Primary Tables for UI Elements**
| UI Element | Primary Table | Secondary Tables | Join Strategy |
|------------|---------------|------------------|---------------|
| **Main S' Display** | `im_sprime_solved_s_prime` | None | Direct query |
| **Gene-Tissue Filtering** | `im_sprime_solved_s_prime` | `im_dep_sprime_damaging_mutations`, `im_omics_genes` | JOIN on `row_name` ↔ `cell_line`, `gene_id` |
| **Aggregated Results** | `fnl_sprime_pooled_delta_sprime` | `im_omics_genes` | JOIN on `gene_id` |
| **Reference Data** | `im_omics_genes` | None | Direct query |

#### **Pre-calculated Fields Utilization**
| Current Calculation | Database Field | Performance Impact |
|-------------------|----------------|-------------------|
| `EFF = upper_limit - lower_limit` | `im_sprime_solved_s_prime.eff` | **1.3M calculations eliminated** |
| `EFF*100` | `im_sprime_solved_s_prime.eff_100` | **1.3M calculations eliminated** |
| `EFF/EC50` | `im_sprime_solved_s_prime.eff_ec50` | **1.3M calculations eliminated** |
| `S' = ASINH((EFF*100)/EC50)` | `im_sprime_solved_s_prime.s_prime` | **1.3M complex calculations eliminated** |
| `delta_s_prime = ref - test` | `fnl_sprime_pooled_delta_sprime.delta_s_prime` | **3.7M calculations eliminated** |
| `sensitivity = WHERE(delta_s_prime < -0.5, 'Sensitive', ...)` | `fnl_sprime_pooled_delta_sprime.sensitivity` | **3.7M conditional operations eliminated** |

### **Migration Implementation Strategy**

#### **Phase 1: Static File Elimination**
1. **Replace CSV loading functions** with MCP database calls
2. **Eliminate real-time calculations** by using pre-calculated fields
3. **Implement caching strategy** for all database queries

#### **Phase 2: Derivative Calculation Elimination**
1. **Replace aggregation functions** with pre-aggregated table queries
2. **Eliminate statistical computations** by using pre-calculated values
3. **Optimize filtering operations** with SQL WHERE clauses

#### **Phase 3: UI Optimization**
1. **Implement progressive loading** for large datasets
2. **Add loading indicators** for database operations
3. **Optimize download functions** with direct database exports

### **Expected Performance Transformation**

#### **Before Migration (Current State)**
- **Initial Load**: 2+ minutes (CSV loading + calculations)
- **Memory Usage**: 2-4GB (multiple large DataFrames)
- **Processing Time**: 30+ seconds for aggregations
- **UI Responsiveness**: Freezes during operations
- **Computation**: Real-time calculations for 1.3M+ rows

#### **After Migration (Database + MCP)**
- **Initial Load**: <5 seconds (pre-calculated data)
- **Memory Usage**: <200MB (cached results)
- **Processing Time**: <2 seconds (database queries)
- **UI Responsiveness**: Instant, no freezing
- **Computation**: Pre-calculated values, direct queries

### **Phase 3: Performance Optimization**
1. **Query Optimization**
   - Implement pagination for large result sets
   - Add query result caching
   - Optimize database indexes

2. **UI Responsiveness**
   - Add loading spinners for async operations
   - Implement progressive data loading
   - Background data prefetching

### **Phase 4: Testing & Validation**
1. **Data Integrity Verification**
   - Compare results between file and database versions
   - Validate all calculations and aggregations
   - Performance benchmarking

2. **User Acceptance Testing**
   - Ensure UI/UX remains identical
   - Test all interactive features
   - Validate download functionality

## 🛠️ **Technical Implementation**

### **Existing Database Schema (Already Implemented)**
The database already contains optimized tables with proper indexing:

```sql
-- Main drug response data (already exists)
-- im_dep_raw_secondary_dose_curve: 20 columns including all CSV fields
-- im_sprime_solved_s_prime: Pre-calculated S' values with derived metrics
-- im_dep_sprime_damaging_mutations: Serialized mutation data
-- im_omics_genes: Gene reference data
-- fnl_sprime_pooled_delta_sprime: Pre-aggregated results

-- Key advantages:
-- ✅ Pre-calculated EFF, EFF*100, EFF/EC50, S' values
-- ✅ Pre-aggregated delta S' calculations
-- ✅ Proper indexing and data types
-- ✅ Optimized for query performance
```

### **Required MCP Tool Definitions**
```yaml
tools:
  explore-drug-response-data:
    kind: postgres-sql
    source: postgres-readonly
    description: Explore drug response data with limited results for inspection
    parameters:
      - name: limit
        type: integer
        description: Maximum number of rows to return
        default: 100
      - name: compound_name
        type: string
        description: Filter by compound name (optional)
    statement: |
      SELECT * FROM im_dep_raw_secondary_dose_curve 
      WHERE ($2 IS NULL OR name ILIKE '%' || $2 || '%')
      ORDER BY name
      LIMIT $1;

  explore-s-prime-calculated:
    kind: postgres-sql
    source: postgres-readonly
    description: Explore pre-calculated S' values
    parameters:
      - name: limit
        type: integer
        description: Maximum number of rows to return
        default: 100
    statement: |
      SELECT * FROM im_sprime_solved_s_prime 
      ORDER BY name
      LIMIT $1;

  explore-damaging-mutations:
    kind: postgres-sql
    source: postgres-readonly
    description: Explore damaging mutation data
    parameters:
      - name: limit
        type: integer
        description: Maximum number of rows to return
        default: 100
    statement: |
      SELECT * FROM im_dep_sprime_damaging_mutations 
      ORDER BY cell_line
      LIMIT $1;

  explore-gene-ontology:
    kind: postgres-sql
    source: postgres-readonly
    description: Explore gene ontology reference data
    statement: SELECT * FROM im_omics_genes;

  explore-aggregated-results:
    kind: postgres-sql
    source: postgres-readonly
    description: Explore pre-aggregated delta S' results
    parameters:
      - name: limit
        type: integer
        description: Maximum number of rows to return
        default: 100
    statement: |
      SELECT * FROM fnl_sprime_pooled_delta_sprime 
      ORDER BY name
      LIMIT $1;
```

### **Streamlit Integration Code**
```python
import streamlit as st
from mcp_toolbox_client import MCPClient

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_s_prime_data(limit=10000, compound_name=None):
    """Get pre-calculated S' data via MCP"""
    client = MCPClient("http://localhost:5000")
    params = {"limit": limit}
    if compound_name:
        params["compound_name"] = compound_name
    
    result = client.call_tool("explore-s-prime-calculated", params)
    return pd.DataFrame(result)

@st.cache_data(ttl=600)  # Cache for 10 minutes
def get_damaging_mutations(limit=10000):
    """Get damaging mutations via MCP"""
    client = MCPClient("http://localhost:5000")
    result = client.call_tool("explore-damaging-mutations", {"limit": limit})
    return pd.DataFrame(result)

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_gene_ontology():
    """Get gene ontology reference data via MCP"""
    client = MCPClient("http://localhost:5000")
    result = client.call_tool("explore-gene-ontology")
    return pd.DataFrame(result)

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_aggregated_results(limit=10000, gene_id=None, tissue=None):
    """Get pre-aggregated delta S' results via MCP"""
    client = MCPClient("http://localhost:5000")
    params = {"limit": limit}
    # Add filtering logic based on gene_id and tissue
    result = client.call_tool("explore-aggregated-results", params)
    return pd.DataFrame(result)
```

## 📈 **Expected Performance Improvements**

### **Load Time Reduction**
- **Before**: 2+ minutes for initial page load (CSV processing + calculations)
- **After**: <5 seconds for initial page load (pre-calculated data)
- **Improvement**: 95%+ reduction in load time

### **Memory Usage**
- **Before**: 2-4GB RAM usage with multiple large DataFrames + calculations
- **After**: <200MB RAM usage with cached, pre-calculated results
- **Improvement**: 90%+ reduction in memory usage

### **Computation Reduction**
- **Before**: Real-time S' calculations, EFF derivations, aggregations
- **After**: Pre-calculated values, direct database queries
- **Improvement**: 100% elimination of real-time calculations

### **User Experience**
- **Before**: UI freezes during data loading and calculations
- **After**: Instant responsive UI with pre-calculated data
- **Improvement**: Seamless, real-time user experience

## 🔧 **Deployment Architecture**

### **Simplified Docker Setup (Remote PostgreSQL)**
```bash
# Run MCP Toolbox with remote PostgreSQL connection
docker run -p 5000:5000 \
  -v $(pwd)/tools.yaml:/app/tools.yaml \
  us-central1-docker.pkg.dev/database-toolbox/toolbox/toolbox:latest \
  --tools-file /app/tools.yaml
```

### **Architecture Overview**
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Streamlit UI  │    │   MCP Toolbox    │    │   Remote        │
│   (Local)       │◄──►│   (Docker)       │◄──►│   PostgreSQL    │
│                 │    │   Port 5000      │    │   Database      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### **Updated tools.yaml Configuration**
```yaml
sources:
  postgres-readonly:
    kind: postgres
    host: your-remote-postgres-host.com  # Remote PostgreSQL host
    port: 5432
    database: depmap_db
    user: depmap_user
    password: your_remote_password
    sslmode: require  # For remote connections
```

## 🚀 **Migration Timeline**

### **Week 1: Data Exploration & Tool Creation**
- ✅ **COMPLETED**: Database schema discovery and analysis
- ✅ **COMPLETED**: Data mapping analysis
- **NEXT**: Create MCP exploration tools for data inspection
- **NEXT**: Validate data integrity and completeness

### **Week 2: Tool Development & Testing**
- Create production MCP tools for data access
- Test data retrieval and caching strategies
- Validate pre-calculated values match current calculations

### **Week 3: Code Migration**
- Replace file loading with MCP calls
- Implement caching strategy
- Add error handling and fallbacks

### **Week 4: Testing & Optimization**
- Performance testing and optimization
- User acceptance testing
- Documentation updates

## 🎯 **Immediate Next Steps**

### **1. Create Exploration Tools**
Add the following tools to `tools.yaml` for initial data inspection:

```yaml
tools:
  explore-drug-response-sample:
    kind: postgres-sql
    source: postgres-readonly
    description: Get sample drug response data for inspection
    statement: |
      SELECT name, moa, target, lower_limit, upper_limit, ec50, auc, ccle_name, row_name, screen_id
      FROM im_dep_raw_secondary_dose_curve 
      ORDER BY name
      LIMIT 100;

  explore-s-prime-sample:
    kind: postgres-sql
    source: postgres-readonly
    description: Get sample pre-calculated S' data for inspection
    statement: |
      SELECT name, moa, target, lower_limit, upper_limit, ec50, auc, eff, eff_100, eff_ec50, s_prime
      FROM im_sprime_solved_s_prime 
      ORDER BY name
      LIMIT 100;

  explore-mutations-sample:
    kind: postgres-sql
    source: postgres-readonly
    description: Get sample mutation data for inspection
    statement: |
      SELECT cell_line, gene_id, mutation_value
      FROM im_dep_sprime_damaging_mutations 
      ORDER BY cell_line
      LIMIT 100;

  explore-aggregated-sample:
    kind: postgres-sql
    source: postgres-readonly
    description: Get sample aggregated results for inspection
    statement: |
      SELECT name, gene_id, delta_s_prime, sensitivity, tissue
      FROM fnl_sprime_pooled_delta_sprime 
      ORDER BY name
      LIMIT 100;
```

### **2. Data Validation Tasks**
- Compare sample data from database vs CSV files
- Verify S' calculations match current implementation
- Test mutation data serialization format
- Validate gene ontology mapping

## 🎯 **Success Metrics**

### **Performance Metrics**
- Page load time: <10 seconds (vs current 2+ minutes)
- Memory usage: <500MB (vs current 2-4GB)
- Database query response time: <2 seconds
- UI responsiveness: No freezing during data operations

### **User Experience Metrics**
- Identical UI/UX to current implementation
- All existing functionality preserved
- Improved error handling and user feedback
- Faster data filtering and analysis

### **Technical Metrics**
- 99.9% uptime for MCP Toolbox service
- Database connection pool efficiency >90%
- Cache hit rate >80%
- Zero data integrity issues

## 🔒 **Risk Mitigation**

### **Technical Risks**
1. **MCP Service Downtime**: Implement fallback to cached data
2. **Database Performance**: Monitor and optimize queries
3. **Data Consistency**: Implement validation checks
4. **Migration Complexity**: Phased rollout with rollback plan

### **Mitigation Strategies**
- Comprehensive testing environment
- Gradual migration with A/B testing
- Monitoring and alerting systems
- Detailed rollback procedures

## 📚 **Documentation Requirements**

1. **Technical Documentation**
   - Database schema documentation
   - MCP tool definitions and usage
   - API documentation for MCP integration
   - Performance tuning guide

2. **User Documentation**
   - Updated README with setup instructions
   - Troubleshooting guide
   - Performance optimization tips
   - Migration guide for developers

3. **Operational Documentation**
   - Deployment procedures
   - Monitoring and maintenance
   - Backup and recovery procedures
   - Security best practices

## 🎉 **Conclusion**

This migration strategy will transform the DepMap application from a file-based, slow-loading system to a high-performance, database-driven application with MCP integration. The result will be a significantly improved user experience while maintaining all existing functionality and UI/UX.

The phased approach ensures minimal risk while delivering substantial performance improvements and setting the foundation for future enhancements and scalability.
