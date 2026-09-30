# geospatial-gee

Earth Engine jobs: Sentinel-5P, FIRMS, MODIS AOD, ERA5/GFS → H3 grid

Starts as a router/module in `services/api/app/` (e.g. `app/geospatial_gee/`).
Split into its own Cloud Run service here only if it needs separate scaling or runtime.
