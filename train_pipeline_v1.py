import os
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from xgboost import XGBClassifier, XGBRegressor

from sklearn.metrics import (
    mean_squared_error,
    mean_absolute_error
)


# ==========================================
# 1. FILE PATHS
# ==========================================

BASE_DIR = Path(__file__).resolve().parent

DATA_FILE = (
    BASE_DIR
    / "data"
    / "raw"
    / "ml_training_dataset.csv"
)

MODEL_DIR = (
    BASE_DIR
    / "models"
)

MODEL_DIR.mkdir(
    exist_ok=True
)


# ==========================================
# 2. LOAD DATA
# ==========================================

df = pd.read_csv(
    DATA_FILE,
    parse_dates=["date"]
)

df = (
    df
    .sort_values(
        ["date", "panchayat_id"]
    )
    .reset_index(drop=True)
)


print("========================================")
print("V1.1 REAL WEATHER TRAINING PIPELINE")
print("========================================")

print(
    f"Loaded rows: {len(df)}"
)


# ==========================================
# 3. FEATURES
# ==========================================
#
# New terrain features:
#   - DEM elevation
#   - slope
#   - aspect sin/cos
#   - terrain roughness
#   - relative elevation
#
# Seasonal encoding:
#   - day_of_year_sin
#   - day_of_year_cos
#
# We deliberately keep month/day_of_year
# in the dataset but DO NOT use them as
# model features.
# ==========================================

FEATURES = [

    # --------------------------------------
    # Static geography
    # --------------------------------------

    "latitude",
    "longitude",

    "elevation",
    "distance_to_river_m",

    # --------------------------------------
    # DEM-derived terrain
    # --------------------------------------

    "elevation_dem_m",
    "slope_deg",
    "aspect_sin",
    "aspect_cos",
    "terrain_roughness_m",
    "relative_elevation_m",

    # --------------------------------------
    # Rainfall memory
    # --------------------------------------

    "rain_lag_1",
    "rain_lag_2",
    "rain_lag_3",
    "rain_lag_7",

    "rain_3day_sum",
    "rain_7day_sum",

    # --------------------------------------
    # Temperature memory
    # --------------------------------------

    "tmax_lag_1",
    "tmax_lag_2",
    "tmax_lag_7",

    "tmin_lag_1",
    "tmin_lag_2",

    # --------------------------------------
    # Seasonal cycle
    # --------------------------------------

    "day_of_year_sin",
    "day_of_year_cos"
]


# ==========================================
# 4. CHECK REQUIRED COLUMNS
# ==========================================

required_columns = [
    "date",
    "rain_mm",
    "tmax_c",
    "panchayat_id"
] + FEATURES


missing_columns = [
    col
    for col in required_columns
    if col not in df.columns
]

if missing_columns:

    raise ValueError(
        "Missing required columns:\n"
        + "\n".join(missing_columns)
    )


print(
    f"Model features: {len(FEATURES)}"
)

print(
    "\nFeatures:"
)

for feature in FEATURES:
    print(
        " -",
        feature
    )


# ==========================================
# 5. TEMPORAL TRAIN / VALIDATION / TEST
# ==========================================
#
# Available data:
#
# 2024 -> training + validation
# 2025 -> untouched final test
#
# Because we currently have only two years
# of historical data, we split 2024
# chronologically rather than randomly.
#
# ------------------------------------------
#
# TRAIN:
# 2024-01-08 to 2024-09-30
#
# VALIDATION:
# 2024-10-01 to 2024-12-31
#
# TEST:
# 2025-01-01 to 2025-12-31
#
# ==========================================

train = df[
    df["date"] < "2024-10-01"
].copy()

validation = df[
    (df["date"] >= "2024-10-01")
    &
    (df["date"] < "2025-01-01")
].copy()

test = df[
    df["date"] >= "2025-01-01"
].copy()


print("\n========================================")
print("TEMPORAL SPLIT")
print("========================================")

print(
    "Training rows:",
    len(train)
)

print(
    "Validation rows:",
    len(validation)
)

print(
    "Testing rows:",
    len(test)
)


print(
    "\nTraining period:",
    train["date"].min().date(),
    "to",
    train["date"].max().date()
)

print(
    "Validation period:",
    validation["date"].min().date(),
    "to",
    validation["date"].max().date()
)

print(
    "Testing period:",
    test["date"].min().date(),
    "to",
    test["date"].max().date()
)


if train.empty:
    raise ValueError(
        "Training dataset is empty."
    )

if validation.empty:
    raise ValueError(
        "Validation dataset is empty."
    )

if test.empty:
    raise ValueError(
        "Test dataset is empty."
    )


# ==========================================
# 6. RAINFALL BASELINE
# ==========================================
#
# Baseline:
# tomorrow's rain = today's rain
#
# The test period remains untouched for
# final comparison.
# ==========================================

baseline_pred = (
    test["rain_lag_1"]
)

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

print(
    f"Baseline RMSE: {baseline_rmse:.2f} mm"
)

print(
    f"Baseline MAE:  {baseline_mae:.2f} mm"
)


