import pandas as pd
from pathlib import Path

# ==========================================
# 1. FILES
# ==========================================



BASE_DIR = Path(__file__).resolve().parent

WEATHER_FILE = BASE_DIR / "raw" / "historical_weather.csv"
PANCHAYAT_FILE = BASE_DIR / "panchayats.csv"
TERRAIN_FILE = BASE_DIR / "raw" / "panchayat_terrain_features.csv"

OUTPUT_FILE = BASE_DIR / "raw" / "ml_training_dataset.csv"
# ==========================================
# 2. LOAD DATA
# ==========================================

weather = pd.read_csv(
    WEATHER_FILE,
    parse_dates=["date"]
)

panchayats = pd.read_csv(
    PANCHAYAT_FILE
)

terrain = pd.read_csv(
    TERRAIN_FILE
)

print("========================================")
print("BUILDING V1.1 ML DATASET")
print("========================================")

print("Weather rows:", len(weather))
print("Panchayats:", len(panchayats))
print("Terrain rows:", len(terrain))


# ==========================================
# 3. SELECT PANCHAYAT FEATURES
# ==========================================

geo_features = panchayats[
    [
        "panchayat_id",
        "latitude",
        "longitude",
        "elevation",
        "distance_to_river_m"
    ]
].copy()


# ==========================================
# 4. SELECT TERRAIN FEATURES
# ==========================================

terrain_features = terrain[
    [
        "panchayat_id",
        "elevation_dem_m",
        "slope_deg",
        "aspect_sin",
        "aspect_cos",
        "terrain_roughness_m",
        "relative_elevation_m"
    ]
].copy()


# ==========================================
# 5. CHECK TERRAIN MATCHING
# ==========================================

terrain_ids = set(
    terrain_features["panchayat_id"]
)

panchayat_ids = set(
    geo_features["panchayat_id"]
)

missing_terrain = (
    panchayat_ids
    -
    terrain_ids
)

if missing_terrain:

    raise ValueError(
        "Missing terrain data for Panchayats: "
        + ", ".join(
            sorted(missing_terrain)
        )
    )

print("\nAll Panchayats have terrain data.")


# ==========================================
# 6. MERGE TERRAIN + PANCHAYAT FEATURES
# ==========================================

geo_features = geo_features.merge(
    terrain_features,
    on="panchayat_id",
    how="left"
)


# ==========================================
# 7. CHECK FOR DUPLICATES
# ==========================================

duplicate_ids = (
    geo_features["panchayat_id"]
    .duplicated()
)

if duplicate_ids.any():

    raise ValueError(
        "Duplicate Panchayat IDs found "
        "after terrain merge."
    )


# ==========================================
# 8. MERGE WEATHER + GEOGRAPHIC FEATURES
# ==========================================

df = weather.merge(
    geo_features,
    on="panchayat_id",
    how="left"
)


# ==========================================
# 9. CHECK GEOGRAPHIC MATCHING
# ==========================================

required_geo_columns = [
    "latitude",
    "longitude",
    "elevation",
    "distance_to_river_m",
    "elevation_dem_m",
    "slope_deg",
    "aspect_sin",
    "aspect_cos",
    "terrain_roughness_m",
    "relative_elevation_m"
]

missing_geo = df[
    required_geo_columns
].isna().sum()

missing_geo = missing_geo[
    missing_geo > 0
]

if not missing_geo.empty:

    print("\nMissing geographic values:")
    print(missing_geo)

    raise ValueError(
        "Geographic feature merge produced "
        "missing values."
    )

print(
    "All weather rows matched with "
    "geographic + terrain data."
)


# ==========================================
# 10. SORT BY PANCHAYAT + DATE
# ==========================================

df = df.sort_values(
    [
        "panchayat_id",
        "date"
    ]
).reset_index(drop=True)


# ==========================================
# 11. CREATE LAG FEATURES
# ==========================================

group = df.groupby(
    "panchayat_id"
)

df["rain_lag_1"] = (
    group["rain_mm"].shift(1)
)

