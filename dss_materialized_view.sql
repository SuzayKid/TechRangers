-- Materialized View for DSS Data
CREATE MATERIALIZED VIEW IF NOT EXISTS village_dss_data AS
SELECT
    v.village_id,
    v.village_name,
    d.district_id,
    d.district_name,
    s.state_id,
    s.state_name,
    v.geometry AS village_geometry,
    va.land_type,
    va.water_index,
    va.population,
    -- Calculate if a village has forest data intersecting it
    EXISTS (
        SELECT 1
        FROM forest_data fd
        WHERE ST_Intersects(v.geometry, fd.geometry)
    ) AS has_forest,
    -- Calculate percentage of village area covered by forest
    COALESCE(
        ST_Area(
            ST_Union(
                ST_Intersection(v.geometry, fd.geometry)
            )
        ) / ST_Area(v.geometry) * 100,
        0
    ) AS forest_area_percentage,
    -- Get water level from the nearest groundwater data point
    (
        SELECT gw.water_level
        FROM groundwater_data gw
        ORDER BY v.geometry <-> gw.geometry
        LIMIT 1
    ) AS nearest_groundwater_level,
    -- Get water quality from the nearest groundwater data point
    (
        SELECT gw.quality
        FROM groundwater_data gw
        ORDER BY v.geometry <-> gw.geometry
        LIMIT 1
    ) AS nearest_groundwater_quality,
    -- Check for road access (e.g., if any infrastructure of type 'Road' is within a certain distance)
    EXISTS (
        SELECT 1
        FROM infrastructure_data id
        WHERE id.infra_type = 'Road' AND ST_DWithin(v.geometry, id.geometry, 0.01) -- 0.01 degrees as a buffer
    ) AS has_road_access,
    -- Calculate distance to the nearest canal (assuming 'Canal' is an infra_type)
    (
        SELECT ST_Distance(v.geometry, id.geometry)
        FROM infrastructure_data id
        WHERE id.infra_type = 'Canal'
        ORDER BY v.geometry <-> id.geometry
        LIMIT 1
    ) AS distance_to_canal
FROM
    villages v
JOIN
    districts d ON v.district_id = d.district_id
JOIN
    states s ON d.state_id = s.state_id
LEFT JOIN
    village_attributes va ON v.village_id = va.village_id
LEFT JOIN
    forest_data fd ON ST_Intersects(v.geometry, fd.geometry)
GROUP BY
    v.village_id, v.village_name, d.district_id, d.district_name, s.state_id, s.state_name, v.geometry, va.land_type, va.water_index, va.population;

-- Create indexes on the materialized view for faster querying
CREATE INDEX IF NOT EXISTS idx_village_dss_data_village_id ON village_dss_data (village_id);
CREATE INDEX IF NOT EXISTS idx_village_dss_data_district_id ON village_dss_data (district_id);
CREATE INDEX IF NOT EXISTS idx_village_dss_data_state_id ON village_dss_data (state_id);
CREATE INDEX IF NOT EXISTS idx_village_dss_data_land_type ON village_dss_data (land_type);
CREATE INDEX IF NOT EXISTS idx_village_dss_data_water_index ON village_dss_data (water_index);
CREATE INDEX IF NOT EXISTS idx_village_dss_data_has_forest ON village_dss_data (has_forest);
CREATE INDEX IF NOT EXISTS idx_village_dss_data_has_road_access ON village_dss_data (has_road_access);
CREATE INDEX IF NOT EXISTS idx_village_dss_data_geometry ON village_dss_data USING GIST (village_geometry);

-- Command to refresh the materialized view (to be run periodically)
-- REFRESH MATERIALIZED VIEW village_dss_data;