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
# TERRAMIND M3 / V2 DOWNSCALING EXPERIMENT
# ============================================================
#
# Retrospective statistical downscaling prototype.
#
# IMPORTANT:
# coarse_block_history.csv is historical archive data,
# not an archived issued forecast.
#
# Therefore these results demonstrate the downscaling
# experiment, NOT operational forecast skill.
#
# Architecture:
#
# Stage 1:
#   Will it rain?
#
# Stage 2:
#   How much rain, given a wet case?
#
# Features:
#   common coarse block weather
#   +
#   Panchayat-specific geography / terrain
#   +
#   historical local context
#   +
#   seasonality
#
# Target:
#   CHIRPS Panchayat rainfall
#
# Temporal split:
#   Train:      2024-01-08 to 2024-08-31
#   Validation: 2024-09-01 to 2024-12-31
#   Test:       2025-01-01 onward
#
# ============================================================


# ============================================================
# SETTINGS
# ============================================================

DATA_FILE = (
    "data/raw/v2_downscaling_training_dataset.csv"
)

MODEL_DIR = "models"

METRICS_FILE = (
    "data/raw/v2_downscaling_metrics.csv"
)

PREDICTIONS_FILE = (
    "data/raw/v2_downscaling_predictions.csv"
)


TARGET = "chirps_rain_mm"

RAIN_THRESHOLD = 0.1

EVENT_THRESHOLD = 2.5


# ============================================================
# FEATURE SET
# ============================================================

FEATURES = [

    # --------------------------------------------------------
    # Coarse block information
    # --------------------------------------------------------

    "coarse_rain_mm",
    "coarse_tmax_c",
    "coarse_tmin_c",

    # --------------------------------------------------------
    # Panchayat spatial information
    # --------------------------------------------------------

    "latitude",
    "longitude",

    "elevation_dem_m",
    "slope_deg",
    "aspect_sin",
    "aspect_cos",
    "terrain_roughness_m",
    "relative_elevation_m",

    # --------------------------------------------------------
    # Local historical rainfall context
    # --------------------------------------------------------

    "rain_mm",

    "rain_lag_1",
    "rain_lag_2",
    "rain_lag_3",
    "rain_lag_7",

    "rain_3day_sum",
    "rain_7day_sum",

    # --------------------------------------------------------
    # Local historical temperature context
    # --------------------------------------------------------

    "tmax_c",

    "tmax_lag_1",
    "tmax_lag_2",
    "tmax_lag_7",

    "tmin_c",

    "tmin_lag_1",
    "tmin_lag_2",

    # --------------------------------------------------------
    # Seasonality
    # --------------------------------------------------------

    "month",
    "day_of_year",
    "day_of_year_sin",
    "day_of_year_cos",
]


# ============================================================
# 1. LOAD DATA
# ============================================================

print(
    "========================================"
)

