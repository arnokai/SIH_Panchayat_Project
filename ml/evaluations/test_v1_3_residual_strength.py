from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error


BASE_DIR = Path(__file__).resolve().parent.parent

DATA_FILE = (
    BASE_DIR
    / "data"
    / "raw"
    / "v1_2_training_dataset.csv"
)

RESIDUAL_MODEL_FILE = (
    BASE_DIR
    / "models"
    / "v1_3_rain_residual.pkl"
)


CALIBRATION_FEATURES = [
    "imerg_rain_mm",
    "imd_rain_mm",
    "rain_mm"
]

FEATURES = [
    "latitude",
    "longitude",
    "elevation",
    "distance_to_river_m",
    "elevation_dem_m",
    "slope_deg",
    "aspect_sin",
    "aspect_cos",
    "terrain_roughness_m",
    "relative_elevation_m",
    "rain_lag_1",
    "rain_lag_2",
    "rain_lag_3",
    "rain_lag_7",
    "rain_3day_sum",
    "rain_7day_sum",
    "tmax_lag_1",
    "tmax_lag_2",
    "tmax_lag_7",
    "tmin_lag_1",
    "tmin_lag_2",
    "imerg_rain_mm",
    "imd_rain_mm",
    "day_of_year_sin",
    "day_of_year_cos",
]


TARGET = "chirps_rain_mm"


# ==========================================
# LOAD
# ==========================================

df = pd.read_csv(
    DATA_FILE,
    parse_dates=["date"]
)

residual_model = joblib.load(
    RESIDUAL_MODEL_FILE
)


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


# ==========================================
# FIT CALIBRATION ON TRAIN ONLY
# ==========================================

calibration = LinearRegression()

calibration.fit(
    train[CALIBRATION_FEATURES],
    train[TARGET]
)


# ==========================================
# BASE PREDICTIONS
# ==========================================

for dataset in [validation, test]:

    dataset["calibrated"] = np.maximum(
        calibration.predict(
            dataset[CALIBRATION_FEATURES]
        ),
        0.0
    )

    dataset["residual"] = (
        residual_model.predict(
            dataset[FEATURES]
        )
    )


# ==========================================
# METRIC FUNCTION
# ==========================================

def calculate_metrics(
    actual,
    prediction
):
    rmse = np.sqrt(
        mean_squared_error(
            actual,
            prediction
        )
    )

    mae = mean_absolute_error(
        actual,
        prediction
    )

    heavy_mask = actual >= 25

    heavy_rmse = np.sqrt(
        mean_squared_error(
            actual[heavy_mask],
            prediction[heavy_mask]
        )
    )

    heavy_mae = mean_absolute_error(
        actual[heavy_mask],
        prediction[heavy_mask]
    )

    return (
        rmse,
        mae,
        heavy_rmse,
        heavy_mae
    )


# ==========================================
# TEST DIFFERENT ALPHA VALUES
# ==========================================

alphas = np.arange(
    0.0,
    1.01,
    0.10
)


results = []


for alpha in alphas:

    validation_prediction = np.maximum(
        validation["calibrated"]
        +
        alpha
        *
        validation["residual"],
        0.0
    )

    test_prediction = np.maximum(
        test["calibrated"]
        +
        alpha
        *
        test["residual"],
        0.0
    )


    v_rmse, v_mae, v_heavy_rmse, v_heavy_mae = (
        calculate_metrics(
            validation[TARGET].values,
            validation_prediction.values
        )
    )


    t_rmse, t_mae, t_heavy_rmse, t_heavy_mae = (
        calculate_metrics(
            test[TARGET].values,
            test_prediction.values
        )
    )


    results.append({

        "alpha":
            round(float(alpha), 2),

        "validation_rmse":
            v_rmse,

        "validation_mae":
            v_mae,

        "validation_heavy_rmse":
            v_heavy_rmse,

        "validation_heavy_mae":
            v_heavy_mae,

        "test_rmse":
            t_rmse,

        "test_mae":
            t_mae,

        "test_heavy_rmse":
            t_heavy_rmse,

        "test_heavy_mae":
            t_heavy_mae
    })


results_df = pd.DataFrame(
    results
)


# ==========================================
# SELECT ALPHA USING VALIDATION ONLY
# ==========================================

best_row = results_df.loc[
    results_df["validation_rmse"].idxmin()
]


best_alpha = float(
    best_row["alpha"]
)


print("========================================")
print("V1.3 RESIDUAL STRENGTH EXPERIMENT")
print("========================================")

print("\nValidation results:")

print(
    results_df[
        [
            "alpha",
            "validation_rmse",
            "validation_mae",
            "validation_heavy_rmse"
        ]
    ]
    .round(2)
    .to_string(index=False)
)


print("\n========================================")
print(
    f"SELECTED ALPHA: {best_alpha:.2f}"
)
print("========================================")

selected_test = results_df[
    results_df["alpha"] == best_alpha
].iloc[0]


print("\nTest performance at selected alpha:")

print(
    f"Test RMSE:        "
    f"{selected_test['test_rmse']:.2f} mm"
)

print(
    f"Test MAE:         "
    f"{selected_test['test_mae']:.2f} mm"
)

print(
    f"Heavy RMSE:       "
    f"{selected_test['test_heavy_rmse']:.2f} mm"
)

print(
    f"Heavy MAE:        "
    f"{selected_test['test_heavy_mae']:.2f} mm"
)


# ==========================================
# SAVE
# ==========================================

output_file = (
    BASE_DIR
    / "data"
    / "raw"
    / "v1_3_residual_strength_results.csv"
)

results_df.to_csv(
    output_file,
    index=False
)


print("\nSaved:")
print(output_file)