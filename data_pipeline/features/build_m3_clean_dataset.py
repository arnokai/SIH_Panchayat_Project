import os

import pandas as pd


# ============================================================
# TERRAMIND M3 — CLEAN DOWNSCALING DATASET
# ============================================================
#
# Clean experiment:
#
#   COARSE BLOCK WEATHER
#          +
#   PANCHAYAT STATIC / TERRAIN FEATURES
#          +
#   SEASONAL FEATURES
#          ↓
#   CHIRPS PANCHAYAT TARGET
#
# IMPORTANT:
# We deliberately DO NOT include local observed weather
# variables such as rain_lag_* or tmax_lag_* here.
#
# This makes the experiment a cleaner test of:
#
#   coarse forecast + local geography
#                 ↓
#          Panchayat forecast
#
# ============================================================


V12_FILE = (
    "data/raw/v1_2_training_dataset.csv"
)

COARSE_FILE = (
    "data/raw/coarse_block_history.csv"
)

TERRAIN_FILE = (
    "data/raw/panchayat_terrain_features.csv"
)

OUTPUT_FILE = (
    "data/raw/m3_clean_downscaling_dataset.csv"
)


# ============================================================
# LOAD
# ============================================================

print(
    "========================================"
)

print(
    "BUILDING CLEAN M3 DATASET"
)

print(
    "========================================"
)


v12 = pd.read_csv(
    V12_FILE,
    parse_dates=["date"]
)

coarse = pd.read_csv(
    COARSE_FILE,
    parse_dates=["date"]
)

terrain = pd.read_csv(
    TERRAIN_FILE
)


print("V1.2 rows:", len(v12))
print("Coarse rows:", len(coarse))
print("Terrain rows:", len(terrain))


# ============================================================
# VALIDATE REQUIRED INPUTS
# ============================================================

v12_required = [
    "date",
    "panchayat_id",
    "panchayat_name",
    "latitude",
    "longitude",
    "elevation",
    "distance_to_river_m",
    "month",
    "day_of_year",
    "day_of_year_sin",
    "day_of_year_cos",
    "chirps_rain_mm",
]

terrain_required = [
    "panchayat_id",
    "panchayat_name",
    "elevation_dem_m",
    "slope_deg",
    "aspect_sin",
    "aspect_cos",
    "terrain_roughness_m",
    "relative_elevation_m",
]

coarse_required = [
    "date",
    "coarse_rain_mm",
    "coarse_tmax_c",
    "coarse_tmin_c",
]


missing_v12 = [
    c for c in v12_required
    if c not in v12.columns
]

missing_terrain = [
    c for c in terrain_required
    if c not in terrain.columns
]

missing_coarse = [
    c for c in coarse_required
    if c not in coarse.columns
]


if missing_v12:
    raise ValueError(
        "Missing V1.2 columns:\n"
        + "\n".join(missing_v12)
    )


if missing_terrain:
    raise ValueError(
        "Missing terrain columns:\n"
        + "\n".join(missing_terrain)
    )


if missing_coarse:
    raise ValueError(
        "Missing coarse columns:\n"
        + "\n".join(missing_coarse)
    )


# ============================================================
# VALIDATE DUPLICATES
# ============================================================

if v12.duplicated(
    subset=[
        "date",
        "panchayat_id"
    ]
).any():

    raise ValueError(
        "Duplicate Panchayat/date rows "
        "found in V1.2 dataset."
    )


if terrain.duplicated(
    subset=["panchayat_id"]
).any():

    raise ValueError(
        "Duplicate Panchayat IDs found "
        "in terrain data."
    )


if coarse.duplicated(
    subset=["date"]
).any():

    raise ValueError(
        "Duplicate dates found in "
        "coarse block history."
    )


# ============================================================
# KEEP ONLY REQUIRED TERRAIN FIELDS
# ============================================================

terrain_small = terrain[
    terrain_required
].copy()


# ============================================================
# BUILD BASE DATASET
# ============================================================

base = v12[
    v12_required
].copy()


print(
    "\nBase rows before joins:",
    len(base)
)


# ============================================================
# JOIN COARSE HISTORY
# ============================================================
#
# many Panchayat rows
#        →
# one coarse row per date
#
# Therefore:
#
# many_to_one
#
# and row count must stay unchanged.
# ============================================================

before = len(base)


base = base.merge(
    coarse[
        coarse_required
    ],
    on="date",
    how="left",
    validate="many_to_one",
)


after = len(base)


print(
    "Rows after coarse join:",
    after
)


if before != after:

    raise ValueError(
        f"Coarse join changed row count: "
        f"{before} -> {after}"
    )


# ============================================================
# CHECK COARSE MATCHES
# ============================================================

