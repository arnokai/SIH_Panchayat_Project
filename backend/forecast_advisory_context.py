from pathlib import Path

import pandas as pd

from advisory_context import AdvisoryContext
try:
    from data_pipeline.metadata.crop_calendar import get_crop_context
except ImportError:
    from data.crop_calendar import get_crop_context


# ============================================================
# TERRAMIND — FORECAST ADVISORY CONTEXT
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = BASE_DIR / "data_pipeline" / "raw"
if not DATA_RAW_DIR.exists():
    DATA_RAW_DIR = BASE_DIR / "data" / "raw"

COARSE_FORECAST_FILE = (
    DATA_RAW_DIR
    / "coarse_block_forecast.parquet"
)

HISTORY_FILE = (
    DATA_RAW_DIR
    / "advisory_context_history.parquet"
)

SOIL_FILE = (
    DATA_RAW_DIR
    / "panchayat_soil_context.parquet"
)

COORDINATE_FILE = (
    DATA_RAW_DIR
    / "panchayat_coordinates.parquet"
)


def _read_table(file_path: Path, parse_dates=None) -> pd.DataFrame:
    """Load Parquet as primary format, fall back to CSV if needed."""
    parquet_path = file_path.with_suffix(".parquet")
    if parquet_path.exists():
        df = pd.read_parquet(parquet_path)
        if parse_dates:
            for col in parse_dates:
                if col in df.columns and not pd.api.types.is_datetime64_any_dtype(df[col]):
                    df[col] = pd.to_datetime(df[col])
        return df
    csv_candidates = [
        file_path.with_suffix(".csv"),
        BASE_DIR / "data_pipeline" / "csv" / "raw" / file_path.with_suffix(".csv").name,
    ]
    for csv_path in csv_candidates:
        if csv_path.exists():
            return pd.read_csv(csv_path, parse_dates=parse_dates)
    raise FileNotFoundError(f"File not found as parquet or csv: {file_path}")


# ============================================================
# PANCHAYAT ID MAPPING
# ============================================================

def get_panchayat_mappings():
    """
    Build the application's canonical Panchayat IDs.

    Application IDs:
        A1 ... A8

    Source soil IDs:
        GPCODE 107777 ... 107784
    """

    coordinates = _read_table(
        COORDINATE_FILE
    )

    required = [
        "GPCODE",
        "GPNAME",
    ]

    missing = [
        column
        for column in required
        if column not in coordinates.columns
    ]

    if missing:
        raise ValueError(
            "Missing coordinate columns: "
            + ", ".join(missing)
        )

    coordinates = coordinates.reset_index(
        drop=True
    )

    coordinates["app_id"] = [
        f"A{i + 1}"
        for i in range(len(coordinates))
    ]

    return coordinates


# ============================================================
# SOIL TYPE
# ============================================================

