import os

import pandas as pd


# ============================================================
# TERRAMIND — SOIL CONTEXT CLASSIFICATION
# ============================================================
#
# Input:
#   SoilGrids sand / clay / silt percentages
#
# Purpose:
#   Preserve the measured values and derive a simple soil
#   context label for the advisory layer.
#
# IMPORTANT:
#   We are NOT inventing a "sandy" label.
#   The handbook requires sandy soil for the dry-spell rule,
#   so the classification must come from measured soil data.
#
# ============================================================


INPUT_FILE = (
    "data/raw/panchayat_soil_features.csv"
)

OUTPUT_FILE = (
    "data/raw/panchayat_soil_context.csv"
)


# ============================================================
# LOAD
# ============================================================

print(
    "========================================"
)

print(
    "CLASSIFYING PANCHAYAT SOIL CONTEXT"
)

print(
    "========================================"
)


df = pd.read_csv(
    INPUT_FILE
)


required = [
    "panchayat_id",
    "panchayat_name",
    "latitude",
    "longitude",
    "depth",
    "source",
    "sand_pct",
    "clay_pct",
    "silt_pct",
]


missing = [
    column
    for column in required
    if column not in df.columns
]


if missing:

    raise ValueError(
        "Missing columns: "
        +
        ", ".join(missing)
    )


# ============================================================
# VALIDATE SOIL FRACTIONS
# ============================================================

for column in [
    "sand_pct",
    "clay_pct",
    "silt_pct",
]:

    if df[column].isna().any():

        raise ValueError(
            f"Missing values in {column}."
        )

    if (
        (
            df[column] < 0
        )
        |
        (
            df[column] > 100
        )
    ).any():

        raise ValueError(
            f"Invalid values in {column}."
        )


fraction_sum = (
    df["sand_pct"]
    +
    df["clay_pct"]
    +
    df["silt_pct"]
)


print(
    "\nTexture fraction sums:"
)

print(
    fraction_sum.round(2)
    .to_string(index=False)
)


# SoilGrids components should approximately sum to 100%.
if (
    (fraction_sum - 100).abs() > 1.0
).any():

    raise ValueError(
        "Sand + clay + silt do not "
        "approximately sum to 100%."
    )


# ============================================================
# SIMPLE ADVISORY CLASS
# ============================================================
#
# We deliberately use a conservative classification.
#
# "sandy" is assigned only when sand is the dominant fraction
# among sand/clay/silt AND exceeds 50%.
#
# Otherwise we use "non_sandy".
#
# This is not a formal USDA soil-texture classification;
# it is only an advisory-context flag for the specific
# handbook dry-spell rule.
# ============================================================

df["soil_type"] = "non_sandy"


sandy_mask = (
    (df["sand_pct"] > 50)
    &
    (
        df["sand_pct"]
        >
        df["clay_pct"]
    )
    &
    (
        df["sand_pct"]
        >
        df["silt_pct"]
    )
)


df.loc[
    sandy_mask,
    "soil_type"
] = "sandy"


# ============================================================
# SUMMARY
# ============================================================

print(
    "\n========================================"
)

print(
    "SOIL CLASSIFICATION"
)

print(
    "========================================"
)


print(
    df[
        [
            "panchayat_id",
            "panchayat_name",
            "sand_pct",
            "clay_pct",
            "silt_pct",
            "soil_type",
        ]
    ]
    .round(1)
    .to_string(index=False)
)


print(
    "\nSoil-type counts:"
)

print(
    df["soil_type"]
    .value_counts()
    .to_string()
)


# ============================================================
# SAVE
# ============================================================

os.makedirs(
    "data/raw",
    exist_ok=True
)


df.to_csv(
    OUTPUT_FILE,
    index=False
)


print(
    "\n========================================"
)

print(
    "SOIL CONTEXT SAVED"
)

print(
    "========================================"
)

print(
    OUTPUT_FILE
)