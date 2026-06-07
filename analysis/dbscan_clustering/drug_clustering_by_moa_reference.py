"""
Drug Clustering Analysis by Mechanism of Action (MOA)
======================================================

This reference code demonstrates various clustering approaches for identifying
patterns in drug sensitivity data grouped by mechanism of action.

Author: NF Streamlit Project
Date: 2025
"""

import pandas as pd
import numpy as np
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score, davies_bouldin_score
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.cluster.hierarchy import dendrogram, linkage
from collections import Counter
import ast
import warnings
warnings.filterwarnings('ignore')

# Database connection (adjust based on your connection setup)
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


class DrugMOAClustering:
    """
    Class for performing clustering analysis on drug sensitivity data
    grouped by mechanism of action.
    """
    
    def __init__(self, tissue=None):
        """
        Initialize the clustering analyzer.
        
        Args:
            tissue (str): Tissue type to filter (e.g., 'PANCREAS'). 
                         If None, uses all tissues.
        """
        self.tissue = tissue
        self.data = None
        self.features = None
        self.feature_names = None
        self.moa_labels = None
        self.scaled_features = None
        self.connection = None
        
    def load_data(self, limit=None):
        """
        Load delta S' data from the database.
        
        Args:
            limit (int): Maximum number of records to load. If None, loads all.
        """
        query = """
        SELECT 
            name,
            gene_id,
            ref_pooled_s_prime,
            ref_median_s_prime,
            ref_mad,
            ref_pooled_auc,
            ref_pooled_ec50,
            num_ref_lines,
            test_pooled_s_prime,
            test_median_s_prime,
            test_mad,
            test_pooled_auc,
            test_pooled_ec50,
            num_test_lines,
            delta_s_prime,
            delta_auc,
            delta_ec50,
            delta_s_prime_median,
            p_val_median_man_whit,
            sensitivity_score,
            sensitivity,
            moa,
            target,
            tissue
        FROM fnl_sprime_pooled_delta_sprime
        """
        
        if self.tissue:
            query += f" WHERE tissue = '{self.tissue}'"
        
        if limit:
            query += f" LIMIT {limit}"
        
        print(f"Loading data from database...")
        # Execute query - adjust based on your database connection method
        self.connection = connect_to_database()
        self.data = pd.read_sql_query(query, self.connection)
        self.connection.close()
        print(f"Loaded {len(self.data)} records")
        
        return self.data
    
    def parse_moa(self, moa_string):
        """
        Parse MOA string from database format ['MOA1', 'MOA2'] to list.
        
        Args:
            moa_string (str): MOA string from database
            
        Returns:
            list: List of MOA values
        """
        if pd.isna(moa_string) or moa_string == 'null':
            return ['Unknown']
        
        try:
            # Try to parse as Python literal (list)
            moa_list = ast.literal_eval(moa_string)
            if isinstance(moa_list, list):
                return [m for m in moa_list if m != 'None']
            return [str(moa_list)]
        except:
            # If parsing fails, treat as string
            return [moa_string.strip("[]'\"")]
    
    def preprocess_data(self):
        """
        Preprocess data for clustering:
        - Parse MOA strings
        - Extract numerical features
        - Handle missing values
        - Group by drug and MOA
        """
        print("Preprocessing data...")
        
        # Parse MOA strings
        self.data['moa_list'] = self.data['moa'].apply(self.parse_moa)
        self.data['moa_primary'] = self.data['moa_list'].apply(lambda x: x[0] if x else 'Unknown')
        
        # Create aggregated features per drug
        feature_columns = [
            'delta_s_prime', 'delta_auc', 'delta_ec50', 'delta_s_prime_median',
            'ref_pooled_s_prime', 'test_pooled_s_prime',
            'ref_pooled_auc', 'test_pooled_auc',
            'ref_pooled_ec50', 'test_pooled_ec50',
            'p_val_median_man_whit', 'sensitivity_score'
        ]
        
        # Aggregate by drug name and MOA
        drug_features = self.data.groupby(['name', 'moa_primary'])[feature_columns].agg([
            'mean', 'std', 'min', 'max', 'count'
        ]).reset_index()
        
        # Flatten column names
        drug_features.columns = ['_'.join(col).strip('_') for col in drug_features.columns.values]
        drug_features.rename(columns={'name': 'name', 'moa_primary': 'moa_primary'}, inplace=True)
        
        # Fill NaN values with 0 (for std where count=1)
        drug_features.fillna(0, inplace=True)
        
        # Extract features for clustering
        self.feature_names = [col for col in drug_features.columns 
                              if col not in ['name', 'moa_primary']]
        self.features = drug_features[self.feature_names].values
        self.moa_labels = drug_features['moa_primary'].values
        self.drug_names = drug_features['name'].values
        
        print(f"Preprocessed into {len(self.features)} drug-MOA combinations")
        print(f"Feature dimensions: {self.features.shape}")
        print(f"Unique MOAs: {len(set(self.moa_labels))}")
        
        return drug_features
    
    def scale_features(self):
        """
        Scale features using StandardScaler (zero mean, unit variance).
        """
        print("Scaling features...")
        scaler = StandardScaler()
        self.scaled_features = scaler.fit_transform(self.features)
        return self.scaled_features
    
    def perform_kmeans(self, n_clusters=5, random_state=42):
        """
        Perform K-means clustering.
        
        Args:
            n_clusters (int): Number of clusters
            random_state (int): Random seed for reproducibility
            
        Returns:
            tuple: (cluster_labels, kmeans_model)
        """
        print(f"Performing K-means clustering with {n_clusters} clusters...")
        kmeans = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
        labels = kmeans.fit_predict(self.scaled_features)
        
        # Calculate metrics
        silhouette = silhouette_score(self.scaled_features, labels)
        davies_bouldin = davies_bouldin_score(self.scaled_features, labels)
        
        print(f"Silhouette Score: {silhouette:.3f}")
        print(f"Davies-Bouldin Score: {davies_bouldin:.3f}")
        
        return labels, kmeans
    
    def perform_hierarchical(self, n_clusters=5, linkage_method='ward'):
        """
        Perform Hierarchical clustering.
        
        Args:
            n_clusters (int): Number of clusters
            linkage_method (str): Linkage method ('ward', 'complete', 'average')
            
        Returns:
            tuple: (cluster_labels, hierarchical_model)
        """
        print(f"Performing Hierarchical clustering with {n_clusters} clusters...")
        hierarchical = AgglomerativeClustering(n_clusters=n_clusters, linkage=linkage_method)
        labels = hierarchical.fit_predict(self.scaled_features)
        
        silhouette = silhouette_score(self.scaled_features, labels)
        print(f"Silhouette Score: {silhouette:.3f}")
        
        return labels, hierarchical
    
    def perform_dbscan(self, eps=0.5, min_samples=5):
        """
        Perform DBSCAN clustering.
        
        Args:
            eps (float): Maximum distance between two samples
            min_samples (int): Minimum samples in a neighborhood
            
        Returns:
            tuple: (cluster_labels, dbscan_model)
        """
        print(f"Performing DBSCAN clustering (eps={eps}, min_samples={min_samples})...")
        dbscan = DBSCAN(eps=eps, min_samples=min_samples)
        labels = dbscan.fit_predict(self.scaled_features)
        
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        n_noise = list(labels).count(-1)
        
        print(f"Found {n_clusters} clusters")
        print(f"Noise points: {n_noise}")
        
        if n_clusters > 1:
            # Exclude noise points for silhouette score
            mask = labels != -1
            if mask.sum() > 0:
                silhouette = silhouette_score(self.scaled_features[mask], labels[mask])
                print(f"Silhouette Score: {silhouette:.3f}")
        
        return labels, dbscan
    
    def find_optimal_clusters(self, max_clusters=10):
        """
        Find optimal number of clusters using elbow method and silhouette scores.
        
        Args:
            max_clusters (int): Maximum number of clusters to test
            
        Returns:
            dict: Results with inertias and silhouette scores
        """
        print("Finding optimal number of clusters...")
        inertias = []
        silhouette_scores = []
        K_range = range(2, max_clusters + 1)
        
        for k in K_range:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = kmeans.fit_predict(self.scaled_features)
            inertias.append(kmeans.inertia_)
            silhouette_scores.append(silhouette_score(self.scaled_features, labels))
            print(f"k={k}: Inertia={kmeans.inertia_:.2f}, Silhouette={silhouette_scores[-1]:.3f}")
        
        return {
            'k_values': list(K_range),
            'inertias': inertias,
            'silhouette_scores': silhouette_scores
        }
    
    def reduce_dimensions_pca(self, n_components=2):
        """
        Reduce dimensions using PCA.
        
        Args:
            n_components (int): Number of principal components
            
        Returns:
            tuple: (reduced_features, pca_model)
        """
        print(f"Reducing dimensions with PCA to {n_components} components...")
        pca = PCA(n_components=n_components)
        reduced = pca.fit_transform(self.scaled_features)
        
        print(f"Explained variance ratio: {pca.explained_variance_ratio_}")
        print(f"Total variance explained: {pca.explained_variance_ratio_.sum():.3f}")
        
        return reduced, pca
    
    def reduce_dimensions_tsne(self, n_components=2, perplexity=30, random_state=42):
        """
        Reduce dimensions using t-SNE.
        
        Args:
            n_components (int): Number of components
            perplexity (float): t-SNE perplexity parameter
            random_state (int): Random seed
            
        Returns:
            ndarray: Reduced features
        """
        print(f"Reducing dimensions with t-SNE to {n_components} components...")
        tsne = TSNE(n_components=n_components, perplexity=perplexity, 
                    random_state=random_state, n_iter=1000)
        reduced = tsne.fit_transform(self.scaled_features)
        
        return reduced
    
    def analyze_moa_patterns(self, cluster_labels):
        """
        Analyze MOA distribution within each cluster.
        
        Args:
            cluster_labels (array): Cluster assignments
            
        Returns:
            dict: MOA distribution per cluster
        """
        print("\nAnalyzing MOA patterns in clusters...")
        
        moa_by_cluster = {}
        for cluster_id in set(cluster_labels):
            if cluster_id == -1:  # Skip noise points in DBSCAN
                continue
            
            mask = cluster_labels == cluster_id
            moa_in_cluster = self.moa_labels[mask]
            moa_counts = Counter(moa_in_cluster)
            
            print(f"\nCluster {cluster_id} ({mask.sum()} drugs):")
            print(f"  Top 5 MOAs:")
            for moa, count in moa_counts.most_common(5):
                print(f"    {moa}: {count} ({count/mask.sum()*100:.1f}%)")
            
            moa_by_cluster[cluster_id] = moa_counts
        
        return moa_by_cluster
    
    def plot_elbow_curve(self, results):
        """
        Plot elbow curve for K-means clustering.
        
        Args:
            results (dict): Results from find_optimal_clusters()
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        
        # Elbow curve
        ax1.plot(results['k_values'], results['inertias'], 'bo-')
        ax1.set_xlabel('Number of Clusters (k)', fontsize=12)
        ax1.set_ylabel('Inertia', fontsize=12)
        ax1.set_title('Elbow Method - Inertia vs. k', fontsize=14)
        ax1.grid(True, alpha=0.3)
        
        # Silhouette scores
        ax2.plot(results['k_values'], results['silhouette_scores'], 'ro-')
        ax2.set_xlabel('Number of Clusters (k)', fontsize=12)
        ax2.set_ylabel('Silhouette Score', fontsize=12)
        ax2.set_title('Silhouette Score vs. k', fontsize=14)
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('clustering_optimization.png', dpi=300, bbox_inches='tight')
        print("Saved plot: clustering_optimization.png")
        plt.close()
    
    def plot_clusters_2d(self, reduced_features, cluster_labels, method='PCA', 
                        color_by='cluster'):
        """
        Plot 2D visualization of clusters.
        
        Args:
            reduced_features (array): 2D reduced features
            cluster_labels (array): Cluster assignments
            method (str): Dimensionality reduction method used
            color_by (str): 'cluster' or 'moa'
        """
        fig, ax = plt.subplots(figsize=(12, 8))
        
        if color_by == 'cluster':
            scatter = ax.scatter(reduced_features[:, 0], reduced_features[:, 1],
                               c=cluster_labels, cmap='viridis', alpha=0.6, s=50)
            plt.colorbar(scatter, ax=ax, label='Cluster')
        else:  # color by MOA
            unique_moas = list(set(self.moa_labels))
            moa_to_int = {moa: i for i, moa in enumerate(unique_moas)}
            colors = [moa_to_int[moa] for moa in self.moa_labels]
            scatter = ax.scatter(reduced_features[:, 0], reduced_features[:, 1],
                               c=colors, cmap='tab20', alpha=0.6, s=50)
        
        ax.set_xlabel(f'{method} Component 1', fontsize=12)
        ax.set_ylabel(f'{method} Component 2', fontsize=12)
        ax.set_title(f'Drug Clustering - {method} Visualization (colored by {color_by})', 
                    fontsize=14)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        filename = f'clusters_{method.lower()}_{color_by}.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"Saved plot: {filename}")
        plt.close()
    
    def plot_dendrogram(self, method='ward'):
        """
        Plot hierarchical clustering dendrogram.
        
        Args:
            method (str): Linkage method
        """
        print("Generating dendrogram...")
        
        # Calculate linkage
        Z = linkage(self.scaled_features, method=method)
        
        # Plot
        fig, ax = plt.subplots(figsize=(15, 8))
        dendrogram(Z, ax=ax, no_labels=True)
        ax.set_xlabel('Drug Index', fontsize=12)
        ax.set_ylabel('Distance', fontsize=12)
        ax.set_title(f'Hierarchical Clustering Dendrogram ({method} linkage)', fontsize=14)
        
        plt.tight_layout()
        plt.savefig('dendrogram.png', dpi=300, bbox_inches='tight')
        print("Saved plot: dendrogram.png")
        plt.close()
    
    def plot_feature_importance(self, pca_model, top_n=10):
        """
        Plot feature importance from PCA loadings.
        
        Args:
            pca_model: Fitted PCA model
            top_n (int): Number of top features to show
        """
        # Get loadings for first two components
        loadings = pd.DataFrame(
            pca_model.components_.T,
            columns=['PC1', 'PC2'],
            index=self.feature_names
        )
        
        # Calculate importance as sum of absolute loadings
        loadings['importance'] = loadings.abs().sum(axis=1)
        loadings = loadings.sort_values('importance', ascending=False).head(top_n)
        
        # Plot
        fig, ax = plt.subplots(figsize=(10, 6))
        loadings[['PC1', 'PC2']].plot(kind='barh', ax=ax)
        ax.set_xlabel('PCA Loading', fontsize=12)
        ax.set_ylabel('Feature', fontsize=12)
        ax.set_title(f'Top {top_n} Features by PCA Importance', fontsize=14)
        ax.legend(['PC1', 'PC2'])
        ax.grid(True, alpha=0.3, axis='x')
        
        plt.tight_layout()
        plt.savefig('feature_importance.png', dpi=300, bbox_inches='tight')
        print("Saved plot: feature_importance.png")
        plt.close()
        
        return loadings


# ============================================================================
# EXAMPLE USAGE AND WORKFLOW
# ============================================================================

def main():
    """
    Main workflow demonstrating clustering analysis.
    """
    print("=" * 80)
    print("Drug Clustering Analysis by Mechanism of Action")
    print("=" * 80)
    
    # Initialize analyzer
    analyzer = DrugMOAClustering(tissue='PANCREAS')  # Or None for all tissues
    
    # Step 1: Load data
    analyzer.load_data(limit=5000)  # Remove limit to use all data
    
    # Step 2: Preprocess
    drug_features = analyzer.preprocess_data()
    
    # Step 3: Scale features
    analyzer.scale_features()
    
    # Step 4: Find optimal number of clusters
    optimization_results = analyzer.find_optimal_clusters(max_clusters=10)
    analyzer.plot_elbow_curve(optimization_results)
    
    # Step 5: Perform clustering with optimal k (e.g., 5)
    optimal_k = 5
    kmeans_labels, kmeans_model = analyzer.perform_kmeans(n_clusters=optimal_k)
    hierarchical_labels, _ = analyzer.perform_hierarchical(n_clusters=optimal_k)
    dbscan_labels, _ = analyzer.perform_dbscan(eps=2.0, min_samples=3)
    
    # Step 6: Dimensionality reduction
    pca_features, pca_model = analyzer.reduce_dimensions_pca(n_components=2)
    tsne_features = analyzer.reduce_dimensions_tsne(n_components=2, perplexity=30)
    
    # Step 7: Visualizations
    analyzer.plot_clusters_2d(pca_features, kmeans_labels, method='PCA', color_by='cluster')
    analyzer.plot_clusters_2d(pca_features, kmeans_labels, method='PCA', color_by='moa')
    analyzer.plot_clusters_2d(tsne_features, kmeans_labels, method='t-SNE', color_by='cluster')
    analyzer.plot_dendrogram(method='ward')
    analyzer.plot_feature_importance(pca_model, top_n=15)
    
    # Step 8: Analyze MOA patterns
    print("\n" + "=" * 80)
    print("K-MEANS CLUSTERING RESULTS")
    print("=" * 80)
    moa_patterns_kmeans = analyzer.analyze_moa_patterns(kmeans_labels)
    
    print("\n" + "=" * 80)
    print("HIERARCHICAL CLUSTERING RESULTS")
    print("=" * 80)
    moa_patterns_hierarchical = analyzer.analyze_moa_patterns(hierarchical_labels)
    
    print("\n" + "=" * 80)
    print("DBSCAN CLUSTERING RESULTS")
    print("=" * 80)
    moa_patterns_dbscan = analyzer.analyze_moa_patterns(dbscan_labels)
    
    # Step 9: Export results
    results_df = drug_features.copy()
    results_df['kmeans_cluster'] = kmeans_labels
    results_df['hierarchical_cluster'] = hierarchical_labels
    results_df['dbscan_cluster'] = dbscan_labels
    results_df['pca_1'] = pca_features[:, 0]
    results_df['pca_2'] = pca_features[:, 1]
    results_df['tsne_1'] = tsne_features[:, 0]
    results_df['tsne_2'] = tsne_features[:, 1]
    
    results_df.to_csv('drug_clustering_results.csv', index=False)
    print("\nSaved results to: drug_clustering_results.csv")
    
    print("\n" + "=" * 80)
    print("Analysis Complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()



