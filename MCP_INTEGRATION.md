# MCP (Model Context Protocol) Integration Guide

## 🎯 **Overview**

This guide covers the MCP (Model Context Protocol) integration for database introspection and data warehouse exploration. MCP provides a standardized way to interact with your PostgreSQL database through Cursor IDE, enabling powerful data analysis and exploration capabilities.

## ** Warnings!!! **
Note, many MCP tools are MALICIOUS - and will steal database credentials. Only use READ-ONLY database accounts (e.g. `compbio_dw_readonly`) with MCP tools, and only use trusted tools. We are using a trusted Google product as our MCP backend - [https://github.com/googleapis/genai-toolbox](https://github.com/googleapis/genai-toolbox)

## 🛠️ **Prerequisites**

### **Required Software**
1. **Cursor IDE** - Download from [cursor.sh](https://cursor.sh)
2. **Docker & Docker Compose** - [Install Docker](https://docs.docker.com/get-docker/)
3. **Git** - [Download Git](https://git-scm.com/downloads)
4. **Python 3.9+** - [Download Python](https://www.python.org/downloads/)

## 🔧 **MCP Toolbox Setup**
### **Database Configuration**
1. **Copy Configuration Template**:
   ```bash
   # Copy the example configuration file
   cp tools.yaml.example tools.yaml
   ```

2. **Update Database Credentials**:
   Edit `tools.yaml` with your actual database connection details:
   ```yaml
   sources:
     postgres-readonly:
       kind: postgres
       host: your-remote-postgres-host.com  # Replace with your remote PostgreSQL host
       port: 5432
       database: data_warehouse              # Replace with your database name
       user: compbio_dw_readonly            # Replace with your database user
       password: PASSWORD_HERE              # Replace with your actual password
   ```

   #### **Test Database Connection**
Before continuing, it is strongly advised to test your Postgres credentials in pgAdmin or a similar GUI first, before troubleshooting testing connections with the MCP.

### **3. Launch MCP Toolbox**

#### **Quick Start (Recommended)**
```bash
# Start MCP Toolbox (Windows)
scripts\mcp-toolbox.bat start

# Start MCP Toolbox (Linux/macOS)
./scripts/mcp-toolbox.sh start
```

#### **Manual Setup**
```bash
# Pull the latest MCP Toolbox image
docker pull us-central1-docker.pkg.dev/database-toolbox/toolbox/toolbox:latest

# Create named MCP Toolbox container with HTTP mode
docker run -d --name mcp-toolbox -p 5001:5001 -v ./tools.yaml:/app/tools.yaml us-central1-docker.pkg.dev/database-toolbox/toolbox/toolbox:latest --tools-file /app/tools.yaml --address 0.0.0.0 --port 5001 --log-level DEBUG

# Verify MCP Toolbox container is running
docker ps | grep mcp-toolbox

# Check that 3 toolsets are initialized (should show "Initialized 3 toolsets")
docker logs mcp-toolbox | grep "Initialized.*toolsets"
```

#### **Test MCP Connection**
```bash
# Test MCP Toolbox is running
curl http://localhost:5001/
# Expected: "🧰 Hello, World! 🧰"

# Test MCP protocol - List available tools
curl -X POST http://localhost:5001/mcp/tools \
  -H "Content-Type: application/json" \
  -d "{\"jsonrpc\":\"2.0\",\"method\":\"tools/list\",\"params\":{},\"id\":1}"

# Test calling a tool - List database tables
curl -X POST http://localhost:5001/mcp/tools \
  -H "Content-Type: application/json" \
  -d "{\"jsonrpc\":\"2.0\",\"method\":\"tools/call\",\"params\":{\"name\":\"list-tables\",\"arguments\":{}},\"id\":1}"

# Check container logs
docker logs mcp-toolbox
```

## 🎯 **Cursor IDE Configuration**

### **1. Install Cursor IDE**
```bash
# Download from https://cursor.sh
# Follow installation instructions for your OS
```

### **2. Configure MCP in Cursor**
1. Open Cursor Settings (Ctrl+,)
2. Search for "MCP"
3. Add MCP server configuration for HTTP mode:

```json
{
  "mcpServers": {
    "datawarehouse-toolbox": {
      "type": "http",
      "url": "http://localhost:5001/mcp/tools"
    }
  }
}
```

**Note**: If Cursor doesn't support HTTP-based MCP servers directly, you may need to use a bridge or proxy. The MCP toolbox is running in HTTP mode on port 5001.

### **3. Toolsets Configuration**
The `tools.yaml` file includes both toolset configurations:
- **`tools`** - Default toolset for MCP protocol compatibility
- **`sprime_analysis`** - Specific toolset for S-prime analysis tools

Both toolsets contain the same 8 tools for database introspection and analysis.

### **4. Restart Cursor IDE**
After adding the MCP configuration, restart Cursor to establish the connection.

## ✅ **Verify MCP Connection**

After restarting Cursor, you should see the MCP server connected successfully in the settings:

![Successful MCP Connection](successful_mcp.png)
*Note: Place the `successful_mcp.png` screenshot in the project root directory*

**What you should see:**
- ✅ **datawarehouse-toolbox** with a green status dot
- ✅ **17 tools enabled** showing all your database tools:
  - `get-delta-sprime`
  - `get-mutation-counts` 
  - `get-drug-response`
  - `get-damaging-mutations`
  - `get-single-s-values`
  - `get-gene-translation`
  - `list-tables`
  - `describe-table-columns`
  - `explore-drug-response-sample`
  - `explore-s-prime-sample`
  - `explore-mutations-sample`
  - `explore-aggregated-sample`
  - `explore-gene-ontology-sample`
  - `get-primary-keys`
  - `get-foreign-keys`
  - `get-table-indexes`
  - `run-query` ⭐ **NEW: Dynamic SQL execution**
- ✅ **Green toggle switch** indicating the MCP is active

## 🚀 **Dynamic SQL Execution with `run-query`**

### **Overview**
The `run-query` tool enables full-power dynamic SQL execution with complete flexibility. This powerful feature allows you to execute any SQL query with no restrictions, leveraging the read-only database account for maximum analytical capability.

### **Full Power Features**
- ✅ **Complete SQL support** - SELECT, JOINs, subqueries, CTEs, window functions, etc.
- ✅ **No row limits** - Execute queries returning millions of rows if needed
- ✅ **All JOIN types** - LEFT, RIGHT, FULL OUTER, CROSS joins supported
- ✅ **Advanced SQL** - Window functions, recursive CTEs, complex aggregations
- ✅ **Read-only database connection** - No data modification possible (account-level security)
- ✅ **Parameterized queries** - Protection against SQL injection

### **Usage Examples**

#### **Basic Query Execution**
```
Use the run-query tool to execute: SELECT name, moa, target FROM im_dep_raw_secondary_dose_curve WHERE name LIKE '%bortezomib%' LIMIT 10
```

#### **Complex Joins**
```
Use run-query to join drug response data with mutations: 
SELECT d.name, d.ec50, d.auc, m.mutation_value 
FROM im_dep_raw_secondary_dose_curve d 
JOIN im_dep_sprime_damaging_mutations m ON d.row_name = m.cell_line 
WHERE d.name = 'bortezomib' 
LIMIT 50
```

#### **Aggregated Analysis**
```
Use run-query to analyze drug effectiveness by tissue:
SELECT tissue, COUNT(*) as drug_count, AVG(delta_s_prime) as avg_delta_s_prime
FROM fnl_sprime_pooled_delta_sprime 
WHERE sensitivity = 'Sensitive'
GROUP BY tissue
ORDER BY avg_delta_s_prime DESC
```

#### **Gene-Specific Analysis**
```
Use run-query to find drugs targeting specific genes:
SELECT name, target, delta_s_prime, sensitivity
FROM fnl_sprime_pooled_delta_sprime 
WHERE gene_id = 4763 AND delta_s_prime < -0.5
ORDER BY delta_s_prime ASC
```

### **Best Practices for `run-query`**

#### **1. Use LIMIT for Large Result Sets (Optional)**
```sql
-- For exploration: Use LIMIT to preview results
SELECT * FROM im_dep_raw_secondary_dose_curve LIMIT 100

-- For analysis: No LIMIT needed for complete datasets
SELECT name, ec50, auc FROM im_dep_raw_secondary_dose_curve 
WHERE name LIKE '%target%'
```

#### **2. Leverage Indexed Columns for Performance**
```sql
-- Good: Use indexed columns for filtering
SELECT * FROM im_sprime_solved_s_prime WHERE name = 'bortezomib'

-- Good: Use gene_id for efficient joins
SELECT * FROM fnl_sprime_pooled_delta_sprime WHERE gene_id = 4763
```

#### **3. Optimize Query Performance**
```sql
-- Good: Select only needed columns for large datasets
SELECT name, delta_s_prime, sensitivity FROM fnl_sprime_pooled_delta_sprime

-- Full power: SELECT * is fine when you need all columns
SELECT * FROM im_dep_raw_secondary_dose_curve  -- Returns all data when needed
```

#### **4. Use Advanced JOIN Capabilities**
```sql
-- LEFT JOIN: Include all records from left table
SELECT d.name, m.mutation_value
FROM im_dep_raw_secondary_dose_curve d
LEFT JOIN im_dep_sprime_damaging_mutations m ON d.row_name = m.cell_line

-- RIGHT JOIN: Include all records from right table
SELECT d.name, g.name as gene_name
FROM fnl_sprime_pooled_delta_sprime d
RIGHT JOIN im_omics_genes g ON d.gene_id = g.id

-- FULL OUTER JOIN: Include all records from both tables
SELECT d.name, m.mutation_value, g.name as gene_name
FROM im_dep_raw_secondary_dose_curve d
FULL OUTER JOIN im_dep_sprime_damaging_mutations m ON d.row_name = m.cell_line
FULL OUTER JOIN im_omics_genes g ON m.gene_id = g.id
```

#### **5. Advanced SQL Features**
```sql
-- Window functions for ranking and analytics
SELECT name, delta_s_prime,
       ROW_NUMBER() OVER (PARTITION BY tissue ORDER BY delta_s_prime DESC) as rank,
       AVG(delta_s_prime) OVER (PARTITION BY tissue) as tissue_avg
FROM fnl_sprime_pooled_delta_sprime

-- Common Table Expressions (CTEs) for complex queries
WITH drug_rankings AS (
    SELECT name, delta_s_prime, tissue,
           RANK() OVER (PARTITION BY tissue ORDER BY delta_s_prime) as rank
    FROM fnl_sprime_pooled_delta_sprime
)
SELECT * FROM drug_rankings WHERE rank <= 5

-- Recursive CTEs for hierarchical data
WITH RECURSIVE gene_hierarchy AS (
    SELECT id, name, 0 as level FROM im_omics_genes WHERE id = 4763
    UNION ALL
    SELECT g.id, g.name, gh.level + 1
    FROM im_omics_genes g
    JOIN gene_hierarchy gh ON g.id = gh.id
)
SELECT * FROM gene_hierarchy
```

### **Common Query Patterns**

#### **Drug Discovery Queries**
```sql
-- Find most effective drugs
SELECT name, delta_s_prime, sensitivity, tissue
FROM fnl_sprime_pooled_delta_sprime 
WHERE sensitivity = 'Sensitive' AND delta_s_prime < -1.0
ORDER BY delta_s_prime ASC
LIMIT 20

-- Analyze drug mechanisms
SELECT moa, COUNT(*) as drug_count, AVG(delta_s_prime) as avg_effectiveness
FROM fnl_sprime_pooled_delta_sprime 
GROUP BY moa
HAVING COUNT(*) > 5
ORDER BY avg_effectiveness ASC
```

#### **Gene Analysis Queries**
```sql
-- Find genes with significant drug responses
SELECT gene_id, COUNT(*) as drug_count, 
       AVG(delta_s_prime) as avg_delta_s_prime,
       COUNT(CASE WHEN sensitivity = 'Sensitive' THEN 1 END) as sensitive_drugs
FROM fnl_sprime_pooled_delta_sprime 
GROUP BY gene_id
HAVING COUNT(*) > 10
ORDER BY sensitive_drugs DESC
```

#### **Tissue-Specific Analysis**
```sql
-- Compare drug effectiveness across tissues
SELECT tissue, 
       COUNT(*) as total_drugs,
       COUNT(CASE WHEN sensitivity = 'Sensitive' THEN 1 END) as sensitive_drugs,
       ROUND(100.0 * COUNT(CASE WHEN sensitivity = 'Sensitive' THEN 1 END) / COUNT(*), 2) as sensitivity_rate
FROM fnl_sprime_pooled_delta_sprime 
GROUP BY tissue
ORDER BY sensitivity_rate DESC
```

### **Error Handling**
The `run-query` tool includes built-in error handling:
- **Syntax errors** are caught and reported with detailed messages
- **Permission errors** are handled gracefully (read-only account prevents data modification)
- **Query timeout protection** prevents indefinitely long-running queries
- **Memory management** handled by PostgreSQL and MCP Toolbox
- **Connection pooling** ensures stable database connections

## 🎯 **Sample MCP Prompts**

Once your MCP connection is established, you can use these sample prompts in Cursor to explore your database:

### **Database Exploration**
```
Use the MCP Tool to list all tables in the database and show me the structure of the main DepMap tables
```

```
Describe the columns and data types for the im_dep_raw_secondary_dose_curve table
```

```
Show me the schema for the fnl_sprime_pooled_delta_sprime table and explain what each column represents
```

### **Direct HTTP API Testing**
You can also test the MCP tools directly using curl commands:

```bash
# List all available tools
curl -X POST http://localhost:5001/mcp/tools \
  -H "Content-Type: application/json" \
  -d "{\"jsonrpc\":\"2.0\",\"method\":\"tools/list\",\"params\":{},\"id\":1}"

# Get database table list
curl -X POST http://localhost:5001/mcp/tools \
  -H "Content-Type: application/json" \
  -d "{\"jsonrpc\":\"2.0\",\"method\":\"tools/call\",\"params\":{\"name\":\"list-tables\",\"arguments\":{}},\"id\":1}"

# Describe table columns (replace 'table_name' with actual table)
curl -X POST http://localhost:5001/mcp/tools \
  -H "Content-Type: application/json" \
  -d "{\"jsonrpc\":\"2.0\",\"method\":\"tools/call\",\"params\":{\"name\":\"describe-table-columns\",\"arguments\":{\"table_name\":\"im_dep_raw_secondary_dose_curve\"}},\"id\":1}"
```

### **Data Analysis Queries**
```
Use the MCP Tool to get drug response data for the top 10 most effective drugs based on AUC values
```

```
Get mutation counts for cell lines that have high sensitivity scores in the delta S prime results
```

```
Show me the gene translation data for genes with significant delta S prime values (p < 0.05)
```

### **Performance Testing**
```
Use the MCP Tool to get a sample of 1000 rows from the dose response curve data to test query performance
```

```
Get damaging mutations data for a specific gene ID and show me the mutation patterns
```

### **Migration Validation**
```
Compare the data structure between the old CSV files and the new database tables using MCP tools
```

```
Verify that all expected columns from the original DepMap CSV are present in the database schema
```

### **Advanced Queries with `run-query`**
```
Use the run-query tool to find drugs with both high AUC and low EC50 values, indicating high potency and effectiveness:
SELECT name, auc, ec50, (auc/ec50) as potency_ratio
FROM im_sprime_solved_s_prime 
WHERE auc > 0.8 AND ec50 < 0.1
ORDER BY potency_ratio DESC
LIMIT 20
```

```
Use run-query to get the pooled delta S prime values for genes that show significant differences:
SELECT name, gene_id, delta_s_prime, p_val_median_man_whit, sensitivity
FROM fnl_sprime_pooled_delta_sprime 
WHERE p_val_median_man_whit < 0.05 AND ABS(delta_s_prime) > 0.5
ORDER BY ABS(delta_s_prime) DESC
LIMIT 50
```

```
Use run-query to analyze drug effectiveness by mechanism of action:
SELECT moa, 
       COUNT(*) as drug_count,
       AVG(delta_s_prime) as avg_delta_s_prime,
       COUNT(CASE WHEN sensitivity = 'Sensitive' THEN 1 END) as sensitive_count
FROM fnl_sprime_pooled_delta_sprime 
WHERE moa IS NOT NULL
GROUP BY moa
HAVING COUNT(*) > 3
ORDER BY sensitive_count DESC
```

```
Use run-query to perform a comprehensive cross-tissue analysis with window functions:
SELECT tissue, name, delta_s_prime,
       RANK() OVER (PARTITION BY tissue ORDER BY delta_s_prime) as tissue_rank,
       PERCENT_RANK() OVER (PARTITION BY tissue ORDER BY delta_s_prime) as percentile,
       AVG(delta_s_prime) OVER (PARTITION BY tissue) as tissue_avg,
       STDDEV(delta_s_prime) OVER (PARTITION BY tissue) as tissue_stddev
FROM fnl_sprime_pooled_delta_sprime 
WHERE tissue IS NOT NULL
ORDER BY tissue, delta_s_prime DESC
```

```
Use run-query to create a comprehensive drug-gene interaction matrix:
SELECT d.name as drug_name, g.name as gene_name, d.delta_s_prime, d.sensitivity,
       d.ref_pooled_s_prime, d.test_pooled_s_prime, d.p_val_median_man_whit
FROM fnl_sprime_pooled_delta_sprime d
FULL OUTER JOIN im_omics_genes g ON d.gene_id = g.id
WHERE d.delta_s_prime IS NOT NULL
ORDER BY ABS(d.delta_s_prime) DESC
```

```
Use run-query to perform a recursive analysis of drug response patterns:
WITH RECURSIVE drug_hierarchy AS (
    SELECT name, delta_s_prime, tissue, 1 as level
    FROM fnl_sprime_pooled_delta_sprime 
    WHERE sensitivity = 'Sensitive' AND delta_s_prime < -1.0
    UNION ALL
    SELECT dh.name, dh.delta_s_prime, dh.tissue, dh.level + 1
    FROM drug_hierarchy dh
    JOIN fnl_sprime_pooled_delta_sprime d ON dh.name = d.name
    WHERE dh.level < 3
)
SELECT * FROM drug_hierarchy ORDER BY level, delta_s_prime
```

### **Troubleshooting**
```
Use MCP tools to check if the database connection is working and list all available tables
```

```
Test the MCP Tool connection by getting a small sample of data from each major table
```

## 🐳 **MCP Toolbox Management**

### **Management Scripts**
We provide convenient scripts to manage the MCP Toolbox container:

**Linux/macOS:**
```bash
# Make script executable
chmod +x scripts/mcp-toolbox.sh

# Start MCP Toolbox
./scripts/mcp-toolbox.sh start

# Check status
./scripts/mcp-toolbox.sh status

# View logs
./scripts/mcp-toolbox.sh logs

# Restart if needed
./scripts/mcp-toolbox.sh restart
```

**Windows:**
```cmd
# Start MCP Toolbox
scripts\mcp-toolbox.bat start

# Check status
scripts\mcp-toolbox.bat status

# View logs
scripts\mcp-toolbox.bat logs

# Restart if needed
scripts\mcp-toolbox.bat restart
```

## 🚨 **Troubleshooting**

### **Current Working Setup**
Based on testing, the MCP toolbox works best with:
- **HTTP mode** instead of stdio mode
- **Port 5001** for HTTP server with logging
- **Address 0.0.0.0** to bind to all interfaces
- **Debug logging enabled** for troubleshooting

### **Common Issues**

1. **MCP Toolbox Connection Failed**:
   ```bash
   # Check if MCP Toolbox container is running
   docker ps | grep mcp-toolbox
   
   # Check logs
   docker logs mcp-toolbox
   
   # Restart MCP Toolbox with working configuration
   docker stop mcp-toolbox
   docker rm mcp-toolbox
   docker run -d --name mcp-toolbox -p 5001:5001 -v ./tools.yaml:/app/tools.yaml us-central1-docker.pkg.dev/database-toolbox/toolbox/toolbox:latest --tools-file /app/tools.yaml --address 0.0.0.0 --port 5001 --log-level DEBUG
   ```

2. **Empty Reply from Server**:
   ```bash
   # This usually means the container is running in stdio mode instead of HTTP mode
   # Restart with explicit HTTP configuration
   docker stop mcp-toolbox && docker rm mcp-toolbox
   docker run -d --name mcp-toolbox -p 5001:5001 -v ./tools.yaml:/app/tools.yaml us-central1-docker.pkg.dev/database-toolbox/toolbox/toolbox:latest --tools-file /app/tools.yaml --address 0.0.0.0 --port 5001 --log-level DEBUG
   ```

3. **Cursor MCP Connection Issues**:
   ```bash
   # The MCP toolbox is running in HTTP mode, not stdio mode
   # Update your Cursor mcp.json configuration to use HTTP endpoint
   # Test the HTTP endpoint directly:
   curl http://localhost:5001/
   curl -X POST http://localhost:5001/mcp/tools -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"tools/list","params":{},"id":1}'
   ```

4. **Database Connection Issues**:
   ```bash
   # Test remote database connection
   psql -h your-remote-postgres-host.com -U compbio_dw_readonly -d data_warehouse -c "SELECT 1;"
   
   # Check tools.yaml configuration
   cat tools.yaml
   ```

3. **MCP Toolbox Health Check**:
   ```bash
   # Check container status
   docker ps | grep mcp-toolbox
   
   # Check container logs
   docker logs mcp-toolbox
   ```

4. **Cursor MCP Extension Issues**:
   - Restart Cursor IDE
   - Check MCP server configuration in settings
   - Verify Docker containers are running

### **Performance Monitoring**
```bash
# Monitor MCP Toolbox container
docker ps | grep mcp-toolbox
docker logs mcp-toolbox

# Monitor container resource usage
docker stats mcp-toolbox

# Check container health
docker inspect mcp-toolbox --format='{{.State.Health.Status}}'
```

## 📊 **Available Database Tables**

The MCP Toolbox provides access to the following database tables:

1. **`fnl_sprime_pooled_delta_sprime`** - Final pooled delta S' results
2. **`im_dep_raw_secondary_dose_curve`** - Raw DepMap dose-response data
3. **`im_dep_sprime_damaging_mutations`** - DepMap damaging mutations
4. **`im_omics_genes`** - Gene information
5. **`im_sprime_solved_s_prime`** - Solved S' values
6. **`im_sprime_s_prime_with_mutations`** - S' values with mutations
7. **`im_dep_sprime_damaging_mutations_temp`** - Temporary mutations table
8. **`fnl_sprime_pooled_delta_sprime_temp`** - Temporary delta S' table

## 🔗 **Integration with Streamlit**

The MCP Toolbox runs in parallel to your Streamlit application, providing database introspection capabilities while your Streamlit app connects directly to PostgreSQL for data display.

### **Architecture**
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Streamlit UI  │    │   MCP Toolbox    │    │   PostgreSQL    │
│                 │◄──►│   (Docker)       │◄──►│   Database      │
│ - Direct DB     │    │ - Tool Registry  │    │ - Optimized     │
│ - Fast Loading  │    │ - Query Engine   │    │ - Indexed       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 📚 **Additional Resources**

- **[MCP Toolbox Documentation](https://github.com/googleapis/genai-toolbox)** - Official MCP Toolbox documentation
- **[Cursor IDE Documentation](https://cursor.sh/docs)** - Cursor IDE setup and usage guide
- **[PostgreSQL Documentation](https://www.postgresql.org/docs/)** - Database setup and optimization
- **[MIGRATION_STRATEGY.md](MIGRATION_STRATEGY.md)** - Detailed migration plan and technical specifications
