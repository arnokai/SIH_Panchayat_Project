from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.linear_model import LinearRegression
from sklearn.metrics import (
    mean_squared_error,
    mean_absolute_error
)

from xgboost import XGBRegressor


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
print("TERRAMIND V1.3 RESIDUAL MODEL")
print("========================================")

print(
    "Loaded rows:",
    len(df)
)


# ==========================================
# 3. FEATURES
# ==========================================
#
# These are information available on day T.
#
# CHIRPS T+1 is the target and MUST NOT
# appear as an input.
# ==========================================

FEATURES = [

    # Geography
    "latitude",
    "longitude",
    "elevation",
    "distance_to_river_m",

    # DEM terrain
    "elevation_dem_m",
    "slope_deg",
    "aspect_sin",
    "aspect_cos",
    "terrain_roughness_m",
    "relative_elevation_m",

    # Previous rainfall
    "rain_lag_1",
    "rain_lag_2",
    "rain_lag_3",
    "rain_lag_7",
    "rain_3day_sum",
    "rain_7day_sum",

    # Previous temperature
    "tmax_lag_1",
    "tmax_lag_2",
    "tmax_lag_7",
    "tmin_lag_1",
    "tmin_lag_2",

    # Gridded rainfall predictors
    "imerg_rain_mm",
    "imd_rain_mm",

    # Seasonal cycle
    "day_of_year_sin",
    "day_of_year_cos"
]


TARGET = "chirps_rain_mm"


# ==========================================
# 4. VALIDATE COLUMNS
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
    "Features:",
    len(FEATURES)
)

print(
    "Target:",
    TARGET
)


# ==========================================
# 5. VERIFY T → T+1
# ==========================================

if (
    (
        df["target_date"]
        -
        df["date"]
    )
    !=
    pd.Timedelta(days=1)
).any():

    raise ValueError(
        "Invalid target alignment."
    )


print(
    "Target alignment: T → T+1 ✅"
)


# ==========================================
# 6. TEMPORAL SPLIT
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
# 7. CALIBRATION INPUTS
# ==========================================
#
# These are the three rainfall products
# available on predictor day T.
# ==========================================

CALIBRATION_FEATURES = [
    "imerg_rain_mm",
    "imd_rain_mm",
    "rain_mm"
]


# ==========================================
# 8. TRAIN CALIBRATION MODEL
# ==========================================
#
# IMPORTANT:
# Only the training period is used to fit
# the linear calibration.
# ==========================================

calibration = LinearRegression()

calibration.fit(
    train[CALIBRATION_FEATURES],
    train[TARGET]
)


# ==========================================
# 9. CALIBRATION PREDICTIONS
# ==========================================

train["calibrated_rain"] = np.maximum(
    calibration.predict(
        train[CALIBRATION_FEATURES]
    ),
    0.0
)

validation["calibrated_rain"] = np.maximum(
    calibration.predict(
        validation[CALIBRATION_FEATURES]
    ),
    0.0
)

test["calibrated_rain"] = np.maximum(
    calibration.predict(
        test[CALIBRATION_FEATURES]
    ),
    0.0
)


# ==========================================
# 10. CALIBRATION RESIDUAL
# ==========================================
#
# residual = actual CHIRPS - calibrated
#
# This is what the XGBoost model learns.
# ==========================================

train["residual"] = (
    train[TARGET]
    -
    train["calibrated_rain"]
)

validation["residual"] = (
    validation[TARGET]
    -
    validation["calibrated_rain"]
)


print("\n========================================")
print("CALIBRATION MODEL")
print("========================================")

print(
    "Coefficients:"
)

for feature, coefficient in zip(
    CALIBRATION_FEATURES,
    calibration.coef_
):

    print(
        f"{feature:<20}"
        f"{coefficient:.4f}"
    )


print(
    f"\nIntercept: "
    f"{calibration.intercept_:.4f}"
)


# ==========================================
# 11. BASELINE METRICS
# ==========================================

def metrics(
    actual,
    predicted
):

    rmse = np.sqrt(
        mean_squared_error(
            actual,
            predicted
        )
    )

    mae = mean_absolute_error(
        actual,
        predicted
    )

    return rmse, mae


validation_cal_rmse, validation_cal_mae = metrics(
    validation[TARGET],
    validation["calibrated_rain"]
)


test_cal_rmse, test_cal_mae = metrics(
    test[TARGET],
    test["calibrated_rain"]
)


print("\n========================================")
print("CALIBRATION BASELINE")
print("========================================")

print(
    f"Validation RMSE: "
    f"{validation_cal_rmse:.2f} mm"
)

