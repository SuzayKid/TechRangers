import geopandas as gpd
import os

def import_village_boundaries(shapefile_path):
    """
    Imports village boundary shapefile and prints basic information.
    Args:
        shapefile_path (str): Path to the village boundary shapefile.
    """
    if not os.path.exists(shapefile_path):
        print(f"Error: Shapefile not found at {shapefile_path}")
        return

    try:
        villages = gpd.read_file(shapefile_path)
        print(f"Successfully loaded village boundaries from {shapefile_path}")
        print("Number of villages:", len(villages))
        print("Columns:", villages.columns.tolist())
        print("CRS:", villages.crs)
        return villages
    except Exception as e:
        print(f"Error loading shapefile: {e}")
        return None

if __name__ == "__main__":
    # Example usage: Replace with your actual shapefile path
    # You would typically get this path from a configuration or user input
    village_shapefile = "data/geospatial/village_boundaries.shp" # Placeholder path
    print(f"Attempting to import village boundaries from: {village_shapefile}")
    imported_villages = import_village_boundaries(village_shapefile)
    if imported_villages is not None:
        print("\nFirst 5 rows of the imported data:")
        print(imported_villages.head())