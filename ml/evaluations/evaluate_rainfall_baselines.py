from pathlib import Path

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


df = pd.read_csv(DATA_FILE)

df["date"] = pd.to_datetime(df["date"])


# ==========================================
# TEST PERIOD
# ==========================================

test = df[
    df["date"] >= "2025-01-01"
].copy()


TARGET = "chirps_rain_mm"


# ==========================================
# BASELINES
# ==========================================

baselines = {

    "IMERG":
        test["imerg_rain_mm"],

    "IMD":
        test["imd_rain_mm"],

    "Open-Meteo":
        test["rain_mm"],

    "Average of IMERG + Open-Meteo":
        (
            test["imerg_rain_mm"]
            +
            test["rain_mm"]
        ) / 2,

    "Average of IMERG + IMD":
        (
            test["imerg_rain_mm"]
            +
            test["imd_rain_mm"]
        ) / 2,

    "Average of all 3":
        (
            test["imerg_rain_mm"]
            +
            test["imd_rain_mm"]
            +
            test["rain_mm"]
        ) / 3
}


print("========================================")
print("RAINFALL BASELINE COMPARISON")
print("========================================")

print(
    "Test rows:",
    len(test)
)


for name, prediction in baselines.items():

    rmse = np.sqrt(
        mean_squared_error(
            test[TARGET],
            prediction
        )
    )

    mae = mean_absolute_error(
        test[TARGET],
        prediction
    )

    print(
        f"{name:<32}"
        f"RMSE={rmse:7.2f} mm   "
        f"MAE={mae:7.2f} mm"
    )


# ==========================================
# LINEAR CALIBRATION
# ==========================================
#
# Train calibration only on 2024.
# Evaluate on untouched 2025.
# ==========================================

train = df[
    df["date"] < "2025-01-01"
].copy()


INPUTS = [
    "imerg_rain_mm",
    "imd_rain_mm",
    "rain_mm"
]


X_train = train[INPUTS]

y_train = train[TARGET]


X_test = test[INPUTS]

y_test = test[TARGET]


model = LinearRegression()

model.fit(
    X_train,
    y_train
)


prediction = model.predict(
    X_test
)


prediction = np.maximum(
    prediction,
    0
)


rmse = np.sqrt(
    mean_squared_error(
        y_test,
        prediction
    )
)

mae = mean_absolute_error(
    y_test,
    prediction
)


print("\n========================================")
print("LINEAR CALIBRATION")
print("========================================")

print(
    f"RMSE: {rmse:.2f} mm"
)

print(
    f"MAE:  {mae:.2f} mm"
)


print("\nCoefficients:")

for feature, coef in zip(
    INPUTS,
    model.coef_
):

    print(
        f"{feature:<20} "
        f"{coef:.4f}"
    )


print(
    f"\nIntercept: "
    f"{model.intercept_:.4f}"
)


# ==========================================
# HEAVY RAIN PERFORMANCE
# ==========================================

heavy_mask = (
    y_test >= 25
)


heavy_rmse = np.sqrt(
    mean_squared_error(
        y_test[heavy_mask],
        prediction[heavy_mask]
    )
)

heavy_mae = mean_absolute_error(
    y_test[heavy_mask],
    prediction[heavy_mask]
)


print("\n========================================")
print("HEAVY RAIN CALIBRATION")
print("========================================")

print(
    "Heavy cases:",
    int(heavy_mask.sum())
)

print(
    f"RMSE: {heavy_rmse:.2f} mm"
)

print(
    f"MAE:  {heavy_mae:.2f} mm"
)