import psycopg2
import pandas as pd
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.cluster import KMeans
import numpy as np
import os

# Database connection details
DB_NAME = os.getenv("DB_NAME", "your_db_name")
DB_USER = os.getenv("DB_USER", "your_db_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "your_db_password")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    return conn

def fetch_village_data(conn):
    """Fetches relevant village data from the materialized view."""
    query = """
    SELECT
        village_id,
        village_name,
        land_type,
        water_index,
        population,
        has_forest,
        forest_area_percentage,
        nearest_groundwater_level,
        nearest_groundwater_quality,
        has_road_access,
        distance_to_canal
    FROM
        village_dss_data;
    """
    df = pd.read_sql(query, conn)
    return df

def preprocess_data(df):
    """
    Preprocesses the data for K-Means clustering.
    Handles missing values, encodes categorical features, and scales numerical features.
    """
    # Define categorical and numerical features
    categorical_features = ['land_type', 'nearest_groundwater_quality', 'has_forest', 'has_road_access']
    numerical_features = ['water_index', 'population', 'forest_area_percentage', 'nearest_groundwater_level', 'distance_to_canal']

    # Handle missing values:
    # For numerical features, fill with median
    for col in numerical_features:
        if df[col].isnull().any():
            df[col] = df[col].fillna(df[col].median())
    
    # For categorical features, fill with mode or a placeholder like 'unknown'
    for col in categorical_features:
        if df[col].isnull().any():
            df[col] = df[col].fillna('unknown')

    # Create a column transformer for preprocessing
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numerical_features),
            ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
        ])
    
    # Apply preprocessing
    X = preprocessor.fit_transform(df)
    
    return X, preprocessor

def perform_kmeans_clustering(X, n_clusters=5, random_state=42):
    """Performs K-Means clustering on the preprocessed data."""
    kmeans = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
    kmeans.fit(X)
    return kmeans

def assign_cluster_labels(df, kmeans_model, preprocessor):
    """
    Assigns cluster labels to the original DataFrame.
    Re-applies preprocessing to the original DataFrame to ensure consistency.
    """
    # Transform the original dataframe using the fitted preprocessor
    X_transformed = preprocessor.transform(df)
    df['cluster_label'] = kmeans_model.predict(X_transformed)
    return df

def main():
    print("Starting K-Means clustering for village asset profiles...")
    conn = None
    try:
        conn = get_db_connection()
        print("Database connection established.")
        
        df = fetch_village_data(conn)
        print(f"Fetched {len(df)} village records.")
        
        if df.empty:
            print("No data to cluster. Exiting.")
            return

        # Store village_id and village_name before preprocessing
        village_identifiers = df[['village_id', 'village_name']].copy()

        X, preprocessor = preprocess_data(df.drop(columns=['village_id', 'village_name']))
        print("Data preprocessed.")
        
        # Determine optimal number of clusters (e.g., using elbow method, not implemented here for brevity)
        # For now, we'll use a fixed number of clusters
        n_clusters = 5 
        kmeans_model = perform_kmeans_clustering(X, n_clusters=n_clusters)
        print(f"K-Means clustering performed with {n_clusters} clusters.")
        
        # Assign cluster labels back to the original village identifiers
        clustered_df = assign_cluster_labels(village_identifiers, kmeans_model, preprocessor)
        
        print("\nVillage Cluster Assignments:")
        print(clustered_df.head())

        # Example: You might want to save these results back to the database
        # For this task, just printing is sufficient.
        # If saving to DB, you'd need a new table like village_clusters (village_id, cluster_label)

    except psycopg2.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")

if __name__ == "__main__":
    main()