import pandas as pd

from advisory_engine import build_advisory_response
from forecast_advisory_context import (
    build_forecast_context,
    calculate_forecast_dry_days,
)


# ============================================================
# TERRAMIND — FORECAST → ADVISORY INTEGRATION TEST
# ============================================================

FORECAST_FILE = (
    "data/raw/coarse_block_forecast.csv"
)

PANCHAYAT_ID = "A2"
CROP = "paddy"


# ============================================================
# LOAD FORECAST
# ============================================================

forecast = pd.read_csv(
    FORECAST_FILE,
    parse_dates=["date"],
)


if forecast.empty:
    raise ValueError(
        "No forecast rows found."
    )


# ============================================================
# CALCULATE FORECAST DRY STREAK
# ============================================================

forecast_dry_days = (
    calculate_forecast_dry_days(
        panchayat_id=PANCHAYAT_ID,
        forecast_rows=forecast,
    )
)


# ============================================================
# RUN ADVISORY ENGINE
# ============================================================

print(
    "========================================"
)

print(
    "TERRAMIND FORECAST → ADVISORY TEST"
)

print(
    "========================================"
)

print(
    "Panchayat:",
    PANCHAYAT_ID
)

print(
    "Crop:",
    CROP
)

print()


for _, row in forecast.iterrows():

    forecast_date = (
        pd.Timestamp(
            row["date"]
        ).date()
    )


    context = build_forecast_context(
        panchayat_id=PANCHAYAT_ID,
        forecast_row=row,
        crop=CROP,
        forecast_dry_days=
            forecast_dry_days[
                forecast_date
            ],
    )


    advisory = build_advisory_response(
        context
    )


    print(
        "----------------------------------------"
    )

    print(
        "Date:",
        forecast_date
    )

    print(
        "Rain:",
        context.rain_mm,
        "mm"
    )

    print(
        "Tmax:",
        context.tmax_c,
        "°C"
    )

    print(
        "Crop:",
        context.crop
    )

    print(
        "Stage:",
        context.crop_stage
    )

    print(
        "Soil:",
        context.soil_type
    )

    print(
        "Dry days:",
        context.dry_days
    )

    print(
        "Rule:",
        advisory["rule_id"]
    )

    print(
        "Priority:",
        advisory["priority"]
    )

    print(
        "English:",
        advisory["text_en"]
    )

    print(
        "Bengali:",
        advisory["text_bn"]
    )


print()

print(
    "========================================"
)

print(
    "FORECAST → ADVISORY TEST COMPLETE"
)

print(
    "========================================"
)