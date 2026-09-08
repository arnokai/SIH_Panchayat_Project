#!/usr/bin/env python3
"""
TerraMind — Statewide Two-Stage Hurdle Downscaling ML Pipeline
Problem Statement: SIH26074 (Ministry of Earth Sciences)

Architecture:
  Stage 1: Binary Rain Occurrence Classifier (HistGradientBoostingClassifier)
  Stage 2: Continuous Precipitation Regressor (P50 Median)
  Stage 3: Quantile Uncertainty Bounds (P10 Dry Bound, P90 Flood Risk Bound)

Validation:
  Temporal Split: Train on 2024, Test on 2025 (Strict Zero-Leakage Guarantee)
"""

import sys
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    mean_absolute_error,
    mean_squared_error,
    roc_auc_score,
)

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT_DIR / "data_pipeline" / "processed" / "statewide"
MODEL_DIR = ROOT_DIR / "ml" / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

MODEL_OUTPUT_FILE = MODEL_DIR / "statewide_hurdle_v2.pkl"

FEATURES = [
    # Meteorological coarse inputs
    "coarse_rain_mm",
    "coarse_tmax_c",
    "coarse_tmin_c",
    # Topography & Terrain
    "elevation_dem_m",
    "slope_deg",
    "aspect_sin",
    "aspect_cos",
    "terrain_roughness_m",
    "relative_elevation_m",
    # Hydrology & Edaphic soil features
    "distance_to_river_m",
    "sand_pct",
    "clay_pct",
    "silt_pct",
    # Seasonal cycle
    "month",
    "day_of_year_sin",
    "day_of_year_cos",
]

TARGET_BINARY = "target_rain_binary"
TARGET_CONTINUOUS = "target_rain_mm"


def load_training_data(districts=None, max_rows=100000):
    """Load statewide partitioned Parquet datasets with optional district sampling."""
    print("============================================================")
    print("TERRAMIND — STATEWIDE HURDLE MODEL TRAINING PIPELINE")
    print("============================================================")
    print(f"Reading statewide Hive partitions from {DATA_DIR}...")

    partition_dirs = sorted(DATA_DIR.glob("district_name=*"))
    if not partition_dirs:
        raise FileNotFoundError(f"No statewide partitions found in {DATA_DIR}")

    frames = []
    total_loaded = 0

    for p_dir in partition_dirs:
        d_name = p_dir.name.split("=")[-1]
        if districts and d_name not in districts:
            continue
        parquet_file = p_dir / "data.parquet"
        if not parquet_file.exists():
            continue

        df_dist = pd.read_parquet(parquet_file)
        frames.append(df_dist)
        total_loaded += len(df_dist)
        print(f"  Loaded {d_name}: {len(df_dist):,} rows")
        if total_loaded >= max_rows:
            break

    df_all = pd.concat(frames, ignore_index=True)
    df_all["date"] = pd.to_datetime(df_all["date"])
    print(f"Total dataset assembled: {len(df_all):,} rows across {len(frames)} districts.")
    return df_all


