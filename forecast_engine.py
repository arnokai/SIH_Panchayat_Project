import pandas as pd
import numpy as np
import joblib


# ============================================================
# TERRAMIND FORECAST ENGINE — V1.3
# ============================================================
#
# Rain probability -> V1 rain classifier (17 features)
# Rain amount      -> V1.3 calibration + residual (25 features)
# Tmax             -> V1 Tmax regressor (17 features)
#
# V1.3 rainfall:
#
# IMERG + IMD + Open-Meteo
#          ↓
# Linear calibration
#          ↓
# Calibrated rainfall
#          +
# 0.10 × residual correction
#          ↓
# Final rainfall estimate
# ============================================================


# ============================================================
# 1. MODEL FEATURES
# ============================================================

# Original V1 models were trained with these 17 features.
V1_FEATURES = [
    "latitude",
    "longitude",
    "elevation",
    "distance_to_river_m",
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
]


# V1.3 residual model was trained with these 25 features.
V13_FEATURES = [
    "latitude",
    "longitude",
    "elevation",
    "distance_to_river_m",
    "elevation_dem_m",
    "slope_deg",
    "aspect_sin",
    "aspect_cos",
    "terrain_roughness_m",
    "relative_elevation_m",
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
    "imerg_rain_mm",
    "imd_rain_mm",
    "day_of_year_sin",
    "day_of_year_cos",
]


CALIBRATION_FEATURES = [
    "imerg_rain_mm",
    "imd_rain_mm",
    "rain_mm",
]


# ============================================================
# 2. LOAD MODELS
# ============================================================

# V1 probability model
rain_clf = joblib.load(
    "models/v1_rain_classifier.pkl"
)


# V1 Tmax model
tmax_reg = joblib.load(
    "models/v1_tmax_regressor.pkl"
)


# V1.3 rainfall calibration model
rain_calibration = joblib.load(
    "models/v1_3_rain_calibration.pkl"
)


# V1.3 rainfall residual model
rain_residual = joblib.load(
    "models/v1_3_rain_residual.pkl"
)


# V1.3 metadata
v13_metadata = joblib.load(
    "models/v1_3_metadata.pkl"
)


# Read the validated residual strength.
RESIDUAL_ALPHA = float(
    v13_metadata.get(
        "residual_alpha",
        0.10
    )
)


# ============================================================
# 3. LOAD HISTORICAL WEATHER
# ============================================================

WEATHER_FILE = (
    "data/raw/historical_weather.csv"
)

weather = pd.read_csv(
    WEATHER_FILE,
    parse_dates=["date"]
)

weather = (
    weather
    .sort_values(
        ["panchayat_id", "date"]
    )
    .reset_index(drop=True)
)


# ============================================================
# 4. LOAD PANCHAYAT INFORMATION
# ============================================================

PANCHAYAT_FILE = (
    "data/panchayats.csv"
)

panchayats = pd.read_csv(
    PANCHAYAT_FILE
)


# ============================================================
# 5. LOAD TERRAIN FEATURES
# ============================================================

TERRAIN_FILE = (
    "data/raw/panchayat_terrain_features.csv"
)

terrain = pd.read_csv(
    TERRAIN_FILE
)


# ============================================================
# 6. LOAD IMERG
# ============================================================

IMERG_FILE = (
    "data/raw/imerg_panchayat_rainfall.csv"
)

imerg = pd.read_csv(
    IMERG_FILE,
    parse_dates=["date"]
)

if "imerg_rain_mm" not in imerg.columns:

    raise ValueError(
        "IMERG file must contain "
        "'imerg_rain_mm'."
    )


# ============================================================
# 7. LOAD IMD
# ============================================================
#
# The actual IMD CSV uses:
#
#     rain_mm
#
# We map that to the internal variable imd_rain_mm.
# ============================================================

IMD_FILE = (
    "data/raw/imd_panchayat_rainfall.csv"
)

imd = pd.read_csv(
    IMD_FILE,
    parse_dates=["date"]
)

if "rain_mm" not in imd.columns:

    raise ValueError(
        "IMD file must contain "
        "'rain_mm'."
    )


# ============================================================
# 8. HELPER — GET LATEST SOURCE VALUE
# ============================================================

def get_latest_source_value(
    dataframe,
    panchayat_id,
    value_column
):

    p = dataframe[
        dataframe["panchayat_id"]
        == panchayat_id
    ].copy()

    if p.empty:

        raise ValueError(
            f"No source data found for "
            f"Panchayat {panchayat_id}."
        )

    p = (
        p
        .sort_values("date")
        .reset_index(drop=True)
    )

    latest = p.iloc[-1]

    return (
        float(latest[value_column]),
        pd.Timestamp(
            latest["date"]
        )
    )


# ============================================================
# 9. BUILD FEATURES
# ============================================================

