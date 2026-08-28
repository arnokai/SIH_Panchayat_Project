import pandas as pd
import requests
import os
import time


# ==========================================
# SETTINGS
# ==========================================

START_DATE = "2024-01-01"
END_DATE = "2025-12-31"

OUTPUT_FILE = "raw/historical_weather.csv"

API_URL = "https://archive-api.open-meteo.com/v1/archive"


# ==========================================
# LOAD PANCHAYATS
# ==========================================

panchayats = pd.read_csv("panchayats.csv")

print("Panchayats loaded:", len(panchayats))


# ==========================================
# DOWNLOAD WEATHER
# ==========================================

all_weather = []

for _, p in panchayats.iterrows():

    print(
        f"\nDownloading weather for "
        f"{p['panchayat_name']} "
        f"({p['latitude']}, {p['longitude']})..."
    )

    params = {
        "latitude": p["latitude"],
        "longitude": p["longitude"],
        "start_date": START_DATE,
        "end_date": END_DATE,
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "rain_sum"
        ],
        "timezone": "Asia/Kolkata"
    }

    response = requests.get(
        API_URL,
        params=params,
        timeout=60
    )

    response.raise_for_status()

    weather = response.json()

    daily = weather["daily"]

    df = pd.DataFrame({
        "date": daily["time"],
        "tmax_c": daily["temperature_2m_max"],
        "tmin_c": daily["temperature_2m_min"],
        "rain_mm": daily["rain_sum"]
    })

    df["panchayat_id"] = p["panchayat_id"]
    df["panchayat_name"] = p["panchayat_name"]

    all_weather.append(df)

    print("Days downloaded:", len(df))

    # Small pause between requests
    time.sleep(1)


# ==========================================
# COMBINE ALL PANCHAYATS
# ==========================================

weather_all = pd.concat(
    all_weather,
    ignore_index=True
)


# ==========================================
# CLEAN COLUMN ORDER
# ==========================================

weather_all = weather_all[
    [
        "date",
        "panchayat_id",
        "panchayat_name",
        "rain_mm",
        "tmax_c",
        "tmin_c"
    ]
]


# ==========================================
# SAVE
# ==========================================

os.makedirs("raw", exist_ok=True)

weather_all.to_csv(
    OUTPUT_FILE,
    index=False
)


print("\n========================================")
print("WEATHER DOWNLOAD COMPLETE")
print("========================================")

print("Total rows:", len(weather_all))

print("\nRows per Panchayat:")
print(
    weather_all
    .groupby("panchayat_name")
    .size()
)

print("\nSaved:")
print(OUTPUT_FILE)