print(
    f"Validation MAE:  "
    f"{validation_cal_mae:.2f} mm"
)

print(
    f"Test RMSE:       "
    f"{test_cal_rmse:.2f} mm"
)

print(
    f"Test MAE:        "
    f"{test_cal_mae:.2f} mm"
)


# ==========================================
# 12. RESIDUAL MODEL
# ==========================================

print("\n========================================")
print("TRAINING RESIDUAL XGBOOST")
print("========================================")


residual_model = XGBRegressor(

    n_estimators=250,

    max_depth=4,

    learning_rate=0.03,

    min_child_weight=5,

    subsample=0.8,

    colsample_bytree=0.8,

    reg_alpha=0.1,

    reg_lambda=1.0,

    random_state=42,

    objective="reg:squarederror",

    n_jobs=-1
)


residual_model.fit(

    train[FEATURES],

    train["residual"]
)


# ==========================================
# 13. VALIDATION RESIDUAL PREDICTION
# ==========================================

validation["predicted_residual"] = (
    residual_model.predict(
        validation[FEATURES]
    )
)


ALPHA = 0.10

validation["hybrid_rain"] = np.maximum(

    validation["calibrated_rain"]
    +
    ALPHA * validation["predicted_residual"],

    0.0
)

# ==========================================
# 14. VALIDATION PERFORMANCE
# ==========================================

validation_hybrid_rmse, validation_hybrid_mae = metrics(
    validation[TARGET],
    validation["hybrid_rain"]
)


print("\n========================================")
print("VALIDATION RESULTS")
print("========================================")

print(
    f"Calibration RMSE: "
    f"{validation_cal_rmse:.2f} mm"
)

print(
    f"Hybrid RMSE:      "
    f"{validation_hybrid_rmse:.2f} mm"
)

print(
    f"Calibration MAE:  "
    f"{validation_cal_mae:.2f} mm"
)

print(
    f"Hybrid MAE:       "
    f"{validation_hybrid_mae:.2f} mm"
)


# ==========================================
# 15. FINAL TEST
# ==========================================

test["predicted_residual"] = (
    residual_model.predict(
        test[FEATURES]
    )
)


ALPHA = 0.10

test["hybrid_rain"] = np.maximum(

    test["calibrated_rain"]
    +
    ALPHA * test["predicted_residual"],

    0.0
)

test_rmse, test_mae = metrics(
    test[TARGET],
    test["hybrid_rain"]
)


test_improvement = (

    (
        test_cal_rmse
        -
        test_rmse
    )
    /
    test_cal_rmse
) * 100


# ==========================================
# 16. RAIN EVENT METRICS
# ==========================================