coarse_missing = (
    base[
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


if coarse_missing:

    raise ValueError(
        f"{coarse_missing} rows have "
        "missing coarse weather."
    )


# ============================================================
# JOIN TERRAIN
# ============================================================

before = len(base)


base = base.merge(
    terrain_small,
    on=[
        "panchayat_id",
        "panchayat_name",
    ],
    how="left",
    validate="many_to_one",
    suffixes=(
        "",
        "_terrain",
    ),
)


after = len(base)


print(
    "Rows after terrain join:",
    after
)


if before != after:

    raise ValueError(
        f"Terrain join changed row count: "
        f"{before} -> {after}"
    )


# ============================================================
# FINAL FEATURES
# ============================================================

FEATURES = [

    # --------------------------------------------------------
    # Coarse block weather
    # --------------------------------------------------------

    "coarse_rain_mm",
    "coarse_tmax_c",
    "coarse_tmin_c",

    # --------------------------------------------------------
    # Panchayat location
    # --------------------------------------------------------

    "latitude",
    "longitude",

    # --------------------------------------------------------
    # Panchayat geography
    # --------------------------------------------------------

    "elevation",
    "distance_to_river_m",

    # --------------------------------------------------------
    # DEM / terrain
    # --------------------------------------------------------

    "elevation_dem_m",
    "slope_deg",
    "aspect_sin",
    "aspect_cos",
    "terrain_roughness_m",
    "relative_elevation_m",

    # --------------------------------------------------------
    # Seasonality
    # --------------------------------------------------------

    "month",
    "day_of_year",
    "day_of_year_sin",
    "day_of_year_cos",
]


TARGET = "chirps_rain_mm"


# ============================================================
# CRITICAL DATA VALIDATION
# ============================================================

required_final = (
    [
        "date",
        "panchayat_id",
        "panchayat_name",
    ]
    +
    FEATURES
    +
    [TARGET]
)


missing_final = [
    c
    for c in required_final
    if c not in base.columns
]


if missing_final:

    raise ValueError(
        "Missing final columns:\n"
        +
        "\n".join(
            missing_final
        )
    )


missing_counts = (
    base[
        required_final
    ]
    .isna()
    .sum()
)


if missing_counts.sum() > 0:

    print(
        "\nMissing values:"
    )

    print(
        missing_counts[
            missing_counts > 0
        ]
        .to_string()
    )

    raise ValueError(
        "Final dataset contains "
        "missing required values."
    )


# ============================================================
# CHECK TARGET
# ============================================================

if (
    base[TARGET] < 0
).any():

    raise ValueError(
        "Negative CHIRPS rainfall found."
    )


# ============================================================
# CHECK EXPECTED STRUCTURE
# ============================================================

panchayat_count = (
    base["panchayat_id"]
    .nunique()
)

date_count = (
    base["date"]
    .nunique()
)

expected_rows = (
    panchayat_count
    *
    date_count
)


if len(base) != expected_rows:

    raise ValueError(
        "Unexpected row count.\n"
        f"Rows: {len(base)}\n"
        f"Expected: {expected_rows}\n"
        f"Panchayats: {panchayat_count}\n"
        f"Dates: {date_count}"
    )


# ============================================================
# SORT
# ============================================================

base = (
    base
    .sort_values(
        [
            "date",
            "panchayat_id",
        ]
    )
    .reset_index(drop=True)
)


# ============================================================
# FINAL OUTPUT
# ============================================================

final_columns = [
    "date",
    "panchayat_id",
    "panchayat_name",
] + FEATURES + [TARGET]


m3 = base[
    final_columns
].copy()


# ============================================================
# SAVE
# ============================================================

os.makedirs(
    "data/raw",
    exist_ok=True
)


m3.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# SUMMARY
# ============================================================

print(
    "\n========================================"
)

print(
    "CLEAN M3 DATASET CREATED"
)

print(
    "========================================"
)

print(
    "Rows:",
    len(m3)
)

print(
    "Columns:",
    len(m3.columns)
)

print(
    "Panchayats:",
    m3[
        "panchayat_id"
    ].nunique()
)

print(
    "Dates:",
    m3["date"].min().date(),
    "to",
    m3["date"].max().date()
)


print(
    "\nFeatures:"
)

for feature in FEATURES:
    print(
        " -",
        feature
    )


print(
    "\nTarget:",
    TARGET
)


print(
    "\nRows per Panchayat:"
)

print(
    m3
    .groupby("panchayat_id")
    .size()
    .to_string()
)


print(
    "\nFirst 8 rows:"
)

print(
    m3
    .head(8)
    .round(3)
    .to_string(index=False)
)


print(
    "\nSaved:"
)

print(
    OUTPUT_FILE
)