import os
import time

import pandas as pd
import requests


# ============================================================
# TERRAMIND — HISTORICAL WEATHER + HUMIDITY
# ============================================================
#
# Downloads historical weather for all Panchayats:
#
#   rain_mm
#   tmax_c
#   tmin_c
#   humidity_pct
#
# Humidity is included so the advisory engine can later
# evaluate the handbook's:
#
#   Humidity > 85% for 3 days on paddy
#
# ============================================================


# ============================================================
# SETTINGS
# ============================================================

START_DATE = "2024-01-01"
END_DATE = "2025-12-31"

OUTPUT_FILE = "data/raw/historical_weather.csv"

API_URL = "https://archive-api.open-meteo.com/v1/archive"

TIMEZONE = "Asia/Kolkata"


# ============================================================
# LOAD PANCHAYATS
# ============================================================

panchayat_file = "data/panchayats.csv"

panchayats = pd.read_csv(
    panchayat_file
)

print(
    "Panchayats loaded:",
    len(panchayats)
)


# ============================================================
# DOWNLOAD WEATHER
# ============================================================

all_weather = []


for _, p in panchayats.iterrows():

    print(
        f"\nDownloading weather for "
        f"{p['panchayat_name']} "
        f"({p['latitude']}, {p['longitude']})..."
    )

    params = {

        "latitude":
            p["latitude"],

        "longitude":
            p["longitude"],

        "start_date":
            START_DATE,

        "end_date":
            END_DATE,

        # Daily weather
        "daily": (
            "temperature_2m_max,"
            "temperature_2m_min,"
            "rain_sum"
        ),

        # Hourly humidity
        "hourly":
            "relative_humidity_2m",

        "timezone":
            TIMEZONE
    }


    # --------------------------------------------------------
    # REQUEST
    # --------------------------------------------------------

    try:

        response = requests.get(
            API_URL,
            params=params,
            timeout=60
        )

        response.raise_for_status()

    except requests.RequestException as exc:

        raise RuntimeError(
            "Weather download failed for "
            f"{p['panchayat_name']}: {exc}"
        ) from exc


    weather = response.json()


    if "daily" not in weather:

        raise ValueError(
            "API response does not contain "
            "'daily'."
        )


    if "hourly" not in weather:

        raise ValueError(
            "API response does not contain "
            "'hourly'."
        )


    daily = weather["daily"]

    hourly = weather["hourly"]


    # ========================================================
    # DAILY WEATHER
    # ========================================================

    daily_df = pd.DataFrame({

        "date":
            pd.to_datetime(
                daily["time"]
            ),

        "tmax_c":
            daily[
                "temperature_2m_max"
            ],

        "tmin_c":
            daily[
                "temperature_2m_min"
            ],

        "rain_mm":
            daily[
                "rain_sum"
            ]

    })


    # ========================================================
    # HOURLY HUMIDITY
    # ========================================================

    hourly_df = pd.DataFrame({

        "time":
            pd.to_datetime(
                hourly["time"]
            ),

        "humidity_pct":
            hourly[
                "relative_humidity_2m"
            ]

    })


    hourly_df["date"] = (
        hourly_df["time"]
        .dt.normalize()
    )


    # --------------------------------------------------------
    # DAILY MEAN HUMIDITY
    # --------------------------------------------------------

    daily_humidity = (
        hourly_df
        .groupby("date")[
            "humidity_pct"
        ]
        .mean()
        .reset_index()
    )


    # ========================================================
    # MERGE DAILY WEATHER + HUMIDITY
    # ========================================================

    df = daily_df.merge(

        daily_humidity,

        on="date",

        how="left",

        validate="one_to_one"

    )


    # ========================================================
    # PANCHAYAT METADATA
    # ========================================================

    df["panchayat_id"] = (
        p["panchayat_id"]
    )

    df["panchayat_name"] = (
        p["panchayat_name"]
    )


    # ========================================================
    # VALIDATE THIS PANCHAYAT
    # ========================================================

    if len(df) == 0:

        raise ValueError(
            f"No weather data returned for "
            f"{p['panchayat_name']}."
        )


    if df["humidity_pct"].isna().any():

        missing_humidity = int(
            df[
                "humidity_pct"
            ]
            .isna()
            .sum()
        )

        raise ValueError(
            f"{missing_humidity} humidity values "
            f"missing for "
            f"{p['panchayat_name']}."
        )


    print(
        "Days downloaded:",
        len(df)
    )

    print(
        "Mean humidity:",
        round(
            df["humidity_pct"].mean(),
            1
        ),
        "%"
    )


    all_weather.append(df)


    # Small pause between requests
    time.sleep(1)


