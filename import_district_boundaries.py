import geopandas as gpd
import os

def import_district_boundaries(shapefile_path):
    """
    Imports district boundary shapefile and prints basic information.
    Args:
        shapefile_path (str): Path to the district boundary shapefile.
    """
    if not os.path.exists(shapefile_path):
        print(f"Error: Shapefile not found at {shapefile_path}")
        return

    try:
        districts = gpd.read_file(shapefile_path)
        print(f"Successfully loaded district boundaries from {shapefile_path}")
        print("Number of districts:", len(districts))
        print("Columns:", districts.columns.tolist())
        print("CRS:", districts.crs)
        return districts
    except Exception as e:
        print(f"Error loading shapefile: {e}")
        return None

if __name__ == "__main__":
    # Example usage: Replace with your actual shapefile path
    # You would typically get this path from a configuration or user input
    district_shapefile = "data/geospatial/district_boundaries.shp" # Placeholder path
    print(f"Attempting to import district boundaries from: {district_shapefile}")
    imported_districts = import_district_boundaries(district_shapefile)
    if imported_districts is not None:
        print("\nFirst 5 rows of the imported data:")
        print(imported_districts.head())