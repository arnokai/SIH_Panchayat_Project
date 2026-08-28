import pandas as pd
import numpy as np
from xgboost import XGBClassifier, XGBRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error
import joblib
import os

# ==========================================
# 1. SYNTHETIC DATA GENERATION (MOCK ERA5)
# ==========================================
# In production, this data comes from ERA5 and IMD Gridded datasets.
# For V0, we generate synthetic data simulating physical terrain relationships.

np.random.seed(42)
days = 1000
panchayats = [
    {"id": "P1", "elev": 12, "coast": 8},
    {"id": "P2", "elev": 3,  "coast": 2},
    {"id": "P3", "elev": 5,  "coast": 5},
]

data = []
for d in range(days):
    # Coarse forecast (Same for the whole block)
    coarse_rain = np.random.choice([0, 0, 0, 5, 15, 30, 50]) # Zero-inflated
    coarse_tmax = np.random.normal(32, 4)
    
    for p in panchayats:
        # Physics simulation: Coast gets more rain, elevation cools temp
        actual_rain = max(0, coarse_rain + (10 - p["coast"]) * 0.5 + np.random.normal(0, 2)) if coarse_rain > 0 else 0
        actual_tmax = coarse_tmax - (p["elev"] * 0.0065) + np.random.normal(0, 0.5)
        
        data.append({
            "date": pd.Timestamp("2020-01-01") + pd.Timedelta(days=d),
            "panchayat_id": p["id"],
            "coarse_rain": coarse_rain,
            "coarse_tmax": coarse_tmax,
            "elevation": p["elev"],
            "dist_to_coast": p["coast"],
            "TARGET_rain_mm": actual_rain,
            "TARGET_tmax_c": actual_tmax
        })

df = pd.DataFrame(data)

# ==========================================
# 2. TIME-BASED SPLIT (Section 7.2)
# ==========================================
# NEVER split randomly. The future must not leak into the past.
train = df[df.date < "2022-01-01"]
test = df[df.date >= "2022-01-01"]

FEATURES = ["coarse_rain", "coarse_tmax", "elevation", "dist_to_coast"]

# ==========================================
# 3. BASELINE MEASUREMENT (Section 6.2)
# ==========================================
# Just copying the coarse block value.
baseline_rmse = np.sqrt(mean_squared_error(test["TARGET_rain_mm"], test["coarse_rain"]))
print(f"BASELINE Rain RMSE: {baseline_rmse:.2f} mm")

# ==========================================
# 4. TWO-STAGE RAINFALL MODEL (Section 8.2 & 11.3)
# ==========================================
print("\nTraining Two-Stage Rainfall Model...")

# STAGE 1: Classifier - Will it rain at all?
clf = XGBClassifier(n_estimators=100, max_depth=4, learning_rate=0.05, random_state=42)
clf.fit(train[FEATURES], (train["TARGET_rain_mm"] > 0.1).astype(int))

# STAGE 2: Regressor - How much? (Trained ONLY on wet days, using log1p)
wet_train = train[train["TARGET_rain_mm"] > 0.1]
reg = XGBRegressor(n_estimators=150, max_depth=5, learning_rate=0.05, random_state=42)
reg.fit(wet_train[FEATURES], np.log1p(wet_train["TARGET_rain_mm"]))

# COMBINE PREDICTIONS ON TEST SET
p_rain = clf.predict_proba(test[FEATURES])[:, 1]
amount = np.expm1(reg.predict(test[FEATURES]))
test = test.copy()
test["PRED_rain_mm"] = np.where(p_rain > 0.5, amount, 0.0)

# ==========================================
# 5. TEMPERATURE MODEL
# ==========================================
print("Training Temperature Model...")
temp_reg = XGBRegressor(n_estimators=100, max_depth=4, learning_rate=0.05, random_state=42)
temp_reg.fit(train[FEATURES], train["TARGET_tmax_c"])
test["PRED_tmax_c"] = temp_reg.predict(test[FEATURES])

# ==========================================
# 6. EVALUATION METRICS (Section 9.2)
# ==========================================
model_rmse = np.sqrt(mean_squared_error(test["TARGET_rain_mm"], test["PRED_rain_mm"]))
print(f"\nMODEL Rain RMSE: {model_rmse:.2f} mm (Improvement: {((baseline_rmse - model_rmse)/baseline_rmse)*100:.1f}%)")

# Contingency Table Metrics (Threshold = 2.5 mm)
obs_wet = test["TARGET_rain_mm"] >= 2.5
pred_wet = test["PRED_rain_mm"] >= 2.5

hits = np.sum(obs_wet & pred_wet)
misses = np.sum(obs_wet & ~pred_wet)
false_alarms = np.sum(~obs_wet & pred_wet)

POD = hits / (hits + misses) if (hits + misses) > 0 else 0
FAR = false_alarms / (hits + false_alarms) if (hits + false_alarms) > 0 else 0
CSI = hits / (hits + misses + false_alarms) if (hits + misses + false_alarms) > 0 else 0

print(f"POD (Probability of Detection): {POD:.2f} (Higher is better)")
print(f"FAR (False Alarm Ratio):      {FAR:.2f} (Lower is better)")
print(f"CSI (Critical Success Index): {CSI:.2f} (Higher is better)")

# ==========================================
# 7. SAVE MODELS (Section 12.2 Model Registry)
# ==========================================
os.makedirs("models", exist_ok=True)
joblib.dump(clf, "models/rain_classifier.pkl")
joblib.dump(reg, "models/rain_regressor.pkl")
joblib.dump(temp_reg, "models/tmax_regressor.pkl")
print("\nModels saved to /models directory.")