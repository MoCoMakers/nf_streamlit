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
