import sys
from pathlib import Path
import pandas as pd

BACKEND_DIR = Path(__file__).resolve().parent
ROOT_DIR = BACKEND_DIR.parent
for p in [BACKEND_DIR, ROOT_DIR]:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))


# ============================================================
# TERRAMIND V2 — FIVE-DAY FORECAST DELIVERY ENGINE
# ============================================================
#
# Current role:
#
#   COARSE 5-DAY FORECAST
#          ↓
#   PANCHAYAT DELIVERY CONTEXT
#          ↓
#   ADVISORY RULE ENGINE
#          ↓
#   BENGALI / ENGLISH ADVISORY
#
# IMPORTANT:
#
# The current V2 rainfall delivery still uses the coarse
# five-day forecast as the safe fallback.
#
# The experimental Panchayat rainfall downscaling model has
# NOT been promoted to operational five-day forecasting.
#
# Therefore:
#
#     degraded = True
#
# remains intentional.
#
# ============================================================


# ============================================================
# ADVISORY INTEGRATION
# ============================================================

from advisory_engine import (
    build_advisory_response
)

from forecast_advisory_context import (
    build_forecast_context,
    calculate_forecast_dry_days,
)


from pathlib import Path
import numpy as np

# ============================================================
# FILES & ML MODEL ARTIFACTS
# ============================================================

ROOT_DIR = Path(__file__).resolve().parent.parent
COARSE_FORECAST_FILE = ROOT_DIR / "data_pipeline" / "raw" / "coarse_block_forecast.parquet"
if not COARSE_FORECAST_FILE.exists():
    COARSE_FORECAST_FILE = ROOT_DIR / "data_pipeline" / "raw" / "coarse_block_forecast.csv"
if not COARSE_FORECAST_FILE.exists():
    COARSE_FORECAST_FILE = ROOT_DIR / "data" / "raw" / "coarse_block_forecast.parquet"
if not COARSE_FORECAST_FILE.exists():
    COARSE_FORECAST_FILE = ROOT_DIR / "data" / "raw" / "coarse_block_forecast.csv"

MODEL_PATH = ROOT_DIR / "ml" / "models" / "statewide_hurdle_v2.pkl"
STATIC_FEATURES_PATH = ROOT_DIR / "data_pipeline" / "features" / "statewide_static_features.parquet"

PILOT_TO_STATEWIDE = {
    "A1": "WB_107777",
    "A2": "WB_107778",
    "A3": "WB_107779",
    "A4": "WB_107780",
    "A5": "WB_107781",
    "A6": "WB_107782",
    "A7": "WB_107783",
    "A8": "WB_107784",
}

_MODEL_ARTIFACT = None
_STATIC_FEATURES = None


def _get_model_artifact():
    global _MODEL_ARTIFACT
    if _MODEL_ARTIFACT is None and MODEL_PATH.exists():
        try:
            import joblib
            _MODEL_ARTIFACT = joblib.load(MODEL_PATH)
        except Exception:
            _MODEL_ARTIFACT = False
    return _MODEL_ARTIFACT if isinstance(_MODEL_ARTIFACT, dict) else None


def _get_static_features():
    global _STATIC_FEATURES
    if _STATIC_FEATURES is None and STATIC_FEATURES_PATH.exists():
        try:
            df = pd.read_parquet(STATIC_FEATURES_PATH)
            _STATIC_FEATURES = df.set_index("panchayat_id")
        except Exception:
            _STATIC_FEATURES = False
    return _STATIC_FEATURES if isinstance(_STATIC_FEATURES, pd.DataFrame) else None


# ============================================================
# PANCHAYATS
# ============================================================

