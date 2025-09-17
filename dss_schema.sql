-- Enable PostGIS if not already enabled
CREATE EXTENSION IF NOT EXISTS postgis;

-- Table for States
CREATE TABLE IF NOT EXISTS states (
    state_id SERIAL PRIMARY KEY,
    state_name VARCHAR(255) NOT NULL,
    geometry GEOMETRY(MultiPolygon, 4326) -- SRID 4326 for WGS 84 geographic coordinates
);

-- Table for Districts
CREATE TABLE IF NOT EXISTS districts (
    district_id SERIAL PRIMARY KEY,
    district_name VARCHAR(255) NOT NULL,
    state_id INTEGER NOT NULL REFERENCES states(state_id),
    geometry GEOMETRY(MultiPolygon, 4326)
);

-- Table for Villages
CREATE TABLE IF NOT EXISTS villages (
    village_id SERIAL PRIMARY KEY,
    village_name VARCHAR(255) NOT NULL,
    district_id INTEGER NOT NULL REFERENCES districts(district_id),
    geometry GEOMETRY(MultiPolygon, 4326)
);

-- Table for Village Attributes (e.g., land type, water index, population)
CREATE TABLE IF NOT EXISTS village_attributes (
    village_id INTEGER PRIMARY KEY REFERENCES villages(village_id),
    land_type VARCHAR(255),
    water_index FLOAT,
    population INTEGER
    -- Add other relevant attributes here
);

-- Table for Schemes
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS schemes (
    scheme_id SERIAL PRIMARY KEY,
    scheme_name VARCHAR(255) NOT NULL,
    description TEXT,
    description_embedding VECTOR(1536) -- Assuming OpenAI's text-embedding-ada-002 dimension
);

-- Table for Eligibility Rules
CREATE TABLE IF NOT EXISTS eligibility_rules (
    rule_id SERIAL PRIMARY KEY,
    scheme_id INTEGER NOT NULL REFERENCES schemes(scheme_id),
    attribute VARCHAR(255) NOT NULL, -- e.g., 'land_type', 'water_index', 'has_forest'
    operator VARCHAR(10) NOT NULL,   -- e.g., '=', '>', '<', '>=', '<=', 'LIKE'
    value TEXT NOT NULL             -- The value to compare against
);

-- Table for Forest Data
CREATE TABLE IF NOT EXISTS forest_data (
    forest_id SERIAL PRIMARY KEY,
    forest_type VARCHAR(255),
    area FLOAT,
    geometry GEOMETRY(MultiPolygon, 4326)
);

-- Table for Groundwater Data
CREATE TABLE IF NOT EXISTS groundwater_data (
    gw_id SERIAL PRIMARY KEY,
    water_level FLOAT,
    quality VARCHAR(255),
    geometry GEOMETRY(Point, 4326) -- Assuming groundwater data points
);

-- Table for Infrastructure Data
CREATE TABLE IF NOT EXISTS infrastructure_data (
    infra_id SERIAL PRIMARY KEY,
    infra_type VARCHAR(255), -- e.g., 'Road', 'Canal', 'Well'
    status VARCHAR(255),
    geometry GEOMETRY(MultiLineString, 4326) -- Can be LineString for roads/canals, Point for wells
);