def build_features(
    panchayat_id
):

    # --------------------------------------------------------
    # Historical weather for this Panchayat
    # --------------------------------------------------------

    p = weather[
        weather["panchayat_id"]
        == panchayat_id
    ].copy()

    if len(p) < 8:

        raise ValueError(
            f"Not enough historical weather "
            f"data for {panchayat_id}."
        )

    p = (
        p
        .sort_values("date")
        .reset_index(drop=True)
    )

    latest = p.iloc[-1]


    # --------------------------------------------------------
    # Predictor / forecast dates
    # --------------------------------------------------------

    predictor_date = pd.Timestamp(
        latest["date"]
    )

    forecast_date = (
        predictor_date
        +
        pd.Timedelta(days=1)
    )


    # --------------------------------------------------------
    # Rainfall lags
    # --------------------------------------------------------

    rain_lag_1 = float(
        p["rain_mm"].iloc[-1]
    )

    rain_lag_2 = float(
        p["rain_mm"].iloc[-2]
    )

    rain_lag_3 = float(
        p["rain_mm"].iloc[-3]
    )

    rain_lag_7 = float(
        p["rain_mm"].iloc[-7]
    )


    # --------------------------------------------------------
    # Temperature lags
    # --------------------------------------------------------

    tmax_lag_1 = float(
        p["tmax_c"].iloc[-1]
    )

    tmax_lag_2 = float(
        p["tmax_c"].iloc[-2]
    )

    tmax_lag_7 = float(
        p["tmax_c"].iloc[-7]
    )

    tmin_lag_1 = float(
        p["tmin_c"].iloc[-1]
    )

    tmin_lag_2 = float(
        p["tmin_c"].iloc[-2]
    )


    # --------------------------------------------------------
    # Rainfall accumulation
    # --------------------------------------------------------

    rain_3day_sum = float(
        p["rain_mm"]
        .iloc[-3:]
        .sum()
    )

    rain_7day_sum = float(
        p["rain_mm"]
        .iloc[-7:]
        .sum()
    )


    # --------------------------------------------------------
    # Panchayat information
    # --------------------------------------------------------

    p_info = panchayats[
        panchayats["panchayat_id"]
        == panchayat_id
    ]

    if p_info.empty:

        raise ValueError(
            f"Panchayat {panchayat_id} not found."
        )

    p_info = p_info.iloc[0]


    # --------------------------------------------------------
    # Terrain information
    # --------------------------------------------------------

    terrain_info = terrain[
        terrain["panchayat_id"]
        == panchayat_id
    ]

    if terrain_info.empty:

        raise ValueError(
            f"Terrain information not found "
            f"for {panchayat_id}."
        )

    terrain_info = terrain_info.iloc[0]


    # --------------------------------------------------------
    # IMERG
    # --------------------------------------------------------

    imerg_rain_mm, imerg_date = (
        get_latest_source_value(
            imerg,
            panchayat_id,
            "imerg_rain_mm"
        )
    )


    # --------------------------------------------------------
    # IMD
    # --------------------------------------------------------

    imd_rain_mm, imd_date = (
        get_latest_source_value(
            imd,
            panchayat_id,
            "rain_mm"
        )
    )


    # --------------------------------------------------------
    # Calendar features
    # --------------------------------------------------------

    month = int(
        forecast_date.month
    )

    day_of_year = int(
        forecast_date.dayofyear
    )

    day_of_year_sin = float(
        np.sin(
            2
            *
            np.pi
            *
            day_of_year
            /
            365.25
        )
    )

    day_of_year_cos = float(
        np.cos(
            2
            *
            np.pi
            *
            day_of_year
            /
            365.25
        )
    )


    # --------------------------------------------------------
    # Create all feature values
    # --------------------------------------------------------

    feature_values = {

        "latitude":
            float(
                p_info["latitude"]
            ),

        "longitude":
            float(
                p_info["longitude"]
            ),

        "elevation":
            float(
                p_info["elevation"]
            ),

        "distance_to_river_m":
            float(
                p_info["distance_to_river_m"]
            ),

        "elevation_dem_m":
            float(
                terrain_info["elevation_dem_m"]
            ),

        "slope_deg":
            float(
                terrain_info["slope_deg"]
            ),

        "aspect_sin":
            float(
                terrain_info["aspect_sin"]
            ),

        "aspect_cos":
            float(
                terrain_info["aspect_cos"]
            ),

        "terrain_roughness_m":
            float(
                terrain_info["terrain_roughness_m"]
            ),

        "relative_elevation_m":
            float(
                terrain_info["relative_elevation_m"]
            ),

        "rain_lag_1":
            rain_lag_1,

        "rain_lag_2":
            rain_lag_2,

        "rain_lag_3":
            rain_lag_3,

        "rain_lag_7":
            rain_lag_7,

        "rain_3day_sum":
            rain_3day_sum,

        "rain_7day_sum":
            rain_7day_sum,

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

        "imerg_rain_mm":
            imerg_rain_mm,

        "imd_rain_mm":
            imd_rain_mm,

        "month":
            month,

        "day_of_year":
            day_of_year,

        "day_of_year_sin":
            day_of_year_sin,

        "day_of_year_cos":
            day_of_year_cos
    }


    # --------------------------------------------------------
    # V1 feature matrix
    # --------------------------------------------------------

    X_v1 = pd.DataFrame(
        [[
            feature_values[feature]
            for feature in V1_FEATURES
        ]],
        columns=V1_FEATURES
    )


    # --------------------------------------------------------
    # V1.3 feature matrix
    # --------------------------------------------------------

    X_v13 = pd.DataFrame(
        [[
            feature_values[feature]
            for feature in V13_FEATURES
        ]],
        columns=V13_FEATURES
    )


    return (
        X_v1,
        X_v13,
        forecast_date,
        imerg_date,
        imd_date
    )