df["rain_lag_2"] = (
    group["rain_mm"].shift(2)
)

df["rain_lag_3"] = (
    group["rain_mm"].shift(3)
)

df["rain_lag_7"] = (
    group["rain_mm"].shift(7)
)

df["tmax_lag_1"] = (
    group["tmax_c"].shift(1)
)

df["tmax_lag_2"] = (
    group["tmax_c"].shift(2)
)

df["tmax_lag_7"] = (
    group["tmax_c"].shift(7)
)

df["tmin_lag_1"] = (
    group["tmin_c"].shift(1)
)

df["tmin_lag_2"] = (
    group["tmin_c"].shift(2)
)


# ==========================================
# 12. CREATE ROLLING RAINFALL FEATURES
# ==========================================

df["rain_3day_sum"] = (
    group["rain_mm"]
    .transform(
        lambda x:
        x.shift(1)
        .rolling(3)
        .sum()
    )
)

df["rain_7day_sum"] = (
    group["rain_mm"]
    .transform(
        lambda x:
        x.shift(1)
        .rolling(7)
        .sum()
    )
)


# ==========================================
# 13. CALENDAR FEATURES
# ==========================================

df["month"] = (
    df["date"].dt.month
)

df["day_of_year"] = (
    df["date"].dt.dayofyear
)


# ==========================================
# 14. CYCLIC SEASONAL FEATURES
# ==========================================
#
# Keep the original calendar columns for now
# so we can compare with the previous V1.
#
# The model will later use these cyclic
# features instead of raw day_of_year.
#

df["day_of_year_sin"] = (
    __import__("numpy").sin(
        2
        * __import__("numpy").pi
        * df["day_of_year"]
        / 365.25
    )
)

df["day_of_year_cos"] = (
    __import__("numpy").cos(
        2
        * __import__("numpy").pi
        * df["day_of_year"]
        / 365.25
    )
)


# ==========================================
# 15. REMOVE ROWS WITHOUT HISTORY
# ==========================================

df = (
    df
    .dropna()
    .reset_index(drop=True)
)


# ==========================================
# 16. FINAL COLUMN CHECK
# ==========================================

expected_columns = [
    "date",
    "panchayat_id",
    "panchayat_name",
    "rain_mm",
    "tmax_c",
    "tmin_c",

    "latitude",
    "longitude",
    "elevation",
    "distance_to_river_m",

    "elevation_dem_m",
    "slope_deg",
    "aspect_sin",
    "aspect_cos",
    "terrain_roughness_m",
    "relative_elevation_m",

    "rain_lag_1",
    "rain_lag_2",
    "rain_lag_3",
    "rain_lag_7",

    "tmax_lag_1",
    "tmax_lag_2",
    "tmax_lag_7",

    "tmin_lag_1",
    "tmin_lag_2",

    "rain_3day_sum",
    "rain_7day_sum",

    "month",
    "day_of_year",

    "day_of_year_sin",
    "day_of_year_cos"
]

missing_columns = [
    col
    for col in expected_columns
    if col not in df.columns
]

if missing_columns:

    raise ValueError(
        "Missing expected columns: "
        + ", ".join(missing_columns)
    )


# ==========================================
# 17. SAVE DATASET
# ==========================================

df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ==========================================
# 18. REPORT
# ==========================================

print("\n========================================")
print("V1.1 ML DATASET CREATED")
print("========================================")

print("Rows:", len(df))
print("Columns:", len(df.columns))

print("\nColumns:")
print(
    list(df.columns)
)

print("\nTerrain feature summary:")

print(
    df[
        [
            "elevation_dem_m",
            "slope_deg",
            "terrain_roughness_m",
            "relative_elevation_m"
        ]
    ]
    .describe()
    .round(3)
    .to_string()
)

print("\nMissing values:")
print(
    df.isna()
    .sum()
    .to_string()
)

print("\nFirst rows:")
print(
    df.head()
    .to_string(index=False)
)

print("\nSaved:")
print(OUTPUT_FILE)