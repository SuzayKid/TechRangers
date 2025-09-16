import geopandas as gpd
import os

def import_state_boundaries(shapefile_path):
    """
    Imports state boundary shapefile and prints basic information.
    Args:
        shapefile_path (str): Path to the state boundary shapefile.
    """
    if not os.path.exists(shapefile_path):
        print(f"Error: Shapefile not found at {shapefile_path}")
        return

    try:
        states = gpd.read_file(shapefile_path)
        print(f"Successfully loaded state boundaries from {shapefile_path}")
        print("Number of states:", len(states))
        print("Columns:", states.columns.tolist())
        print("CRS:", states.crs)
        return states
    except Exception as e:
        print(f"Error loading shapefile: {e}")
        return None

if __name__ == "__main__":
    # Example usage: Replace with your actual shapefile path
    # You would typically get this path from a configuration or user input
    state_shapefile = "data/geospatial/state_boundaries.shp" # Placeholder path
    print(f"Attempting to import state boundaries from: {state_shapefile}")
    imported_states = import_state_boundaries(state_shapefile)
    if imported_states is not None:
        print("\nFirst 5 rows of the imported data:")
        print(imported_states.head())