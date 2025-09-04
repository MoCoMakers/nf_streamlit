"""
Database Connection Test Utility for DepMap Migration

This utility helps test PostgreSQL database connections and verify
that the required tables exist for the DepMap migration.
"""

import streamlit as st
import psycopg
from psycopg import sql
import pandas as pd
from typing import Dict, List, Optional, Tuple


def test_postgres_connection() -> Tuple[bool, str, Optional[psycopg.Connection]]:
    """
    Test PostgreSQL database connection using Streamlit secrets.
    
    Returns:
        Tuple of (success: bool, message: str, connection: Optional[psycopg.Connection])
    """
    try:
        # Get connection details from Streamlit secrets
        conn_config = st.secrets["connections"]["datawarehouse_postgres"]
        
        # Build connection parameters
        conn_params = {
            'host': conn_config['host'],
            'port': conn_config['port'],
            'dbname': conn_config['database'],  # psycopg 3 uses 'dbname' instead of 'database'
            'user': conn_config['username'],
            'password': conn_config['password'],
        }
        
        # Add SSL mode if specified
        if 'sslmode' in conn_config:
            conn_params['sslmode'] = conn_config['sslmode']
        
        # Attempt connection
        conn = psycopg.connect(**conn_params)
        
        # Test basic query
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        cursor.close()
        
        return True, f"✅ Connection successful! PostgreSQL version: {version}", conn
        
    except Exception as e:
        return False, f"❌ Connection failed: {str(e)}", None


def get_required_tables() -> List[str]:
    """Get list of required tables for DepMap migration."""
    return [
        'im_dep_raw_secondary_dose_curve',
        'im_dep_sprime_damaging_mutations', 
        'im_omics_genes',
        'im_sprime_solved_s_prime',
        'fnl_sprime_pooled_delta_sprime',
        'im_sprime_s_prime_with_mutations'
    ]


