import os

import joblib
import numpy as np
import pandas as pd

from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
)

from xgboost import XGBClassifier, XGBRegressor


# ============================================================
# TERRAMIND M3 — CLEAN DOWNSCALING MODEL
# ============================================================
#
# Architecture:
#
#   Coarse block weather
#          +
#   Panchayat static/terrain features
#          +
#   Seasonality
#          ↓
#   Stage 1: rain occurrence
#          +
#   Stage 2: wet-day rainfall amount
#          ↓
#   Panchayat rainfall
#
# This is a retrospective downscaling experiment because the
# historical coarse input is from an archive rather than an
# archive of issued forecasts.
#
# ============================================================


DATA_FILE = (
    "data/raw/m3_clean_downscaling_dataset.csv"
)

MODEL_DIR = "models"

PREDICTIONS_FILE = (
    "data/raw/m3_clean_predictions.csv"
)

METRICS_FILE = (
    "data/raw/m3_clean_metrics.csv"
)


TARGET = "chirps_rain_mm"

RAIN_THRESHOLD = 0.1

EVENT_THRESHOLD = 2.5


# ============================================================
# FEATURES
# ============================================================

FEATURES = [

    # Coarse block weather
    "coarse_rain_mm",
    "coarse_tmax_c",
    "coarse_tmin_c",

    # Panchayat coordinates
    "latitude",
    "longitude",

    # Panchayat geography
    "elevation",
    "distance_to_river_m",

    # Terrain
    "elevation_dem_m",
    "slope_deg",
    "aspect_sin",
    "aspect_cos",
    "terrain_roughness_m",
    "relative_elevation_m",

    # Seasonality
    "month",
    "day_of_year",
    "day_of_year_sin",
    "day_of_year_cos",
]


# ============================================================
# 1. LOAD
# ============================================================

print(
    "========================================"
)

print(
    "TERRAMIND CLEAN M3 TRAINING"
)

print(
    "========================================"
)


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


print(
    "Loaded rows:",
    len(df)
)

print(
    "Panchayats:",
    df["panchayat_id"].nunique()
)

print(
    "Dates:",
    df["date"].min().date(),
    "to",
    df["date"].max().date()
)


# ============================================================
# 2. VALIDATE
# ============================================================

missing_features = [
    feature
    for feature in FEATURES
    if feature not in df.columns
]


if missing_features:

    raise ValueError(
        "Missing features:\n"
        +
        "\n".join(
            missing_features
        )
    )


if TARGET not in df.columns:

    raise ValueError(
        f"Missing target: {TARGET}"
    )


missing_values = (
    df[
        FEATURES + [TARGET]
    ]
    .isna()
    .sum()
)


if missing_values.sum() > 0:

    raise ValueError(
        "Missing values found:\n"
        +
        missing_values[
            missing_values > 0
        ]
        .to_string()
    )


# ============================================================
# 3. TEMPORAL SPLIT
# ============================================================

TRAIN_END = pd.Timestamp(
    "2024-08-31"
)

VALIDATION_START = pd.Timestamp(
    "2024-09-01"
)

VALIDATION_END = pd.Timestamp(
    "2024-12-31"
)

TEST_START = pd.Timestamp(
    "2025-01-01"
)


train = df[
    df["date"] <= TRAIN_END
].copy()


validation = df[
    (
        df["date"] >= VALIDATION_START
    )
    &
    (
        df["date"] <= VALIDATION_END
    )
].copy()


test = df[
    df["date"] >= TEST_START
].copy()


print(
    "\n========================================"
)

print(
    "TEMPORAL SPLIT"
)

print(
    "========================================"
)

print(
    "Training:",
    len(train),
    train["date"].min().date(),
    "to",
    train["date"].max().date()
)

print(
    "Validation:",
    len(validation),
    validation["date"].min().date(),
    "to",
    validation["date"].max().date()
)

