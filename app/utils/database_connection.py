"""
Database Connection Utility for DepMap Migration

This module provides database connection management and query utilities
for the DepMap migration from CSV files to PostgreSQL database.
"""

import streamlit as st
import psycopg
from psycopg import sql
import pandas as pd
from typing import Dict, List, Optional, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseConnection:
    """PostgreSQL database connection manager for DepMap migration."""
    
    def __init__(self):
        self.connection = None
        self.config = None
        
    def get_connection_config(self) -> Optional[Dict]:
        """Get database connection configuration from Streamlit secrets."""
        try:
            self.config = st.secrets["connections"]["datawarehouse_postgres"]
            return self.config
        except Exception as e:
            logger.error(f"Failed to get database config: {e}")
            return None
    
    def connect(self) -> bool:
        """
        Establish database connection.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            config = self.get_connection_config()
            if not config:
                return False
            
            # Build connection parameters
            conn_params = {
                'host': config['host'],
                'port': config['port'],
                'dbname': config['database'],  # psycopg 3 uses 'dbname' instead of 'database'
                'user': config['username'],
                'password': config['password'],
            }
            
            # Add SSL mode if specified
            if 'sslmode' in config:
                conn_params['sslmode'] = config['sslmode']
            
            # Establish connection
            self.connection = psycopg.connect(**conn_params)
            logger.info("Database connection established successfully")
            return True
            
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("Database connection closed")
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> Optional[pd.DataFrame]:
        """
        Execute a SQL query and return results as DataFrame.
        
        Args:
            query: SQL query string
            params: Query parameters tuple
            
        Returns:
            DataFrame with query results or None if error
        """
        if not self.connection:
            if not self.connect():
                return None
        
        try:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # Get column names
            columns = [desc[0] for desc in cursor.description]
            
            # Fetch all results
            results = cursor.fetchall()
            
            cursor.close()
            
            # Convert to DataFrame
            df = pd.DataFrame(results, columns=columns)
            return df
            
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return None
    
    def get_s_prime_data(self, studies: Optional[List[str]] = None, 
                        tissue: Optional[str] = None, 
                        limit: int = 10000) -> Optional[pd.DataFrame]:
        """
        Get S' data with pre-calculated metrics.
        
        Args:
            studies: List of study IDs to filter by
            tissue: Tissue type to filter by
            limit: Maximum number of rows to return
            
        Returns:
            DataFrame with S' data
        """
        query = """
            SELECT name, moa, target, lower_limit, upper_limit, ec50, auc, 
                   ccle_name, row_name, screen_id, eff, eff_100, eff_ec50, s_prime
            FROM im_sprime_solved_s_prime 
            WHERE 1=1
        """
        params = []
        
        if studies:
            query += " AND screen_id = ANY(%s)"
            params.append(studies)
        
        if tissue:
            query += " AND tissue = %s"
            params.append(tissue)
        
        query += " ORDER BY name LIMIT %s"
        params.append(limit)
        
        return self.execute_query(query, tuple(params))
    
    def get_damaging_mutations(self, limit: int = 10000) -> Optional[pd.DataFrame]:
        """
        Get damaging mutation data.
        
        Args:
            limit: Maximum number of rows to return
            
        Returns:
            DataFrame with mutation data
        """
        query = """
            SELECT cell_line, gene_id, mutation_value
            FROM im_dep_sprime_damaging_mutations 
            ORDER BY cell_line
            LIMIT %s
        """
        return self.execute_query(query, (limit,))
    
    def get_gene_ontology(self) -> Optional[pd.DataFrame]:
        """
        Get gene ontology reference data.
        
        Returns:
            DataFrame with gene ontology data
        """
        query = "SELECT id, name FROM im_omics_genes ORDER BY name"
        return self.execute_query(query)
    
    def get_aggregated_results(self, gene_name: str, tissue: str) -> Optional[pd.DataFrame]:
        """
        Get pre-aggregated delta S' results.
        
        Args:
            gene_name: Gene name to filter by
            tissue: Tissue type to filter by
            
        Returns:
            DataFrame with aggregated results
        """
        query = """
            SELECT f.name, f.gene_id, f.delta_s_prime, f.sensitivity, f.tissue,
                   f.ref_pooled_s_prime, f.test_pooled_s_prime, f.p_val_median_man_whit,
                   f.num_ref_lines, f.num_test_lines, f.moa, f.target
            FROM fnl_sprime_pooled_delta_sprime f
            JOIN im_omics_genes g ON f.gene_id = g.id
            WHERE g.name = %s AND f.tissue = %s
            ORDER BY f.delta_s_prime DESC
        """
        return self.execute_query(query, (gene_name, tissue))
    
    def get_filtered_data(self, gene_name: str, tissue: str, 
                         studies: List[str]) -> Optional[pd.DataFrame]:
        """
        Get filtered S' data with mutation status.
        
        Args:
            gene_name: Gene name to filter by
            tissue: Tissue type to filter by
            studies: List of study IDs
            
        Returns:
            DataFrame with filtered data
        """
        query = """
            SELECT s.name, s.moa, s.target, s.s_prime, s.tissue, s.screen_id,
                   m.mutation_value, g.name as gene_name
            FROM im_sprime_solved_s_prime s
            JOIN im_dep_sprime_damaging_mutations m ON s.row_name = m.cell_line
            JOIN im_omics_genes g ON m.gene_id = g.id
            WHERE g.name = %s 
              AND s.tissue = %s 
              AND s.screen_id = ANY(%s)
              AND m.mutation_value IN (0, 2)
        """
        return self.execute_query(query, (gene_name, tissue, studies))
    
    def get_unique_combinations(self) -> Optional[List[str]]:
        """
        Get unique group-subgroup combinations.
        
        Returns:
            List of unique combinations
        """
        query = """
            SELECT DISTINCT CONCAT(g.name, ' | ', g.name) as group_subgroup
            FROM im_omics_genes g
            ORDER BY group_subgroup
        """
        df = self.execute_query(query)
        if df is not None:
            return df['group_subgroup'].tolist()
        return None
    
    def get_unique_moas(self) -> Optional[List[str]]:
        """
        Get unique mechanisms of action.
        
        Returns:
            List of unique MOAs
        """
        query = """
            SELECT DISTINCT unnest(string_to_array(moa, ',')) as moa
            FROM im_sprime_solved_s_prime
            WHERE moa IS NOT NULL
            ORDER BY moa
        """
        df = self.execute_query(query)
        if df is not None:
            return df['moa'].tolist()
        return None


# Global database connection instance
db_connection = DatabaseConnection()


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_cached_s_prime_data(studies: Optional[List[str]] = None, 
                           tissue: Optional[str] = None, 
                           limit: int = 10000) -> Optional[pd.DataFrame]:
    """Cached version of get_s_prime_data."""
    return db_connection.get_s_prime_data(studies, tissue, limit)


@st.cache_data(ttl=600)  # Cache for 10 minutes
def get_cached_damaging_mutations(limit: int = 10000) -> Optional[pd.DataFrame]:
    """Cached version of get_damaging_mutations."""
    return db_connection.get_damaging_mutations(limit)


@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_cached_gene_ontology() -> Optional[pd.DataFrame]:
    """Cached version of get_gene_ontology."""
    return db_connection.get_gene_ontology()


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_cached_aggregated_results(gene_name: str, tissue: str) -> Optional[pd.DataFrame]:
    """Cached version of get_aggregated_results."""
    return db_connection.get_aggregated_results(gene_name, tissue)


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_cached_filtered_data(gene_name: str, tissue: str, 
                            studies: List[str]) -> Optional[pd.DataFrame]:
    """Cached version of get_filtered_data."""
    return db_connection.get_filtered_data(gene_name, tissue, studies)


@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_cached_unique_combinations() -> Optional[List[str]]:
    """Cached version of get_unique_combinations."""
    return db_connection.get_unique_combinations()


@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_cached_unique_moas() -> Optional[List[str]]:
    """Cached version of get_unique_moas."""
    return db_connection.get_unique_moas()


def is_database_available() -> bool:
    """
    Check if database is available and configured.
    
    Returns:
        bool: True if database is available, False otherwise
    """
    try:
        # Check if migration mode is enabled
        migration_mode = st.secrets.get("depmap", {}).get("migration_mode", False)
        if not migration_mode:
            return False
        
        # Test connection
        if db_connection.connect():
            db_connection.disconnect()
            return True
        return False
        
    except Exception as e:
        logger.error(f"Database availability check failed: {e}")
        return False


def get_fallback_message() -> str:
    """
    Get fallback message when database is not available.
    
    Returns:
        str: Fallback message
    """
    return """
    ⚠️ **Database Mode Unavailable**
    
    The application is currently running in CSV mode because:
    - Database connection is not configured, or
    - Migration mode is disabled, or
    - Database is temporarily unavailable
    
    To enable database mode:
    1. Configure PostgreSQL connection in `secrets.toml`
    2. Set `migration_mode = true` in the `[depmap]` section
    3. Ensure all required tables exist in the database
    
    See `POSTGRESQL_SETUP_GUIDE.md` for detailed setup instructions.
    """
