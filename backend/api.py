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

from forecast_engine_v2 import forecast_panchayat_v2


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

    return {

        "status":
            "ok",

        "service":
            "TerraMind Panchayat Forecast API",

        "model_version":
            "V2 delivery scaffold",

        "rainfall_model":
            "Coarse forecast fallback",

        "degraded":
            True,

        "reason":
            (
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

        description=
            "Panchayat ID, for example A2",

    ),

    days: int = Query(

        5,

        ge=1,

        le=5,

        description=
            "Number of forecast days (1 to 5)",

    ),

    lang: str = Query(

        "bn",

        description=
            "Preferred advisory language: bn or en",

    ),

    crop: str = Query(

        "paddy",

        description=
            "Crop used by the advisory context",

    ),

):

    # ========================================================
    # NORMALIZE
    # ========================================================

    panchayat_id = (
        panchayat_id
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

    if panchayat_id not in PANCHAYAT_DB:

        raise HTTPException(

            status_code=404,

            detail={

                "error":
                    "Panchayat not found",

                "panchayat_id":
                    panchayat_id,

                "available_panchayats":
                    list(
                        PANCHAYAT_DB.keys()
                    ),

            },

        )


    # ========================================================
    # VALIDATE LANGUAGE
    # ========================================================

    if lang not in {
        "bn",
        "en"
    }:

        raise HTTPException(

            status_code=422,

            detail=(
                "lang must be either "
                "'bn' or 'en'."
            ),

        )


    # ========================================================
    # VALIDATE CROP
    # ========================================================

    if not crop:

        raise HTTPException(

            status_code=422,

            detail=
                "crop must not be empty.",

        )


    # ========================================================
    # GENERATE FORECAST
    # ========================================================

    try:

        result = forecast_panchayat_v2(

            panchayat_id=
                panchayat_id,

            days=
                days,

            crop=
                crop,

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


        if lang == "bn":

            advisory_text = (
                advisory[
                    "text_bn"
                ]
            )

        else:

            advisory_text = (
                advisory[
                    "text_en"
                ]
            )


        forecast_days.append({

            "date":
                day[
                    "date"
                ],

            "rain_mm": {

                "p50":
                    day[
                        "rain_mm"
                    ],

                "p10":
                    None,

                "p90":
                    None,

            },

            "tmax_c": {

                "p50":
                    day[
                        "tmax_c"
                    ],

                "p10":
                    None,

                "p90":
                    None,

            },

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