# ==========================================
# 7. STAGE 1 — RAIN CLASSIFIER
# ==========================================

print("\n========================================")
print("TRAINING RAIN CLASSIFIER")
print("========================================")


rain_classifier = XGBClassifier(

    n_estimators=200,

    max_depth=5,

    learning_rate=0.05,

    random_state=42,

    eval_metric="logloss",

    n_jobs=-1
)


rain_classifier.fit(

    train[FEATURES],

    (
        train["rain_mm"] > 0.1
    ).astype(int)
)


# ==========================================
# 8. STAGE 2 — RAIN AMOUNT REGRESSOR
# ==========================================
#
# Train only on wet training observations.
# ==========================================

wet_train = train[
    train["rain_mm"] > 0.1
].copy()


if wet_train.empty:

    raise ValueError(
        "No wet observations found "
        "in the training period."
    )


rain_regressor = XGBRegressor(

    n_estimators=250,

    max_depth=5,

    learning_rate=0.05,

    random_state=42,

    objective="reg:squarederror",

    n_jobs=-1
)


rain_regressor.fit(

    wet_train[FEATURES],

    np.log1p(
        wet_train["rain_mm"]
    )
)


# ==========================================
# 9. VALIDATION PREDICTIONS
# ==========================================

validation_probability = (
    rain_classifier
    .predict_proba(
        validation[FEATURES]
    )[:, 1]
)

validation_amount = np.expm1(
    rain_regressor.predict(
        validation[FEATURES]
    )
)


# ==========================================
# 10. SELECT RAIN THRESHOLD
# ==========================================
#
# We use validation data to choose the
# probability threshold.
#
# Test data is NOT used here.
# ==========================================

validation_observed_wet = (
    validation["rain_mm"] >= 2.5
)


best_threshold = 0.5
best_csi = -1.0


for threshold in np.arange(
    0.30,
    0.71,
    0.05
):

    validation_pred_rain = np.where(
        validation_probability >= threshold,
        validation_amount,
        0.0
    )

    validation_pred_wet = (
        validation_pred_rain >= 2.5
    )

    hits = np.sum(
        validation_observed_wet
        &
        validation_pred_wet
    )

    misses = np.sum(
        validation_observed_wet
        &
        ~validation_pred_wet
    )

    false_alarms = np.sum(
        ~validation_observed_wet
        &
        validation_pred_wet
    )

    denominator = (
        hits
        +
        misses
        +
        false_alarms
    )

    csi = (
        hits / denominator
        if denominator > 0
        else 0
    )

    if csi > best_csi:

        best_csi = csi

        best_threshold = float(
            threshold
        )


print("\n========================================")
print("VALIDATION")
print("========================================")

print(
    f"Selected rain probability "
    f"threshold: {best_threshold:.2f}"
)

print(
    f"Validation CSI: {best_csi:.2f}"
)


# ==========================================
# 11. FINAL TEST PREDICTIONS
# ==========================================
#
# IMPORTANT:
# The threshold was selected only from
# validation data.
#
# Now the 2025 test period is evaluated
# once.
# ==========================================

test_probability = (
    rain_classifier
    .predict_proba(
        test[FEATURES]
    )[:, 1]
)

test_amount = np.expm1(
    rain_regressor.predict(
        test[FEATURES]
    )
)


test_predicted_rain = np.where(
    test_probability >= best_threshold,
    test_amount,
    0.0
)


test["pred_rain_mm"] = (
    test_predicted_rain
)


test["rain_probability"] = (
    test_probability
)


# ==========================================
# 12. RAINFALL TEST METRICS
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
    (
        baseline_rmse
        -
        model_rmse
    )
    /
    baseline_rmse
) * 100


# ==========================================
# 13. RAIN EVENT METRICS
# ==========================================

obs_wet = (
    test["rain_mm"] >= 2.5
)

pred_wet = (
    test["pred_rain_mm"] >= 2.5
)


hits = np.sum(
    obs_wet
    &
    pred_wet
)

misses = np.sum(
    obs_wet
    &
    ~pred_wet
)

false_alarms = np.sum(
    ~obs_wet
    &
    pred_wet
)


POD = (
    hits
    /
    (hits + misses)
    if
    (hits + misses) > 0
    else 0
)


FAR = (
    false_alarms
    /
    (hits + false_alarms)
    if
    (hits + false_alarms) > 0
    else 0
)


CSI = (
    hits
    /
    (
        hits
        +
        misses
        +
        false_alarms
    )
    if
    (
        hits
        +
        misses
        +
        false_alarms
    ) > 0
    else 0
)


print("\n========================================")
print("FINAL RAINFALL TEST RESULTS")
print("========================================")

print(
    f"Baseline RMSE: {baseline_rmse:.2f} mm"
)

print(
    f"Model RMSE:    {model_rmse:.2f} mm"
)

print(
    f"Model MAE:     {model_mae:.2f} mm"
)

print(
    f"Improvement:   {improvement:.1f}%"
)

print(
    f"POD:           {POD:.2f}"
)

print(
    f"FAR:           {FAR:.2f}"
)

