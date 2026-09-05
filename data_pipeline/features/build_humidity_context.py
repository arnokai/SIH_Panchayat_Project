import os

import pandas as pd


# ============================================================
# TERRAMIND — HUMIDITY ADVISORY CONTEXT
# ============================================================
#
# Calculates consecutive days where:
#
#     humidity_pct > 85
#
# for each Panchayat.
#
# The resulting humidity_days field supports the handbook rule:
#
#     humidity > 85% for 3 days on paddy
#
# ============================================================


INPUT_FILE = (
    "data/raw/historical_weather.csv"
)

OUTPUT_FILE = (
    "data/raw/advisory_weather_history.csv"
)

HUMIDITY_THRESHOLD = 85.0


# ============================================================
# LOAD
# ============================================================

print(
    "========================================"
)

print(
    "BUILDING HUMIDITY ADVISORY CONTEXT"
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


if df["humidity_pct"].isna().any():

    raise ValueError(
        "Missing humidity values found."
    )


# ============================================================
# DETERMINE HIGH-HUMIDITY DAYS
# ============================================================

df["humidity_high"] = (
    df["humidity_pct"]
    > HUMIDITY_THRESHOLD
)


# ============================================================
# CONSECUTIVE HIGH-HUMIDITY DAYS
# ============================================================
#
# A new run starts whenever humidity_high changes from
# True to False or False to True.
#
# We then count the position inside each True run.
# ============================================================

df["humidity_run"] = (
    df
    .groupby("panchayat_id")[
        "humidity_high"
    ]
    .transform(
        lambda x:
            x.ne(x.shift()).cumsum()
    )
)


df["humidity_days"] = 0


high_mask = df["humidity_high"]


df.loc[high_mask, "humidity_days"] = (
    df.loc[high_mask]
    .groupby(
        [
            "panchayat_id",
            "humidity_run"
        ]
    )
    .cumcount()
    + 1
)


# ============================================================
# CLEAN
# ============================================================

df = df.drop(
    columns=[
        "humidity_high",
        "humidity_run"
    ]
)


# ============================================================
# VALIDATION OF DERIVED FIELD
# ============================================================

if (
    df["humidity_days"] < 0
).any():

    raise ValueError(
        "Invalid negative humidity_days."
    )


# A day with humidity <= 85 must have zero consecutive
# high-humidity days.
invalid_zero = (
    (
        df["humidity_pct"]
        <= HUMIDITY_THRESHOLD
    )
    &
    (
        df["humidity_days"] != 0
    )
)


if invalid_zero.any():

    raise ValueError(
        "humidity_days calculation failed."
    )


# ============================================================
# SUMMARY
# ============================================================

print(
    "\n========================================"
)

print(
    "HUMIDITY CONTEXT SUMMARY"
)

print(
    "========================================"
)

print(
    "Humidity threshold:",
    HUMIDITY_THRESHOLD,
    "%"
)


print(
    "Maximum humidity streak:",
    int(
        df["humidity_days"].max()
    ),
    "days"
)


print(
    "Rows reaching 3-day threshold:",
    int(
        (
            df["humidity_days"]
            >= 3
        ).sum()
    )
)


print(
    "\nPanchayat maximum streak:"
)

print(
    df
    .groupby("panchayat_id")[
        "humidity_days"
    ]
    .max()
    .to_string()
)


# ============================================================
# SAMPLE TRIGGER CANDIDATES
# ============================================================

trigger_candidates = df[
    df["humidity_days"] >= 3
]


print(
    "\n========================================"
)

print(
    "SAMPLE BLAST-RISK CONTEXT"
)

print(
    "========================================"
)


if trigger_candidates.empty:

    print(
        "No 3-day high-humidity periods found."
    )

else:

    print(
        trigger_candidates[
            [
                "date",
                "panchayat_id",
                "panchayat_name",
                "humidity_pct",
                "humidity_days"
            ]
        ]
        .head(20)
        .round(2)
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
    "HUMIDITY CONTEXT CREATED"
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