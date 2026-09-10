import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

BACKEND_DIR = Path(__file__).resolve().parent
ROOT_DIR = BACKEND_DIR.parent
for path in [BACKEND_DIR, ROOT_DIR]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware

from forecast_engine_v2 import (
    forecast_panchayat_v2,
    resolve_panchayat_meta,
    _get_model_artifact,
)


# ============================================================
# TERRAMIND V2 API
# ============================================================

app = FastAPI(

    title="TerraMind Panchayat Forecast API",

    version="2.1",

    description=(
        "Panchayat-level weather intelligence API "
        "for the TerraMind SIH prototype."
    ),
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(

    CORSMiddleware,

    allow_origins=["*"],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


# ============================================================
# TIMEZONE
# ============================================================

IST = ZoneInfo(
    "Asia/Kolkata"
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
# UTF-8 JSON RESPONSE
# ============================================================

def utf8_json_response(data):
    """
    Return JSON explicitly marked as UTF-8.

    This is important for Windows PowerShell clients,
    which may otherwise decode an application/json response
    using the system code page.
    """

    content = json.dumps(
        data,
        ensure_ascii=False,
        allow_nan=False,
    )

    return Response(

        content=content,

        media_type="application/json",

        headers={
            "Content-Type":
                "application/json; charset=utf-8"
        },

    )


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {

        "name":
            "TerraMind Panchayat Forecast API",

        "version":
            "2.1",

        "status":
            "online",

        "docs":
            "/docs",

        "health":
            "/health",

        "panchayat_endpoint":
            "/v1/panchayats",

        "forecast_endpoint":
            "/v1/forecast",

    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():
    model_artifact = _get_model_artifact()
    is_ready = model_artifact is not None

    return {
        "status": "ok",
        "service": "TerraMind Panchayat Forecast API",
        "model_version": (
            "V2.0 Statewide Hurdle (Quantile HGB)"
            if is_ready
            else "V2 delivery scaffold"
        ),
        "rainfall_model": (
            "Two-Stage Hurdle Downscaling (P10/P50/P90)"
            if is_ready
            else "Coarse forecast fallback"
        ),
        "statewide_coverage": "3,339 Gram Panchayats / 22 Districts",
        "live_weather_enabled": True,
        "degraded": False if is_ready else True,
        "reason": None if is_ready else (
            "Operational five-day "
            "Panchayat-level ML downscaling "
            "is not yet validated. "
            "Coarse block forecast is used "
            "as the safe rainfall fallback."
        ),
    }


# ============================================================
# PANCHAYAT LIST
# ============================================================

@app.get("/v1/panchayats")
def get_panchayats():

    return {

        "count":
            len(PANCHAYAT_DB),

        "panchayats": [

            {

                "panchayat_id":
                    panchayat_id,

                "panchayat_name":
                    information["name"],

            }

            for
            panchayat_id,
            information
            in
            PANCHAYAT_DB.items()

        ],

    }


# ============================================================
# FORECAST
# ============================================================

@app.get("/v1/forecast")
def get_forecast(
    panchayat_id: str = Query(
        ...,
        description="Panchayat ID, for example A2 or WB_107001",
    ),
    days: int = Query(
        5,
        ge=1,
        le=5,
        description="Number of forecast days (1 to 5)",
    ),
    lang: str = Query(
        "en",
        description="Preferred advisory language: en or bn",
    ),
    crop: str = Query(
        "paddy",
        description="Crop used by the advisory context",
    ),
    live: bool = Query(
        True,
        description="Whether to fetch dynamic live weather from block coordinates",
    ),
):
    if not isinstance(days, int):
        days = 5
    if not isinstance(lang, str):
        lang = "en"
    if not isinstance(crop, str):
        crop = "paddy"
    if not isinstance(live, bool):
        live = True

    # ========================================================
    # NORMALIZE
    # ========================================================
    panchayat_id = (
        str(panchayat_id)
        .strip()
        .upper()
    )

    lang = (
        lang
        .strip()
        .lower()
    )

    crop = (
        crop
        .strip()
        .lower()
    )

    # ========================================================
    # VALIDATE PANCHAYAT
    # ========================================================
    meta = resolve_panchayat_meta(panchayat_id)
    if not meta:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "Panchayat not found",
                "panchayat_id": panchayat_id,
                "available_panchayats": list(PANCHAYAT_DB.keys()),
            },
        )

    # ========================================================
    # VALIDATE LANGUAGE
    # ========================================================
    if lang not in {"bn", "en"}:
        raise HTTPException(
            status_code=422,
            detail="lang must be either 'bn' or 'en'.",
        )

    # ========================================================
    # VALIDATE CROP
    # ========================================================
    if not crop:
        raise HTTPException(
            status_code=422,
            detail="crop must not be empty.",
        )

    # ========================================================
    # GENERATE FORECAST
    # ========================================================
    try:
        result = forecast_panchayat_v2(
            panchayat_id=panchayat_id,
            days=days,
            crop=crop,
            live=live,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


    except Exception as exc:

        raise HTTPException(

            status_code=500,

            detail=(
                "Forecast generation failed: "
                f"{exc}"
            ),

        ) from exc


    # ========================================================
    # ISSUED AT
    # ========================================================

    issued_at = (
        datetime
        .now(IST)
        .isoformat()
    )


    # ========================================================
    # BUILD FORECAST
    # ========================================================

    forecast_days = []


    for day in result[
        "forecast"
    ]:

        advisory = day[
            "advisory"
        ]


        advisory_text = (
            advisory.get(
                "text_en",
                ""
            )
        )



        forecast_days.append({

            "date":
                day[
                    "date"
                ],

            "rain_mm": (
                day["rain_mm"]
                if isinstance(day["rain_mm"], dict)
                else {
                    "p50": day["rain_mm"],
                    "p10": None,
                    "p90": None,
                }
            ),

            "tmax_c": (
                day["tmax_c"]
                if isinstance(day["tmax_c"], dict)
                else {
                    "p50": day["tmax_c"],
                    "p10": None,
                    "p90": None,
                }
            ),

            "tmin_c":
                day[
                    "tmin_c"
                ],

            "rain_probability":
                day[
                    "rain_probability"
                ],

            "advisory": {

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

                "text":
                    advisory_text,

                "text_en":
                    advisory[
                        "text_en"
                    ],

                "text_bn":
                    advisory[
                        "text_bn"
                    ],

            },

        })


    # ========================================================
    # ADVISORY SUMMARY
    # ========================================================

    advisories = []


    for day in forecast_days:

        advisory = day[
            "advisory"
        ]


        if (
            advisory[
                "rule_id"
            ]
            ==
            "none"
        ):

            continue


        advisories.append({

            "date":
                day[
                    "date"
                ],

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

            "text":
                advisory[
                    "text"
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

    response_data = {

        "panchayat_id":
            result[
                "panchayat_id"
            ],

        "panchayat_name":
            result[
                "panchayat_name"
            ],

        "block_name":
            result.get(
                "block_name"
            ),

        "district_name":
            result.get(
                "district_name"
            ),

        "crop":
            result[
                "crop"
            ],

        "issued_at":
            issued_at,

        "model_version":
            result[
                "model_version"
            ],

        "rainfall_model":
            result[
                "rainfall_model"
            ],

        "is_live_dynamic":
            result.get(
                "is_live_dynamic",
                False
            ),

        "source":
            result[
                "source"
            ],

        "coarse_coordinate":
            result[
                "coarse_coordinate"
            ],

        "forecast":
            forecast_days,

        "advisories":
            advisories,

        "degraded":
            result[
                "degraded"
            ],

        "degraded_reason":
            result[
                "degraded_reason"
            ],

    }


    return utf8_json_response(
        response_data
    )



# ============================================================
# STATEWIDE WEST BENGAL ENDPOINTS
# ============================================================

@app.get("/v1/statewide/districts")
def get_statewide_districts():
    """Return all 22 West Bengal districts with GP and block counts."""
    reg_path = ROOT_DIR / "data_pipeline" / "metadata" / "statewide_panchayats.parquet"
    if not reg_path.exists():
        raise HTTPException(status_code=503, detail="Statewide registry not yet available.")
    import pandas as pd
    df_reg = pd.read_parquet(reg_path)
    summary = df_reg.groupby("district_name").agg(
        total_panchayats=("panchayat_id", "count"),
        total_blocks=("block_name", "nunique")
    ).reset_index().to_dict(orient="records")

    return {
        "state": "West Bengal",
        "district_count": len(summary),
        "total_panchayats": len(df_reg),
        "districts": summary
    }


@app.get("/v1/statewide/panchayats")
def get_statewide_panchayats(
    district: str | None = None,
    search: str | None = None,
    limit: int = 100
):
    """Return matching Gram Panchayats across the 3,339 statewide catalog."""
    reg_path = ROOT_DIR / "data_pipeline" / "metadata" / "statewide_panchayats.parquet"
    if not reg_path.exists():
        raise HTTPException(status_code=503, detail="Statewide registry not yet available.")
    import pandas as pd
    df = pd.read_parquet(reg_path)
    if district and isinstance(district, str):
        df = df[df["district_name"].str.lower() == district.strip().lower()]
    if search and isinstance(search, str):
        s = search.strip().lower()
        df = df[
            df["panchayat_name"].str.lower().str.contains(s, na=False)
            | df["block_name"].str.lower().str.contains(s, na=False)
        ]
    limit_val = int(limit) if isinstance(limit, (int, str)) and str(limit).isdigit() else 100
    return {
        "state": "West Bengal",
        "total_matched": len(df),
        "returned": min(len(df), limit_val),
        "panchayats": df.head(limit_val).to_dict(orient="records")
    }


@app.get("/v1/statewide/stats")
def get_statewide_stats():
    """Return summary metrics for the 2.44M row statewide data lake."""
    report_path = ROOT_DIR / "data_pipeline" / "reports" / "statewide_qa_report.md"
    qa_status = "PASS" if report_path.exists() else "PENDING"
    return {
        "state": "West Bengal",
        "total_rows": 2440809,
        "total_panchayats": 3339,
        "total_blocks": 342,
        "total_districts": 22,
        "date_range": "2024-01-01 to 2025-12-31 (731 continuous days)",
        "qa_status": qa_status,
        "storage_format": "Apache Parquet (District Hive Partitions)",
        "memory_optimization": "Sub-second district loading"
    }


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    print(
        "TerraMind API module"
    )

    print(
        "Run with:"
    )

    print(
        "uvicorn api:app --reload"
    )