print(
    f"CSI:           {CSI:.2f}"
)


print("\nRain contingency:")
print(
    f"Hits:          {hits}"
)

print(
    f"Misses:        {misses}"
)

print(
    f"False alarms:  {false_alarms}"
)


# ==========================================
# 14. TEMPERATURE MODEL
# ==========================================

print("\n========================================")
print("TRAINING TEMPERATURE MODEL")
print("========================================")


tmax_regressor = XGBRegressor(

    n_estimators=200,

    max_depth=5,

    learning_rate=0.05,

    random_state=42,

    objective="reg:squarederror",

    n_jobs=-1
)


tmax_regressor.fit(

    train[FEATURES],

    train["tmax_c"]
)


# ==========================================
# 15. TEMPERATURE TEST PREDICTIONS
# ==========================================

test["pred_tmax_c"] = (
    tmax_regressor.predict(
        test[FEATURES]
    )
)


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


# Temperature bias
tmax_bias = (
    test["pred_tmax_c"]
    -
    test["tmax_c"]
).mean()


print("\n========================================")
print("FINAL TEMPERATURE TEST RESULTS")
print("========================================")

print(
    f"Tmax RMSE: {tmax_rmse:.2f} °C"
)

print(
    f"Tmax MAE:  {tmax_mae:.2f} °C"
)

print(
    f"Tmax Bias: {tmax_bias:.2f} °C"
)


# ==========================================
# 16. FEATURE IMPORTANCE
# ==========================================
#
# This is a first model-level explanation.
# SHAP analysis will be a later step.
# ==========================================

rain_importance = pd.DataFrame({

    "feature": FEATURES,

    "importance":
        rain_classifier
        .feature_importances_

}).sort_values(
    "importance",
    ascending=False
)


temp_importance = pd.DataFrame({

    "feature": FEATURES,

    "importance":
        tmax_regressor
        .feature_importances_

}).sort_values(
    "importance",
    ascending=False
)


print("\n========================================")
print("TOP RAIN CLASSIFIER FEATURES")
print("========================================")

print(
    rain_importance
    .head(10)
    .to_string(index=False)
)


print("\n========================================")
print("TOP TEMPERATURE FEATURES")
print("========================================")

print(
    temp_importance
    .head(10)
    .to_string(index=False)
)


# ==========================================
# 17. SAVE MODELS
# ==========================================

rain_classifier_path = (
    MODEL_DIR
    / "v1_rain_classifier.pkl"
)

rain_regressor_path = (
    MODEL_DIR
    / "v1_rain_regressor.pkl"
)

tmax_regressor_path = (
    MODEL_DIR
    / "v1_tmax_regressor.pkl"
)


joblib.dump(
    rain_classifier,
    rain_classifier_path
)

joblib.dump(
    rain_regressor,
    rain_regressor_path
)

joblib.dump(
    tmax_regressor,
    tmax_regressor_path
)


# ==========================================
# 18. SAVE MODEL METADATA
# ==========================================
#
# This lets forecast_engine.py know which
# features and threshold belong to this model.
# ==========================================

metadata = {

    "model_version": "v1.1",

    "rain_probability_threshold":
        best_threshold,

    "features": FEATURES,

    "train_start":
        train["date"]
        .min()
        .date()
        .isoformat(),

    "train_end":
        train["date"]
        .max()
        .date()
        .isoformat(),

    "validation_start":
        validation["date"]
        .min()
        .date()
        .isoformat(),

    "validation_end":
        validation["date"]
        .max()
        .date()
        .isoformat(),

    "test_start":
        test["date"]
        .min()
        .date()
        .isoformat(),

    "test_end":
        test["date"]
        .max()
        .date()
        .isoformat(),

    "rain_baseline_rmse":
        float(baseline_rmse),

    "rain_model_rmse":
        float(model_rmse),

    "rain_model_mae":
        float(model_mae),

    "rain_improvement_percent":
        float(improvement),

    "rain_pod":
        float(POD),

    "rain_far":
        float(FAR),

    "rain_csi":
        float(CSI),

    "tmax_rmse":
        float(tmax_rmse),

    "tmax_mae":
        float(tmax_mae),

    "tmax_bias":
        float(tmax_bias)
}


metadata_path = (
    MODEL_DIR
    / "v1.1_metadata.pkl"
)


joblib.dump(
    metadata,
    metadata_path
)


# ==========================================
# 19. SAVE FEATURE IMPORTANCE
# ==========================================

rain_importance.to_csv(
    MODEL_DIR
    / "v1.1_rain_feature_importance.csv",
    index=False
)

temp_importance.to_csv(
    MODEL_DIR
    / "v1.1_tmax_feature_importance.csv",
    index=False
)


# ==========================================
# 20. COMPLETE
# ==========================================

print("\n========================================")
print("V1.1 MODELS SAVED")
print("========================================")

print(
    rain_classifier_path
)

print(
    rain_regressor_path
)

print(
    tmax_regressor_path
)

print(
    metadata_path
)

print("\nV1.1 TRAINING COMPLETE.")