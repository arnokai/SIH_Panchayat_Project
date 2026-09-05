import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from sklearn.metrics import mean_squared_error, mean_absolute_error


# ============================================================
# CONFIG
# ============================================================

DATA_PATH = Path("data/raw/v1_2_training_dataset.csv")
MODEL_DIR = Path("models")

CLASSIFIER_PATH = MODEL_DIR / "v1_2_rain_classifier.pkl"
REGRESSOR_PATH = MODEL_DIR / "v1_2_rain_regressor.pkl"

OUTPUT_PATH = Path("data/raw/v1_2_evaluation_predictions.csv")


# ============================================================
# LOAD DATA + MODELS
# ============================================================

print("=" * 40)
print("TERRAMIND V1.2 ERROR ANALYSIS")
print("=" * 40)

df = pd.read_csv(DATA_PATH)

classifier = joblib.load(CLASSIFIER_PATH)
regressor = joblib.load(REGRESSOR_PATH)

print(f"Loaded rows: {len(df)}")


# ============================================================
# DETERMINE FEATURES
# ============================================================

# Use the same features that are available to the models.
# Remove identifiers, dates and target columns.

excluded = {
    "date",
    "target_date",
    "panchayat_id",
    "panchayat_name",
    "chirps_rain_mm",
}

features = [
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

X = df[features]
y = df["chirps_rain_mm"]


# ============================================================
# TEST SET
# ============================================================

# Same temporal split as the V1.2 training pipeline.

dates = pd.to_datetime(df["date"])

test_mask = dates >= pd.Timestamp("2025-01-01")

test = df.loc[test_mask].copy()
X_test = test[features]

print("Evaluation features:", len(features))
print(features)

y_test = test["chirps_rain_mm"]


print(f"Test rows: {len(test)}")
print(
    f"Test period: "
    f"{test['date'].min()} to {test['date'].max()}"
)


# ============================================================
# PREDICTION
# ============================================================

print("\nGenerating predictions...")

rain_probability = classifier.predict_proba(X_test)[:, 1]

# The V1.2 pipeline selected 0.30 as its validation threshold.
threshold = 0.30

rain_event = rain_probability >= threshold

amount_prediction = regressor.predict(X_test)

# If classifier says no rain, prediction becomes zero.
prediction = np.where(rain_event, amount_prediction, 0.0)

# Rainfall cannot physically be negative.
prediction = np.maximum(prediction, 0.0)


test["actual"] = y_test.values
test["predicted"] = prediction
test["rain_probability"] = rain_probability
test["predicted_rain_event"] = rain_event.astype(int)

test["error"] = test["predicted"] - test["actual"]
test["absolute_error"] = np.abs(test["error"])

test["squared_error"] = test["error"] ** 2


# ============================================================
# OVERALL METRICS
# ============================================================

rmse = np.sqrt(mean_squared_error(test["actual"], test["predicted"]))
mae = mean_absolute_error(test["actual"], test["predicted"])

print("\n" + "=" * 40)
print("OVERALL TEST PERFORMANCE")
print("=" * 40)

print(f"RMSE: {rmse:.2f} mm")
print(f"MAE:  {mae:.2f} mm")


# ============================================================
# PERFORMANCE BY RAINFALL INTENSITY
# ============================================================

print("\n" + "=" * 40)
print("PERFORMANCE BY ACTUAL RAINFALL")
print("=" * 40)

ranges = [
    ("0 mm", test["actual"] == 0),
    ("> 0 mm", test["actual"] > 0),
    ("> 5 mm", test["actual"] > 5),
    ("> 10 mm", test["actual"] > 10),
    ("> 25 mm", test["actual"] > 25),
    ("> 50 mm", test["actual"] > 50),
]

for name, mask in ranges:

    subset = test.loc[mask]

    if len(subset) == 0:
        continue

    subset_rmse = np.sqrt(
        mean_squared_error(
            subset["actual"],
            subset["predicted"]
        )
    )

    subset_mae = mean_absolute_error(
        subset["actual"],
        subset["predicted"]
    )

    print(
        f"{name:<8} "
        f"N={len(subset):4d}  "
        f"RMSE={subset_rmse:6.2f}  "
        f"MAE={subset_mae:6.2f}"
    )


# ============================================================
# RAIN EVENT DETECTION
# ============================================================

print("\n" + "=" * 40)
print("RAIN EVENT DETECTION")
print("=" * 40)

actual_event = test["actual"] > 0
pred_event = test["predicted_rain_event"] == 1

hits = int((actual_event & pred_event).sum())
misses = int((actual_event & ~pred_event).sum())
false_alarms = int((~actual_event & pred_event).sum())
correct_negatives = int((~actual_event & ~pred_event).sum())

pod = hits / (hits + misses) if hits + misses else 0
far = false_alarms / (hits + false_alarms) if hits + false_alarms else 0
csi = hits / (hits + misses + false_alarms) if (
    hits + misses + false_alarms
) else 0

print(f"Hits:             {hits}")
print(f"Misses:           {misses}")
print(f"False alarms:     {false_alarms}")
print(f"Correct negatives:{correct_negatives}")

print(f"POD:  {pod:.2f}")
print(f"FAR:  {far:.2f}")
print(f"CSI:  {csi:.2f}")


# ============================================================
# PANCHAYAT PERFORMANCE
# ============================================================

print("\n" + "=" * 40)
print("PERFORMANCE BY PANCHAYAT")
print("=" * 40)

for name, group in test.groupby("panchayat_name"):

    group_rmse = np.sqrt(
        mean_squared_error(
            group["actual"],
            group["predicted"]
        )
    )

    group_mae = mean_absolute_error(
        group["actual"],
        group["predicted"]
    )

    print(
        f"{name:<15} "
        f"N={len(group):3d}  "
        f"RMSE={group_rmse:6.2f}  "
        f"MAE={group_mae:6.2f}"
    )


# ============================================================
# MONTHLY PERFORMANCE
# ============================================================

print("\n" + "=" * 40)
print("PERFORMANCE BY MONTH")
print("=" * 40)

test["month"] = pd.to_datetime(test["date"]).dt.month

for month, group in test.groupby("month"):

    month_rmse = np.sqrt(
        mean_squared_error(
            group["actual"],
            group["predicted"]
        )
    )

    month_mae = mean_absolute_error(
        group["actual"],
        group["predicted"]
    )

    print(
        f"Month {month:02d}: "
        f"N={len(group):3d}  "
        f"RMSE={month_rmse:6.2f}  "
        f"MAE={month_mae:6.2f}"
    )


# ============================================================
# BIGGEST MISSED EVENTS
# ============================================================

print("\n" + "=" * 40)
print("BIGGEST MISSED RAIN EVENTS")
print("=" * 40)

missed = test[
    (test["actual"] > 0)
    & (test["predicted_rain_event"] == 0)
].copy()

missed = missed.sort_values(
    "actual",
    ascending=False
)

if len(missed) > 0:

    print(
        missed[
            [
                "date",
                "panchayat_id",
                "panchayat_name",
                "actual",
                "predicted",
                "rain_probability",
            ]
        ]
        .head(15)
        .to_string(index=False)
    )

else:
    print("No missed rain events.")


# ============================================================
# BIGGEST OVERPREDICTIONS
# ============================================================

print("\n" + "=" * 40)
print("BIGGEST OVERPREDICTIONS")
print("=" * 40)

over = test.sort_values(
    "error",
    ascending=False
)

print(
    over[
        [
            "date",
            "panchayat_id",
            "panchayat_name",
            "actual",
            "predicted",
            "error",
        ]
    ]
    .head(15)
    .to_string(index=False)
)


# ============================================================
# BIGGEST UNDERPREDICTIONS
# ============================================================

print("\n" + "=" * 40)
print("BIGGEST UNDERPREDICTIONS")
print("=" * 40)

under = test.sort_values(
    "error",
    ascending=True
)

print(
    under[
        [
            "date",
            "panchayat_id",
            "panchayat_name",
            "actual",
            "predicted",
            "error",
        ]
    ]
    .head(15)
    .to_string(index=False)
)


# ============================================================
# SAVE PREDICTIONS
# ============================================================

test.to_csv(
    OUTPUT_PATH,
    index=False
)

print("\n" + "=" * 40)
print("EVALUATION COMPLETE")
print("=" * 40)

print(f"Saved predictions:")
print(OUTPUT_PATH)