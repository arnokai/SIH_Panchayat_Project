from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Optional

import pandas as pd


# ============================================================
# TERRAMIND — ADVISORY CONTEXT
# ============================================================


@dataclass
class AdvisoryContext:
    """
    Context available to the agricultural advisory engine.

    None means the value is unknown/unavailable.
    """

    # Forecast weather
    rain_mm: float
    tmax_c: float

    # Humidity context
    humidity: Optional[float] = None
    humidity_days: Optional[int] = None

    # Dry-spell context
    dry_days: Optional[int] = None

    # Farm context
    soil_type: Optional[str] = None
    crop: Optional[str] = None
    crop_stage: Optional[str] = None

    # Harvest timing
    harvest_window: Optional[bool] = None


# ============================================================
# VALIDATION
# ============================================================

def validate_context(
    context: AdvisoryContext
) -> None:
    """
    Basic sanity checks.
    These are not agricultural validation rules.
    """

    if context.rain_mm < 0:
        raise ValueError(
            "rain_mm cannot be negative."
        )

    if context.humidity is not None:
        if not 0 <= context.humidity <= 100:
            raise ValueError(
                "humidity must be between 0 and 100."
            )

    if context.humidity_days is not None:
        if context.humidity_days < 0:
            raise ValueError(
                "humidity_days cannot be negative."
            )

    if context.dry_days is not None:
        if context.dry_days < 0:
            raise ValueError(
                "dry_days cannot be negative."
            )


# ============================================================
# LOAD PANCHAYAT SOIL
# ============================================================

def get_soil_type(
    panchayat_id
) -> Optional[str]:
    """
    Return the measured soil-context classification
    for a Panchayat.

    The source file is derived from SoilGrids measurements.
    """

    root_dir = Path(__file__).resolve().parent.parent
    soil_parquet = root_dir / "data_pipeline" / "raw" / "panchayat_soil_context.parquet"
    if not soil_parquet.exists():
        soil_parquet = root_dir / "data" / "raw" / "panchayat_soil_context.parquet"

    if soil_parquet.exists():
        soil_df = pd.read_parquet(soil_parquet)
    else:
        soil_csv = root_dir / "data_pipeline" / "csv" / "raw" / "panchayat_soil_context.csv"
        if not soil_csv.exists():
            soil_csv = root_dir / "data_pipeline" / "raw" / "panchayat_soil_context.csv"
        if not soil_csv.exists():
            raise FileNotFoundError(
                f"Soil context file not found: {soil_parquet}"
            )
        soil_df = pd.read_csv(soil_csv)

    required_columns = [
        "panchayat_id",
        "soil_type",
    ]

    missing = [
        column
        for column in required_columns
        if column not in soil_df.columns
    ]

    if missing:
        raise ValueError(
            "Missing soil-context columns: "
            + ", ".join(missing)
        )

    # Soil file currently uses GPCODE-style numeric IDs.
    panchayat_id = str(
        panchayat_id
    )

    matches = soil_df[
        soil_df["panchayat_id"]
        .astype(str)
        == panchayat_id
    ]

    if matches.empty:
        raise ValueError(
            f"Soil context not found for "
            f"Panchayat {panchayat_id}."
        )

    soil_type = matches.iloc[0][
        "soil_type"
    ]

    if pd.isna(soil_type):
        return None

    return str(
        soil_type
    ).strip().lower()


# ============================================================
# BUILD CONTEXT FROM CROP CALENDAR + SOIL
# ============================================================

def build_context_from_calendar(
    panchayat_id,
    target_date,
    rain_mm,
    tmax_c,
    crop="paddy",
    humidity=None,
    humidity_days=None,
    dry_days=None,
):
    """
    Build AdvisoryContext using:

    1. Crop calendar
       -> crop
       -> crop stage
       -> harvest window

    2. Panchayat soil context
       -> soil type

    Weather/history values are supplied by the caller.
    """

    from data.crop_calendar import (
        get_crop_context
    )

    # --------------------------------------------------------
    # Normalize date
    # --------------------------------------------------------

    if isinstance(
        target_date,
        str
    ):
        target_date = date.fromisoformat(
            target_date
        )


    # --------------------------------------------------------
    # Crop calendar lookup
    # --------------------------------------------------------

    calendar_context = (
        get_crop_context(
            target_date,
            crop
        )
    )


    # --------------------------------------------------------
    # Panchayat soil lookup
    # --------------------------------------------------------

    soil_type = get_soil_type(
        panchayat_id
    )


    # --------------------------------------------------------
    # Build context
    # --------------------------------------------------------

    context = AdvisoryContext(

        rain_mm=float(
            rain_mm
        ),

        tmax_c=float(
            tmax_c
        ),

        humidity=(
            float(humidity)
            if humidity is not None
            else None
        ),

        humidity_days=(
            int(humidity_days)
            if humidity_days is not None
            else None
        ),

        dry_days=(
            int(dry_days)
            if dry_days is not None
            else None
        ),

        soil_type=soil_type,

        crop=calendar_context[
            "crop"
        ],

        crop_stage=calendar_context[
            "crop_stage"
        ],

        harvest_window=calendar_context[
            "harvest_window"
        ],

    )


    # --------------------------------------------------------
    # Validate
    # --------------------------------------------------------

    validate_context(
        context
    )


    return context


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print(
        "========================================"
    )

    print(
        "ADVISORY CONTEXT TEST"
    )

    print(
        "========================================"
    )


    for panchayat_id in [
        "107777",
        "107778",
        "107782",
    ]:

        context = (
            build_context_from_calendar(
                panchayat_id=panchayat_id,
                target_date="2026-09-20",
                rain_mm=8.7,
                tmax_c=29.1,
                crop="paddy",
            )
        )

        print(
            f"\nPanchayat: {panchayat_id}"
        )

        print(
            context
        )