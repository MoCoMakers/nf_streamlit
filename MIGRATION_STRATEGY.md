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

### **Phase 1: Database Setup & Data Import**
1. **PostgreSQL Schema Design**
   - Create optimized tables with proper indexing
   - Implement partitioning for large datasets
   - Set up foreign key relationships

2. **Data Import Pipeline**
   - Import CSV files into PostgreSQL
   - Data validation and cleaning
   - Performance optimization

3. **MCP Toolbox Configuration**
   - Deploy MCP Toolbox Docker container
   - Configure `tools.yaml` with database connections
   - Set up tool definitions for each data access pattern

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

### **Database Schema Design**
```sql
-- Main drug response data
CREATE TABLE im_dep_raw_secondary_dose_curve (
    id SERIAL PRIMARY KEY,
    ccle_name VARCHAR(255),
    screen_id VARCHAR(50),
    upper_limit DECIMAL,
    lower_limit DECIMAL,
    auc DECIMAL,
    ec50 DECIMAL,
    name VARCHAR(255),
    moa TEXT,
    target TEXT,
    row_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Damaging mutations data
CREATE TABLE im_dep_sprime_damaging_mutations (
    id SERIAL PRIMARY KEY,
    cell_line VARCHAR(255),
    gene_id VARCHAR(50),
    mutation_status INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Gene ontology reference
CREATE TABLE im_omics_genes (
    id SERIAL PRIMARY KEY,
    gene_id VARCHAR(50),
    gene_name VARCHAR(255),
    group_name VARCHAR(255),
    sub_group VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_dose_curve_name ON im_dep_raw_secondary_dose_curve(name);
CREATE INDEX idx_dose_curve_ccle ON im_dep_raw_secondary_dose_curve(ccle_name);
CREATE INDEX idx_mutations_gene ON im_dep_sprime_damaging_mutations(gene_id);
```

### **MCP Tool Definitions**
```yaml
tools:
  get-drug-response-data:
    kind: postgres-sql
    source: postgres-readonly
    description: Get drug response data with optional filtering
    parameters:
      - name: limit
        type: integer
        description: Maximum number of rows to return
        default: 10000
      - name: compound_name
        type: string
        description: Filter by compound name (optional)
    statement: |
      SELECT * FROM im_dep_raw_secondary_dose_curve 
      WHERE ($2 IS NULL OR name ILIKE '%' || $2 || '%')
      ORDER BY name
      LIMIT $1;

  get-damaging-mutations:
    kind: postgres-sql
    source: postgres-readonly
    description: Get damaging mutation data
    statement: SELECT * FROM im_dep_sprime_damaging_mutations;

  get-gene-ontology:
    kind: postgres-sql
    source: postgres-readonly
    description: Get gene ontology reference data
    statement: SELECT * FROM im_omics_genes;
```

### **Streamlit Integration Code**
```python
import streamlit as st
from mcp_toolbox_client import MCPClient

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_drug_response_data(limit=10000, compound_name=None):
    """Get drug response data via MCP"""
    client = MCPClient("http://localhost:5000")
    params = {"limit": limit}
    if compound_name:
        params["compound_name"] = compound_name
    
    result = client.call_tool("get-drug-response-data", params)
    return pd.DataFrame(result)

@st.cache_data(ttl=600)  # Cache for 10 minutes
def get_damaging_mutations():
    """Get damaging mutations via MCP"""
    client = MCPClient("http://localhost:5000")
    result = client.call_tool("get-damaging-mutations")
    return pd.DataFrame(result)
```

## 📈 **Expected Performance Improvements**

### **Load Time Reduction**
- **Before**: 2+ minutes for initial page load
- **After**: <10 seconds for initial page load
- **Improvement**: 90%+ reduction in load time

### **Memory Usage**
- **Before**: 2-4GB RAM usage with multiple large DataFrames
- **After**: <500MB RAM usage with cached, paginated results
- **Improvement**: 75%+ reduction in memory usage

### **User Experience**
- **Before**: UI freezes during data loading
- **After**: Responsive UI with progress indicators
- **Improvement**: Seamless user experience

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

### **Week 1: Infrastructure Setup**
- Set up PostgreSQL database
- Deploy MCP Toolbox Docker container
- Configure database schema and indexes

### **Week 2: Data Migration**
- Import CSV data into PostgreSQL
- Validate data integrity
- Optimize database performance

### **Week 3: Code Migration**
- Replace file loading with MCP calls
- Implement caching strategy
- Add error handling and fallbacks

### **Week 4: Testing & Optimization**
- Performance testing and optimization
- User acceptance testing
- Documentation updates

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