def check_required_tables(conn: psycopg.Connection) -> Dict[str, Dict]:
    """
    Check if required tables exist and get basic info about them.
    
    Args:
        conn: PostgreSQL connection object
        
    Returns:
        Dictionary with table information
    """
    required_tables = get_required_tables()
    table_info = {}
    
    try:
        cursor = conn.cursor()
        
        for table_name in required_tables:
            try:
                # Check if table exists
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = %s
                    );
                """, (table_name,))
                
                exists = cursor.fetchone()[0]
                
                if exists:
                    # Get row count
                    cursor.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(
                        sql.Identifier(table_name)
                    ))
                    row_count = cursor.fetchone()[0]
                    
                    # Get column count
                    cursor.execute("""
                        SELECT COUNT(*) 
                        FROM information_schema.columns 
                        WHERE table_schema = 'public' 
                        AND table_name = %s
                    """, (table_name,))
                    column_count = cursor.fetchone()[0]
                    
                    table_info[table_name] = {
                        'exists': True,
                        'row_count': row_count,
                        'column_count': column_count,
                        'status': '✅ Available'
                    }
                else:
                    table_info[table_name] = {
                        'exists': False,
                        'row_count': 0,
                        'column_count': 0,
                        'status': '❌ Missing'
                    }
                    
            except Exception as e:
                table_info[table_name] = {
                    'exists': False,
                    'row_count': 0,
                    'column_count': 0,
                    'status': f'❌ Error: {str(e)}'
                }
        
        cursor.close()
        return table_info
        
    except Exception as e:
        return {table: {'status': f'❌ Connection error: {str(e)}'} for table in required_tables}


def test_sample_queries(conn: psycopg.Connection) -> Dict[str, any]:
    """
    Test sample queries to verify data access.
    
    Args:
        conn: PostgreSQL connection object
        
    Returns:
        Dictionary with query results
    """
    results = {}
    
    try:
        cursor = conn.cursor()
        
        # Test 1: Get sample S' data
        try:
            cursor.execute("""
                SELECT name, moa, target, s_prime, eff, eff_100, eff_ec50
                FROM im_sprime_solved_s_prime 
                LIMIT 5
            """)
            results['s_prime_sample'] = cursor.fetchall()
        except Exception as e:
            results['s_prime_sample'] = f"Error: {str(e)}"
        
        # Test 2: Get sample aggregated data
        try:
            cursor.execute("""
                SELECT name, gene_id, delta_s_prime, sensitivity, tissue
                FROM fnl_sprime_pooled_delta_sprime 
                LIMIT 5
            """)
            results['aggregated_sample'] = cursor.fetchall()
        except Exception as e:
            results['aggregated_sample'] = f"Error: {str(e)}"
        
        # Test 3: Get gene count
        try:
            cursor.execute("SELECT COUNT(*) FROM im_omics_genes")
            results['gene_count'] = cursor.fetchone()[0]
        except Exception as e:
            results['gene_count'] = f"Error: {str(e)}"
        
        cursor.close()
        return results
        
    except Exception as e:
        return {'error': f'Query test failed: {str(e)}'}


def run_database_test():
    """
    Run comprehensive database test and display results in Streamlit.
    """
    st.title("🔍 Database Connection Test")
    st.write("Testing PostgreSQL connection and verifying required tables for DepMap migration.")
    
    # Test connection
    st.subheader("1. Connection Test")
    success, message, conn = test_postgres_connection()
    st.write(message)
    
    if not success:
        st.error("❌ Cannot proceed with table checks due to connection failure.")
        st.write("Please check your PostgreSQL configuration in `secrets.toml`.")
        return
    
    # Check required tables
    st.subheader("2. Required Tables Check")
    table_info = check_required_tables(conn)
    
    # Display table status
    table_df = pd.DataFrame([
        {
            'Table': table,
            'Status': info['status'],
            'Rows': info.get('row_count', 'N/A'),
            'Columns': info.get('column_count', 'N/A')
        }
        for table, info in table_info.items()
    ])
    
    st.dataframe(table_df, use_container_width=True)
    
    # Check if all tables exist
    missing_tables = [table for table, info in table_info.items() if not info.get('exists', False)]
    if missing_tables:
        st.warning(f"⚠️ Missing tables: {', '.join(missing_tables)}")
    else:
        st.success("✅ All required tables are available!")
    
    # Test sample queries
    st.subheader("3. Sample Data Test")
    query_results = test_sample_queries(conn)
    
    if 's_prime_sample' in query_results:
        st.write("**Sample S' Data:**")
        if isinstance(query_results['s_prime_sample'], list):
            s_prime_df = pd.DataFrame(query_results['s_prime_sample'], 
                                    columns=['name', 'moa', 'target', 's_prime', 'eff', 'eff_100', 'eff_ec50'])
            st.dataframe(s_prime_df, use_container_width=True)
        else:
            st.error(query_results['s_prime_sample'])
    
    if 'aggregated_sample' in query_results:
        st.write("**Sample Aggregated Data:**")
        if isinstance(query_results['aggregated_sample'], list):
            agg_df = pd.DataFrame(query_results['aggregated_sample'],
                                columns=['name', 'gene_id', 'delta_s_prime', 'sensitivity', 'tissue'])
            st.dataframe(agg_df, use_container_width=True)
        else:
            st.error(query_results['aggregated_sample'])
    
    if 'gene_count' in query_results:
        st.write(f"**Gene Count:** {query_results['gene_count']}")
    
    # Close connection
    conn.close()
    
    # Summary
    st.subheader("4. Test Summary")
    if success and not missing_tables:
        st.success("🎉 Database is ready for DepMap migration!")
        st.write("You can now enable database mode in the Delta S Prime page.")
    else:
        st.error("❌ Database setup needs attention before migration can proceed.")
        st.write("Please address the issues above and run this test again.")


if __name__ == "__main__":
    run_database_test()
