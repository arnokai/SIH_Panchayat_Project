from pathlib import Path

import numpy as np
import pandas as pd


# ==========================================
# 1. PATHS
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent

WEATHER_FILE = (
    BASE_DIR
    / "data"
    / "raw"
    / "historical_weather.csv"
)

TERRAIN_FILE = (
    BASE_DIR
    / "data"
    / "raw"
    / "panchayat_terrain_features.csv"
)

CHIRPS_FILE = (
    BASE_DIR
    / "data"
    / "raw"
    / "chirps_panchayat_rainfall.csv"
)

IMERG_FILE = (
    BASE_DIR
    / "data"
    / "raw"
    / "imerg_panchayat_rainfall.csv"
)

IMD_FILE = (
    BASE_DIR
    / "data"
    / "raw"
    / "imd_panchayat_rainfall.csv"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "raw"
    / "v1_2_training_dataset.csv"
)

PANCHAYAT_FILE = (
    BASE_DIR
    / "data"
    / "panchayats.csv"
)

# ==========================================
# 2. LOAD DATA
# ==========================================

print("========================================")
print("BUILDING V1.2 TRAINING DATASET")
print("========================================")


weather = pd.read_csv(
    WEATHER_FILE,
    parse_dates=["date"]
)

terrain = pd.read_csv(
    TERRAIN_FILE
)

chirps = pd.read_csv(
    CHIRPS_FILE,
    parse_dates=["date"]
)

imerg = pd.read_csv(
    IMERG_FILE,
    parse_dates=["date"]
)

imd = pd.read_csv(
    IMD_FILE,
    parse_dates=["date"]
)

panchayats = pd.read_csv(
    PANCHAYAT_FILE
)

print(
    "Open-Meteo rows:",
    len(weather)
)

print(
    "Terrain rows:",
    len(terrain)
)

print(
    "CHIRPS rows:",
    len(chirps)
)

print(
    "IMERG rows:",
    len(imerg)
)

print(
    "IMD rows:",
    len(imd)
)


# ==========================================
# 3. CLEAN / SELECT WEATHER
# ==========================================

weather = weather[
    [
        "date",
        "panchayat_id",
        "panchayat_name",
        "rain_mm",
        "tmax_c",
        "tmin_c"
    ]
].copy()


# ==========================================
# 4. ADD WEATHER LAG FEATURES
# ==========================================

weather = weather.sort_values(
    [
        "panchayat_id",
        "date"
    ]
).reset_index(drop=True)


group = weather.groupby(
    "panchayat_id"
)


weather["rain_lag_1"] = (
    group["rain_mm"].shift(1)
)

weather["rain_lag_2"] = (
    group["rain_mm"].shift(2)
)

weather["rain_lag_3"] = (
    group["rain_mm"].shift(3)
)

weather["rain_lag_7"] = (
    group["rain_mm"].shift(7)
)


weather["tmax_lag_1"] = (
    group["tmax_c"].shift(1)
)

weather["tmax_lag_2"] = (
    group["tmax_c"].shift(2)
)

weather["tmax_lag_7"] = (
    group["tmax_c"].shift(7)
)


weather["tmin_lag_1"] = (
    group["tmin_c"].shift(1)
)

weather["tmin_lag_2"] = (
    group["tmin_c"].shift(2)
)


# ==========================================
# 5. ROLLING RAINFALL
# ==========================================

weather["rain_3day_sum"] = (
    group["rain_mm"]
    .transform(
        lambda x:
        x.shift(1)
        .rolling(3)
        .sum()
    )
)

weather["rain_7day_sum"] = (
    group["rain_mm"]
    .transform(
        lambda x:
        x.shift(1)
        .rolling(7)
        .sum()
    )
)


# ==========================================
# 6. SEASONAL FEATURES
# ==========================================

weather["month"] = (
    weather["date"].dt.month
)

weather["day_of_year"] = (
    weather["date"].dt.dayofyear
)


weather["day_of_year_sin"] = (
    np.sin(
        2
        * np.pi
        * weather["day_of_year"]
        / 365.25
    )
)

weather["day_of_year_cos"] = (
    np.cos(
        2
        * np.pi
        * weather["day_of_year"]
        / 365.25
    )
)


# ==========================================
# 7. PREPARE CHIRPS AS T+1 TARGET
# ==========================================
#
# Predictor date = T
# Target date    = T+1
#
# This avoids accidentally training on
# same-day CHIRPS rainfall.
# ==========================================

chirps_target = chirps[
    [
        "date",
        "panchayat_id",
        "chirps_rain_mm"
    ]
].copy()


chirps_target = (
    chirps_target
    .rename(
        columns={
            "date": "target_date"
        }
    )
)


