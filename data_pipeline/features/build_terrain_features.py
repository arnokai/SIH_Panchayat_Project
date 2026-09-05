import numpy as np
import pandas as pd
import rasterio
from scipy.ndimage import uniform_filter


# ==========================================
# 1. FILES
# ==========================================

DEM_FILE = "data/raw/dem/Copernicus_N22_E088_DEM.tif"
PANCHAYAT_FILE = "data/panchayats.csv"
OUTPUT_FILE = "data/raw/panchayat_terrain_features.csv"


# ==========================================
# 2. LOAD PANCHAYATS
# ==========================================

panchayats = pd.read_csv(PANCHAYAT_FILE)

print("========================================")
print("TERRAIN FEATURE EXTRACTION")
print("========================================")
print("Panchayats:", len(panchayats))
print("DEM:", DEM_FILE)


# ==========================================
# 3. OPEN DEM
# ==========================================

with rasterio.open(DEM_FILE) as src:

    dem = src.read(1).astype(float)

    transform = src.transform
    bounds = src.bounds
    nodata = src.nodata

    print("\nDEM information:")
    print("CRS:", src.crs)
    print("Resolution:", src.res)
    print("Bounds:", bounds)

    if nodata is not None:
        dem[dem == nodata] = np.nan


# ==========================================
# 4. APPROXIMATE METERS/PER PIXEL
# ==========================================
#
# DEM is EPSG:4326.
# Convert degree resolution to approximate metres.
#

mean_lat = panchayats["latitude"].mean()

meters_per_degree_lat = 111320.0

meters_per_degree_lon = (
    111320.0 * np.cos(
        np.deg2rad(mean_lat)
    )
)

pixel_x_m = (
    abs(transform.a)
    * meters_per_degree_lon
)

pixel_y_m = (
    abs(transform.e)
    * meters_per_degree_lat
)

print("\nApproximate pixel size:")
print(f"X: {pixel_x_m:.2f} m")
print(f"Y: {pixel_y_m:.2f} m")


# ==========================================
# 5. TERRAIN DERIVATIVES
# ==========================================

# np.gradient returns derivative with respect
# to rows and columns.

grad_y, grad_x = np.gradient(
    dem,
    pixel_y_m,
    pixel_x_m
)


# ------------------------------------------
# SLOPE
# ------------------------------------------

slope_rad = np.arctan(
    np.sqrt(
        grad_x ** 2
        +
        grad_y ** 2
    )
)

slope_deg = np.degrees(
    slope_rad
)


# ------------------------------------------
# ASPECT
# ------------------------------------------

aspect_rad = np.arctan2(
    -grad_x,
    grad_y
)

aspect_deg = (
    np.degrees(aspect_rad)
    + 360
) % 360


# ------------------------------------------
# TERRAIN ROUGHNESS
# ------------------------------------------
#
# Standard deviation of elevation
# in a moving window.
#
# 11 x 11 pixels ≈ 330 m window.
#

window_size = 11

mean_elevation = uniform_filter(
    np.nan_to_num(
        dem,
        nan=np.nanmean(dem)
    ),
    size=window_size,
    mode="nearest"
)

mean_elevation_sq = uniform_filter(
    np.nan_to_num(
        dem ** 2,
        nan=np.nanmean(dem ** 2)
    ),
    size=window_size,
    mode="nearest"
)

roughness = np.sqrt(
    np.maximum(
        mean_elevation_sq
        -
        mean_elevation ** 2,
        0
    )
)


# ------------------------------------------
# RELATIVE ELEVATION
# ------------------------------------------

relative_elevation = (
    dem
    -
    mean_elevation
)


# ==========================================
# 6. SAMPLE VALUES AT PANCHAYAT CENTROIDS
# ==========================================

records = []

with rasterio.open(DEM_FILE) as src:

    for _, p in panchayats.iterrows():

        lon = p["longitude"]
        lat = p["latitude"]

        row, col = src.index(
            lon,
            lat
        )

        elevation = dem[row, col]
        slope = slope_deg[row, col]
        aspect = aspect_deg[row, col]
        terrain_roughness = roughness[row, col]
        relative_elev = relative_elevation[row, col]

        # Cyclic aspect representation.
        aspect_sin = np.sin(
            np.deg2rad(aspect)
        )

        aspect_cos = np.cos(
            np.deg2rad(aspect)
        )

        records.append({

            "panchayat_id":
                p["panchayat_id"],

            "panchayat_name":
                p["panchayat_name"],

            "latitude":
                lat,

            "longitude":
                lon,

            "elevation_dem_m":
                elevation,

            "slope_deg":
                slope,

            "aspect_deg":
                aspect,

            "aspect_sin":
                aspect_sin,

            "aspect_cos":
                aspect_cos,

            "terrain_roughness_m":
                terrain_roughness,

            "relative_elevation_m":
                relative_elev
        })


# ==========================================
# 7. CREATE DATAFRAME
# ==========================================

features = pd.DataFrame(
    records
)


# ==========================================
# 8. CLEAN NUMERIC VALUES
# ==========================================

numeric_columns = [
    "elevation_dem_m",
    "slope_deg",
    "aspect_deg",
    "aspect_sin",
    "aspect_cos",
    "terrain_roughness_m",
    "relative_elevation_m"
]

for col in numeric_columns:

    features[col] = pd.to_numeric(
        features[col],
        errors="coerce"
    )


# ==========================================
# 9. DISPLAY
# ==========================================

print("\nPanchayat terrain features:")
print(
    features.to_string(
        index=False
    )
)


# ==========================================
# 10. SAVE
# ==========================================

features.to_csv(
    OUTPUT_FILE,
    index=False
)

print("\n========================================")
print("TERRAIN FEATURES SAVED")
print("========================================")
print(OUTPUT_FILE)