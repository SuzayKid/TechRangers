import geopandas as gpd
from sqlalchemy import create_engine
import psycopg2
import os

def import_data_to_postgis(shapefile_path, table_name, db_connection_string):
    """
    Imports a geospatial shapefile into a PostGIS database.

    Args:
        shapefile_path (str): Path to the input shapefile.
        table_name (str): Name of the table to create/overwrite in PostGIS.
        db_connection_string (str): SQLAlchemy compatible database connection string
                                    (e.g., "postgresql://user:password@host:port/database").
    """
    if not os.path.exists(shapefile_path):
        print(f"Error: Shapefile not found at {shapefile_path}")
        return

    try:
        # Read the shapefile using geopandas
        gdf = gpd.read_file(shapefile_path)
        print(f"Successfully loaded data from {shapefile_path}")
        print("Number of features:", len(gdf))
        print("Columns:", gdf.columns.tolist())
        print("CRS:", gdf.crs)

        # Create a SQLAlchemy engine for PostGIS connection
        engine = create_engine(db_connection_string)

        # Import data to PostGIS
        # 'if_exists='replace'' will drop the table if it exists and recreate it.
        # Use 'append' if you want to add to an existing table.
        gdf.to_postgis(table_name, engine, if_exists='replace', index=False)
        print(f"Successfully imported data to PostGIS table: {table_name}")

    except Exception as e:
        print(f"Error importing data to PostGIS: {e}")

if __name__ == "__main__":
    # --- Configuration ---
    # Replace with your actual database connection details
    DB_USER = os.getenv("POSTGIS_DB_USER", "gisuser") # Placeholder
    DB_PASSWORD = os.getenv("POSTGIS_DB_PASSWORD", "gispassword") # Placeholder
    DB_HOST = os.getenv("POSTGIS_DB_HOST", "localhost")
    DB_PORT = os.getenv("POSTGIS_DB_PORT", "5432")
    DB_NAME = os.getenv("POSTGIS_DB_NAME", "gisdb")

    # Example shapefile paths and table names
    # Replace with your actual data paths and desired table names
    FOREST_SHAPEFILE = "data/external/forest_data.shp" # Placeholder path
    FOREST_TABLE_NAME = "forest_data"

    GROUNDWATER_SHAPEFILE = "data/external/groundwater_data.shp" # Placeholder path
    GROUNDWATER_TABLE_NAME = "groundwater_data"

    INFRASTRUCTURE_SHAPEFILE = "data/external/infrastructure_data.shp" # Placeholder path
    INFRASTRUCTURE_TABLE_NAME = "infrastructure_data"

    # Construct the database connection string
    DB_CONNECTION_STRING = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

    print("--- Importing Forest Data ---")
    import_data_to_postgis(FOREST_SHAPEFILE, FOREST_TABLE_NAME, DB_CONNECTION_STRING)

    print("\n--- Importing Groundwater Data ---")
    import_data_to_postgis(GROUNDWATER_SHAPEFILE, GROUNDWATER_TABLE_NAME, DB_CONNECTION_STRING)

    print("\n--- Importing Infrastructure Data ---")
    import_data_to_postgis(INFRASTRUCTURE_SHAPEFILE, INFRASTRUCTURE_TABLE_NAME, DB_CONNECTION_STRING)

    print("\n--- Important: Ensure PostGIS is installed and configured in your PostgreSQL database. ---")
    print("--- You also need to install required Python packages: geopandas, psycopg2-binary, sqlalchemy. ---")
    print("--- pip install geopandas psycopg2-binary sqlalchemy ---")