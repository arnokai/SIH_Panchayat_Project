import pandas as pd
import numpy as np
import joblib


# ==========================================
# 1. LOAD V1 MODELS
# ==========================================

rain_clf = joblib.load(
    "models/v1_rain_classifier.pkl"
)

rain_reg = joblib.load(
    "models/v1_rain_regressor.pkl"
)

tmax_reg = joblib.load(
    "models/v1_tmax_regressor.pkl"
)


# ==========================================
# 2. LOAD HISTORICAL WEATHER
# ==========================================

WEATHER_FILE = "data/raw/historical_weather.csv"

weather = pd.read_csv(
    WEATHER_FILE,
    parse_dates=["date"]
)

weather = weather.sort_values(
    ["panchayat_id", "date"]
).reset_index(drop=True)


# ==========================================
# 3. LOAD PANCHAYAT FEATURES
# ==========================================

PANCHAYAT_FILE = "data/panchayats.csv"

panchayats = pd.read_csv(
    PANCHAYAT_FILE
)


# ==========================================
# 4. CREATE HISTORICAL FEATURES
# ==========================================

def build_features(panchayat_id):

    # Get weather history for this Panchayat
    p = weather[
        weather["panchayat_id"] == panchayat_id
    ].copy()

    if len(p) < 8:
        raise ValueError(
            "Not enough historical weather data."
        )

    # Most recent observation
    latest = p.iloc[-1]

    # --------------------------------------
    # Rainfall lag features
    # --------------------------------------

    rain_lag_1 = p["rain_mm"].iloc[-1]

    rain_lag_2 = p["rain_mm"].iloc[-2]

    rain_lag_3 = p["rain_mm"].iloc[-3]

    rain_lag_7 = p["rain_mm"].iloc[-7]


    # --------------------------------------
    # Temperature lag features
    # --------------------------------------

    tmax_lag_1 = p["tmax_c"].iloc[-1]

    tmax_lag_2 = p["tmax_c"].iloc[-2]

    tmax_lag_7 = p["tmax_c"].iloc[-7]

    tmin_lag_1 = p["tmin_c"].iloc[-1]

    tmin_lag_2 = p["tmin_c"].iloc[-2]


    # --------------------------------------
    # Recent rainfall accumulation
    # --------------------------------------

    rain_3day_sum = (
        p["rain_mm"]
        .iloc[-3:]
        .sum()
    )

    rain_7day_sum = (
        p["rain_mm"]
        .iloc[-7:]
        .sum()
    )


    # --------------------------------------
    # Panchayat geographical information
    # --------------------------------------

    p_info = panchayats[
        panchayats["panchayat_id"] == panchayat_id
    ]

    if p_info.empty:
        raise ValueError(
            "Panchayat not found."
        )

    p_info = p_info.iloc[0]


    # --------------------------------------
    # Calendar features
    # --------------------------------------

    next_date = (
        latest["date"]
        + pd.Timedelta(days=1)
    )

    month = next_date.month

    day_of_year = next_date.dayofyear


    # --------------------------------------
    # Build feature dictionary
    # --------------------------------------

    features = {

        "latitude":
            p_info["latitude"],

        "longitude":
            p_info["longitude"],

        "elevation":
            p_info["elevation"],

        "distance_to_river_m":
            p_info["distance_to_river_m"],

        "rain_lag_1":
            rain_lag_1,

        "rain_lag_2":
            rain_lag_2,

        "rain_lag_3":
            rain_lag_3,

        "rain_lag_7":
            rain_lag_7,

        "tmax_lag_1":
            tmax_lag_1,

        "tmax_lag_2":
            tmax_lag_2,

        "tmax_lag_7":
            tmax_lag_7,

        "tmin_lag_1":
            tmin_lag_1,

        "tmin_lag_2":
            tmin_lag_2,

        "rain_3day_sum":
            rain_3day_sum,

        "rain_7day_sum":
            rain_7day_sum,

        "month":
            month,

        "day_of_year":
            day_of_year
    }


    return pd.DataFrame([features]), next_date


# ==========================================
# 5. FORECAST FUNCTION
# ==========================================

def forecast_panchayat(panchayat_id):

    X, forecast_date = build_features(
        panchayat_id
    )


    # --------------------------------------
    # Rain probability
    # --------------------------------------

    rain_probability = rain_clf.predict_proba(
        X
    )[0, 1]


    # --------------------------------------
    # Rain amount
    # --------------------------------------

    rain_amount = np.expm1(
        rain_reg.predict(X)[0]
    )


    if rain_probability > 0.5:
        final_rain = max(
            0,
            float(rain_amount)
        )
    else:
        final_rain = 0.0


    # --------------------------------------
    # Maximum temperature
    # --------------------------------------

    final_tmax = float(
        tmax_reg.predict(X)[0]
    )


    return {
        "date":
            forecast_date.date().isoformat(),

        "rain_mm":
            round(final_rain, 1),

        "rain_probability":
            round(float(rain_probability), 2),

        "tmax_c":
            round(final_tmax, 1)
    }


# ==========================================
# 6. TEST
# ==========================================

if __name__ == "__main__":

    result = forecast_panchayat("A2")

    print("\nV1 FORECAST")
    print("----------------------------------------")

    print(
        "Panchayat: AMDANGA"
    )

    print(
        "Forecast date:",
        result["date"]
    )

    print(
        "Rain:",
        result["rain_mm"],
        "mm"
    )

    print(
        "Rain probability:",
        result["rain_probability"]
    )

    print(
        "Maximum temperature:",
        result["tmax_c"],
        "°C"
    )