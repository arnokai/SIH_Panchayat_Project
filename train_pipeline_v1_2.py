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
# 1. PATHS
# ==========================================

BASE_DIR = Path(__file__).resolve().parent

DATA_FILE = (
    BASE_DIR
    / "data"
    / "raw"
    / "v1_2_training_dataset.csv"
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
    parse_dates=[
        "date",
        "target_date"
    ]
)

df = (
    df
    .sort_values(
        [
            "date",
            "panchayat_id"
        ]
    )
    .reset_index(drop=True)
)


print("========================================")
print("TERRAMIND V1.2 TRAINING PIPELINE")
print("========================================")

print(
    "Loaded rows:",
    len(df)
)


# ==========================================
# 3. FEATURES
# ==========================================
#
# Predictor information available on day T.
#
# IMPORTANT:
# CHIRPS rainfall at T+1 is the target.
# We do NOT use chirps_rain_mm as a feature.
# ==========================================

FEATURES = [

    # --------------------------------------
    # Panchayat geography
    # --------------------------------------

    "latitude",
    "longitude",

    # Existing elevation / river feature
    "elevation",
    "distance_to_river_m",

    # --------------------------------------
    # DEM terrain features
    # --------------------------------------

    "elevation_dem_m",
    "slope_deg",
    "aspect_sin",
    "aspect_cos",
    "terrain_roughness_m",
    "relative_elevation_m",

    # --------------------------------------
    # Previous local rainfall
    # --------------------------------------

    "rain_lag_1",
    "rain_lag_2",
    "rain_lag_3",
    "rain_lag_7",

    "rain_3day_sum",
    "rain_7day_sum",

    # --------------------------------------
    # Previous temperature
    # --------------------------------------

    "tmax_lag_1",
    "tmax_lag_2",
    "tmax_lag_7",

    "tmin_lag_1",
    "tmin_lag_2",

    # --------------------------------------
    # Same-day gridded rainfall predictors
    # --------------------------------------

    "imerg_rain_mm",
    "imd_rain_mm",

    # --------------------------------------
    # Seasonal cycle
    # --------------------------------------

    "day_of_year_sin",
    "day_of_year_cos"
]


TARGET = "chirps_rain_mm"


# ==========================================
# 4. COLUMN VALIDATION
# ==========================================

required_columns = [
    "date",
    "target_date",
    "panchayat_id",
    TARGET
] + FEATURES


missing_columns = [
    col
    for col in required_columns
    if col not in df.columns
]


if missing_columns:

    raise ValueError(
        "Missing required columns:\n"
        +
        "\n".join(
            missing_columns
        )
    )


print(
    "Model features:",
    len(FEATURES)
)

print(
    "Target:",
    TARGET
)


# ==========================================
# 5. CHECK TARGET ALIGNMENT
# ==========================================

date_difference = (
    df["target_date"]
    -
    df["date"]
)


invalid_alignment = (
    date_difference
    !=
    pd.Timedelta(days=1)
)


if invalid_alignment.any():

    raise ValueError(
        "Some rows do not have "
        "target_date = date + 1 day."
    )


print(
    "Target alignment: T → T+1 ✅"
)


# ==========================================
# 6. TEMPORAL TRAIN / VALIDATION / TEST
# ==========================================
#
# We keep 2025 as the untouched final test.
#
# TRAIN:
#   2024-01-08 → 2024-08-31
#
# VALIDATION:
#   2024-09-01 → 2024-12-31
#
# TEST:
#   2025-01-01 → 2025-09-29
#
# This is a temporal split, never random.
# ==========================================

train = df[
    df["date"] < "2024-09-01"
].copy()


validation = df[
    (df["date"] >= "2024-09-01")
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
    "\nTraining:",
    train["date"].min().date(),
    "to",
    train["date"].max().date()
)

print(
    "Validation:",
    validation["date"].min().date(),
    "to",
    validation["date"].max().date()
)

print(
    "Testing:",
    test["date"].min().date(),
    "to",
    test["date"].max().date()
)


# ==========================================
# 7. HELPER — RAIN METRICS
# ==========================================

def rain_metrics(
    observed,
    predicted
):

    observed_wet = (
        observed >= 2.5
    )

    predicted_wet = (
        predicted >= 2.5
    )

    hits = np.sum(
        observed_wet
        &
        predicted_wet
    )

    misses = np.sum(
        observed_wet
        &
        ~predicted_wet
    )

    false_alarms = np.sum(
        ~observed_wet
        &
        predicted_wet
    )

    POD = (
        hits
        /
        (hits + misses)
        if
        (hits + misses) > 0
        else 0.0
    )

    FAR = (
        false_alarms
        /
        (hits + false_alarms)
        if
        (hits + false_alarms) > 0
        else 0.0
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
        else 0.0
    )

    return {
        "hits": int(hits),
        "misses": int(misses),
        "false_alarms": int(false_alarms),
        "POD": float(POD),
        "FAR": float(FAR),
        "CSI": float(CSI)
    }