print(
    "Test:",
    len(test),
    test["date"].min().date(),
    "to",
    test["date"].max().date()
)


# ============================================================
# 4. COARSE BASELINE
# ============================================================

print(
    "\n========================================"
)

print(
    "COARSE BASELINE"
)

print(
    "========================================"
)


baseline_val = (
    validation[
        "coarse_rain_mm"
    ]
    .to_numpy()
)

baseline_test = (
    test[
        "coarse_rain_mm"
    ]
    .to_numpy()
)


y_val = (
    validation[TARGET]
    .to_numpy()
)

y_test = (
    test[TARGET]
    .to_numpy()
)


baseline_val_rmse = np.sqrt(
    mean_squared_error(
        y_val,
        baseline_val
    )
)

baseline_val_mae = (
    mean_absolute_error(
        y_val,
        baseline_val
    )
)


baseline_test_rmse = np.sqrt(
    mean_squared_error(
        y_test,
        baseline_test
    )
)

baseline_test_mae = (
    mean_absolute_error(
        y_test,
        baseline_test
    )
)


print(
    f"Validation RMSE: "
    f"{baseline_val_rmse:.2f} mm"
)

print(
    f"Validation MAE:  "
    f"{baseline_val_mae:.2f} mm"
)

print(
    f"Test RMSE:       "
    f"{baseline_test_rmse:.2f} mm"
)

print(
    f"Test MAE:        "
    f"{baseline_test_mae:.2f} mm"
)


# ============================================================
# 5. STAGE 1 — RAIN OCCURRENCE
# ============================================================

print(
    "\n========================================"
)

print(
    "TRAINING RAIN OCCURRENCE MODEL"
)

print(
    "========================================"
)


y_train_event = (
    train[TARGET]
    > RAIN_THRESHOLD
).astype(int)


classifier = XGBClassifier(

    n_estimators=400,

    max_depth=6,

    learning_rate=0.05,

    subsample=0.9,

    colsample_bytree=0.9,

    objective="binary:logistic",

    eval_metric="logloss",

    random_state=42,

    n_jobs=-1,
)


classifier.fit(
    train[FEATURES],
    y_train_event
)


# ============================================================
# 6. STAGE 2 — WET-DAY AMOUNT
# ============================================================

print(
    "\n========================================"
)

print(
    "TRAINING WET-DAY RAINFALL MODEL"
)

print(
    "========================================"
)


wet_train = train[
    train[TARGET]
    >
    RAIN_THRESHOLD
].copy()


if wet_train.empty:

    raise ValueError(
        "No wet observations in training set."
    )


regressor = XGBRegressor(

    n_estimators=600,

    max_depth=7,

    learning_rate=0.05,

    subsample=0.9,

    colsample_bytree=0.9,

    objective="reg:squarederror",

    random_state=42,

    n_jobs=-1,
)


regressor.fit(

    wet_train[FEATURES],

    np.log1p(
        wet_train[TARGET]
    )
)


# ============================================================
# 7. PREDICTION FUNCTION
# ============================================================

def predict_rain(data):

    probability = (
        classifier
        .predict_proba(
            data[FEATURES]
        )[:, 1]
    )


    amount = np.expm1(
        regressor.predict(
            data[FEATURES]
        )
    )


    prediction = np.where(
        probability >= 0.30,
        amount,
        0.0
    )


    prediction = np.clip(
        prediction,
        0.0,
        None
    )


    return (
        probability,
        prediction
    )


# ============================================================
# 8. VALIDATION
# ============================================================

print(
    "\n========================================"
)

print(
    "VALIDATION RESULTS"
)

print(
    "========================================"
)


val_probability, val_prediction = (
    predict_rain(validation)
)


val_rmse = np.sqrt(
    mean_squared_error(
        y_val,
        val_prediction
    )
)

val_mae = (
    mean_absolute_error(
        y_val,
        val_prediction
    )
)


val_obs_event = (
    y_val >= EVENT_THRESHOLD
)

