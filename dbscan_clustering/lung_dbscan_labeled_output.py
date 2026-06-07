#!/usr/bin/env python3
"""
DBSCAN Clustering with Labeled Output and Visualization
Applies DBSCAN clustering with min_samples=10, exports labeled dataset, and creates visualization
"""

import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
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
    conn.autocommit = True
    return conn

def query_drug_responses():
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
    
    return features_scaled, scaler, moa_encoded.columns, df

def apply_dbscan(features, eps=4.0, min_samples=10):
    """Apply DBSCAN clustering"""
    dbscan = DBSCAN(eps=eps, min_samples=min_samples)
    cluster_labels = dbscan.fit_predict(features)
    return cluster_labels

def add_cluster_labels_to_dataframe(df, cluster_labels):
    """Add cluster labels column to the original dataframe"""
    df_labeled = df.copy()
    df_labeled['dbscan_cluster_label'] = cluster_labels
    
    return df_labeled

def analyze_cluster_patterns(df_labeled):
    """Analyze patterns within each cluster"""
    print("\n" + "="*80)
    print("CLUSTER ANALYSIS")
    print("="*80)
    
    unique_clusters = sorted([c for c in df_labeled['dbscan_cluster_label'].unique() if c != -1])
    n_clusters = len(unique_clusters)
    n_noise = list(df_labeled['dbscan_cluster_label']).count(-1)
    
    print(f"\nTotal clusters: {n_clusters}")
    print(f"Noise/outliers: {n_noise}")
    print(f"\nCluster breakdown:")
    
    for cluster_id in unique_clusters:
        cluster_data = df_labeled[df_labeled['dbscan_cluster_label'] == cluster_id]
        cluster_size = len(cluster_data)
        
        # Get most common MOA in cluster
        most_common_moa = cluster_data['moa'].value_counts().index[0] if len(cluster_data['moa'].value_counts()) > 0 else 'N/A'
        n_unique_moas = cluster_data['moa'].nunique()
        
        # Average delta_s_prime
        avg_delta = cluster_data['avg_delta_s_prime'].mean()
        
        print(f"\n  Cluster {cluster_id}:")
        print(f"    Size: {cluster_size} drugs")
        print(f"    Avg Pooled Delta S': {avg_delta:.4f}")
        print(f"    Dominant MOA: {most_common_moa} ({n_unique_moas} unique MOAs)")
        
        # Show sample drug names
        sample_drugs = cluster_data['drug_name'].head(5).tolist()
        print(f"    Sample drugs: {', '.join(sample_drugs)}")
    
    print("\n" + "="*80)

