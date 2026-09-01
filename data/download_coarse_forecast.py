import os

import pandas as pd
import requests


# ============================================================
# TERRAMIND — COARSE BLOCK FORECAST
# ============================================================
#
# IMPORTANT:
# This is a SINGLE coarse forecast representing the block.
#
# It is NOT requested separately for each Panchayat.
#
# The same coarse forecast will later be passed into the
# Panchayat downscaling model together with Panchayat-specific
# terrain/geographical features.
#
# ============================================================


# ============================================================
# SETTINGS
# ============================================================

API_URL = (
    "https://api.open-meteo.com/v1/forecast"
)

FORECAST_DAYS = 5

TIMEZONE = "Asia/Kolkata"

OUTPUT_FILE = (
    "data/raw/coarse_block_forecast.csv"
)


# ============================================================
# REPRESENTATIVE BLOCK LOCATION
# ============================================================
#
# Calculated from the mean latitude/longitude of the
# eight selected Panchayats.
#
# Latitude  = 22.836123
# Longitude = 88.492335
#
# ============================================================

BLOCK_LATITUDE = 22.836123

BLOCK_LONGITUDE = 88.492335


# ============================================================
# DISPLAY
# ============================================================

print(
    "========================================"
)

print(
    "TERRAMIND COARSE BLOCK FORECAST"
)

print(
    "========================================"
)

print(
    f"Block coordinate: "
    f"{BLOCK_LATITUDE}, "
    f"{BLOCK_LONGITUDE}"
)

print(
    f"Forecast days: {FORECAST_DAYS}"
)


# ============================================================
# REQUEST PARAMETERS
# ============================================================

params = {

    "latitude":
        BLOCK_LATITUDE,

    "longitude":
        BLOCK_LONGITUDE,

    "daily": (
        "rain_sum,"
        "temperature_2m_max,"
        "temperature_2m_min,"
        "precipitation_probability_max"
    ),

    "forecast_days":
        FORECAST_DAYS,

    "timezone":
        TIMEZONE
}


# ============================================================
# DOWNLOAD
# ============================================================

print(
    "\nFetching coarse block forecast..."
)


try:

    response = requests.get(
        API_URL,
        params=params,
        timeout=60
    )

    response.raise_for_status()

except requests.RequestException as exc:

    raise RuntimeError(
        "Failed to download coarse block "
        f"forecast: {exc}"
    ) from exc


data = response.json()


if "daily" not in data:

    raise ValueError(
        "Forecast response does not "
        "contain 'daily'."
    )


daily = data["daily"]


# ============================================================
# BUILD DATAFRAME
# ============================================================

required_keys = [

    "time",

    "rain_sum",

    "temperature_2m_max",

    "temperature_2m_min",

    "precipitation_probability_max"

]


missing_keys = [

    key
    for key in required_keys
    if key not in daily

]


if missing_keys:

    raise ValueError(
        "Missing forecast fields: "
        +
        ", ".join(missing_keys)
    )


forecast = pd.DataFrame({

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
        ],

    "coarse_rain_probability":
        daily[
            "precipitation_probability_max"
        ]

})


# ============================================================
# ADD METADATA
# ============================================================

forecast["source"] = (
    "Open-Meteo forecast"
)

forecast["coarse_latitude"] = (
    BLOCK_LATITUDE
)

forecast["coarse_longitude"] = (
    BLOCK_LONGITUDE
)


# ============================================================
# VALIDATION
# ============================================================

print(
    "\n========================================"
)

print(
    "VALIDATING FORECAST"
)

print(
    "========================================"
)


# Row count
if len(forecast) != FORECAST_DAYS:

    raise ValueError(
        f"Expected {FORECAST_DAYS} forecast rows, "
        f"got {len(forecast)}."
    )


# Duplicate dates
if forecast["date"].duplicated().any():

    raise ValueError(
        "Duplicate forecast dates found."
    )


# Missing values
required_columns = [

    "date",

    "coarse_rain_mm",

    "coarse_tmax_c",

    "coarse_tmin_c",

    "coarse_rain_probability"

]


missing_values = (
    forecast[
        required_columns
    ]
    .isna()
    .sum()
)


if missing_values.sum() > 0:

    print(
        "\nMissing values:"
    )

    print(
        missing_values[
            missing_values > 0
        ]
        .to_string()
    )

    raise ValueError(
        "Missing values found in "
        "coarse forecast."
    )


# Rainfall cannot be negative
if (
    forecast["coarse_rain_mm"] < 0
).any():

    raise ValueError(
        "Negative rainfall found."
    )


# Probability must be 0–100
if (
    (
        forecast[
            "coarse_rain_probability"
        ] < 0
    )
    |
    (
        forecast[
            "coarse_rain_probability"
        ] > 100
    )
).any():

    raise ValueError(
        "Rain probability outside "
        "0–100%."
    )


# Temperature sanity checks
if (
    (
        forecast[
            "coarse_tmax_c"
        ] < -50
    )
    |
    (
        forecast[
            "coarse_tmax_c"
        ] > 60
    )
).any():

    raise ValueError(
        "Tmax outside reasonable range."
    )


if (
    (
        forecast[
            "coarse_tmin_c"
        ] < -60
    )
    |
    (
        forecast[
            "coarse_tmin_c"
        ] > 50
    )
).any():

    raise ValueError(
        "Tmin outside reasonable range."
    )


# ============================================================
# SAVE
# ============================================================

os.makedirs(
    "data/raw",
    exist_ok=True
)


forecast.to_csv(
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
    "COARSE BLOCK FORECAST READY"
)

print(
    "========================================"
)

print(
    "Rows:",
    len(forecast)
)

print(
    "Dates:",
    forecast["date"].min(),
    "to",
    forecast["date"].max()
)

print(
    "\nForecast:"
)

print(
    forecast.to_string(
        index=False
    )
)

print(
    "\nSaved:"
)

print(
    OUTPUT_FILE
)