val_pred_event = (
    val_prediction >= EVENT_THRESHOLD
)


val_hits = np.sum(
    val_obs_event
    &
    val_pred_event
)

val_misses = np.sum(
    val_obs_event
    &
    ~val_pred_event
)

val_false_alarms = np.sum(
    ~val_obs_event
    &
    val_pred_event
)


val_pod = (
    val_hits
    /
    (val_hits + val_misses)
    if val_hits + val_misses
    else 0
)

val_far = (
    val_false_alarms
    /
    (
        val_hits
        +
        val_false_alarms
    )
    if (
        val_hits
        +
        val_false_alarms
    )
    else 0
)

val_csi = (
    val_hits
    /
    (
        val_hits
        +
        val_misses
        +
        val_false_alarms
    )
    if (
        val_hits
        +
        val_misses
        +
        val_false_alarms
    )
    else 0
)


print(
    f"Baseline RMSE: "
    f"{baseline_val_rmse:.2f} mm"
)

print(
    f"Model RMSE:    "
    f"{val_rmse:.2f} mm"
)

print(
    f"Baseline MAE:  "
    f"{baseline_val_mae:.2f} mm"
)

print(
    f"Model MAE:     "
    f"{val_mae:.2f} mm"
)

print(
    f"POD: {val_pod:.2f}"
)

print(
    f"FAR: {val_far:.2f}"
)

print(
    f"CSI: {val_csi:.2f}"
)


# ============================================================
# 9. FINAL TEST
# ============================================================

print(
    "\n========================================"
)

print(
    "FINAL CLEAN M3 TEST"
)

print(
    "========================================"
)


test_probability, test_prediction = (
    predict_rain(test)
)


test_rmse = np.sqrt(
    mean_squared_error(
        y_test,
        test_prediction
    )
)

test_mae = (
    mean_absolute_error(
        y_test,
        test_prediction
    )
)


improvement = (
    (
        baseline_test_rmse
        -
        test_rmse
    )
    /
    baseline_test_rmse
    *
    100
)


obs_event = (
    y_test >= EVENT_THRESHOLD
)

pred_event = (
    test_prediction >= EVENT_THRESHOLD
)


hits = np.sum(
    obs_event
    &
    pred_event
)

misses = np.sum(
    obs_event
    &
    ~pred_event
)

false_alarms = np.sum(
    ~obs_event
    &
    pred_event
)

correct_negatives = np.sum(
    ~obs_event
    &
    ~pred_event
)


pod = (
    hits
    /
    (hits + misses)
    if hits + misses
    else 0
)


far = (
    false_alarms
    /
    (
        hits
        +
        false_alarms
    )
    if (
        hits
        +
        false_alarms
    )
    else 0
)


csi = (
    hits
    /
    (
        hits
        +
        misses
        +
        false_alarms
    )
    if (
        hits
        +
        misses
        +
        false_alarms
    )
    else 0
)


print(
    f"Baseline RMSE: {baseline_test_rmse:.2f} mm"
)

print(
    f"Model RMSE:    {test_rmse:.2f} mm"
)

print(
    f"Baseline MAE:  {baseline_test_mae:.2f} mm"
)

print(
    f"Model MAE:     {test_mae:.2f} mm"
)

print(
    f"Improvement:   {improvement:.1f}%"
)


print(
    "\nRain event metrics:"
)

print(
    f"Hits:             {hits}"
)

print(
    f"Misses:           {misses}"
)

print(
    f"False alarms:     {false_alarms}"
)

print(
    f"Correct negatives:{correct_negatives}"
)

print(
    f"POD:              {pod:.2f}"
)

print(
    f"FAR:              {far:.2f}"
)

print(
    f"CSI:              {csi:.2f}"
)


# ============================================================
# 10. HEAVY RAIN
# ============================================================

print(
    "\n========================================"
)

print(
    "HEAVY RAIN >= 25 MM"
)

