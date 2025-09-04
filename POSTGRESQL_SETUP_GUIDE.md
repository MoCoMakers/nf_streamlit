# PostgreSQL Database Setup Guide for DepMap Migration

## Overview
This guide helps you configure PostgreSQL database connections for the DepMap Delta S Prime page migration from static CSV files to database-driven data access.

**Note:** This setup uses [psycopg 3](https://pypi.org/project/psycopg/), the modern successor to psycopg2, which provides better performance and improved features for PostgreSQL connectivity.

## Configuration Files

### 1. Streamlit Secrets Configuration
The main configuration is in `app/.streamlit/secrets.toml`. Use the template file `app/.streamlit/secrets.toml.template` as a starting point.

### 2. Streamlit Config Configuration
Additional settings are in `app/.streamlit/config.toml` for database connection pooling and migration features.

## Required PostgreSQL Connection Parameters

### Primary Connection Section
```toml
[connections.datawarehouse_postgres]
dialect = "postgresql"
host = "your-postgres-host.com"        # Your PostgreSQL server
port = "5432"                          # PostgreSQL port
database = "depmap_db"                 # Database name
username = "depmap_user"               # Database username
password = "your_postgres_password"    # Database password
sslmode = "require"                    # SSL mode
```

### Alternative URL Format
```toml
[connections.datawarehouse_postgres_alt]
url = "postgresql://depmap_user:your_postgres_password@your-postgres-host.com:5432/depmap_db?sslmode=require"
```

## Environment-Specific Examples

### Local Development
```toml
[connections.datawarehouse_postgres]
dialect = "postgresql"
host = "localhost"
port = "5432"
database = "depmap_local"
username = "postgres"
password = "your_local_password"
sslmode = "disable"
```

### Docker Environment
```toml
[connections.datawarehouse_postgres]
dialect = "postgresql"
host = "postgres"  # Docker service name
port = "5432"
database = "depmap_db"
username = "depmap_user"
password = "your_docker_password"
sslmode = "disable"
```

### Cloud Production (AWS RDS, Google Cloud SQL, etc.)
```toml
[connections.datawarehouse_postgres]
dialect = "postgresql"
host = "your-instance.region.rds.amazonaws.com"
port = "5432"
database = "depmap_prod"
username = "depmap_user"
password = "your_secure_password"
sslmode = "require"
```

## MCP Toolbox Configuration

### MCP Toolbox Settings
```toml
[mcp_toolbox]
enabled = true
base_url = "http://localhost:5000"    # MCP Toolbox server URL
timeout = 30                          # Request timeout
retry_attempts = 3                    # Retry attempts
```

### DepMap Migration Settings
```toml
[depmap]
migration_mode = true                 # Enable database mode
fallback_to_csv = true               # Fallback to CSV if DB unavailable
cache_ttl_seconds = 300              # Cache duration (5 minutes)
max_rows_per_query = 10000           # Max rows per query
```

## Database Requirements

### Required Tables
The PostgreSQL database must contain the following tables:
- `im_dep_raw_secondary_dose_curve` - Raw drug response data
- `im_dep_sprime_damaging_mutations` - Mutation data
- `im_omics_genes` - Gene reference data
- `im_sprime_solved_s_prime` - Pre-calculated S' values
- `fnl_sprime_pooled_delta_sprime` - Pre-aggregated delta S' results
- `im_sprime_s_prime_with_mutations` - S' values with mutation status

### Database Permissions
The database user needs:
- `SELECT` permissions on all required tables
- Connection permissions to the database
- Appropriate SSL permissions (if using SSL)

## Setup Steps

### 1. Copy Template File
```bash
cp app/.streamlit/secrets.toml.template app/.streamlit/secrets.toml
```

### 2. Install Dependencies
Install the required PostgreSQL dependencies:
```bash
pip install -r app/requirements.txt
```

Or install psycopg 3 directly:
```bash
pip install "psycopg[binary,pool]"
```

### 3. Edit Configuration
Update `app/.streamlit/secrets.toml` with your actual PostgreSQL connection details:
- Replace `your-postgres-host.com` with your server hostname/IP
- Replace `depmap_db` with your database name
- Replace `depmap_user` with your database username
- Replace `your_postgres_password` with your actual password

### 4. Test Connection
The application will automatically test the connection when it starts. Check the Streamlit logs for connection status.

### 5. Enable Migration Mode
Ensure `migration_mode = true` in the `[depmap]` section to enable database-driven data access.

## Troubleshooting

### Connection Issues
- Verify PostgreSQL server is running and accessible
- Check firewall settings and port accessibility
- Verify username/password credentials
- Test SSL settings (try `sslmode = "disable"` for local development)

### Performance Issues
- Adjust `max_rows_per_query` based on your server capacity
- Modify `cache_ttl_seconds` for different caching strategies
- Check database connection pool settings in `config.toml`

### Fallback Mode
If database connection fails, the application will automatically fall back to CSV files if `fallback_to_csv = true` is set.

## Security Considerations

### Production Environment
- Use strong passwords
- Enable SSL (`sslmode = "require"`)
- Restrict database user permissions to only required tables
- Use environment variables for sensitive data in production

### Development Environment
- Use local PostgreSQL instance
- Disable SSL for local development (`sslmode = "disable"`)
- Use test database with sample data

## Next Steps

After configuring the database connection:

1. **Test the connection** by starting the Streamlit application
2. **Verify data access** by checking the Delta S Prime page loads
3. **Monitor performance** using the built-in performance monitoring
4. **Begin migration** by enabling database mode in the UI

## Support

For issues with database configuration:
1. Check Streamlit logs for connection errors
2. Verify PostgreSQL server logs
3. Test connection using PostgreSQL client tools
4. Review the migration strategy document for detailed implementation guidance