def train_hurdle_model():
    start_time = time.time()
    # Load representative districts including Gangetic Delta, North Bengal, and Western Rarh
    target_districts = ["North_24_Parganas", "South_24_Parganas", "Darjeeling", "Purulia"]
    df = load_training_data(districts=target_districts, max_rows=250000)

    # Temporal split (2024 = Train, 2025 = Validation/Test)
    train_mask = df["date"].dt.year == 2024
    test_mask = df["date"].dt.year == 2025

    df_train = df[train_mask].copy()
    df_test = df[test_mask].copy()

    print(f"\nZero-leakage temporal split:")
    print(f"  Training set (2024):   {len(df_train):,} rows")
    print(f"  Validation set (2025): {len(df_test):,} rows")

    X_train = df_train[FEATURES]
    y_train_bin = df_train[TARGET_BINARY]
    y_train_reg = df_train[TARGET_CONTINUOUS]

    X_test = df_test[FEATURES]
    y_test_bin = df_test[TARGET_BINARY]
    y_test_reg = df_test[TARGET_CONTINUOUS]

    # ----------------------------------------------------
    # Stage 1: Rain Occurrence Classifier
    # ----------------------------------------------------
    print("\nTraining Stage 1: Rain Occurrence Classifier (HistGradientBoosting)...")
    clf = HistGradientBoostingClassifier(
        max_iter=120,
        learning_rate=0.08,
        max_depth=7,
        random_state=42,
    )
    clf.fit(X_train, y_train_bin)

    test_probs = clf.predict_proba(X_test)[:, 1]
    test_preds_bin = (test_probs >= 0.5).astype(int)

    acc = accuracy_score(y_test_bin, test_preds_bin)
    auc = roc_auc_score(y_test_bin, test_probs)
    tn, fp, fn, tp = confusion_matrix(y_test_bin, test_preds_bin).ravel()
    pod = tp / (tp + fn) if (tp + fn) > 0 else 0.0  # Probability of Detection (Recall)
    far = fp / (tp + fp) if (tp + fp) > 0 else 0.0  # False Alarm Ratio

    print(f"  Stage 1 Validation Accuracy: {acc:.4f}")
    print(f"  Stage 1 ROC-AUC Score:       {auc:.4f}")
    print(f"  Stage 1 POD (Hit Rate):      {pod:.4f}")
    print(f"  Stage 1 FAR (False Alarm):   {far:.4f}")

    # ----------------------------------------------------
    # Stage 2: Continuous Precipitation Regressor (P50)
    # ----------------------------------------------------
    print("\nTraining Stage 2: Rain Amount Regressor (P50 Median)...")
    wet_train_mask = y_train_reg > 0.1
    X_train_wet = X_train[wet_train_mask]
    y_train_wet = y_train_reg[wet_train_mask]

    reg_p50 = HistGradientBoostingRegressor(
        loss="squared_error",
        max_iter=120,
        learning_rate=0.08,
        max_depth=7,
        random_state=42,
    )
    reg_p50.fit(X_train_wet, y_train_wet)

    # ----------------------------------------------------
    # Stage 3: Quantile Uncertainty Regressors (P10 and P90)
    # ----------------------------------------------------
    print("Training Stage 3: Quantile Regressors (P10 Dry Bound & P90 Flood Risk)...")
    reg_p10 = HistGradientBoostingRegressor(
        loss="quantile",
        quantile=0.10,
        max_iter=80,
        learning_rate=0.08,
        max_depth=6,
        random_state=42,
    )
    reg_p10.fit(X_train_wet, y_train_wet)

    reg_p90 = HistGradientBoostingRegressor(
        loss="quantile",
        quantile=0.90,
        max_iter=80,
        learning_rate=0.08,
        max_depth=6,
        random_state=42,
    )
    reg_p90.fit(X_train_wet, y_train_wet)

    # Overall Hurdle Prediction on Test Set
    raw_p50 = np.clip(reg_p50.predict(X_test), 0.0, None)
    raw_p10 = np.clip(reg_p10.predict(X_test), 0.0, None)
    raw_p90 = np.clip(reg_p90.predict(X_test), 0.0, None)

    # Compound Hurdle Output (Zero if probability < 0.35)
    hurdle_pred_p50 = np.where(test_probs >= 0.35, raw_p50, 0.0)
    hurdle_pred_p10 = np.where(test_probs >= 0.35, raw_p10, 0.0)
    hurdle_pred_p90 = np.where(test_probs >= 0.35, raw_p90, 0.0)

    mae = mean_absolute_error(y_test_reg, hurdle_pred_p50)
    rmse = np.sqrt(mean_squared_error(y_test_reg, hurdle_pred_p50))

    print(f"\nFinal Hurdle Pipeline Evaluation (2025 Test Horizon):")
    print(f"  MAE (Mean Absolute Error):   {mae:.2f} mm")
    print(f"  RMSE (Root Mean Sq Error):   {rmse:.2f} mm")
    print(f"  Quantile Bounds Consistency: {(hurdle_pred_p90 >= hurdle_pred_p10).mean() * 100:.1f}% valid")

    # ----------------------------------------------------
    # Package and Serialize Artifact
    # ----------------------------------------------------
    pipeline_artifact = {
        "model_version": "2.0-statewide-hurdle",
        "trained_at": pd.Timestamp.now().isoformat(),
        "classifier": clf,
        "regressor_p50": reg_p50,
        "regressor_p10": reg_p10,
        "regressor_p90": reg_p90,
        "features": FEATURES,
        "metrics": {
            "accuracy": float(acc),
            "roc_auc": float(auc),
            "pod": float(pod),
            "far": float(far),
            "mae_mm": float(mae),
            "rmse_mm": float(rmse),
            "test_rows": len(df_test),
            "train_rows": len(df_train),
        },
    }

    joblib.dump(pipeline_artifact, MODEL_OUTPUT_FILE)
    elapsed = time.time() - start_time
    file_size_kb = MODEL_OUTPUT_FILE.stat().st_size / 1024

    print(f"\nModel artifact successfully serialized:")
    print(f"  Saved to:  {MODEL_OUTPUT_FILE}")
    print(f"  File size: {file_size_kb:.1f} KB")
    print(f"  Elapsed:   {elapsed:.2f} seconds")
    print("============================================================")


if __name__ == "__main__":
    train_hurdle_model()