print(
    "========================================"
)


heavy = (
    y_test >= 25.0
)


if heavy.sum() > 0:

    heavy_truth = (
        y_test[heavy]
    )

    heavy_model = (
        test_prediction[heavy]
    )

    heavy_baseline = (
        baseline_test[heavy]
    )


    heavy_baseline_rmse = np.sqrt(
        mean_squared_error(
            heavy_truth,
            heavy_baseline
        )
    )


    heavy_model_rmse = np.sqrt(
        mean_squared_error(
            heavy_truth,
            heavy_model
        )
    )


    heavy_baseline_mae = (
        mean_absolute_error(
            heavy_truth,
            heavy_baseline
        )
    )


    heavy_model_mae = (
        mean_absolute_error(
            heavy_truth,
            heavy_model
        )
    )


    print(
        "Cases:",
        len(heavy_truth)
    )

    print(
        f"Baseline RMSE: "
        f"{heavy_baseline_rmse:.2f} mm"
    )

    print(
        f"Model RMSE:    "
        f"{heavy_model_rmse:.2f} mm"
    )

    print(
        f"Baseline MAE:  "
        f"{heavy_baseline_mae:.2f} mm"
    )

    print(
        f"Model MAE:     "
        f"{heavy_model_mae:.2f} mm"
    )

else:

    heavy_baseline_rmse = np.nan
    heavy_model_rmse = np.nan
    heavy_baseline_mae = np.nan
    heavy_model_mae = np.nan

    print(
        "No heavy-rain cases."
    )


# ============================================================
# 11. PANCHAYAT PERFORMANCE
# ============================================================

print(
    "\n========================================"
)

print(
    "PERFORMANCE BY PANCHAYAT"
)

print(
    "========================================"
)


results = []


for panchayat_id, group in (
    test.groupby("panchayat_id")
):

    indices = (
        test.index
        .get_indexer(
            group.index
        )
    )


    actual = (
        group[TARGET]
        .to_numpy()
    )

    model_values = (
        test_prediction[
            indices
        ]
    )

    baseline_values = (
        baseline_test[
            indices
        ]
    )


    model_rmse = np.sqrt(
        mean_squared_error(
            actual,
            model_values
        )
    )

    baseline_rmse = np.sqrt(
        mean_squared_error(
            actual,
            baseline_values
        )
    )


    model_mae = (
        mean_absolute_error(
            actual,
            model_values
        )
    )

    baseline_mae = (
        mean_absolute_error(
            actual,
            baseline_values
        )
    )


    results.append({

        "panchayat_id":
            panchayat_id,

        "n":
            len(group),

        "baseline_rmse":
            baseline_rmse,

        "model_rmse":
            model_rmse,

        "rmse_improvement_pct":
            (
                (
                    baseline_rmse
                    -
                    model_rmse
                )
                /
                baseline_rmse
                *
                100
            ),

        "baseline_mae":
            baseline_mae,

        "model_mae":
            model_mae,

        "mae_improvement_pct":
            (
                (
                    baseline_mae
                    -
                    model_mae
                )
                /
                baseline_mae
                *
                100
            )

    })


panchayat_results = (
    pd.DataFrame(results)
    .sort_values(
        "panchayat_id"
    )
)


print(
    panchayat_results
    .round(3)
    .to_string(index=False)
)


# ============================================================
# 12. FEATURE IMPORTANCE
# ============================================================

print(
    "\n========================================"
)

print(
    "FEATURE IMPORTANCE"
)

print(
    "========================================"
)


importance = pd.DataFrame({

    "feature":
        FEATURES,

    "importance":
        regressor.feature_importances_

})


importance = (
    importance
    .sort_values(
        "importance",
        ascending=False
    )
)


print(
    importance
    .round(6)
    .to_string(index=False)
)


# ============================================================
# 13. SAVE TEST PREDICTIONS
# ============================================================

