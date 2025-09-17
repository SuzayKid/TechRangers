# DSS Database Optimization Plan

This document outlines the plan for optimizing the database for the Decision Support System (DSS).

## 1. Proposed Database Schema

A normalized database schema will be used to store the data.

**Schema Diagram:**

```mermaid
erDiagram
    states {
        int state_id PK
        varchar state_name
        geometry geometry
    }
    districts {
        int district_id PK
        varchar district_name
        int state_id FK
        geometry geometry
    }
    villages {
        int village_id PK
        varchar village_name
        int district_id FK
        geometry geometry
    }
    village_attributes {
        int village_id FK
        varchar land_type
        float water_index
        int population
    }
    schemes {
        int scheme_id PK
        varchar scheme_name
        text description
    }
    eligibility_rules {
        int rule_id PK
        int scheme_id FK
        varchar attribute
        varchar operator
        varchar value
    }
    forest_data {
        int forest_id PK
        varchar forest_type
        float area
        geometry geometry
    }
    groundwater_data {
        int gw_id PK
        float water_level
        varchar quality
        geometry geometry
    }
    infrastructure_data {
        int infra_id PK
        varchar infra_type
        varchar status
        geometry geometry
    }

    states ||--o{ districts : "has"
    districts ||--o{ villages : "has"
    villages ||--|{ village_attributes : "has"
    schemes ||--o{ eligibility_rules : "has"
```

## 2. Performance Optimization with a Materialized View

To ensure the DSS is fast and responsive, a materialized view called `village_dss_data` will be created.

**Materialized View (`village_dss_data`) Structure:**

*   `village_id`
*   `village_name`
*   `district_name`
*   `state_name`
*   `geometry`
*   `land_type`
*   `water_index`
*   `population`
*   `has_forest`
*   `forest_area_percentage`
*   `nearest_groundwater_level`
*   `nearest_groundwater_quality`
*   `has_road_access`
*   `distance_to_canal`
*   ...and other relevant pre-computed attributes.

## 3. Implementation Steps

1.  **Data Loading:** Load raw data into the tables defined in the schema.
2.  **Materialized View Creation:** Create the `village_dss_data` materialized view.
3.  **DSS Queries:** The DSS will primarily query the `village_dss_data` materialized view.
4.  **Data Refresh:** Set up a periodic job to refresh the materialized view.