weather["target_date"] = (
    weather["date"]
    +
    pd.Timedelta(days=1)
)

# ==========================================
# MERGE BASE PANCHAYAT GEOGRAPHY
# ==========================================

panchayat_input = panchayats[
    [
        "panchayat_id",
        "latitude",
        "longitude",
        "elevation",
        "distance_to_river_m"
    ]
].copy()


weather = weather.merge(
    panchayat_input,
    on="panchayat_id",
    how="left"
)


# ==========================================
# CHECK PANCHAYAT GEOGRAPHY
# ==========================================

geo_columns = [
    "latitude",
    "longitude",
    "elevation",
    "distance_to_river_m"
]


missing_geo = (
    weather[geo_columns]
    .isna()
    .sum()
)


missing_geo = missing_geo[
    missing_geo > 0
]


if not missing_geo.empty:

    raise ValueError(
        "Missing Panchayat geographic values:\n"
        +
        missing_geo.to_string()
    )

# ==========================================
# 8. MERGE CHIRPS TARGET
# ==========================================

df = weather.merge(
    chirps_target,
    on=[
        "target_date",
        "panchayat_id"
    ],
    how="inner"
)


print(
    "\nAfter CHIRPS target merge:",
    len(df)
)


# ==========================================
# 9. MERGE IMERG
# ==========================================
#
# IMERG value is from the information
# available on predictor day T.
# ==========================================

imerg_input = imerg[
    [
        "date",
        "panchayat_id",
        "imerg_rain_mm"
    ]
].copy()


df = df.merge(
    imerg_input,
    on=[
        "date",
        "panchayat_id"
    ],
    how="left"
)


# ==========================================
# 10. MERGE IMD
# ==========================================
#
# IMD rainfall is also treated as a
# predictor available at day T.
# ==========================================

imd_input = imd[
    [
        "date",
        "panchayat_id",
        "rain_mm"
    ]
].copy()


imd_input = (
    imd_input
    .rename(
        columns={
            "rain_mm": "imd_rain_mm"
        }
    )
)


df = df.merge(
    imd_input,
    on=[
        "date",
        "panchayat_id"
    ],
    how="left"
)


# ==========================================
# 11. MERGE TERRAIN
# ==========================================

terrain_input = terrain[
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


df = df.merge(
    terrain_input,
    on="panchayat_id",
    how="left"
)


# ==========================================
# 12. CHECK DUPLICATES
# ==========================================

duplicate_rows = df.duplicated(
    subset=[
        "date",
        "panchayat_id"
    ]
)


if duplicate_rows.any():

    raise ValueError(
        "Duplicate predictor rows found."
    )


# ==========================================
# 13. CHECK REQUIRED DATA
# ==========================================

required_predictors = [

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

    "day_of_year_sin",
    "day_of_year_cos",

    "imerg_rain_mm",
    "imd_rain_mm",

    "elevation_dem_m",
    "slope_deg",
    "aspect_sin",
    "aspect_cos",
    "terrain_roughness_m",
    "relative_elevation_m",

    "chirps_rain_mm"
]


missing = (
    df[required_predictors]
    .isna()
    .sum()
)


missing = missing[
    missing > 0
]


print("\nMissing values before final cleanup:")

print(
    missing.to_string()
    if not missing.empty
    else "None"
)


# ==========================================
# 14. DROP ROWS WITHOUT COMPLETE HISTORY
# ==========================================

df = (
    df
    .dropna(
        subset=required_predictors
    )
    .reset_index(drop=True)
)


# ==========================================
# 15. FINAL ORDER
# ==========================================

df = df.sort_values(
    [
        "date",
        "panchayat_id"
    ]
).reset_index(drop=True)


# ==========================================
# 16. SAVE
# ==========================================

df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ==========================================
# 17. REPORT
# ==========================================

print("\n========================================")
print("V1.2 DATASET CREATED")
print("========================================")

print(
    "Rows:",
    len(df)
)

print(
    "Columns:",
    len(df.columns)
)

print(
    "Panchayats:",
    df["panchayat_id"].nunique()
)

print(
    "Predictor dates:",
    df["date"].min().date(),
    "to",
    df["date"].max().date()
)

print(
    "Target dates:",
    df["target_date"].min().date(),
    "to",
    df["target_date"].max().date()
)


print("\nTarget rainfall summary:")

print(
    df[
        [
            "panchayat_id",
            "panchayat_name",
            "chirps_rain_mm"
        ]
    ]
    .groupby(
        [
            "panchayat_id",
            "panchayat_name"
        ]
    )["chirps_rain_mm"]
    .agg(
        [
            "count",
            "mean",
            "std",
            "max"
        ]
    )
    .round(2)
    .to_string()
)


print("\nSaved:")
print(OUTPUT_FILE)