PANCHAYAT_DB = {

    "A1": {
        "name": "ADHATA"
    },

    "A2": {
        "name": "AMDANGA"
    },

    "A3": {
        "name": "BERABERIA"
    },

    "A4": {
        "name": "BODAI"
    },

    "A5": {
        "name": "CHANDIGARH"
    },

    "A6": {
        "name": "MARICHA"
    },

    "A7": {
        "name": "SADHANPUR"
    },

    "A8": {
        "name": "TARABERIA"
    },

    # LGD Code Aliases
    "WB_107777": {
        "name": "ADHATA",
        "alias": "A1"
    },

    "WB_107778": {
        "name": "AMDANGA",
        "alias": "A2"
    },

    "WB_107779": {
        "name": "BERABERIA",
        "alias": "A3"
    },

    "WB_107780": {
        "name": "BODAI",
        "alias": "A4"
    },

    "WB_107781": {
        "name": "CHANDIGARH",
        "alias": "A5"
    },

    "WB_107782": {
        "name": "MARICHA",
        "alias": "A6"
    },

    "WB_107783": {
        "name": "SADHANPUR",
        "alias": "A7"
    },

    "WB_107784": {
        "name": "TARABERIA",
        "alias": "A8"
    },

}


# ============================================================
# LOAD COARSE FORECAST
# ============================================================

def load_coarse_forecast():
    if COARSE_FORECAST_FILE.suffix == ".parquet":
        df = pd.read_parquet(COARSE_FORECAST_FILE)
        if not pd.api.types.is_datetime64_any_dtype(df["date"]):
            df["date"] = pd.to_datetime(df["date"])
    else:
        df = pd.read_csv(
            COARSE_FORECAST_FILE,
            parse_dates=["date"]
        )


    required_columns = [

        "date",

        "coarse_rain_mm",

        "coarse_tmax_c",

        "coarse_tmin_c",

        "coarse_rain_probability",

        "source",

        "coarse_latitude",

        "coarse_longitude",

    ]


    missing = [

        column

        for column in required_columns

        if column not in df.columns

    ]


    if missing:

        raise ValueError(
            "Missing coarse forecast columns: "
            +
            ", ".join(missing)
        )


    df = (
        df
        .sort_values("date")
        .reset_index(drop=True)
    )


    if df.empty:

        raise ValueError(
            "Coarse forecast is empty."
        )


    # --------------------------------------------------------
    # Basic forecast validation
    # --------------------------------------------------------

    if df["date"].duplicated().any():

        raise ValueError(
            "Duplicate forecast dates found."
        )


    if (
        df["coarse_rain_mm"] < 0
    ).any():

        raise ValueError(
            "Negative coarse rainfall found."
        )


    if (
        (
            df[
                "coarse_rain_probability"
            ] < 0
        )
        |
        (
            df[
                "coarse_rain_probability"
            ] > 100
        )
    ).any():

        raise ValueError(
            "Coarse rainfall probability "
            "must be between 0 and 100."
        )


    return df


# ============================================================
# FORECAST FUNCTION
# ============================================================

