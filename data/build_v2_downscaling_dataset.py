import os

import pandas as pd


# ============================================================
# TERRAMIND V2 — DOWNSCALING TRAINING DATASET
# ============================================================
#
# Purpose:
# Build the historical training table for the actual
# coarse-block -> Panchayat downscaling experiment.
#
# For every date:
#
#   ONE coarse block weather state
#              +
#   Panchayat-specific terrain/location
#              +
#   historical local context
#              ↓
#        Panchayat target
#
# IMPORTANT:
# This script DOES NOT train a model.
# ============================================================


# ============================================================
# FILES
# ============================================================

V12_DATASET = (
    "data/raw/v1_2_training_dataset.csv"
)

COARSE_HISTORY = (
    "data/raw/coarse_block_history.csv"
)

TERRAIN_FILE = (
    "data/raw/panchayat_terrain_features.csv"
)

OUTPUT_FILE = (
    "data/raw/v2_downscaling_training_dataset.csv"
)


# ============================================================
# LOAD DATA
# ============================================================

print(
    "========================================"
)

print(
    "BUILDING V2 DOWNSCALING DATASET"
)

print(
    "========================================"
)


v12 = pd.read_csv(
    V12_DATASET,
    parse_dates=["date"]
)

coarse = pd.read_csv(
    COARSE_HISTORY,
    parse_dates=["date"]
)

terrain = pd.read_csv(
    TERRAIN_FILE
)


print(
    "V1.2 rows:",
    len(v12)
)

print(
    "Coarse history rows:",
    len(coarse)
)

print(
    "Terrain rows:",
    len(terrain)
)


# ============================================================
# 1. VALIDATE COARSE HISTORY
# ============================================================

print(
    "\n========================================"
)

print(
    "VALIDATING COARSE HISTORY"
)

print(
    "========================================"
)


required_coarse = [
    "date",
    "coarse_rain_mm",
    "coarse_tmax_c",
    "coarse_tmin_c",
]


missing_coarse = [
    c
    for c in required_coarse
    if c not in coarse.columns
]


if missing_coarse:

    raise ValueError(
        "Missing coarse columns: "
        +
        ", ".join(missing_coarse)
    )


if coarse["date"].duplicated().any():

    raise ValueError(
        "Coarse block history contains "
        "duplicate dates."
    )


if coarse[
    required_coarse
].isna().any().any():

    raise ValueError(
        "Missing values found in coarse "
        "history."
    )


# ============================================================
# 2. VALIDATE V1.2 DATASET
# ============================================================

print(
    "\n========================================"
)

print(
    "VALIDATING V1.2 DATASET"
)

print(
    "========================================"
)


required_v12 = [
    "date",
    "panchayat_id",
    "panchayat_name",
    "chirps_rain_mm",
    "rain_mm",
    "tmax_c",
    "tmin_c",
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
    "day_of_year_cos",
]


missing_v12 = [
    c
    for c in required_v12
    if c not in v12.columns
]


if missing_v12:

    raise ValueError(
        "Missing V1.2 columns: "
        +
        ", ".join(missing_v12)
    )


# Each Panchayat/date should occur exactly once.
duplicate_v12 = (
    v12
    .duplicated(
        subset=[
            "date",
            "panchayat_id"
        ]
    )
    .sum()
)


if duplicate_v12 > 0:

    raise ValueError(
        "V1.2 dataset contains "
        f"{duplicate_v12} duplicate "
        "Panchayat/date rows."
    )


# ============================================================
# 3. VALIDATE TERRAIN
# ============================================================

print(
    "\n========================================"
)

print(
    "VALIDATING TERRAIN"
)

print(
    "========================================"
)


required_terrain = [
    "panchayat_id",
    "panchayat_name",
    "latitude",
    "longitude",
    "elevation_dem_m",
    "slope_deg",
    "aspect_sin",
    "aspect_cos",
    "terrain_roughness_m",
    "relative_elevation_m",
]


missing_terrain = [
    c
    for c in required_terrain
    if c not in terrain.columns
]


if missing_terrain:

    raise ValueError(
        "Missing terrain columns: "
        +
        ", ".join(missing_terrain)
    )


duplicate_terrain = (
    terrain
    .duplicated(
        subset=["panchayat_id"]
    )
    .sum()
)


