import geopandas as gpd
import pandas as pd

# ==========================================
# 1. LOAD GOVERNMENT PANCHAYAT BOUNDARIES
# ==========================================

geojson_file = "raw/amdanga_gps.geojson"

gdf = gpd.read_file(geojson_file)

print("Loaded GP boundary records:", len(gdf))


# ==========================================
# 2. COMBINE MULTIPLE PARTS OF SAME PANCHAYAT
# ==========================================

# Some Panchayats can have more than one polygon.
# Example: BODAI appears twice in the data.

combined = gdf.dissolve(
    by="GPCODE",
    as_index=False
)

print("Unique Panchayats:", len(combined))


# ==========================================
# 3. CALCULATE CENTRE POINT
# ==========================================

# The GeoJSON is already in longitude/latitude (EPSG:4326).

# Project to a metric CRS before calculating centroid.
projected = combined.to_crs("EPSG:32645")

projected["centroid"] = projected.geometry.centroid

# Convert centroid back to latitude/longitude.
centroids = projected.set_geometry("centroid").to_crs("EPSG:4326")

combined["longitude"] = centroids.geometry.x
combined["latitude"] = centroids.geometry.y

# ==========================================
# 4. SHOW RESULTS
# ==========================================

print("\nPanchayat coordinates:")
print(
    combined[
        ["GPCODE", "GPNAME", "latitude", "longitude"]
    ].to_string(index=False)
)


# ==========================================
# 5. SAVE COORDINATES
# ==========================================

coordinates = combined[
    ["GPCODE", "GPNAME", "latitude", "longitude"]
].copy()

coordinates.to_csv(
    "raw/panchayat_coordinates.csv",
    index=False
)

print("\nSaved: raw/panchayat_coordinates.csv")