# ==========================================
# 8. BASELINE — PERSISTENCE
# ==========================================
#
# Predict tomorrow's CHIRPS rainfall from
# today's Open-Meteo local rain.
#
# This is intentionally simple.
# ==========================================

baseline_validation = (
    validation["rain_lag_1"]
)

baseline_test = (
    test["rain_lag_1"]
)


baseline_validation_rmse = np.sqrt(
    mean_squared_error(
        validation[TARGET],
        baseline_validation
    )
)


baseline_validation_mae = (
    mean_absolute_error(
        validation[TARGET],
        baseline_validation
    )
)


baseline_test_rmse = np.sqrt(
    mean_squared_error(
        test[TARGET],
        baseline_test
    )
)


baseline_test_mae = (
    mean_absolute_error(
        test[TARGET],
        baseline_test
    )
)


print("\n========================================")
print("BASELINE")
print("========================================")

print(
    f"Validation RMSE: "
    f"{baseline_validation_rmse:.2f} mm"
)

print(
    f"Validation MAE:  "
    f"{baseline_validation_mae:.2f} mm"
)

print(
    f"Test RMSE:       "
    f"{baseline_test_rmse:.2f} mm"
)

print(
    f"Test MAE:        "
    f"{baseline_test_mae:.2f} mm"
)


# ==========================================
# 9. RAIN CLASSIFIER
# ==========================================

print("\n========================================")
print("TRAINING RAIN CLASSIFIER")
print("========================================")


rain_classifier = XGBClassifier(

    n_estimators=300,

    max_depth=5,

    learning_rate=0.05,

    random_state=42,

    eval_metric="logloss",

    n_jobs=-1
)


rain_classifier.fit(

    train[FEATURES],

    (
        train[TARGET] > 0.1
    ).astype(int)
)


# ==========================================
# 10. RAIN AMOUNT REGRESSOR
# ==========================================

print("\n========================================")
print("TRAINING RAIN AMOUNT MODEL")
print("========================================")


wet_train = train[
    train[TARGET] > 0.1
].copy()


if wet_train.empty:

    raise ValueError(
        "No wet training observations."
    )


rain_regressor = XGBRegressor(

    n_estimators=350,

    max_depth=5,

    learning_rate=0.05,

    random_state=42,

    objective="reg:squarederror",

    n_jobs=-1
)


rain_regressor.fit(

    wet_train[FEATURES],

    np.log1p(
        wet_train[TARGET]
    )
)

# ==========================================
# 11. VALIDATION PREDICTIONS
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
# 12. SELECT PROBABILITY THRESHOLD
# ==========================================
#
# Threshold selected ONLY on validation.
# ==========================================

best_threshold = 0.50
best_csi = -1.0


for threshold in np.arange(
    0.30,
    0.81,
    0.05
):

    validation_prediction = (
        np.where(
            validation_probability
            >=
            threshold,

            validation_amount,

            0.0
        )
    )


    metrics = rain_metrics(

        validation[TARGET]
        .values,

        validation_prediction

    )


    if metrics["CSI"] > best_csi:

        best_csi = (
            metrics["CSI"]
        )

        best_threshold = float(
            threshold
        )


# ==========================================
# 13. VALIDATION RAIN METRICS
# ==========================================

validation_prediction = np.where(

    validation_probability
    >=
    best_threshold,

    validation_amount,

    0.0
)


validation_rmse = np.sqrt(
    mean_squared_error(
        validation[TARGET],
        validation_prediction
    )
)


validation_mae = (
    mean_absolute_error(
        validation[TARGET],
        validation_prediction
    )
)


validation_metrics = rain_metrics(

    validation[TARGET].values,

    validation_prediction

)


print("\n========================================")
print("VALIDATION RESULTS")
print("========================================")

print(
    f"Selected threshold: "
    f"{best_threshold:.2f}"
)

print(
    f"RMSE: {validation_rmse:.2f} mm"
)

print(
    f"MAE:  {validation_mae:.2f} mm"
)

print(
    f"POD:  {validation_metrics['POD']:.2f}"
)

print(
    f"FAR:  {validation_metrics['FAR']:.2f}"
)

print(
    f"CSI:  {validation_metrics['CSI']:.2f}"
)


# ==========================================
# 14. FINAL TEST PREDICTION
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


test_prediction = np.where(

    test_probability
    >=
    best_threshold,

    test_amount,

    0.0
)


test["pred_chirps_rain_mm"] = (
    test_prediction
)


test["rain_probability"] = (
    test_probability
)


# ==========================================
# 15. FINAL RAINFALL METRICS
# ==========================================

test_rmse = np.sqrt(
    mean_squared_error(
        test[TARGET],
        test["pred_chirps_rain_mm"]
    )
)


test_mae = (
    mean_absolute_error(
        test[TARGET],
        test["pred_chirps_rain_mm"]
    )
)


test_improvement = (

    (
        baseline_test_rmse
        -
        test_rmse
    )

    /

    baseline_test_rmse

) * 100


test_rain_metrics = rain_metrics(

    test[TARGET].values,

    test["pred_chirps_rain_mm"]
    .values

)