def event_metrics(
    actual,
    predicted
):

    actual_event = (
        actual >= 2.5
    )

    predicted_event = (
        predicted >= 2.5
    )

    hits = np.sum(
        actual_event
        &
        predicted_event
    )

    misses = np.sum(
        actual_event
        &
        ~predicted_event
    )

    false_alarms = np.sum(
        ~actual_event
        &
        predicted_event
    )

    pod = (
        hits
        /
        (hits + misses)
        if hits + misses
        else 0.0
    )

    far = (
        false_alarms
        /
        (hits + false_alarms)
        if hits + false_alarms
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

    return (
        int(hits),
        int(misses),
        int(false_alarms),
        float(pod),
        float(far),
        float(csi)
    )


hits, misses, false_alarms, pod, far, csi = (
    event_metrics(
        test[TARGET].values,
        test["hybrid_rain"].values
    )
)


# ==========================================
# 17. HEAVY RAIN METRICS
# ==========================================

heavy_mask = (
    test[TARGET] >= 25
)


heavy_cal_rmse = np.sqrt(
    mean_squared_error(
        test.loc[
            heavy_mask,
            TARGET
        ],
        test.loc[
            heavy_mask,
            "calibrated_rain"
        ]
    )
)


heavy_hybrid_rmse = np.sqrt(
    mean_squared_error(
        test.loc[
            heavy_mask,
            TARGET
        ],
        test.loc[
            heavy_mask,
            "hybrid_rain"
        ]
    )
)


heavy_cal_mae = (
    mean_absolute_error(
        test.loc[
            heavy_mask,
            TARGET
        ],
        test.loc[
            heavy_mask,
            "calibrated_rain"
        ]
    )
)


heavy_hybrid_mae = (
    mean_absolute_error(
        test.loc[
            heavy_mask,
            TARGET
        ],
        test.loc[
            heavy_mask,
            "hybrid_rain"
        ]
    )
)


# ==========================================
# 18. FINAL RESULTS
# ==========================================

print("\n========================================")
print("FINAL V1.3 TEST RESULTS")
print("========================================")

print(
    f"Calibration RMSE: "
    f"{test_cal_rmse:.2f} mm"
)

print(
    f"Hybrid RMSE:      "
    f"{test_rmse:.2f} mm"
)

print(
    f"Calibration MAE:  "
    f"{test_cal_mae:.2f} mm"
)

print(
    f"Hybrid MAE:       "
    f"{test_mae:.2f} mm"
)

print(
    f"Improvement over calibration: "
    f"{test_improvement:.1f}%"
)


print("\nRain event metrics:")

print(
    f"Hits:          {hits}"
)

print(
    f"Misses:        {misses}"
)

print(
    f"False alarms:  {false_alarms}"
)

print(
    f"POD:           {pod:.2f}"
)

print(
    f"FAR:           {far:.2f}"
)

print(
    f"CSI:           {csi:.2f}"
)


print("\nHeavy rainfall (>=25 mm):")

print(
    f"Calibration RMSE: "
    f"{heavy_cal_rmse:.2f} mm"
)

print(
    f"Hybrid RMSE:      "
    f"{heavy_hybrid_rmse:.2f} mm"
)

print(
    f"Calibration MAE:  "
    f"{heavy_cal_mae:.2f} mm"
)

print(
    f"Hybrid MAE:       "
    f"{heavy_hybrid_mae:.2f} mm"
)


# ==========================================
# 19. FEATURE IMPORTANCE
# ==========================================

importance = pd.DataFrame({

    "feature":
        FEATURES,

    "importance":
        residual_model
        .feature_importances_

}).sort_values(
    "importance",
    ascending=False
)


print("\n========================================")
print("TOP RESIDUAL MODEL FEATURES")
print("========================================")

print(
    importance
    .head(15)
    .to_string(
        index=False
    )
)


# ==========================================
# 20. SAVE MODELS
# ==========================================

calibration_path = (
    MODEL_DIR
    / "v1_3_rain_calibration.pkl"
)

residual_path = (
    MODEL_DIR
    / "v1_3_rain_residual.pkl"
)


joblib.dump(
    calibration,
    calibration_path
)

joblib.dump(
    residual_model,
    residual_path
)


# ==========================================
# 21. SAVE METADATA
# ==========================================

metadata = {

    "model_version":
        "v1.3",

    "architecture":
        "linear rainfall calibration "
        "+ XGBoost residual correction",

    "target":
        "CHIRPS rainfall at T+1",


    "residual_alpha":
        0.10,

    "features":
        FEATURES,

    "calibration_features":
        CALIBRATION_FEATURES,

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

    "test_calibration_rmse":
        float(
            test_cal_rmse
        ),

    "test_calibration_mae":
        float(
            test_cal_mae
        ),

    "test_hybrid_rmse":
        float(
            test_rmse
        ),

    "test_hybrid_mae":
        float(
            test_mae
        ),

    "improvement_over_calibration_percent":
        float(
            test_improvement
        ),

    "pod":
        float(
            pod
        ),

    "far":
        float(
            far
        ),

    "csi":
        float(
            csi
        ),

    "heavy_calibration_rmse":
        float(
            heavy_cal_rmse
        ),

    "heavy_hybrid_rmse":
        float(
            heavy_hybrid_rmse
        ),

    "heavy_calibration_mae":
        float(
            heavy_cal_mae
        ),

    "heavy_hybrid_mae":
        float(
            heavy_hybrid_mae
        )
}


metadata_path = (
    MODEL_DIR
    / "v1_3_metadata.pkl"
)


joblib.dump(
    metadata,
    metadata_path
)


# ==========================================
# 22. SAVE FEATURE IMPORTANCE
# ==========================================

importance.to_csv(
    MODEL_DIR
    / "v1_3_residual_feature_importance.csv",
    index=False
)


# ==========================================
# 23. SAVE TEST PREDICTIONS
# ==========================================

prediction_columns = [
    "date",
    "target_date",
    "panchayat_id",
    "panchayat_name",
    TARGET,
    "calibrated_rain",
    "predicted_residual",
    "hybrid_rain"
]


test[
    prediction_columns
].to_csv(
    BASE_DIR
    / "data"
    / "raw"
    / "v1_3_predictions.csv",
    index=False
)


# ==========================================
# 24. COMPLETE
# ==========================================

print("\n========================================")
print("V1.3 MODELS SAVED")
print("========================================")

print(
    calibration_path
)

print(
    residual_path
)

print(
    metadata_path
)

print(
    BASE_DIR
    / "data"
    / "raw"
    / "v1_3_predictions.csv"
)

print("\nV1.3 TRAINING COMPLETE.")