# ============================================================
# 10. FORECAST FUNCTION
# ============================================================

def forecast_panchayat(
    panchayat_id
):

    (
        X_v1,
        X_v13,
        forecast_date,
        imerg_date,
        imd_date
    ) = build_features(
        panchayat_id
    )


    # ========================================================
    # RAIN PROBABILITY — V1
    # ========================================================

    rain_probability = float(
        rain_clf.predict_proba(
            X_v1
        )[0, 1]
    )


    # ========================================================
    # RAINFALL AMOUNT — V1.3
    # ========================================================

    calibration_X = pd.DataFrame(
        [[
            X_v13[
                "imerg_rain_mm"
            ].iloc[0],

            X_v13[
                "imd_rain_mm"
            ].iloc[0],

            # Latest Open-Meteo rainfall
            # available at predictor time T.
            X_v13[
                "rain_lag_1"
            ].iloc[0]
        ]],
        columns=CALIBRATION_FEATURES
    )


    # --------------------------------------------------------
    # Linear calibrated rainfall
    # --------------------------------------------------------

    calibrated_rain = float(
        rain_calibration.predict(
            calibration_X
        )[0]
    )

    calibrated_rain = max(
        0.0,
        calibrated_rain
    )


    # --------------------------------------------------------
    # XGBoost residual
    # --------------------------------------------------------

    predicted_residual = float(
        rain_residual.predict(
            X_v13
        )[0]
    )


    # --------------------------------------------------------
    # Conservative V1.3 correction
    # --------------------------------------------------------

    final_rain = (
        calibrated_rain
        +
        RESIDUAL_ALPHA
        *
        predicted_residual
    )

    final_rain = max(
        0.0,
        float(final_rain)
    )


    # --------------------------------------------------------
    # Rain probability gate
    #
    # The validated V1/V1.2 event threshold was 0.30.
    # --------------------------------------------------------

    if rain_probability < 0.30:

        final_rain = 0.0


    # ========================================================
    # MAXIMUM TEMPERATURE — V1
    # ========================================================

    final_tmax = float(
        tmax_reg.predict(
            X_v1
        )[0]
    )


    # ========================================================
    # RETURN FORECAST
    # ========================================================

    return {

        "date":
            forecast_date
            .date()
            .isoformat(),

        "rain_mm":
            round(
                final_rain,
                1
            ),

        "rain_probability":
            round(
                rain_probability,
                2
            ),

        "tmax_c":
            round(
                final_tmax,
                1
            ),

        "model_version":
            "V1.3 rainfall + V1 probability/Tmax",

        "rainfall_model":
            "V1.3",

        "residual_alpha":
            RESIDUAL_ALPHA,

        "imerg_source_date":
            imerg_date
            .date()
            .isoformat(),

        "imd_source_date":
            imd_date
            .date()
            .isoformat()
    }


# ============================================================
# 11. LOCAL TEST
# ============================================================

if __name__ == "__main__":

    TEST_PANCHAYAT = "A2"

    print(
        "========================================"
    )

    print(
        "TERRAMIND V1.3 FORECAST TEST"
    )

    print(
        "========================================"
    )

    try:

        result = forecast_panchayat(
            TEST_PANCHAYAT
        )

        print(
            f"Panchayat: AMDANGA "
            f"({TEST_PANCHAYAT})"
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

        print(
            "Model:",
            result["model_version"]
        )

        print(
            "Rainfall model:",
            result["rainfall_model"]
        )

        print(
            "Residual alpha:",
            result["residual_alpha"]
        )

        print(
            "IMERG source date:",
            result["imerg_source_date"]
        )

        print(
            "IMD source date:",
            result["imd_source_date"]
        )

    except Exception as e:

        print(
            "FORECAST ERROR:"
        )

        print(
            type(e).__name__ + ":",
            str(e)
        )

        raise