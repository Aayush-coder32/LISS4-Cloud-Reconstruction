# Database Schema

## Core tables

- `users`: local identity, Google identity linkage, role, activation state.
- `image_assets`: uploaded rasters, previews, extracted metadata, approximate cloud statistics.
- `processing_jobs`: pipeline execution state, artifact paths, evaluation metrics, timing, and failures.

## Spatial handling

- Raster footprints are persisted as `bounds_json` and `transform_json`.
- For production PostGIS deployments, add geometry columns for polygon footprints and GIST indexing through migrations.

## Suggested production extensions

- `experiments`: experiment metadata linked to MLflow runs.
- `audit_logs`: security and operator action tracking.
- `vector_layers`: uploaded GeoJSON, shapefiles, and AOI references.
