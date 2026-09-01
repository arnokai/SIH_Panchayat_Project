import pandas as pd


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


# ============================================================
# FILES
# ============================================================

COARSE_FORECAST_FILE = (
    "data/raw/coarse_block_forecast.csv"
)


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
    }

}


# ============================================================
# LOAD COARSE FORECAST
# ============================================================

def load_coarse_forecast():

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

    # --------------------------------------------------------
    # Panchayat validation
    # --------------------------------------------------------

    if panchayat_id not in PANCHAYAT_DB:

        raise ValueError(
            "Panchayat not found."
        )


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
            panchayat_id=panchayat_id,
            forecast_rows=coarse
        )
    )


    # --------------------------------------------------------
    # Build daily outputs
    # --------------------------------------------------------

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


        # ----------------------------------------------------
        # Forecast advisory context
        # ----------------------------------------------------

        context = build_forecast_context(

            panchayat_id=panchayat_id,

            forecast_row=row,

            crop=crop,

            forecast_dry_days=
                forecast_dry_days[
                    forecast_date
                ],

        )


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
                round(
                    rain,
                    1
                ),

            "rain_probability":
                round(
                    rain_probability,
                    2
                ),

            "tmax_c":
                round(
                    tmax,
                    1
                ),

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
            "V2 delivery scaffold",

        "rainfall_model":
            "Coarse forecast fallback",

        "source":
            source,

        "coarse_coordinate":
            coarse_coordinate,

        "forecast":
            forecast,

        "advisories":
            advisories,

        "degraded":
            True,

        "degraded_reason":
            (
                "Operational five-day "
                "Panchayat-level ML downscaling "
                "is not yet validated. "
                "Coarse block forecast is used "
                "as the safe rainfall fallback."
            )

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