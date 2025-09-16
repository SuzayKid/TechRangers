import rasterio
import geopandas as gpd
import numpy as np
from shapely.geometry import mapping, box
from rasterio.mask import mask
from rasterio.features import rasterize
import cv2
import os

class SatelliteImageProcessor:
    def __init__(self, image_path, label_path, tile_size=(256, 256), overlap=0.25):
        self.image_path = image_path
        self.label_path = label_path
        self.tile_size = tile_size
        self.overlap = overlap
        self.image_dataset = None
        self.labels_gdf = None

    def load_data(self):
        """Loads the satellite image and geospatial labels."""
        self.image_dataset = rasterio.open(self.image_path)
        self.labels_gdf = gpd.read_file(self.label_path)
        print(f"Loaded image: {self.image_path}")
        print(f"Loaded labels: {self.label_path} with {len(self.labels_gdf)} features.")

    def create_tiles(self):
        """Generates image tiles and corresponding segmentation masks."""
        if self.image_dataset is None or self.labels_gdf is None:
            raise ValueError("Data not loaded. Call load_data() first.")

        width, height = self.image_dataset.width, self.image_dataset.height
        tile_w, tile_h = self.tile_size
        stride_w = int(tile_w * (1 - self.overlap))
        stride_h = int(tile_h * (1 - self.overlap))

        tiles = []
        masks = []

        for y in range(0, height - tile_h + 1, stride_h):
            for x in range(0, width - tile_w + 1, stride_w):
                # Define tile bounding box
                bbox = box(
                    self.image_dataset.xy(x, y)[0],
                    self.image_dataset.xy(x, y)[1],
                    self.image_dataset.xy(x + tile_w, y + tile_h)[0],
                    self.image_dataset.xy(x + tile_w, y + tile_h)[1]
                )

                # Extract image tile
                out_image, out_transform = mask(self.image_dataset, [bbox], crop=True)
                # Ensure image has 3 channels (RGB) and is in HWC format
                if out_image.shape[0] == 4: # Assuming RGBA or similar, drop alpha
                    out_image = out_image[:3, :, :]
                out_image = np.transpose(out_image, (1, 2, 0)) # C, H, W -> H, W, C

                # Rasterize labels to create mask for the current tile
                tile_labels = self.labels_gdf.cx[bbox.bounds[0]:bbox.bounds[2], bbox.bounds[1]:bbox.bounds[3]]
                
                mask_image = np.zeros((tile_h, tile_w), dtype=np.uint8)
                if not tile_labels.empty:
                    # Assuming 'class_id' column exists in labels_gdf for multi-class segmentation
                    # Class ID 0 is typically reserved for background
                    for class_id in tile_labels['class_id'].unique():
                        if class_id == 0: # Skip background class if present in labels
                            continue
                        class_geometries = tile_labels[tile_labels['class_id'] == class_id].geometry
                        shapes_for_class = [(geom, class_id) for geom in class_geometries]
                        
                        # Rasterize each class into the mask_image
                        # Use merge_alg=MergeAlg.replace to ensure higher class_id overwrites lower if overlaps
                        rasterized_class_mask = rasterize(
                            shapes=shapes_for_class,
                            out_shape=(tile_h, tile_w),
                            transform=out_transform,
                            fill=0, # Background value
                            all_touched=True,
                            dtype=rasterio.uint8
                        )
                        mask_image = np.maximum(mask_image, rasterized_class_mask) # Combine masks, higher class_id takes precedence
                        print(f"  Rasterized class_id {class_id} for tile at ({x}, {y})")
                else:
                    print(f"  No labels found for tile at ({x}, {y})")

                tiles.append(out_image)
                masks.append(mask_image)
        
        return np.array(tiles), np.array(masks)

    def normalize_image(self, image_tile):
        """Normalizes image pixel values to 0-1."""
        return image_tile.astype(np.float32) / 255.0

    def augment_data(self, image_tile, mask_tile):
        """Applies basic data augmentation (e.g., flips, rotations)."""
        # Example: Random horizontal flip
        if np.random.rand() > 0.5:
            image_tile = cv2.flip(image_tile, 1)
            mask_tile = cv2.flip(mask_tile, 1)
        
        # Example: Random rotation (90 degrees)
        k = np.random.randint(0, 4)
        image_tile = np.rot90(image_tile, k)
        mask_tile = np.rot90(mask_tile, k)

        return image_tile, mask_tile

    def run_pipeline(self):
        """Runs the complete preprocessing pipeline."""
        self.load_data()
        tiles, masks = self.create_tiles()
        
        processed_images = []
        processed_masks = []

        for i in range(len(tiles)):
            img = self.normalize_image(tiles[i])
            msk = masks[i]
            img_aug, msk_aug = self.augment_data(img, msk)
            processed_images.append(img_aug)
            processed_masks.append(msk_aug)
        
        return np.array(processed_images), np.array(processed_masks)

if __name__ == "__main__":
    # This is a placeholder for demonstration.
    # In a real scenario, you would have actual paths to satellite imagery and label files.
    # For testing, you might need to create dummy files or use small samples.
    
    # Example usage (requires dummy data or actual paths)
    # image_path = "path/to/your/satellite_image.tif"
    # label_path = "path/to/your/labels.geojson" # or .shp

    # processor = SatelliteImageProcessor(image_path, label_path)
    # images, masks = processor.run_pipeline()
    # print(f"Processed {len(images)} images and {len(masks)} masks.")
    # print(f"Shape of first image: {images[0].shape}, mask: {masks[0].shape}")
    pass