import torch
import numpy as np
import rasterio
from rasterio.features import shapes
from shapely.geometry import shape
import geopandas as gpd
from cv_models.model import UNET # Assuming UNET is defined in model.py

class ModelInference:
    def __init__(self, model_path, in_channels=3, num_classes=1, device="cuda" if torch.cuda.is_available() else "cpu"):
        self.device = device
        self.model = UNET(in_channels=in_channels, num_classes=num_classes).to(self.device)
        self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        self.model.eval()
        print(f"Model loaded from {model_path} and moved to {self.device}")

    def preprocess_image(self, image_array):
        """
        Preprocesses a raw image array for model inference.
        Assumes image_array is HWC (Height, Width, Channels) and values 0-255.
        Converts to C, H, W and normalizes to 0-1.
        """
        image = image_array.astype(np.float32) / 255.0
        image = np.transpose(image, (2, 0, 1)) # HWC -> CHW
        image = torch.from_numpy(image).unsqueeze(0) # Add batch dimension
        return image.to(self.device)

    def postprocess_mask(self, prediction_tensor, original_transform, original_crs):
        """
        Converts model prediction (tensor) into vector polygons.
        """
        # Convert prediction to numpy array. For multi-class, take argmax.
        # prediction_tensor is (1, num_classes, H, W)
        predicted_mask = torch.argmax(prediction_tensor, dim=1).squeeze().cpu().numpy()
        # predicted_mask is now (H, W) with class indices

        # Generate shapes from the multi-class mask
        # Iterate over each class to extract polygons
        all_geometries = []
        for class_id in range(self.model.num_classes): # Assuming num_classes is accessible
            if class_id == 0: # Assuming class 0 is background
                continue
            
            class_mask = (predicted_mask == class_id).astype(np.uint8)
            
            results = (
                {'properties': {'class_id': class_id, 'raster_val': v}, 'geometry': s}
                for i, (s, v) in enumerate(
                    shapes(class_mask, transform=original_transform))
            )
            
            for geom in results:
                if geom['properties']['raster_val'] == 1: # Only take the segmented class
                    all_geometries.append({
                        'geometry': shape(geom['geometry']),
                        'class_id': class_id
                    })
        
        if not all_geometries:
            return gpd.GeoDataFrame({'geometry': []}, crs=original_crs)

        gdf = gpd.GeoDataFrame(all_geometries, crs=original_crs)

        # Add properties like area, etc.
        gdf['area_sq_m'] = gdf.geometry.area
        return gdf

    def predict_and_vectorize(self, image_path, output_geojson_path=None):
        """
        Performs inference on a satellite image and saves vectorized assets.
        """
        with rasterio.open(image_path) as src:
            image_array = src.read()
            # Assuming image_array is C, H, W. Convert to HWC for preprocessing.
            if image_array.shape[0] == 4: # Assuming RGBA or similar, drop alpha
                image_array = image_array[:3, :, :]
            image_array = np.transpose(image_array, (1, 2, 0)) # C, H, W -> H, W, C

            preprocessed_image = self.preprocess_image(image_array)
            
            with torch.no_grad():
                prediction = self.model(preprocessed_image)
            
            vector_assets_gdf = self.postprocess_mask(prediction, src.transform, src.crs)
            
            if output_geojson_path:
                vector_assets_gdf.to_file(output_geojson_path, driver='GeoJSON')
                print(f"Vectorized assets saved to {output_geojson_path}")
            
            return vector_assets_gdf

if __name__ == "__main__":
    # This is a placeholder for demonstration.
    # In a real scenario, you would have a trained model and actual satellite imagery.
    
    # This is a placeholder for demonstration.
    # In a real scenario, you would have a trained model and actual satellite imagery.
    
    # Path to your trained model (e.g., after running cv_models/train.py)
    trained_model_path = "trained_unet_model.pth"
    
    # Example usage (replace with your actual image and output paths)
    image_path = "path/to/your/new_satellite_image.tif"
    output_geojson = "output_assets.geojson"

    num_classes_inference = 5 # Must match the num_classes used in training

    print(f"Attempting inference with model: {trained_model_path} on image: {image_path}")
    inference_processor = ModelInference(trained_model_path, num_classes=num_classes_inference)
    assets = inference_processor.predict_and_vectorize(image_path, output_geojson)
    print(f"Detected {len(assets)} assets and saved to {output_geojson}.")
    
    # Note: In a real application, you would not typically remove the trained model file here.
    # This cleanup is only for the dummy file created in the original placeholder.
    # if os.path.exists(trained_model_path):
    #     os.remove(trained_model_path)