if duplicate_terrain > 0:

    raise ValueError(
        "Terrain table contains duplicate "
        "Panchayat IDs."
    )


if terrain[
    required_terrain
].isna().any().any():

    raise ValueError(
        "Missing terrain values found."
    )


# ============================================================
# 4. CHECK PANCHAYAT COVERAGE
# ============================================================

v12_ids = set(
    v12["panchayat_id"].unique()
)

terrain_ids = set(
    terrain["panchayat_id"].unique()
)


missing_terrain_ids = (
    v12_ids
    -
    terrain_ids
)


if missing_terrain_ids:

    raise ValueError(
        "Terrain missing for Panchayats: "
        +
        ", ".join(
            sorted(missing_terrain_ids)
        )
    )


print(
    "Panchayats in V1.2:",
    len(v12_ids)
)

print(
    "Panchayats in terrain:",
    len(terrain_ids)
)


# ============================================================
# 5. JOIN COARSE HISTORY TO V1.2
# ============================================================
#
# The coarse history has ONE row per date.
#
# The V1.2 dataset has 8 Panchayat rows per date.
#
# Therefore this many-to-one relationship should produce
# EXACTLY the same number of rows as V1.2.
# ============================================================

print(
    "\n========================================"
)

print(
    "JOINING COARSE BLOCK HISTORY"
)

print(
    "========================================"
)


before = len(v12)


v2 = v12.merge(
    coarse[
        [
            "date",
            "coarse_rain_mm",
            "coarse_tmax_c",
            "coarse_tmin_c",
            "coarse_latitude",
            "coarse_longitude",
            "source",
        ]
    ],
    on="date",
    how="left",
    validate="many_to_one",
)


after = len(v2)


print(
    "Rows before join:",
    before
)

print(
    "Rows after join:",
    after
)


# Handbook-style row-count assertion.
if after != before:

    raise ValueError(
        "JOIN CHANGED ROW COUNT: "
        f"{before} -> {after}"
    )


# Check for dates that failed to match.
missing_coarse_matches = (
    v2[
        [
            "coarse_rain_mm",
            "coarse_tmax_c",
            "coarse_tmin_c",
        ]
    ]
    .isna()
    .any(axis=1)
    .sum()
)


if missing_coarse_matches > 0:

    raise ValueError(
        "Coarse forecast/history missing "
        f"for {missing_coarse_matches} "
        "Panchayat/date rows."
    )


# ============================================================
# 6. JOIN TERRAIN
# ============================================================
#
# Terrain is static and has exactly one row per Panchayat.
#
# Again, the row count MUST NOT change.
# ============================================================

print(
    "\n========================================"
)

print(
    "JOINING TERRAIN FEATURES"
)

print(
    "========================================"
)


before = len(v2)


v2 = v2.merge(
    terrain[
        required_terrain
    ],
    on=[
        "panchayat_id",
        "panchayat_name",
    ],
    how="left",
    validate="many_to_one",
    suffixes=(
        "",
        "_terrain"
    ),
)


after = len(v2)


print(
    "Rows before terrain join:",
    before
)

print(
    "Rows after terrain join:",
    after
)


if after != before:

    raise ValueError(
        "TERRAIN JOIN CHANGED ROW COUNT: "
        f"{before} -> {after}"
    )


# ============================================================
# 7. CHECK FINAL MISSING VALUES
# ============================================================

print(
    "\n========================================"
)

print(
    "FINAL DATASET VALIDATION"
)

print(
    "========================================"
)


# The V1.2 dataset was already cleaned, but verify again.
critical_columns = [

    "date",
    "panchayat_id",
    "panchayat_name",

    "coarse_rain_mm",
    "coarse_tmax_c",
    "coarse_tmin_c",

    "latitude",
    "longitude",
    "elevation_dem_m",
    "slope_deg",
    "aspect_sin",
    "aspect_cos",
    "terrain_roughness_m",
    "relative_elevation_m",

    "chirps_rain_mm",
    "rain_lag_1",
    "rain_lag_2",
    "rain_lag_3",
    "rain_lag_7",
    "rain_3day_sum",
    "rain_7day_sum",

    "tmax_lag_1",
    "tmax_lag_2",
    "tmax_lag_7",
    "tmin_lag_1",
    "tmin_lag_2",

    "month",
    "day_of_year",
    "day_of_year_sin",
    "day_of_year_cos",

]


