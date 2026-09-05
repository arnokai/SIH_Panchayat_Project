import sys
from pathlib import Path

# Ensure project root and backend are on sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "backend"))

import pandas as pd

from advisory_context import AdvisoryContext
from advisory_engine import evaluate_advisories


# ============================================================
# TERRAMIND — REAL DATA ADVISORY RULE TEST
# ============================================================

WEATHER_FILE = (
    ROOT_DIR
    / "data_pipeline"
    / "raw"
    / "advisory_context_history.csv"
)

SOIL_FILE = (
    ROOT_DIR
    / "data_pipeline"
    / "raw"
    / "panchayat_soil_context.csv"
)


# ============================================================
# LOAD DATA
# ============================================================

weather = pd.read_csv(
    WEATHER_FILE,
    parse_dates=["date"]
)

soil = pd.read_csv(
    SOIL_FILE
)


# ============================================================
# NORMALIZE PANCHAYAT NAMES
# ============================================================

weather["panchayat_name_key"] = (
    weather["panchayat_name"]
    .astype(str)
    .str.strip()
    .str.upper()
)

soil["panchayat_name_key"] = (
    soil["panchayat_name"]
    .astype(str)
    .str.strip()
    .str.upper()
)


# ============================================================
# JOIN SOIL
# ============================================================

df = weather.merge(
    soil[
        [
            "panchayat_name_key",
            "soil_type"
        ]
    ],
    on="panchayat_name_key",
    how="left",
    validate="many_to_one"
)


if df["soil_type"].isna().any():
    raise ValueError(
        "Some weather rows could not be matched "
        "to Panchayat soil context."
    )


# ============================================================
# IMPORT CROP CALENDAR
# ============================================================

try:
    from data_pipeline.metadata.crop_calendar import get_crop_context
except ImportError:
    from data.crop_calendar import get_crop_context


# ============================================================
# RULE COUNTS
# ============================================================

rule_counts = {}

example_rows = {}


# ============================================================
# EVALUATE EACH HISTORICAL ROW
# ============================================================

for _, row in df.iterrows():

    calendar = get_crop_context(
        row["date"].date(),
        crop="paddy"
    )

    context = AdvisoryContext(

        rain_mm=float(
            row["rain_mm"]
        ),

        tmax_c=float(
            row["tmax_c"]
        ),

        humidity=float(
            row["humidity_pct"]
        ),

        humidity_days=int(
            row["humidity_days"]
        ),

        dry_days=int(
            row["dry_days"]
        ),

        soil_type=str(
            row["soil_type"]
        ).strip().lower(),

        crop=calendar["crop"],

        crop_stage=calendar[
            "crop_stage"
        ],

        harvest_window=calendar[
            "harvest_window"
        ],

    )


    matches = evaluate_advisories(
        context
    )


    for rule in matches:

        rule_id = rule["id"]

        rule_counts[
            rule_id
        ] = (
            rule_counts.get(
                rule_id,
                0
            )
            + 1
        )


        # Keep one example of each rule
        if rule_id not in example_rows:

            example_rows[
                rule_id
            ] = {

                "date":
                    row["date"].date().isoformat(),

                "panchayat":
                    row["panchayat_name"],

                "rain_mm":
                    round(
                        float(
                            row["rain_mm"]
                        ),
                        2
                    ),

                "tmax_c":
                    round(
                        float(
                            row["tmax_c"]
                        ),
                        2
                    ),

                "humidity_pct":
                    round(
                        float(
                            row["humidity_pct"]
                        ),
                        2
                    ),

                "humidity_days":
                    int(
                        row["humidity_days"]
                    ),

                "dry_days":
                    int(
                        row["dry_days"]
                    ),

                "soil_type":
                    row["soil_type"],

                "crop_stage":
                    calendar[
                        "crop_stage"
                    ],

                "harvest_window":
                    calendar[
                        "harvest_window"
                    ],
            }


# ============================================================
# HANDBOOK RULES
# ============================================================

HANDBOOK_RULES = [
    "no_spray_rain",
    "heat_stress",
    "blast_disease_risk",
    "sandy_soil_dry_spell",
    "harvest_rain",
]


# ============================================================
# REPORT
# ============================================================

print(
    "========================================"
)

print(
    "TERRAMIND REAL DATA ADVISORY TEST"
)

print(
    "========================================"
)

print(
    "Historical rows:",
    len(df)
)

print(
    "Panchayats:",
    df["panchayat_name"]
    .nunique()
)

print(
    "Date range:",
    df["date"].min().date(),
    "to",
    df["date"].max().date()
)


print(
    "\n========================================"
)

print(
    "HANDBOOK RULE RESULTS"
)

print(
    "========================================"
)


for rule_id in HANDBOOK_RULES:

    count = rule_counts.get(
        rule_id,
        0
    )

    print(
        f"{rule_id}: {count} matches"
    )

    if rule_id in example_rows:

        print(
            "  Example:",
            example_rows[
                rule_id
            ]
        )

    else:

        print(
            "  Example: none found"
        )


# ============================================================
# ADDITIONAL PROJECT RULES
# ============================================================

print(
    "\n========================================"
)

print(
    "ADDITIONAL PROJECT RULES"
)

print(
    "========================================"
)


for rule_id in [
    "moderate_rain",
    "light_rain",
    "dry_day",
]:

    print(
        f"{rule_id}: "
        f"{rule_counts.get(rule_id, 0)} matches"
    )


# ============================================================
# SOIL CHECK
# ============================================================

print(
    "\n========================================"
)

print(
    "SOIL CONTEXT CHECK"
)

print(
    "========================================"
)

print(
    df[
        [
            "panchayat_name",
            "soil_type"
        ]
    ]
    .drop_duplicates()
    .sort_values("panchayat_name")
    .to_string(index=False)
)


# ============================================================
# COMPLETION
# ============================================================

print(
    "\n========================================"
)

print(
    "REAL DATA ADVISORY TEST COMPLETE"
)

print(
    "========================================"
)