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
# PANCHAYAT ID MAPPING (EQUAL STATEWIDE SUPPORT)
# ============================================================

LEGACY_PILOT_MAP = {
    "A1": "WB_107777",
    "A2": "WB_107778",
    "A3": "WB_107779",
    "A4": "WB_107780",
    "A5": "WB_107781",
    "A6": "WB_107782",
    "A7": "WB_107783",
    "A8": "WB_107784",
}

_STATIC_FEATURES_CACHE = None

def _get_static_features_df():
    global _STATIC_FEATURES_CACHE
    if _STATIC_FEATURES_CACHE is None:
        static_feat_file = BASE_DIR / "data_pipeline" / "features" / "statewide_static_features.parquet"
        if static_feat_file.exists():
            _STATIC_FEATURES_CACHE = pd.read_parquet(static_feat_file)
        else:
            _STATIC_FEATURES_CACHE = pd.DataFrame()
    return _STATIC_FEATURES_CACHE


def get_panchayat_mappings():
    """
    Build canonical Panchayat mappings for all Gram Panchayats statewide.
    All 3,339 Gram Panchayats are treated equally with their official LGD IDs.
    """
    reg_path = BASE_DIR / "data_pipeline" / "metadata" / "statewide_panchayats.parquet"
    if reg_path.exists():
        df = pd.read_parquet(reg_path)
        df["app_id"] = df["panchayat_id"]
        df["GPCODE"] = df["gp_code"]
        df["GPNAME"] = df["panchayat_name"]
        return df

    coordinates = _read_table(COORDINATE_FILE)
    coordinates = coordinates.reset_index(drop=True)
    coordinates["app_id"] = [f"WB_{c}" for c in coordinates["GPCODE"]]
    return coordinates


# ============================================================
# SOIL TYPE (EQUAL STATEWIDE RESOLUTION)
# ============================================================

def get_panchayat_soil_type(
    panchayat_id
):
    """
    Return SoilGrids-derived soil type for any Gram Panchayat statewide.
    All 3,339 Gram Panchayats are supported equally without legacy pilot tiers.
    """
    clean_id = str(panchayat_id).strip().upper()
    if clean_id in LEGACY_PILOT_MAP:
        clean_id = LEGACY_PILOT_MAP[clean_id]

    sf = _get_static_features_df()
    if not sf.empty:
        raw_code = clean_id.replace("WB_", "")
        match = sf[
            (sf["panchayat_id"].astype(str).str.upper() == clean_id)
            | (sf["gp_code"].astype(str) == raw_code)
        ]
        if not match.empty:
            st = match.iloc[0].get("soil_type", "non_sandy")
            if pd.notna(st):
                return str(st).strip().lower()

    if SOIL_FILE.exists():
        try:
            soil = _read_table(SOIL_FILE)
            gpcode = clean_id.replace("WB_", "")
            matches = soil[soil["panchayat_id"].astype(str) == gpcode]
            if not matches.empty:
                st = matches.iloc[0]["soil_type"]
                if pd.notna(st):
                    return str(st).strip().lower()
        except Exception:
            pass

    return "non_sandy"


# ============================================================
# LATEST OBSERVED DRY STREAK (EQUAL STATEWIDE RESOLUTION)
# ============================================================

def get_latest_dry_days(
    panchayat_id
):
    """
    Return the latest observed consecutive dry-day streak for any Gram Panchayat.
    All 3,339 Gram Panchayats are supported equally.
    """
    clean_id = str(panchayat_id).strip().upper()
    resolved_id = LEGACY_PILOT_MAP.get(clean_id, clean_id)
    raw_code = resolved_id.replace("WB_", "")

    if not HISTORY_FILE.exists():
        return 0

    history = _read_table(
        HISTORY_FILE,
        parse_dates=["date"]
    )

    p = history[
        (history["panchayat_id"].astype(str).str.upper() == clean_id)
        | (history["panchayat_id"].astype(str).str.upper() == resolved_id)
        | (history["panchayat_id"].astype(str) == raw_code)
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
# FORECAST HUMIDITY-DAY CALCULATION
# ============================================================

def calculate_forecast_humidity_days(
    forecast_rows,
    threshold: float = 80.0,
):
    """
    Calculate the consecutive high-humidity day streak (>= threshold %)
    across the future forecast window.
    Default antecedent streak of 2 days reflects Bengal monsoon/post-monsoon microclimate.
    """
    hum_streak = 2
    result = {}

    for _, row in forecast_rows.iterrows():
        forecast_date = pd.Timestamp(row["date"]).date()
        hum = float(row.get("coarse_humidity_pct", 82.0)) if "coarse_humidity_pct" in row and row["coarse_humidity_pct"] is not None else 82.0
        if hum >= threshold:
            hum_streak += 1
        else:
            hum_streak = 0
        result[forecast_date] = hum_streak

    return result


# ============================================================
# BUILD FORECAST CONTEXT
# ============================================================

def build_forecast_context(
    panchayat_id,
    forecast_row,
    crop="paddy",
    forecast_dry_days=0,
    forecast_humidity_days=None,
):
    """
    Build AdvisoryContext for one forecast day.

    Future forecast values:
        rain_mm
        tmax_c
        humidity (if available in live/offline profile)
        humidity_days

    Permanent Panchayat context:
        soil_type

    Crop calendar:
        crop
        crop_stage
        harvest_window
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
    # Humidity telemetry (if provided by live API or diurnal synthesis)
    # --------------------------------------------------------

    hum_val = None
    hum_days_val = None

    if "coarse_humidity_pct" in forecast_row and forecast_row["coarse_humidity_pct"] is not None:
        try:
            hum_val = float(forecast_row["coarse_humidity_pct"])
        except (ValueError, TypeError):
            hum_val = None

    if hum_val is not None:
        if forecast_humidity_days is not None:
            hum_days_val = int(forecast_humidity_days)
        elif "coarse_humidity_days" in forecast_row and forecast_row["coarse_humidity_days"] is not None:
            try:
                hum_days_val = int(forecast_row["coarse_humidity_days"])
            except (ValueError, TypeError):
                hum_days_val = 2 if hum_val >= 80.0 else 0
        else:
            hum_days_val = 3 if hum_val >= 80.0 else 0

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

        humidity=hum_val,

        humidity_days=hum_days_val,

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