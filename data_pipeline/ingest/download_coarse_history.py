import os

import pandas as pd
import requests


# ============================================================
# TERRAMIND — HISTORICAL COARSE BLOCK WEATHER
# ============================================================
#
# Purpose:
# Download historical weather for ONE representative block
# coordinate.
#
# This creates the coarse-input side of the downscaling
# training table.
#
# It deliberately does NOT request weather separately for
# every Panchayat.
#
# ============================================================


# ============================================================
# SETTINGS
# ============================================================

API_URL = (
    "https://archive-api.open-meteo.com/v1/archive"
)

START_DATE = "2024-01-01"

END_DATE = "2025-12-31"

TIMEZONE = "Asia/Kolkata"

OUTPUT_FILE = (
    "data/raw/coarse_block_history.csv"
)


# ============================================================
# REPRESENTATIVE BLOCK COORDINATE
# ============================================================
#
# Mean coordinate of the eight Panchayats.
#
# Latitude  = 22.836123
# Longitude = 88.492335
#
# ============================================================

BLOCK_LATITUDE = 22.836123

BLOCK_LONGITUDE = 88.492335


# ============================================================
# START
# ============================================================

print(
    "========================================"
)

print(
    "TERRAMIND HISTORICAL COARSE BLOCK DATA"
)

print(
    "========================================"
)

print(
    f"Block latitude:  {BLOCK_LATITUDE}"
)

print(
    f"Block longitude: {BLOCK_LONGITUDE}"
)

print(
    f"Date range: {START_DATE} to {END_DATE}"
)


# ============================================================
# REQUEST PARAMETERS
# ============================================================

params = {

    "latitude":
        BLOCK_LATITUDE,

    "longitude":
        BLOCK_LONGITUDE,

    "start_date":
        START_DATE,

    "end_date":
        END_DATE,

    "daily": (
        "temperature_2m_max,"
        "temperature_2m_min,"
        "rain_sum"
    ),

    "timezone":
        TIMEZONE
}


# ============================================================
# DOWNLOAD
# ============================================================

print(
    "\nDownloading historical block weather..."
)


try:

    response = requests.get(
        API_URL,
        params=params,
        timeout=120
    )

    response.raise_for_status()

except requests.RequestException as exc:

    raise RuntimeError(
        "Historical weather download failed: "
        f"{exc}"
    ) from exc


data = response.json()


# ============================================================
# CHECK RESPONSE
# ============================================================

if "daily" not in data:

    raise ValueError(
        "Open-Meteo response does not contain "
        "'daily' data."
    )


daily = data["daily"]


required_fields = [

    "time",

    "temperature_2m_max",

    "temperature_2m_min",

    "rain_sum"

]


missing_fields = [

    field
    for field in required_fields
    if field not in daily

]


if missing_fields:

    raise ValueError(
        "Missing fields from historical "
        "weather response: "
        +
        ", ".join(missing_fields)
    )


# ============================================================
# BUILD DATAFRAME
# ============================================================

coarse_history = pd.DataFrame({

    "date":
        daily["time"],

    "coarse_rain_mm":
        daily["rain_sum"],

    "coarse_tmax_c":
        daily[
            "temperature_2m_max"
        ],

    "coarse_tmin_c":
        daily[
            "temperature_2m_min"
        ]

})


# ============================================================
# ADD COARSE LOCATION METADATA
# ============================================================

coarse_history["coarse_latitude"] = (
    BLOCK_LATITUDE
)

coarse_history["coarse_longitude"] = (
    BLOCK_LONGITUDE
)

coarse_history["source"] = (
    "Open-Meteo historical archive"
)


# ============================================================
# DATE TYPE
# ============================================================

coarse_history["date"] = pd.to_datetime(
    coarse_history["date"]
)


# ============================================================
# SORT
# ============================================================

coarse_history = (
    coarse_history
    .sort_values("date")
    .reset_index(drop=True)
)


# ============================================================
# VALIDATION
# ============================================================

print(
    "\n========================================"
)

print(
    "VALIDATING HISTORICAL DATA"
)

print(
    "========================================"
)


# Expected number of calendar days
expected_days = (
    pd.Timestamp(END_DATE)
    -
    pd.Timestamp(START_DATE)
).days + 1


if len(coarse_history) != expected_days:

    raise ValueError(
        f"Expected {expected_days} rows, "
        f"got {len(coarse_history)}."
    )


# Duplicate dates
duplicate_dates = (
    coarse_history["date"]
    .duplicated()
    .sum()
)


if duplicate_dates > 0:

    raise ValueError(
        f"Duplicate dates found: "
        f"{duplicate_dates}"
    )


# Missing values
required_columns = [

    "date",

    "coarse_rain_mm",

    "coarse_tmax_c",

    "coarse_tmin_c"

]


missing_counts = (
    coarse_history[
        required_columns
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
        "Missing values found in "
        "historical coarse data."
    )


# Rainfall sanity check
if (
    coarse_history[
        "coarse_rain_mm"
    ] < 0
).any():

    raise ValueError(
        "Negative rainfall found."
    )


# Temperature sanity checks
if (
    (
        coarse_history[
            "coarse_tmax_c"
        ] < -50
    )
    |
    (
        coarse_history[
            "coarse_tmax_c"
        ] > 60
    )
).any():

    raise ValueError(
        "Tmax outside reasonable range."
    )


if (
    (
        coarse_history[
            "coarse_tmin_c"
        ] < -60
    )
    |
    (
        coarse_history[
            "coarse_tmin_c"
        ] > 50
    )
).any():

    raise ValueError(
        "Tmin outside reasonable range."
    )


# Tmax should not normally be lower than Tmin
if (
    coarse_history[
        "coarse_tmax_c"
    ]
    <
    coarse_history[
        "coarse_tmin_c"
    ]
).any():

    bad_rows = (
        coarse_history[
            coarse_history[
                "coarse_tmax_c"
            ]
            <
            coarse_history[
                "coarse_tmin_c"
            ]
        ]
    )

    raise ValueError(
        "Found rows where Tmax < Tmin:\n"
        +
        bad_rows.to_string(index=False)
    )


# ============================================================
# SAVE
# ============================================================

os.makedirs(
    "data/raw",
    exist_ok=True
)


coarse_history.to_csv(
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
    "HISTORICAL COARSE DATA READY"
)

print(
    "========================================"
)

print(
    "Rows:",
    len(coarse_history)
)

print(
    "Date range:",
    coarse_history["date"].min().date(),
    "to",
    coarse_history["date"].max().date()
)

print(
    "\nRainfall summary:"
)

print(
    coarse_history[
        "coarse_rain_mm"
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