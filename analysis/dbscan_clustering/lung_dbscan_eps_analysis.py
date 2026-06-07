#!/usr/bin/env python3
"""
DBSCAN Epsilon (EPS) Analysis for Drug Response Clustering
Analyzes LUNG tissue drug-sensitive responses to find optimal DBSCAN epsilon value.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler
import psycopg
import toml

def load_db_config():
    """Load database configuration from secrets.toml"""
    with open('../app/.streamlit/secrets.toml', 'r') as f:
        secrets = toml.load(f)
    return secrets['connections']['datawarehouse_postgres']

def connect_to_database():
    """Establish connection to PostgreSQL database"""
    config = load_db_config()
    conn = psycopg.connect(
        host=config['host'],
        port=config['port'],
        dbname=config['database'],
        user=config['username'],
        password=config['password']
    )
    # Note: psycopg3 uses autocommit by default, but we can enable it explicitly
    conn.autocommit = True
    return conn

def query_drug_sensitive_data():
    """Query all drug responses from LUNG tissue"""
    query = """
    SELECT 
        name as drug_name,
        moa,
        AVG(delta_s_prime) as avg_delta_s_prime,
        COUNT(*) as gene_count
    FROM fnl_sprime_pooled_delta_sprime
    WHERE tissue = 'LUNG'
      AND moa IS NOT NULL
    GROUP BY name, moa
    ORDER BY avg_delta_s_prime ASC
    """
    
    conn = connect_to_database()
    # psycopg3 uses cursor context manager
    with conn.cursor() as cursor:
        df = pd.read_sql_query(query, conn)
    conn.close()
    
    return df

def prepare_features(df):
    """Prepare features for clustering: one-hot encode MOA and scale"""
    # Separate target variable and MOA
    target = df['avg_delta_s_prime'].values.reshape(-1, 1)
    moa_encoded = pd.get_dummies(df['moa'], prefix='moa')
    
    # Combine features
    features = np.hstack([target, moa_encoded.values])
    
    # Standardize features
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)
    
    return features_scaled, scaler, moa_encoded.columns

def calculate_k_distances(features, k=5):
    """Calculate k-nearest neighbor distances for EPS estimation"""
    # Fit NearestNeighbors model
    neigh = NearestNeighbors(n_neighbors=k)
    nbrs = neigh.fit(features)
    
    # Calculate distances to k-th nearest neighbor
    distances, indices = nbrs.kneighbors(features)
    
    # Sort distances (taking k-th neighbor, which is index k-1)
    distances = np.sort(distances, axis=0)
    distances = distances[:, k-1]
    
    return distances

def plot_k_distance(distances, save_path='lung_dbscan_eps_plot.png'):
    """Create and display k-distance elbow plot"""
    plt.figure(figsize=(12, 6))
    plt.plot(distances, linewidth=1.5)
    plt.xlabel("Samples (sorted by distance)", fontsize=14)
    plt.ylabel("Distance to 5th Nearest Neighbor (EPS)", fontsize=14)
    plt.title("K-Distance Plot for Optimal EPS Selection\nLUNG Tissue - All Drug Responses", 
              fontsize=16, fontweight='bold')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # Save figure
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"\nPlot saved to: {save_path}")
    
    plt.show()

def print_summary_statistics(df, distances):
    """Print summary statistics of the data"""
    print("\n" + "="*70)
    print("DBSCAN EPS ANALYSIS - SUMMARY STATISTICS")
    print("="*70)
    
    print(f"\nTotal drug-MOA combinations analyzed: {len(df)}")
    print(f"Number of unique drugs: {df['drug_name'].nunique()}")
    print(f"Number of unique MOAs: {df['moa'].nunique()}")
    
    print(f"\ndelta_s_prime statistics:")
    print(f"  Mean: {df['avg_delta_s_prime'].mean():.4f}")
    print(f"  Median: {df['avg_delta_s_prime'].median():.4f}")
    print(f"  Min: {df['avg_delta_s_prime'].min():.4f}")
    print(f"  Max: {df['avg_delta_s_prime'].max():.4f}")
    print(f"  Std Dev: {df['avg_delta_s_prime'].std():.4f}")
    
    print(f"\nK-distance (EPS) statistics:")
    print(f"  Mean: {distances.mean():.4f}")
    print(f"  Median: {np.median(distances):.4f}")
    print(f"  Min: {distances.min():.4f}")
    print(f"  Max: {distances.max():.4f}")
    print(f"  Std Dev: {distances.std():.4f}")
    
    # Suggest EPS range
    percentile_75 = np.percentile(distances, 75)
    percentile_90 = np.percentile(distances, 90)
    print(f"\nSuggested EPS range based on percentiles:")
    print(f"  Conservative (75th percentile): {percentile_75:.4f}")
    print(f"  Liberal (90th percentile): {percentile_90:.4f}")
    
    print("\n" + "="*70)
    print("Interpretation: Look for the 'elbow' in the plot where the curve")
    print("sharply increases - this indicates the optimal EPS value for DBSCAN.")
    print("="*70 + "\n")

def main():
    """Main execution function"""
    print("Starting DBSCAN EPS Analysis for LUNG tissue drug responses...")
    
    # Query data from database
    print("\n1. Querying drug response data from database...")
    df = query_drug_sensitive_data()
    print(f"   Retrieved {len(df)} drug-MOA combinations")
    
    # Prepare features
    print("\n2. Preparing features (one-hot encoding MOA, standardizing)...")
    features_scaled, scaler, moa_columns = prepare_features(df)
    print(f"   Feature matrix shape: {features_scaled.shape}")
    print(f"   Features: avg_delta_s_prime + {len(moa_columns)} encoded MOA categories")
    
    # Calculate k-distances
    print("\n3. Calculating k-nearest neighbor distances (k=5)...")
    distances = calculate_k_distances(features_scaled, k=5)
    print(f"   Calculated distances for {len(distances)} samples")
    
    # Print summary statistics
    print_summary_statistics(df, distances)
    
    # Create visualization
    print("\n4. Generating k-distance plot...")
    plot_k_distance(distances)
    
    print("\nAnalysis complete!")

if __name__ == "__main__":
    main()