print(
    "TERRAMIND M3 DOWNSCALING EXPERIMENT"
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
# 2. VALIDATE FEATURES
# ============================================================

missing_features = [
    feature
    for feature in FEATURES
    if feature not in df.columns
]


if missing_features:

    raise ValueError(
        "Missing required features:\n"
        +
        "\n".join(
            missing_features
        )
    )


if TARGET not in df.columns:

    raise ValueError(
        f"Missing target: {TARGET}"
    )


if df[
    FEATURES + [TARGET]
].isna().any().any():

    missing = (
        df[
            FEATURES + [TARGET]
        ]
        .isna()
        .sum()
    )

    raise ValueError(
        "Missing values detected:\n"
        +
        missing[
            missing > 0
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


train_mask = (
    df["date"]
    <= TRAIN_END
)

validation_mask = (
    (df["date"] >= VALIDATION_START)
    &
    (df["date"] <= VALIDATION_END)
)

test_mask = (
    df["date"]
    >= TEST_START
)


train = df.loc[
    train_mask
].copy()

validation = df.loc[
    validation_mask
].copy()

test = df.loc[
    test_mask
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
    "Training:",
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


# ============================================================
# 4. BASELINE — COARSE BLOCK VALUE
# ============================================================
#
# This is the critical comparison.
#
# We simply copy the coarse block rainfall to every Panchayat.
#
# The downscaling model must beat this baseline.
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


baseline_prediction = (
    test["coarse_rain_mm"]
    .to_numpy()
)

y_test = (
    test[TARGET]
    .to_numpy()
)


baseline_rmse = np.sqrt(
    mean_squared_error(
        y_test,
        baseline_prediction
    )
)

baseline_mae = (
    mean_absolute_error(
        y_test,
        baseline_prediction
    )
)


print(
    f"RMSE: {baseline_rmse:.2f} mm"
)

print(
    f"MAE:  {baseline_mae:.2f} mm"
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

y_validation_event = (
    validation[TARGET]
    > RAIN_THRESHOLD
).astype(int)

y_test_event = (
    test[TARGET]
    > RAIN_THRESHOLD
).astype(int)


rain_classifier = XGBClassifier(

    n_estimators=400,

    max_depth=6,

    learning_rate=0.05,

    subsample=0.9,

    colsample_bytree=0.9,

    objective="binary:logistic",

    eval_metric="logloss",

    random_state=42,

    n_jobs=-1

)


rain_classifier.fit(
    train[FEATURES],
    y_train_event
)


# ============================================================
# 6. STAGE 2 — WET-DAY RAIN AMOUNT
# ============================================================

print(
    "\n========================================"
)

print(
    "TRAINING RAIN AMOUNT MODEL"
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
        "No wet training observations."
    )


rain_regressor = XGBRegressor(

    n_estimators=600,

    max_depth=7,

    learning_rate=0.05,

    subsample=0.9,

    colsample_bytree=0.9,

    objective="reg:squarederror",

    random_state=42,

    n_jobs=-1

)


rain_regressor.fit(

    wet_train[FEATURES],

    np.log1p(
        wet_train[TARGET]
    )

)


# ============================================================
# 7. HELPER — GENERATE PREDICTIONS
# ============================================================

def predict_rain(
    data
):

    probability = (
        rain_classifier
        .predict_proba(
            data[FEATURES]
        )[:, 1]
    )


    wet_amount = np.expm1(
        rain_regressor.predict(
            data[FEATURES]
        )
    )


    final = np.where(
        probability >= 0.30,
        wet_amount,
        0.0
    )


    final = np.clip(
        final,
        0.0,
        None
    )


    return (
        probability,
        final
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


val_truth = (
    validation[TARGET]
    .to_numpy()
)


val_rmse = np.sqrt(
    mean_squared_error(
        val_truth,
        val_prediction
    )
)

val_mae = (
    mean_absolute_error(
        val_truth,
        val_prediction
    )
)


val_obs_event = (
    val_truth >= EVENT_THRESHOLD
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
    if (val_hits + val_misses)
    else 0.0
)

val_far = (
    val_false_alarms
    /
    (val_hits + val_false_alarms)
    if (val_hits + val_false_alarms)
    else 0.0
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
    else 0.0
)


print(
    f"RMSE: {val_rmse:.2f} mm"
)

print(
    f"MAE:  {val_mae:.2f} mm"
)

print(
    f"POD:  {val_pod:.2f}"
)

print(
    f"FAR:  {val_far:.2f}"
)

print(
    f"CSI:  {val_csi:.2f}"
)


# ============================================================
# 9. FINAL TEST
# ============================================================

print(
    "\n========================================"
)

print(
    "FINAL M3 TEST RESULTS"
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
        baseline_rmse
        -
        test_rmse
    )
    /
    baseline_rmse
    *
    100
)


# ------------------------------------------------------------
# Event metrics
# ------------------------------------------------------------

obs_event = (
    y_test
    >= EVENT_THRESHOLD
)

pred_event = (
    test_prediction
    >= EVENT_THRESHOLD
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
    if (hits + misses)
    else 0.0
)


far = (
    false_alarms
    /
    (hits + false_alarms)
    if (
        hits + false_alarms
    )
    else 0.0
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
    else 0.0
)


print(
    f"Baseline RMSE: {baseline_rmse:.2f} mm"
)

print(
    f"Model RMSE:    {test_rmse:.2f} mm"
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
# 10. HEAVY RAIN ANALYSIS
# ============================================================

print(
    "\n========================================"
)

print(
    "HEAVY RAIN ANALYSIS"
)

print(
    "========================================"
)


heavy_mask = (
    y_test
    >= 25.0
)


if heavy_mask.sum() > 0:

    heavy_truth = (
        y_test[
            heavy_mask
        ]
    )

    heavy_pred = (
        test_prediction[
            heavy_mask
        ]
    )

    heavy_baseline = (
        baseline_prediction[
            heavy_mask
        ]
    )


    heavy_rmse = np.sqrt(
        mean_squared_error(
            heavy_truth,
            heavy_pred
        )
    )


    heavy_mae = (
        mean_absolute_error(
            heavy_truth,
            heavy_pred
        )
    )


    heavy_baseline_rmse = (
        np.sqrt(
            mean_squared_error(
                heavy_truth,
                heavy_baseline
            )
        )
    )


    heavy_baseline_mae = (
        mean_absolute_error(
            heavy_truth,
            heavy_baseline
        )
    )


    print(
        "Heavy cases:",
        len(heavy_truth)
    )

    print(
        f"Baseline RMSE: "
        f"{heavy_baseline_rmse:.2f} mm"
    )

    print(
        f"Model RMSE:    "
        f"{heavy_rmse:.2f} mm"
    )

    print(
        f"Baseline MAE:  "
        f"{heavy_baseline_mae:.2f} mm"
    )

    print(
        f"Model MAE:     "
        f"{heavy_mae:.2f} mm"
    )

else:

    heavy_rmse = np.nan

    heavy_mae = np.nan

    heavy_baseline_rmse = np.nan

    heavy_baseline_mae = np.nan

    print(
        "No heavy-rain cases."
    )


# ============================================================
# 11. PERFORMANCE BY PANCHAYAT
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


panchayat_results = []


for panchayat_id, group in (
    test.groupby("panchayat_id")
):

    idx = group.index

    truth = (
        group[TARGET]
        .to_numpy()
    )

    pred = (
        test_prediction[
            test.index.get_indexer(idx)
        ]
    )


    rmse = np.sqrt(
        mean_squared_error(
            truth,
            pred
        )
    )

    mae = (
        mean_absolute_error(
            truth,
            pred
        )
    )


    panchayat_results.append({

        "panchayat_id":
            panchayat_id,

        "n":
            len(group),

        "rmse":
            rmse,

        "mae":
            mae

    })


panchayat_results = (
    pd.DataFrame(
        panchayat_results
    )
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
    "TOP FEATURES"
)

print(
    "========================================"
)


importance = pd.DataFrame({

    "feature":
        FEATURES,

    "importance":
        rain_regressor
        .feature_importances_

})


importance = (
    importance
    .sort_values(
        "importance",
        ascending=False
    )
    .reset_index(drop=True)
)


print(
    importance
    .head(20)
    .round(6)
    .to_string(index=False)
)


# ============================================================
# 13. SAVE PREDICTIONS
# ============================================================

prediction_output = test[
    [
        "date",
        "panchayat_id",
        "panchayat_name",
        "coarse_rain_mm",
        "coarse_tmax_c",
        "coarse_tmin_c",
        TARGET
    ]
].copy()


prediction_output = (
    prediction_output
    .rename(
        columns={
            TARGET:
                "actual_rain_mm"
        }
    )
)


prediction_output[
    "rain_probability"
] = test_probability


prediction_output[
    "predicted_rain_mm"
] = test_prediction


prediction_output[
    "baseline_rain_mm"
] = baseline_prediction


prediction_output[
    "absolute_error"
] = (
    np.abs(
        prediction_output[
            "actual_rain_mm"
        ]
        -
        prediction_output[
            "predicted_rain_mm"
        ]
    )
)


prediction_output.to_csv(
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


classifier_path = (
    os.path.join(
        MODEL_DIR,
        "v2_downscaling_rain_classifier.pkl"
    )
)


regressor_path = (
    os.path.join(
        MODEL_DIR,
        "v2_downscaling_rain_regressor.pkl"
    )
)


joblib.dump(
    rain_classifier,
    classifier_path
)


joblib.dump(
    rain_regressor,
    regressor_path
)


# ============================================================
# 15. SAVE METADATA
# ============================================================

metadata = {

    "model_version":
        "M3-downscaling-v2",

    "experiment_type":
        "retrospective_statistical_downscaling",

    "coarse_source":
        "Open-Meteo historical archive",

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

    "baseline_rmse":
        float(
            baseline_rmse
        ),

    "baseline_mae":
        float(
            baseline_mae
        ),

    "test_rmse":
        float(
            test_rmse
        ),

    "test_mae":
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

    "heavy_rmse":
        (
            float(
                heavy_rmse
            )
            if not np.isnan(
                heavy_rmse
            )
            else None
        ),

    "heavy_baseline_mae":
        (
            float(
                heavy_baseline_mae
            )
            if not np.isnan(
                heavy_baseline_mae
            )
            else None
        ),

    "heavy_mae":
        (
            float(
                heavy_mae
            )
            if not np.isnan(
                heavy_mae
            )
            else None
        ),

    "warning":
        (
            "Historical archive data is a "
            "retrospective proxy for the coarse "
            "forecast input. These results do "
            "not represent operational forecast "
            "skill until trained/evaluated using "
            "archived issued forecasts."
        )
}


metadata_path = (
    os.path.join(
        MODEL_DIR,
        "v2_downscaling_metadata.pkl"
    )
)


joblib.dump(
    metadata,
    metadata_path
)


# ============================================================
# 16. SAVE METRICS TABLE
# ============================================================

metrics = pd.DataFrame([{

    "baseline_rmse":
        baseline_rmse,

    "baseline_mae":
        baseline_mae,

    "model_rmse":
        test_rmse,

    "model_mae":
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
        heavy_rmse,

    "heavy_baseline_mae":
        heavy_baseline_mae,

    "heavy_model_mae":
        heavy_mae,

}])


metrics.to_csv(
    METRICS_FILE,
    index=False
)


# ============================================================
# 17. COMPLETE
# ============================================================

print(
    "\n========================================"
)

print(
    "M3 DOWNSCALING TRAINING COMPLETE"
)

print(
    "========================================"
)

print(
    "Models saved:"
)

print(
    classifier_path
)

print(
    regressor_path
)

print(
    metadata_path
)

print(
    "\nPredictions:"
)

print(
    PREDICTIONS_FILE
)

print(
    "\nMetrics:"
)

print(
    METRICS_FILE
)