missing_counts = (
    v2[
        critical_columns
    ]
    .isna()
    .sum()
)


if missing_counts.sum() > 0:

    print(
        "Missing values:"
    )

    print(
        missing_counts[
            missing_counts > 0
        ]
        .to_string()
    )

    raise ValueError(
        "Final dataset contains missing "
        "critical values."
    )


# ============================================================
# 8. VERIFY EXPECTED ROW COUNT
# ============================================================

panchayat_count = (
    v2["panchayat_id"]
    .nunique()
)


date_count = (
    v2["date"]
    .nunique()
)


expected_rows = (
    panchayat_count
    *
    date_count
)


if len(v2) != expected_rows:

    raise ValueError(
        "Unexpected final row count: "
        f"{len(v2)}. "
        f"Expected {expected_rows} "
        f"({panchayat_count} × "
        f"{date_count})."
    )


# ============================================================
# 9. SORT
# ============================================================

v2 = (
    v2
    .sort_values(
        [
            "date",
            "panchayat_id"
        ]
    )
    .reset_index(drop=True)
)


# ============================================================
# 10. SELECT FINAL COLUMNS
# ============================================================

final_columns = [

    # Identification
    "date",
    "panchayat_id",
    "panchayat_name",

    # --------------------------------------------------------
    # Coarse block forecast/history
    # --------------------------------------------------------

    "coarse_rain_mm",
    "coarse_tmax_c",
    "coarse_tmin_c",

    "coarse_latitude",
    "coarse_longitude",

    "source",

    # --------------------------------------------------------
    # Panchayat geography / terrain
    # --------------------------------------------------------

    "latitude",
    "longitude",

    "elevation_dem_m",
    "slope_deg",
    "aspect_sin",
    "aspect_cos",
    "terrain_roughness_m",
    "relative_elevation_m",

    # --------------------------------------------------------
    # Local historical context
    # --------------------------------------------------------

    "rain_mm",

    "rain_lag_1",
    "rain_lag_2",
    "rain_lag_3",
    "rain_lag_7",

    "rain_3day_sum",
    "rain_7day_sum",

    "tmax_c",

    "tmax_lag_1",
    "tmax_lag_2",
    "tmax_lag_7",

    "tmin_c",

    "tmin_lag_1",
    "tmin_lag_2",

    # --------------------------------------------------------
    # Seasonal features
    # --------------------------------------------------------

    "month",
    "day_of_year",
    "day_of_year_sin",
    "day_of_year_cos",

    # --------------------------------------------------------
    # Targets
    # --------------------------------------------------------

    "chirps_rain_mm",

]


# Verify every requested final column exists.
missing_final_columns = [
    c
    for c in final_columns
    if c not in v2.columns
]


if missing_final_columns:

    raise ValueError(
        "Missing final columns: "
        +
        ", ".join(
            missing_final_columns
        )
    )


v2 = v2[
    final_columns
]


# ============================================================
# 11. SAVE
# ============================================================

os.makedirs(
    "data/raw",
    exist_ok=True
)


v2.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# 12. SUMMARY
# ============================================================

print(
    "\n========================================"
)

print(
    "V2 DOWNSCALING DATASET CREATED"
)

print(
    "========================================"
)

print(
    "Rows:",
    len(v2)
)

print(
    "Columns:",
    len(v2.columns)
)

print(
    "Panchayats:",
    v2[
        "panchayat_id"
    ].nunique()
)

print(
    "Dates:",
    v2["date"].min().date(),
    "to",
    v2["date"].max().date()
)


print(
    "\nRows per Panchayat:"
)

print(
    v2
    .groupby("panchayat_id")
    .size()
    .to_string()
)


print(
    "\nCoarse block source:"
)

print(
    v2["source"]
    .drop_duplicates()
    .to_string(index=False)
)


print(
    "\nTarget rainfall summary:"
)

print(
    v2[
        "chirps_rain_mm"
    ]
    .describe()
    .round(2)
    .to_string()
)


print(
    "\nSaved:"
)

print(
    OUTPUT_FILE
)