output = test[
    [
        "date",
        "panchayat_id",
        "panchayat_name",
        "coarse_rain_mm",
        "coarse_tmax_c",
        "coarse_tmin_c",
        TARGET,
    ]
].copy()


output = output.rename(
    columns={
        TARGET:
            "actual_rain_mm"
    }
)


output[
    "rain_probability"
] = test_probability


output[
    "predicted_rain_mm"
] = test_prediction


output[
    "baseline_rain_mm"
] = baseline_test


output[
    "absolute_error"
] = (
    np.abs(
        output[
            "actual_rain_mm"
        ]
        -
        output[
            "predicted_rain_mm"
        ]
    )
)


os.makedirs(
    "data/raw",
    exist_ok=True
)


output.to_csv(
    PREDICTIONS_FILE,
    index=False
)


# ============================================================
# 14. SAVE MODELS
# ============================================================

os.makedirs(
    MODEL_DIR,
    exist_ok=True
)


classifier_path = os.path.join(
    MODEL_DIR,
    "m3_clean_rain_classifier.pkl"
)

regressor_path = os.path.join(
    MODEL_DIR,
    "m3_clean_rain_regressor.pkl"
)

metadata_path = os.path.join(
    MODEL_DIR,
    "m3_clean_metadata.pkl"
)


joblib.dump(
    classifier,
    classifier_path
)

joblib.dump(
    regressor,
    regressor_path
)


metadata = {

    "model_version":
        "M3-clean-downscaling",

    "architecture":
        "XGBoost two-stage rainfall downscaling",

    "data_type":
        "retrospective archive experiment",

    "target":
        TARGET,

    "rain_threshold":
        RAIN_THRESHOLD,

    "event_threshold":
        EVENT_THRESHOLD,

    "features":
        FEATURES,

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

    "model_test_rmse":
        float(
            test_rmse
        ),

    "baseline_test_mae":
        float(
            baseline_test_mae
        ),

    "model_test_mae":
        float(
            test_mae
        ),

    "improvement_percent":
        float(
            improvement
        ),

    "pod":
        float(pod),

    "far":
        float(far),

    "csi":
        float(csi),

    "heavy_baseline_rmse":
        (
            float(
                heavy_baseline_rmse
            )
            if not np.isnan(
                heavy_baseline_rmse
            )
            else None
        ),

    "heavy_model_rmse":
        (
            float(
                heavy_model_rmse
            )
            if not np.isnan(
                heavy_model_rmse
            )
            else None
        ),

    "warning":
        (
            "Coarse historical archive values "
            "are used as retrospective predictors. "
            "This is not operational forecast skill."
        )
}


joblib.dump(
    metadata,
    metadata_path
)


# ============================================================
# 15. SAVE METRICS
# ============================================================

metrics = pd.DataFrame([{

    "baseline_test_rmse":
        baseline_test_rmse,

    "model_test_rmse":
        test_rmse,

    "baseline_test_mae":
        baseline_test_mae,

    "model_test_mae":
        test_mae,

    "improvement_percent":
        improvement,

    "pod":
        pod,

    "far":
        far,

    "csi":
        csi,

    "heavy_baseline_rmse":
        heavy_baseline_rmse,

    "heavy_model_rmse":
        heavy_model_rmse,

    "heavy_baseline_mae":
        heavy_baseline_mae,

    "heavy_model_mae":
        heavy_model_mae,

}])


metrics.to_csv(
    METRICS_FILE,
    index=False
)


# ============================================================
# COMPLETE
# ============================================================

print(
    "\n========================================"
)

print(
    "CLEAN M3 TRAINING COMPLETE"
)

print(
    "========================================"
)

print(
    "Classifier:",
    classifier_path
)

print(
    "Regressor:",
    regressor_path
)

print(
    "Metadata:",
    metadata_path
)

print(
    "Predictions:",
    PREDICTIONS_FILE
)

print(
    "Metrics:",
    METRICS_FILE
)