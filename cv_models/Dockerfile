# Use an official Python runtime as a parent image
FROM python:3.9-slim-buster

# Set the working directory in the container
WORKDIR /app

# Install system dependencies for GDAL and other geospatial libraries
# This might vary based on the specific Linux distribution
RUN apt-get update && apt-get install -y \
    build-essential \
    libgdal-dev \
    gdal-bin \
    python3-gdal \
    # Add other necessary system libs if any
    && rm -rf /var/lib/apt/lists/*

# Copy the current directory contents into the container at /app
COPY . /app

# Install Python dependencies
# It's good practice to use a requirements.txt
# For now, listing them directly
RUN pip install --no-cache-dir \
    torch \
    torchvision \
    numpy \
    rasterio \
    geopandas \
    shapely \
    opencv-python \
    scikit-learn \
    celery \
    redis # Or rabbitmq client if using RabbitMQ

# Expose the port for Celery if needed (e.g., for Flower monitoring)
# EXPOSE 5555

# Command to run the Celery worker
# This assumes you have a celery_app defined in celery_tasks.py
# CMD ["celery", "-A", "cv_models.celery_tasks", "worker", "--loglevel=info"]