def get_panchayat_soil_type(
    panchayat_id
):
    """
    Return SoilGrids-derived soil type for A1 ... A8.
    """

    mappings = get_panchayat_mappings()

    soil = _read_table(
        SOIL_FILE
    )

    required = [
        "panchayat_id",
        "soil_type",
    ]

    missing = [
        column
        for column in required
        if column not in soil.columns
    ]

    if missing:
        raise ValueError(
            "Missing soil columns: "
            + ", ".join(missing)
        )

    mapping = mappings[
        mappings["app_id"].astype(str)
        ==
        str(panchayat_id)
    ]

    if mapping.empty:
        static_feat_file = BASE_DIR / "data_pipeline" / "features" / "statewide_static_features.parquet"
        if static_feat_file.exists():
            sf = pd.read_parquet(static_feat_file)
            clean_id = str(panchayat_id).strip().upper()
            match = sf[(sf["panchayat_id"] == clean_id) | (sf["gp_code"].astype(str) == clean_id.replace("WB_", ""))]
            if not match.empty:
                st = match.iloc[0].get("soil_type", "non_sandy")
                return str(st).strip().lower()
        return "non_sandy"

    gpcode = str(
        mapping.iloc[0]["GPCODE"]
    )

    matches = soil[
        soil["panchayat_id"]
        .astype(str)
        ==
        gpcode
    ]

    if matches.empty:
        raise ValueError(
            f"No soil context found for "
            f"{panchayat_id} / GPCODE {gpcode}."
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
# LATEST OBSERVED DRY STREAK
# ============================================================

def get_latest_dry_days(
    panchayat_id
):
    """
    Return the latest observed consecutive dry-day streak.

    This is historical context only.
    """

    history = _read_table(
        HISTORY_FILE,
        parse_dates=["date"]
    )

    p = history[
        history["panchayat_id"]
        .astype(str)
        ==
        str(panchayat_id)
    ].copy()

    if p.empty:
        return 0

    p = p.sort_values(
        "date"
    )

    latest = p.iloc[-1]

    return int(
        latest["dry_days"]
    )


# ============================================================
# FORECAST DRY-DAY CALCULATION
# ============================================================

def calculate_forecast_dry_days(
    panchayat_id,
    forecast_rows
):
    """
    Calculate the dry-day streak across the boundary between
    the latest observed day and the future forecast.

    A dry day is defined as exactly:

        rain_mm == 0

    Example:

        Latest observed streak = 5

        Day 1: 0 mm -> 6
        Day 2: 0 mm -> 7
        Day 3: 4 mm -> 0
        Day 4: 0 mm -> 1
    """

    dry_streak = get_latest_dry_days(
        panchayat_id
    )

    result = {}

    for _, row in forecast_rows.iterrows():

        forecast_date = (
            pd.Timestamp(
                row["date"]
            ).date()
        )

        rain_mm = float(
            row["coarse_rain_mm"]
        )

        if rain_mm == 0:
            dry_streak += 1
        else:
            dry_streak = 0

        result[
            forecast_date
        ] = dry_streak

    return result


# ============================================================
# BUILD FORECAST CONTEXT
# ============================================================

def build_forecast_context(
    panchayat_id,
    forecast_row,
    crop="paddy",
    forecast_dry_days=0
):
    """
    Build AdvisoryContext for one forecast day.

    Future forecast values:
        rain_mm
        tmax_c

    Permanent Panchayat context:
        soil_type

    Crop calendar:
        crop
        crop_stage
        harvest_window

    Forecast humidity is intentionally unavailable because
    the current coarse forecast file does not contain humidity.
    """

    target_date = (
        pd.Timestamp(
            forecast_row["date"]
        ).date()
    )

    # --------------------------------------------------------
    # Crop calendar
    # --------------------------------------------------------

    crop_context = get_crop_context(
        target_date,
        crop
    )


    # --------------------------------------------------------
    # Soil
    # --------------------------------------------------------

    soil_type = get_panchayat_soil_type(
        panchayat_id
    )


    # --------------------------------------------------------
    # Context
    # --------------------------------------------------------

    context = AdvisoryContext(

        rain_mm=float(
            forecast_row[
                "coarse_rain_mm"
            ]
        ),

        tmax_c=float(
            forecast_row[
                "coarse_tmax_c"
            ]
        ),

        # No actual forecast humidity currently available.
        humidity=None,

        humidity_days=None,

        dry_days=int(
            forecast_dry_days
        ),

        soil_type=soil_type,

        crop=crop_context[
            "crop"
        ],

        crop_stage=crop_context[
            "crop_stage"
        ],

        harvest_window=crop_context[
            "harvest_window"
        ],
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
        "FORECAST ADVISORY CONTEXT TEST"
    )

    print(
        "========================================"
    )


    # --------------------------------------------------------
    # Load current coarse forecast
    # --------------------------------------------------------

    forecast = _read_table(
        COARSE_FORECAST_FILE,
        parse_dates=["date"]
    )


    print(
        "Forecast rows:",
        len(forecast)
    )

    print(
        "Testing Panchayat: A2"
    )

    print()


    # --------------------------------------------------------
    # Calculate future dry streaks
    # --------------------------------------------------------

    forecast_dry_days = (
        calculate_forecast_dry_days(
            panchayat_id="A2",
            forecast_rows=forecast
        )
    )


    # --------------------------------------------------------
    # Build each forecast context
    # --------------------------------------------------------

    for _, row in forecast.iterrows():

        forecast_date = (
            pd.Timestamp(
                row["date"]
            ).date()
        )

        context = build_forecast_context(

            panchayat_id="A2",

            forecast_row=row,

            crop="paddy",

            forecast_dry_days=
                forecast_dry_days[
                    forecast_date
                ],
        )

        print(
            forecast_date,
            "→",
            context
        )


    print()

    print(
        "========================================"
    )

    print(
        "FORECAST CONTEXT TEST COMPLETE"
    )

    print(
        "========================================"
    )