def forecast_panchayat_v2(
    panchayat_id,
    days=5,
    crop="paddy"
):

    panchayat_id = str(panchayat_id).strip().upper()

    if panchayat_id not in PANCHAYAT_DB:

        raise ValueError(
            "Panchayat not found."
        )

    canonical_id = PANCHAYAT_DB[panchayat_id].get("alias", panchayat_id)


    # --------------------------------------------------------
    # Days validation
    # --------------------------------------------------------

    if days < 1 or days > 5:

        raise ValueError(
            "days must be between 1 and 5."
        )


    # --------------------------------------------------------
    # Load coarse forecast
    # --------------------------------------------------------

    coarse = load_coarse_forecast()


    coarse = (
        coarse
        .head(days)
        .copy()
    )


    if len(coarse) < days:

        raise ValueError(
            f"Only {len(coarse)} forecast "
            f"days are available."
        )


    # --------------------------------------------------------
    # Calculate forecast-aware dry streak
    # --------------------------------------------------------
    #
    # This combines the latest historical dry streak with
    # future forecast rainfall.
    #
    # Example:
    #
    # latest observed dry_days = 5
    #
    # forecast:
    # 0 mm → 6
    # 0 mm → 7
    # 5 mm → 0
    #
    # --------------------------------------------------------

    forecast_dry_days = (
        calculate_forecast_dry_days(
            panchayat_id=canonical_id,
            forecast_rows=coarse
        )
    )


    # --------------------------------------------------------
    # Build daily outputs
    # --------------------------------------------------------

    model_artifact = _get_model_artifact()
    static_features = _get_static_features()
    statewide_id = PILOT_TO_STATEWIDE.get(canonical_id, canonical_id)
    gp_feat = (
        static_features.loc[statewide_id]
        if (static_features is not None and statewide_id in static_features.index)
        else None
    )
    is_downscaled = model_artifact is not None and gp_feat is not None

    forecast = []


    for _, row in coarse.iterrows():

        forecast_date = (
            pd.Timestamp(
                row["date"]
            ).date()
        )


        # ----------------------------------------------------
        # Forecast values
        # ----------------------------------------------------

        rain = float(
            row[
                "coarse_rain_mm"
            ]
        )


        tmax = float(
            row[
                "coarse_tmax_c"
            ]
        )


        tmin = float(
            row[
                "coarse_tmin_c"
            ]
        )


        rain_probability = (
            float(
                row[
                    "coarse_rain_probability"
                ]
            )
            / 100.0
        )


        if is_downscaled:
            day_of_year = forecast_date.timetuple().tm_yday
            f_row = pd.DataFrame([{
                "coarse_rain_mm": rain,
                "coarse_tmax_c": tmax,
                "coarse_tmin_c": tmin,
                "elevation_dem_m": float(gp_feat.get("elevation_dem_m", 15.0)),
                "slope_deg": float(gp_feat.get("slope_deg", 0.5)),
                "aspect_sin": float(gp_feat.get("aspect_sin", 0.0)),
                "aspect_cos": float(gp_feat.get("aspect_cos", 1.0)),
                "terrain_roughness_m": float(gp_feat.get("terrain_roughness_m", 1.0)),
                "relative_elevation_m": float(gp_feat.get("relative_elevation_m", 0.0)),
                "distance_to_river_m": float(gp_feat.get("distance_to_river_m", 5000.0)),
                "sand_pct": float(gp_feat.get("sand_pct", 45.0)),
                "clay_pct": float(gp_feat.get("clay_pct", 25.0)),
                "silt_pct": float(gp_feat.get("silt_pct", 30.0)),
                "month": forecast_date.month,
                "day_of_year_sin": np.sin(2 * np.pi * day_of_year / 365.25),
                "day_of_year_cos": np.cos(2 * np.pi * day_of_year / 365.25),
            }])

            clf = model_artifact["classifier"]
            prob = float(clf.predict_proba(f_row)[0, 1])

            if prob >= 0.35:
                p50_val = max(0.0, float(model_artifact["regressor_p50"].predict(f_row)[0]))
                p10_val = max(0.0, float(model_artifact["regressor_p10"].predict(f_row)[0]))
                p90_val = max(p50_val, float(model_artifact["regressor_p90"].predict(f_row)[0]))
            else:
                p10_val, p50_val, p90_val = 0.0, 0.0, 0.0

            rain_probability = prob
            rain_dict = {
                "p10": round(p10_val, 1),
                "p50": round(p50_val, 1),
                "p90": round(p90_val, 1),
            }
        else:
            rain_dict = {
                "p10": round(max(0.0, rain * 0.7), 1),
                "p50": round(rain, 1),
                "p90": round(rain * 1.3, 1),
            }


        # ----------------------------------------------------
        # Forecast advisory context
        # ----------------------------------------------------

        context = build_forecast_context(

            panchayat_id=canonical_id,

            forecast_row=row,

            crop=crop,

            forecast_dry_days=
                forecast_dry_days[
                    forecast_date
                ],

        )
        context.rain_mm = rain_dict["p50"]


        # ----------------------------------------------------
        # Advisory engine
        # ----------------------------------------------------

        advisory = (
            build_advisory_response(
                context
            )
        )


        # ----------------------------------------------------
        # Daily forecast response
        # ----------------------------------------------------

        forecast.append({

            "date":
                forecast_date.isoformat(),

            "rain_mm":
                rain_dict,

            "rain_probability":
                round(
                    rain_probability,
                    2
                ),

            "tmax_c": {
                "p50":
                    round(
                        tmax,
                        1
                    ),
            },

            "tmin_c":
                round(
                    tmin,
                    1
                ),

            "advisory":
                advisory,

        })


    # ========================================================
    # SOURCE
    # ========================================================

    source = str(
        coarse[
            "source"
        ].iloc[0]
    )


    # ========================================================
    # COARSE COORDINATE
    # ========================================================

    coarse_coordinate = {

        "latitude":
            float(
                coarse[
                    "coarse_latitude"
                ].iloc[0]
            ),

        "longitude":
            float(
                coarse[
                    "coarse_longitude"
                ].iloc[0]
            ),

    }


    # ========================================================
    # ADVISORY SUMMARY
    # ========================================================
    #
    # Include only days that actually have an advisory rule.
    # "none" is not included in the summary.
    #
    # ========================================================

    advisories = []


    for day in forecast:

        advisory = day[
            "advisory"
        ]


        if (
            advisory["rule_id"]
            !=
            "none"
        ):

            advisories.append({

                "date":
                    day["date"],

                "rule_id":
                    advisory[
                        "rule_id"
                    ],

                "priority":
                    advisory[
                        "priority"
                    ],

                "type":
                    advisory[
                        "type"
                    ],

                "text_en":
                    advisory[
                        "text_en"
                    ],

                "text_bn":
                    advisory[
                        "text_bn"
                    ],

            })


    # ========================================================
    # FINAL RESPONSE
    # ========================================================

    return {

        "panchayat_id":
            panchayat_id,

        "panchayat_name":
            PANCHAYAT_DB[
                panchayat_id
            ]["name"],

        "crop":
            crop,

        "model_version":
            "V2.0 Statewide Hurdle (Quantile HGB)" if is_downscaled else "V2 delivery scaffold",

        "rainfall_model":
            "Two-Stage Hurdle Downscaling (P10/P50/P90)" if is_downscaled else "Coarse forecast fallback",

        "source":
            source,

        "coarse_coordinate":
            coarse_coordinate,

        "forecast":
            forecast,

        "advisories":
            advisories,

        "degraded":
            False if is_downscaled else True,

        "degraded_reason":
            None if is_downscaled else (
                "Operational five-day "
                "Panchayat-level ML downscaling "
                "is not yet validated. "
                "Coarse block forecast is used "
                "as the safe rainfall fallback."
            ),

    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print(
        "========================================"
    )

    print(
        "TERRAMIND V2 FIVE-DAY TEST"
    )

    print(
        "========================================"
    )


    result = forecast_panchayat_v2(
        "A2",
        days=5,
        crop="paddy"
    )


    print(
        "\nPanchayat:",
        result[
            "panchayat_name"
        ]
    )

    print(
        "Crop:",
        result[
            "crop"
        ]
    )

    print(
        "Model:",
        result[
            "model_version"
        ]
    )

    print(
        "Rainfall model:",
        result[
            "rainfall_model"
        ]
    )

    print(
        "Degraded:",
        result[
            "degraded"
        ]
    )


    print(
        "\nFive-day forecast:"
    )


    for day in result[
        "forecast"
    ]:

        print(
            day
        )


    print(
        "\nAdvisory summary:"
    )


    for advisory in result[
        "advisories"
    ]:

        print(
            advisory
        )


    print(
        "\n========================================"
    )

    print(
        "V2 FIVE-DAY TEST COMPLETE"
    )

    print(
        "========================================"
    )