# ==========================================
# 16. TEMPERATURE MODEL
# ==========================================
#
# Tmax target remains the existing
# Open-Meteo Tmax.
#
# We evaluate it separately because
# this pipeline's rainfall target is CHIRPS.
# ==========================================

print("\n========================================")
print("TRAINING TEMPERATURE MODEL")
print("========================================")


tmax_regressor = XGBRegressor(

    n_estimators=250,

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


test["pred_tmax_c"] = (
    tmax_regressor
    .predict(
        test[FEATURES]
    )
)


tmax_rmse = np.sqrt(
    mean_squared_error(
        test["tmax_c"],
        test["pred_tmax_c"]
    )
)


tmax_mae = (
    mean_absolute_error(
        test["tmax_c"],
        test["pred_tmax_c"]
    )
)


tmax_bias = (
    test["pred_tmax_c"]
    -
    test["tmax_c"]
).mean()


# ==========================================
# 17. FEATURE IMPORTANCE
# ==========================================

rain_importance = pd.DataFrame({

    "feature":
        FEATURES,

    "importance":
        rain_classifier
        .feature_importances_

}).sort_values(
    "importance",
    ascending=False
)


tmax_importance = pd.DataFrame({

    "feature":
        FEATURES,

    "importance":
        tmax_regressor
        .feature_importances_

}).sort_values(
    "importance",
    ascending=False
)


print("\n========================================")
print("TOP RAIN FEATURES")
print("========================================")

print(
    rain_importance
    .head(15)
    .to_string(
        index=False
    )
)


print("\n========================================")
print("TOP TEMPERATURE FEATURES")
print("========================================")

print(
    tmax_importance
    .head(15)
    .to_string(
        index=False
    )
)


# ==========================================
# 18. FINAL RESULTS
# ==========================================

print("\n========================================")
print("FINAL V1.2 TEST RESULTS")
print("========================================")

print(
    f"Baseline RMSE: "
    f"{baseline_test_rmse:.2f} mm"
)

print(
    f"Model RMSE:    "
    f"{test_rmse:.2f} mm"
)

print(
    f"Model MAE:     "
    f"{test_mae:.2f} mm"
)

print(
    f"Improvement:   "
    f"{test_improvement:.1f}%"
)

print(
    f"POD:           "
    f"{test_rain_metrics['POD']:.2f}"
)

print(
    f"FAR:           "
    f"{test_rain_metrics['FAR']:.2f}"
)

print(
    f"CSI:           "
    f"{test_rain_metrics['CSI']:.2f}"
)


print("\nRain contingency:")
print(
    f"Hits:          "
    f"{test_rain_metrics['hits']}"
)

print(
    f"Misses:        "
    f"{test_rain_metrics['misses']}"
)

print(
    f"False alarms:  "
    f"{test_rain_metrics['false_alarms']}"
)


print("\nTemperature:")
print(
    f"Tmax RMSE:     "
    f"{tmax_rmse:.2f} °C"
)

print(
    f"Tmax MAE:      "
    f"{tmax_mae:.2f} °C"
)

print(
    f"Tmax Bias:     "
    f"{tmax_bias:.2f} °C"
)


# ==========================================
# 19. SAVE MODELS
# ==========================================

rain_classifier_path = (
    MODEL_DIR
    / "v1_2_rain_classifier.pkl"
)

rain_regressor_path = (
    MODEL_DIR
    / "v1_2_rain_regressor.pkl"
)

tmax_regressor_path = (
    MODEL_DIR
    / "v1_2_tmax_regressor.pkl"
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
# 20. SAVE METADATA
# ==========================================

metadata = {

    "model_version":
        "v1.2",

    "target":
        "CHIRPS rainfall at T+1",

    "features":
        FEATURES,

    "rain_probability_threshold":
        best_threshold,

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

    "baseline_test_rmse":
        float(
            baseline_test_rmse
        ),

    "rain_test_rmse":
        float(
            test_rmse
        ),

    "rain_test_mae":
        float(
            test_mae
        ),

    "rain_improvement_percent":
        float(
            test_improvement
        ),

    "rain_pod":
        float(
            test_rain_metrics["POD"]
        ),

    "rain_far":
        float(
            test_rain_metrics["FAR"]
        ),

    "rain_csi":
        float(
            test_rain_metrics["CSI"]
        ),

    "tmax_rmse":
        float(
            tmax_rmse
        ),

    "tmax_mae":
        float(
            tmax_mae
        ),

    "tmax_bias":
        float(
            tmax_bias
        )
}


metadata_path = (
    MODEL_DIR
    / "v1_2_metadata.pkl"
)


joblib.dump(
    metadata,
    metadata_path
)


# ==========================================
# 21. SAVE FEATURE IMPORTANCE
# ==========================================

rain_importance.to_csv(

    MODEL_DIR
    / "v1_2_rain_feature_importance.csv",

    index=False
)


tmax_importance.to_csv(

    MODEL_DIR
    / "v1_2_tmax_feature_importance.csv",

    index=False
)


# ==========================================
# 22. COMPLETE
# ==========================================

print("\n========================================")
print("V1.2 MODELS SAVED")
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

print("\nV1.2 TRAINING COMPLETE.")