# ============================================================
# COMBINE ALL PANCHAYATS
# ============================================================

weather_all = pd.concat(
    all_weather,
    ignore_index=True
)


# ============================================================
# CLEAN COLUMN ORDER
# ============================================================

weather_all = weather_all[
    [
        "date",
        "panchayat_id",
        "panchayat_name",
        "rain_mm",
        "tmax_c",
        "tmin_c",
        "humidity_pct"
    ]
]


# ============================================================
# SORT
# ============================================================

weather_all = (
    weather_all
    .sort_values(
        [
            "panchayat_id",
            "date"
        ]
    )
    .reset_index(drop=True)
)


# ============================================================
# FINAL VALIDATION
# ============================================================

print(
    "\n========================================"
)

print(
    "FINAL WEATHER VALIDATION"
)

print(
    "========================================"
)


# Expected rows
expected_days = (
    pd.Timestamp(END_DATE)
    -
    pd.Timestamp(START_DATE)
).days + 1

expected_rows = (
    expected_days
    *
    len(panchayats)
)


if len(weather_all) != expected_rows:

    raise ValueError(
        "Unexpected row count.\n"
        f"Expected: {expected_rows}\n"
        f"Got:      {len(weather_all)}"
    )


# Duplicate check
if weather_all.duplicated(
    subset=[
        "date",
        "panchayat_id"
    ]
).any():

    raise ValueError(
        "Duplicate date/Panchayat rows found."
    )


# Missing values
required_columns = [

    "date",
    "panchayat_id",
    "panchayat_name",
    "rain_mm",
    "tmax_c",
    "tmin_c",
    "humidity_pct"

]


missing = (
    weather_all[
        required_columns
    ]
    .isna()
    .sum()
)


if missing.sum() > 0:

    print(
        "\nMissing values:"
    )

    print(
        missing[
            missing > 0
        ]
        .to_string()
    )

    raise ValueError(
        "Missing required weather values."
    )


# Rainfall sanity
if (
    weather_all["rain_mm"] < 0
).any():

    raise ValueError(
        "Negative rainfall found."
    )


# Humidity sanity
if (
    (
        weather_all[
            "humidity_pct"
        ] < 0
    )
    |
    (
        weather_all[
            "humidity_pct"
        ] > 100
    )
).any():

    raise ValueError(
        "Humidity outside 0–100% found."
    )


# ============================================================
# SAVE
# ============================================================

os.makedirs(
    "data/raw",
    exist_ok=True
)


weather_all.to_csv(
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
    "WEATHER + HUMIDITY DOWNLOAD COMPLETE"
)

print(
    "========================================"
)

print(
    "Total rows:",
    len(weather_all)
)

print(
    "Dates:",
    weather_all["date"].min().date(),
    "to",
    weather_all["date"].max().date()
)

print(
    "Panchayats:",
    weather_all[
        "panchayat_id"
    ].nunique()
)

print(
    "Humidity range:",
    round(
        weather_all[
            "humidity_pct"
        ].min(),
        1
    ),
    "to",
    round(
        weather_all[
            "humidity_pct"
        ].max(),
        1
    ),
    "%"
)

print(
    "\nRows per Panchayat:"
)

print(
    weather_all
    .groupby("panchayat_name")
    .size()
    .to_string()
)

print(
    "\nSample:"
)

print(
    weather_all
    .head(10)
    .to_string(index=False)
)

print(
    "\nSaved:"
)

print(
    OUTPUT_FILE
)