import os

import pandas as pd


# ============================================================
# TERRAMIND — DRY-SPELL ADVISORY CONTEXT
# ============================================================
#
# Calculates consecutive dry days for each Panchayat.
#
# A day is considered dry when:
#
#     rain_mm == 0
#
# This supports the handbook rule:
#
#     No rain for 7 days on sandy soil
#
# ============================================================


INPUT_FILE = (
    "data/raw/advisory_weather_history.csv"
)

OUTPUT_FILE = (
    "data/raw/advisory_context_history.csv"
)


# ============================================================
# LOAD
# ============================================================

print(
    "========================================"
)

print(
    "BUILDING DRY-SPELL ADVISORY CONTEXT"
)

print(
    "========================================"
)


df = pd.read_csv(
    INPUT_FILE,
    parse_dates=["date"]
)


required = [
    "date",
    "panchayat_id",
    "panchayat_name",
    "rain_mm",
    "tmax_c",
    "tmin_c",
    "humidity_pct",
    "humidity_days",
]


missing = [
    column
    for column in required
    if column not in df.columns
]


if missing:

    raise ValueError(
        "Missing columns:\n"
        +
        "\n".join(missing)
    )


df = (
    df[required]
    .sort_values(
        [
            "panchayat_id",
            "date"
        ]
    )
    .reset_index(drop=True)
)


# ============================================================
# VALIDATION
# ============================================================

if df.duplicated(
    subset=[
        "date",
        "panchayat_id"
    ]
).any():

    raise ValueError(
        "Duplicate Panchayat/date rows found."
    )


# ============================================================
# DETERMINE DRY DAYS
# ============================================================
#
# IMPORTANT:
# We use exactly 0 mm here because the handbook wording is
# "No rain for 7 days".
#
# This threshold can be revised later after agricultural review.
# ============================================================

df["dry_day"] = (
    df["rain_mm"] == 0
)


# ============================================================
# CONSECUTIVE DRY DAYS
# ============================================================

df["dry_run"] = (
    df
    .groupby("panchayat_id")[
        "dry_day"
    ]
    .transform(
        lambda x:
            x.ne(x.shift()).cumsum()
    )
)


df["dry_days"] = 0


dry_mask = df["dry_day"]


df.loc[dry_mask, "dry_days"] = (
    df.loc[dry_mask]
    .groupby(
        [
            "panchayat_id",
            "dry_run"
        ]
    )
    .cumcount()
    + 1
)


# ============================================================
# CLEAN INTERNAL COLUMNS
# ============================================================

df = df.drop(
    columns=[
        "dry_day",
        "dry_run"
    ]
)


# ============================================================
# VALIDATE DERIVED FIELD
# ============================================================

invalid = (
    (
        df["rain_mm"] != 0
    )
    &
    (
        df["dry_days"] != 0
    )
)


if invalid.any():

    raise ValueError(
        "dry_days calculation failed."
    )


# ============================================================
# SUMMARY
# ============================================================

print(
    "\n========================================"
)

print(
    "DRY-SPELL CONTEXT SUMMARY"
)

print(
    "========================================"
)

print(
    "Maximum dry streak:",
    int(
        df["dry_days"].max()
    ),
    "days"
)


print(
    "Rows reaching 7-day threshold:",
    int(
        (
            df["dry_days"]
            >= 7
        ).sum()
    )
)


print(
    "\nPanchayat maximum dry streak:"
)

print(
    df
    .groupby("panchayat_id")[
        "dry_days"
    ]
    .max()
    .to_string()
)


# ============================================================
# SAMPLE DRY-SPELL CANDIDATES
# ============================================================

dry_candidates = df[
    df["dry_days"] >= 7
]


print(
    "\n========================================"
)

print(
    "SAMPLE DRY-SPELL CONTEXT"
)

print(
    "========================================"
)


if dry_candidates.empty:

    print(
        "No 7-day dry periods found."
    )

else:

    print(
        dry_candidates[
            [
                "date",
                "panchayat_id",
                "panchayat_name",
                "rain_mm",
                "dry_days"
            ]
        ]
        .head(20)
        .to_string(index=False)
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
    "DRY-SPELL CONTEXT CREATED"
)

print(
    "========================================"
)

print(
    "Rows:",
    len(df)
)

print(
    "Columns:",
    len(df.columns)
)

print(
    "Saved:"
)

print(
    OUTPUT_FILE
)