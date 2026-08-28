from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import yaml

from forecast_engine import forecast_panchayat


# ==========================================
# INITIALIZE API
# ==========================================

app = FastAPI(
    title="Panchayat Forecast API",
    version="1.1"
)


# ==========================================
# CORS
# ==========================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# LOAD ADVISORY RULES
# ==========================================

with open(
    "rules.yaml",
    "r",
    encoding="utf-8"
) as file:

    rules_data = yaml.safe_load(file)

    advisory_rules = rules_data["rules"]


# ==========================================
# PANCHAYAT DATABASE
# ==========================================

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


# ==========================================
# ADVISORY RULE ENGINE
# ==========================================

def evaluate_rules(rain_mm, tmax_c):

    for rule in advisory_rules:

        condition = rule["condition"]

        # Prototype-only evaluation.
        # We will replace this with a safer parser later.

        if eval(
            condition,
            {
                "__builtins__": {}
            },
            {
                "rain_mm": rain_mm,
                "tmax_c": tmax_c
            }
        ):

            return rule

    return None


# ==========================================
# FORECAST ENDPOINT
# ==========================================

@app.get("/v1/forecast")
def get_forecast(panchayat_id: str):

    # --------------------------------------
    # Check Panchayat
    # --------------------------------------

    if panchayat_id not in PANCHAYAT_DB:

        raise HTTPException(
            status_code=404,
            detail="Panchayat not found"
        )


    p_info = PANCHAYAT_DB[
        panchayat_id
    ]


    # --------------------------------------
    # Get V1 forecast
    # --------------------------------------

    try:

        forecast = forecast_panchayat(
            panchayat_id
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


    # --------------------------------------
    # Generate advisory
    # --------------------------------------

    advisory = evaluate_rules(
        forecast["rain_mm"],
        forecast["tmax_c"]
    )


    # --------------------------------------
    # Final API response
    # --------------------------------------

    return {

        "panchayat_id":
            panchayat_id,

        "panchayat_name":
            p_info["name"],

        "model_version":
            "gbt-v1.0",

        "source":
            "historical weather + "
            "panchayat terrain data",

        "forecast": {

            "date":
                forecast["date"],

            "rain_mm":
                forecast["rain_mm"],

            "rain_probability":
                forecast["rain_probability"],

            "tmax_c":
                forecast["tmax_c"]
        },

        "advisory": {

            "rule_id":
                advisory["id"]
                if advisory
                else "none",

            "priority":
                advisory["priority"]
                if advisory
                else "low",

            "type":
                advisory["type"]
                if advisory
                else "info",

            "text_en":
                advisory["text_en"]
                if advisory
                else "",

            "text_bn":
                advisory["text_bn"]
                if advisory
                else ""
        }
    }