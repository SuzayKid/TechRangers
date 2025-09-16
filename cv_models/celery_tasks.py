from celery import Celery
from cv_models.inference import ModelInference
import os

# Configure Celery
# BROKER_URL and RESULT_BACKEND should be configured in a real application
# For local development, Redis or RabbitMQ are common choices.
# Example: BROKER_URL = 'redis://localhost:6379/0'
# Example: RESULT_BACKEND = 'redis://localhost:6379/0'
celery_app = Celery(
    'cv_pipeline',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
)

# Optional: Configure Celery to discover tasks automatically
# celery_app.autodiscover_tasks(['cv_models'])

@celery_app.task(bind=True)
def process_satellite_image_task(self, image_path, model_path, num_classes, output_geojson_path):
    """
    Celery task to process a satellite image, perform inference,
    and convert raster output to vector polygons.
    """
    try:
        print(f"Starting image processing for: {image_path}")
        inference_processor = ModelInference(model_path, num_classes=num_classes)
        vector_assets_gdf = inference_processor.predict_and_vectorize(image_path, output_geojson_path)
        
        print(f"Finished processing {image_path}. Detected {len(vector_assets_gdf)} assets.")
        return {
            "status": "SUCCESS",
            "image_path": image_path,
            "output_geojson_path": output_geojson_path,
            "num_assets_detected": len(vector_assets_gdf)
        }
    except Exception as e:
        self.update_state(state='FAILURE', meta={'exc_type': type(e).__name__, 'exc_message': str(e)})
        print(f"Error processing {image_path}: {e}")
        raise