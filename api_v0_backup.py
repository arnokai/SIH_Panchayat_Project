from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import joblib
import numpy as np
import yaml
import datetime

# Initialize API
app = FastAPI(title="Panchayat Forecast API", version="1.0")

# Allow frontend to communicate
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Models
try:
    rain_clf = joblib.load("models/rain_classifier.pkl")
    rain_reg = joblib.load("models/rain_regressor.pkl")
    tmax_reg = joblib.load("models/tmax_regressor.pkl")
except FileNotFoundError:
    print("Warning: Models not found. Run train_pipeline.py first.")

# Load Rules
with open("rules.yaml", "r", encoding="utf-8") as file:
    rules_data = yaml.safe_load(file)
    advisory_rules = rules_data["rules"]

# Mock Database of Panchayats (Terrain data)
PANCHAYAT_DB = {
    "P1": {"name": "Madhusudanpur", "elevation": 12, "dist_to_coast": 8},
    "P2": {"name": "Sagar", "elevation": 3, "dist_to_coast": 2},
    "P3": {"name": "Namkhana", "elevation": 5, "dist_to_coast": 5},
}

def evaluate_rules(rain_mm, tmax_c):
    """Evaluates weather against YAML rules to generate advisory."""
    for rule in advisory_rules:
        # Warning: eval is used here for simplicity in the prototype. 
        # In production, use a safer expression parser or direct if/else mapping.
        if eval(rule["condition"], {"rain_mm": rain_mm, "tmax_c": tmax_c}):
            return rule
    return None

@app.get("/v1/forecast")
def get_forecast(panchayat_id: str):
    if panchayat_id not in PANCHAYAT_DB:
        raise HTTPException(status_code=404, detail="Panchayat not found")
        
    p_info = PANCHAYAT_DB[panchayat_id]
    
    # 1. Fetch latest coarse block forecast (Mocked for V0)
    # In reality, this reads today's ERA5/IMDAA values from a database
    coarse_rain = 25.0
    coarse_tmax = 34.5
    
    # 2. Build feature vector: ["coarse_rain", "coarse_tmax", "elevation", "dist_to_coast"]
    features = np.array([[coarse_rain, coarse_tmax, p_info["elevation"], p_info["dist_to_coast"]]])
    
    # 3. Two-Stage Rain Inference
    p_rain = rain_clf.predict_proba(features)[0, 1]
    amount = np.expm1(rain_reg.predict(features)[0])
    final_rain = float(amount) if p_rain > 0.5 else 0.0
    
    # 4. Temperature Inference
    final_tmax = float(tmax_reg.predict(features)[0])
    
    # 5. Generate Advisory
    advisory = evaluate_rules(final_rain, final_tmax)
    
    # 6. Return response conforming to Appendix G (Page 75)
    return {
        "panchayat_id": panchayat_id,
        "panchayat_name": p_info["name"],
        "issued_at": datetime.datetime.now().isoformat(),
        "model_version": "gbt-v0.1",
        "source": "downscaled from mock-NWP; supplementary to IMD official",
        "forecast": {
            "date": datetime.date.today().isoformat(),
            "rain_mm": round(final_rain, 1),
            "rain_probability": round(float(p_rain), 2),
            "tmax_c": round(final_tmax, 1)
        },
        "advisory": {
            "rule_id": advisory["id"] if advisory else "none",
            "priority": advisory["priority"] if advisory else "low",
            "text_en": advisory["text_en"] if advisory else "",
            "text_bn": advisory["text_bn"] if advisory else ""
        }
    }