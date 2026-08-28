import pandas as pd
import numpy as np
from xgboost import XGBClassifier, XGBRegressor
from sklearn.metrics import (
    mean_squared_error,
    mean_absolute_error
)
import joblib
import os


# ==========================================
# 1. LOAD REAL ML DATASET
# ==========================================

DATA_FILE = "data/raw/ml_training_dataset.csv"

df = pd.read_csv(
    DATA_FILE,
    parse_dates=["date"]
)

print("========================================")
print("V1 REAL WEATHER TRAINING PIPELINE")
print("========================================")

print(f"Loaded rows: {len(df)}")


# ==========================================
# 2. SORT BY TIME
# ==========================================

df = df.sort_values(
    ["date", "panchayat_id"]
).reset_index(drop=True)


# ==========================================
# 3. FEATURES
# ==========================================

FEATURES = [
    "latitude",
    "longitude",
    "elevation",
    "distance_to_river_m",

    "rain_lag_1",
    "rain_lag_2",
    "rain_lag_3",
    "rain_lag_7",

    "tmax_lag_1",
    "tmax_lag_2",
    "tmax_lag_7",

    "tmin_lag_1",
    "tmin_lag_2",

    "rain_3day_sum",
    "rain_7day_sum",

    "month",
    "day_of_year"
]


# ==========================================
# 4. TIME-BASED TRAIN / TEST SPLIT
# ==========================================
#
# 2024 -> training
# 2025 -> testing
#
# We deliberately do NOT randomly split.
# Future information must not leak into training.
#

train = df[df["date"] < "2025-01-01"].copy()

test = df[df["date"] >= "2025-01-01"].copy()

print("\nTraining rows:", len(train))
print("Testing rows:", len(test))

print(
    "Training period:",
    train["date"].min().date(),
    "to",
    train["date"].max().date()
)

print(
    "Testing period:",
    test["date"].min().date(),
    "to",
    test["date"].max().date()
)


# ==========================================
# 5. RAINFALL BASELINE
# ==========================================
#
# Simple baseline:
# Tomorrow's rain = today's rain
#

baseline_pred = test["rain_lag_1"]

baseline_rmse = np.sqrt(
    mean_squared_error(
        test["rain_mm"],
        baseline_pred
    )
)

baseline_mae = mean_absolute_error(
    test["rain_mm"],
    baseline_pred
)

print("\n========================================")
print("RAINFALL BASELINE")
print("========================================")

print(f"Baseline RMSE: {baseline_rmse:.2f} mm")
print(f"Baseline MAE:  {baseline_mae:.2f} mm")


# ==========================================
# 6. TWO-STAGE RAINFALL MODEL
# ==========================================

print("\n========================================")
print("TRAINING RAINFALL MODEL")
print("========================================")


# ------------------------------------------
# Stage 1: Rain / No Rain classifier
# ------------------------------------------

rain_classifier = XGBClassifier(
    n_estimators=200,
    max_depth=5,
    learning_rate=0.05,
    random_state=42,
    eval_metric="logloss"
)

rain_classifier.fit(
    train[FEATURES],
    (train["rain_mm"] > 0.1).astype(int)
)


# ------------------------------------------
# Stage 2: Rain amount regressor
# ------------------------------------------

wet_train = train[
    train["rain_mm"] > 0.1
].copy()

rain_regressor = XGBRegressor(
    n_estimators=250,
    max_depth=5,
    learning_rate=0.05,
    random_state=42,
    objective="reg:squarederror"
)

rain_regressor.fit(
    wet_train[FEATURES],
    np.log1p(wet_train["rain_mm"])
)


# ==========================================
# 7. RAINFALL PREDICTION
# ==========================================

probability = rain_classifier.predict_proba(
    test[FEATURES]
)[:, 1]

amount = np.expm1(
    rain_regressor.predict(test[FEATURES])
)

predicted_rain = np.where(
    probability > 0.5,
    amount,
    0.0
)

test["pred_rain_mm"] = predicted_rain


# ==========================================
# 8. RAINFALL EVALUATION
# ==========================================

model_rmse = np.sqrt(
    mean_squared_error(
        test["rain_mm"],
        test["pred_rain_mm"]
    )
)

model_mae = mean_absolute_error(
    test["rain_mm"],
    test["pred_rain_mm"]
)

improvement = (
    (baseline_rmse - model_rmse)
    / baseline_rmse
) * 100


print("\n========================================")
print("RAINFALL MODEL RESULTS")
print("========================================")

print(f"Model RMSE: {model_rmse:.2f} mm")
print(f"Model MAE:  {model_mae:.2f} mm")

print(
    f"Improvement over baseline: "
    f"{improvement:.1f}%"
)


# ==========================================
# 9. RAIN EVENT METRICS
# ==========================================

obs_wet = test["rain_mm"] >= 2.5

pred_wet = test["pred_rain_mm"] >= 2.5

hits = np.sum(
    obs_wet & pred_wet
)

misses = np.sum(
    obs_wet & ~pred_wet
)

false_alarms = np.sum(
    ~obs_wet & pred_wet
)


POD = (
    hits / (hits + misses)
    if (hits + misses) > 0
    else 0
)

FAR = (
    false_alarms /
    (hits + false_alarms)
    if (hits + false_alarms) > 0
    else 0
)

CSI = (
    hits /
    (hits + misses + false_alarms)
    if (hits + misses + false_alarms) > 0
    else 0
)


print("\n========================================")
print("RAIN EVENT METRICS")
print("========================================")

print(f"POD: {POD:.2f}")
print(f"FAR: {FAR:.2f}")
print(f"CSI: {CSI:.2f}")


# ==========================================
# 10. TEMPERATURE MODEL
# ==========================================

print("\n========================================")
print("TRAINING TEMPERATURE MODEL")
print("========================================")


tmax_regressor = XGBRegressor(
    n_estimators=200,
    max_depth=5,
    learning_rate=0.05,
    random_state=42,
    objective="reg:squarederror"
)

tmax_regressor.fit(
    train[FEATURES],
    train["tmax_c"]
)


# Predict Tmax
test["pred_tmax_c"] = tmax_regressor.predict(
    test[FEATURES]
)


# Evaluate Tmax
tmax_rmse = np.sqrt(
    mean_squared_error(
        test["tmax_c"],
        test["pred_tmax_c"]
    )
)

tmax_mae = mean_absolute_error(
    test["tmax_c"],
    test["pred_tmax_c"]
)


print("\nTemperature results:")
print(f"Tmax RMSE: {tmax_rmse:.2f} °C")
print(f"Tmax MAE:  {tmax_mae:.2f} °C")


# ==========================================
# 11. SAVE MODELS
# ==========================================

os.makedirs(
    "models",
    exist_ok=True
)


joblib.dump(
    rain_classifier,
    "models/v1_rain_classifier.pkl"
)

joblib.dump(
    rain_regressor,
    "models/v1_rain_regressor.pkl"
)

joblib.dump(
    tmax_regressor,
    "models/v1_tmax_regressor.pkl"
)


print("\n========================================")
print("MODELS SAVED")
print("========================================")

print("models/v1_rain_classifier.pkl")
print("models/v1_rain_regressor.pkl")
print("models/v1_tmax_regressor.pkl")

print("\nV1 TRAINING COMPLETE.")