def create_labeled_visualization(df_labeled, features_scaled):
    """Create visualization with all clusters and legend table"""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(18, 14), 
                                    height_ratios=[7, 3], 
                                    gridspec_kw={'hspace': 0.3})
    
    # Reduce dimensions for visualization
    pca = PCA(n_components=2)
    features_2d = pca.fit_transform(features_scaled)
    
    cluster_labels = df_labeled['dbscan_cluster_label'].values
    unique_clusters = sorted(df_labeled['dbscan_cluster_label'].unique())
    n_clusters = len([c for c in unique_clusters if c != -1])
    n_noise = list(cluster_labels).count(-1)
    
    # Get colormap
    cmap = plt.colormaps['tab20']  # tab20 has 20 distinct colors
    
    # Plot each cluster
    for idx, cluster_id in enumerate(unique_clusters):
        mask = cluster_labels == cluster_id
        
        if cluster_id == -1:
            # Noise points
            ax1.scatter(features_2d[mask, 0], features_2d[mask, 1],
                       marker='x', s=50, alpha=0.5, c='black', 
                       linewidths=1, label='Noise/Outliers')
        else:
            # Regular clusters - use modulo to cycle through colors
            color = cmap(idx % 20)
            ax1.scatter(features_2d[mask, 0], features_2d[mask, 1],
                       marker='o', s=40, alpha=0.7, c=[color], 
                       linewidths=0, edgecolors='white', linewidth=0.5)
    
    ax1.set_xlabel("PCA Component 1", fontsize=14)
    ax1.set_ylabel("PCA Component 2", fontsize=14)
    ax1.set_title(f"DBSCAN Clustering: LUNG Tissue Drug Responses (min_samples=10)\n"
                  f"Total Clusters: {n_clusters}, Noise Points: {n_noise}",
                  fontsize=16, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    
    # Legend area (lower 30% of figure) with cluster info table
    ax2.axis('off')
    
    # Create cluster summary information
    cluster_info = []
    
    for cluster_id in sorted([c for c in unique_clusters if c != -1]):
        cluster_data = df_labeled[df_labeled['dbscan_cluster_label'] == cluster_id]
        cluster_size = len(cluster_data)
        avg_delta = cluster_data['avg_delta_s_prime'].mean()
        
        # Get most common MOA
        most_common_moa = cluster_data['moa'].value_counts().index[0] if len(cluster_data['moa'].value_counts()) > 0 else 'N/A'
        # Truncate long MOA strings
        moa_display = most_common_moa[:60] + '...' if len(most_common_moa) > 60 else most_common_moa
        
        # Get color for this cluster
        color_idx = [c for c in unique_clusters].index(cluster_id)
        color = cmap(color_idx % 20)
        
        cluster_info.append({
            'Color': color,
            'Cluster': cluster_id,
            'Cluster_Count': cluster_size,
            'Avg Pooled Delta S\'': f'{avg_delta:.3f}',
            'Dominant MOA': moa_display
        })
    
    # Convert to DataFrame for better display
    info_df = pd.DataFrame(cluster_info)
    
    # Sort by Cluster_Count (largest first)
    info_df = info_df.sort_values('Cluster_Count', ascending=False).reset_index(drop=True)
    
    # Prepare table data (excluding Color column, it will be displayed visually)
    table_data = []
    colors_list = []
    for idx, row in info_df.iterrows():
        table_data.append([
            int(row['Cluster']),
            int(row['Cluster_Count']),
            row['Avg Pooled Delta S\''],
            row['Dominant MOA']
        ])
        colors_list.append(row['Color'])
    
    # Create table
    table = ax2.table(cellText=table_data,
                     colLabels=['Cluster', 'Cluster_Count', 'Avg Pooled Delta S\'', 'Dominant MOA'],
                     cellLoc='left',
                     loc='center',
                     bbox=[0, 0, 1, 1])
    
    table.auto_set_font_size(False)
    table.set_fontsize(7)
    table.scale(1, 2)
    
    # Style the header
    for i in range(len(table_data[0]) if table_data else 0):
        table[(0, i)].set_facecolor('#4CAF50')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    # Add colored dots to cluster column cells
    for i in range(len(table_data)):
        # Add colored dot to the left of cluster number
        cell = table[(i+1, 0)]  # +1 because row 0 is header
        cell_text = cell.get_text().get_text()
        cell.get_text().set_text(f'● {cell_text}')
        # Set text color to match cluster color
        cell.get_text().set_color(colors_list[i])
        cell.get_text().set_fontweight('bold')
    
    plt.tight_layout()
    
    # Save figure
    save_path = 'lung_dbscan_labeled_clusters_with_legend.png'
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"Saved visualization to: {save_path}")
    plt.close()

def main():
    """Main execution function"""
    print("DBSCAN Clustering with Labeled Output for LUNG tissue")
    print("EPS=4.0, Min_Samples=10\n")
    
    # Query data
    print("1. Querying drug response data...")
    df = query_drug_responses()
    print(f"   Retrieved {len(df)} drug-MOA combinations")
    
    # Prepare features
    print("\n2. Preparing features...")
    features_scaled, scaler, moa_columns, df_full = prepare_features(df)
    print(f"   Feature matrix shape: {features_scaled.shape}")
    
    # Apply DBSCAN
    print("\n3. Applying DBSCAN clustering (EPS=4.0, Min_Samples=10)...")
    cluster_labels = apply_dbscan(features_scaled, eps=4.0, min_samples=10)
    unique_clusters = np.unique(cluster_labels)
    n_clusters = len(unique_clusters) - (1 if -1 in unique_clusters else 0)
    n_noise = list(cluster_labels).count(-1)
    print(f"   Found {n_clusters} clusters and {n_noise} noise points")
    
    # Add labels to dataframe
    print("\n4. Adding cluster labels to dataframe...")
    df_labeled = add_cluster_labels_to_dataframe(df_full, cluster_labels)
    
    # Analyze clusters
    analyze_cluster_patterns(df_labeled)
    
    # Save to CSV
    output_file = 'lung_dbscan_labeled_results.csv'
    print(f"\n5. Saving labeled results to {output_file}...")
    df_labeled.to_csv(output_file, index=False)
    print(f"   Saved {len(df_labeled)} rows to {output_file}")
    
    # Create visualization with legend
    print(f"\n6. Creating visualization with cluster legend...")
    create_labeled_visualization(df_labeled, features_scaled)
    
    # Display first few rows
    print("\n" + "="*80)
    print("SAMPLE OF LABELED DATA")
    print("="*80)
    print(df_labeled[['drug_name', 'moa', 'avg_delta_s_prime', 'gene_count', 'dbscan_cluster_label']].head(20).to_string())
    
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE!")
    print("="*80)
    print(f"\nKey biological labels in our data:")
    print("  - drug_name: Compound/drug identifier")
    print("  - moa: Mechanism of action")
    print("  - avg_delta_s_prime: Mean pooled delta S' (drug response metric)")
    print("  - gene_count: Number of genes tested")
    print("  - dbscan_cluster_label: DBSCAN cluster assignment")
    print("\nClusters group drugs with similar response profiles and MOAs!")

if __name__ == "__main__":
    main()

