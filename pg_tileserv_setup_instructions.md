# pg_tileserv Setup and Configuration Instructions

This document outlines the steps to set up and configure `pg_tileserv` to serve vector tiles (MVT) from your PostGIS database. `pg_tileserv` is a lightweight PostGIS-only tile server that automatically serves vector tiles from your database tables and views.

## Prerequisites

*   A running PostgreSQL database with PostGIS extension enabled.
*   Your geospatial data (state, district, village boundaries, forest data, groundwater data, infrastructure data) imported into PostGIS.
*   `git` and `go` (version 1.16 or higher) installed on your system for building `pg_tileserv` from source. Alternatively, you can use pre-built binaries if available for your OS.

## Step 1: Install pg_tileserv

You can install `pg_tileserv` by building it from source.

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/CrunchyData/pg_tileserv.git
    cd pg_tileserv
    ```

2.  **Build the application:**
    ```bash
    go build -o pg_tileserv .
    ```
    This will create an executable named `pg_tileserv` in the current directory.

3.  **Move the executable to your PATH (optional but recommended):**
    ```bash
    sudo mv pg_tileserv /usr/local/bin/
    ```

## Step 2: Configure pg_tileserv

`pg_tileserv` can be configured using environment variables or a configuration file. For simplicity, we'll primarily use environment variables for basic setup.

1.  **Database Connection:**
    `pg_tileserv` connects to your PostgreSQL database using a connection string. Set the `DATABASE_URL` environment variable:

    ```bash
    export DATABASE_URL="postgresql://user:password@host:port/database_name?sslmode=disable"
    ```
    Replace `user`, `password`, `host`, `port`, and `database_name` with your actual PostGIS database credentials. `sslmode=disable` is often used for local development; adjust as needed for production environments.

2.  **Port (Optional):**
    By default, `pg_tileserv` runs on port `7800`. If you want to use a different port, set the `PORT` environment variable:

    ```bash
    export PORT="8080"
    ```

3.  **Configuration File (Advanced - Optional):**
    For more complex configurations, you can use a YAML configuration file. Create a file named `pg_tileserv.toml` (or `.yaml`, `.json`) in the directory where you run `pg_tileserv` or specify its path using the `-c` flag.

    Example `pg_tileserv.toml`:
    ```toml
    [server]
    port = 7800
    # bind = "0.0.0.0" # Listen on all interfaces

    [database]
    url = "postgresql://user:password@host:port/database_name?sslmode=disable"

    [viewer]
    enabled = true # Enable the built-in web viewer
    ```

## Step 3: Define Layers for Tiling

`pg_tileserv` automatically discovers tables and views in your PostGIS database that have a `geometry` column. For optimal performance and control, it's recommended to create **views** that define the specific data you want to serve as tiles.

**Example SQL for creating a view for state boundaries:**

```sql
CREATE OR REPLACE VIEW public.state_boundaries_tiles AS
SELECT
    gid, -- Primary key or unique identifier
    name, -- Example attribute
    ST_AsMVTGeom(
        ST_Transform(geom, 3857), -- Transform to Web Mercator (SRID 3857)
        ST_TileEnvelope(z, x, y),
        4096, -- Tile buffer (pixels)
        256,  -- Extent (pixels)
        true  -- Clip geometry
    ) AS geom
FROM
    state_boundaries
WHERE
    geom && ST_TileEnvelope(z, x, y);
```

*   **`state_boundaries`**: Replace with your actual table name (e.g., `state_boundaries`, `district_boundaries`, `village_boundaries`, `forest_data`, `groundwater_data`, `infrastructure_data`).
*   **`gid`, `name`**: Include any attributes you want to be available in the vector tiles.
*   **`ST_AsMVTGeom`**: This is the core PostGIS function for generating MVT geometries.
    *   `ST_Transform(geom, 3857)`: Transforms your geometry to Web Mercator (SRID 3857), which is standard for web maps.
    *   `ST_TileEnvelope(z, x, y)`: Defines the bounding box of the current tile. `pg_tileserv` automatically injects `z`, `x`, `y` variables.
    *   `4096`, `256`: These are common values for tile buffer and extent.
    *   `true`: Clips the geometry to the tile extent.
*   **`WHERE geom && ST_TileEnvelope(z, x, y)`**: This is crucial for performance. It filters the data to only include features that intersect with the current tile's bounding box, leveraging PostGIS's spatial indexing.

**Repeat this process for all layers you want to serve:** `district_boundaries`, `village_boundaries`, `forest_data`, `groundwater_data`, and `infrastructure_data`.

## Step 4: Run pg_tileserv

Once configured and your views are set up, run `pg_tileserv`:

```bash
pg_tileserv
```

You should see output indicating that the server is starting and listening on the configured port.

## Step 5: Accessing Tiles

`pg_tileserv` provides a built-in web viewer (if `viewer.enabled = true` in config or default) at `http://localhost:7800/`. You can browse your layers and inspect the generated tiles.

The vector tiles will be available at URLs like:

*   `http://localhost:7800/public.state_boundaries_tiles/{z}/{x}/{y}.pbf`
*   `http://localhost:7800/public.district_boundaries_tiles/{z}/{x}/{y}.pbf`
*   And so on for your other layers.

You can then integrate these tile URLs into your WebGIS frontend (e.g., using Mapbox GL JS, OpenLayers, Leaflet with a vector tile plugin).

## Troubleshooting

*   **Database Connection Issues:** Double-check your `DATABASE_URL` environment variable or configuration file. Ensure your PostgreSQL server is running and accessible from where `pg_tileserv` is running.
*   **No Layers Appearing:** Verify that your PostGIS tables/views have a `geometry` column and that the `ST_AsMVTGeom` function is correctly used in your views.
*   **Performance:** Ensure you have spatial indexes on your geometry columns (`CREATE INDEX GIST (geom)`). The `WHERE geom && ST_TileEnvelope(z, x, y)` clause in your views is critical for efficient tile generation.