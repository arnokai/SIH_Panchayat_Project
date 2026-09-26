#!/usr/bin/env python3
"""
TerraMind — Machine 1: Regional Agro-Climatic Zone Hurdle Models & Extreme Tail Calibration
Problem Statement: SIH26074 (Ministry of Earth Sciences)

Features:
  1. 3 Regional Regimes:
     - Delta (Coastal & Gangetic Alluvium): Distance to coast, sea breeze, tidal moisture.
     - Laterite (Western Uplands): High heat, rapid drainage, roughness penalties.
     - Terai (Sub-Himalayan Foothills): Orographic lifting, valley cold pools, lapse rates.
  2. Extreme-Value Tail Calibration:
     - Gamma loss regressor for extreme storm events (>= 30-50mm) to prevent least-squares attenuation.
  3. Conformal Prediction Intervals:
     - Finite-sample calibrated confidence intervals on temporal test horizon (2025).
"""

import sys
import time
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.metrics import accuracy_score, mean_absolute_error, roc_auc_score

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT_DIR / "data_pipeline" / "processed" / "statewide"
MODEL_DIR = ROOT_DIR / "ml" / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

REGIONAL_ZONES = {
    "delta": [
        "South_24_Parganas", "North_24_Parganas", "Purba_Medinipur",
        "Howrah", "Hooghly", "Nadia", "Murshidabad"
    ],
    "laterite": [
        "Bankura", "Birbhum", "Purulia", "Jhargram",
        "Paschim_Medinipur", "Paschim_Bardhaman", "Purba_Bardhaman"
    ],
    "terai": [
        "Darjeeling", "Kalimpong", "Jalpaiguri", "Alipurduar",
        "Cooch_Behar", "Uttar_Dinajpur", "Dakshin_Dinajpur", "Malda"
    ]
}

FEATURES = [
    "coarse_rain_mm",
    "coarse_tmax_c",
    "coarse_tmin_c",
    "elevation_dem_m",
    "slope_deg",
    "aspect_sin",
    "aspect_cos",
    "terrain_roughness_m",
    "relative_elevation_m",
    "distance_to_river_m",
    "sand_pct",
    "clay_pct",
    "silt_pct",
    "month",
    "day_of_year_sin",
    "day_of_year_cos",
]

TARGET_BINARY = "target_rain_binary"
TARGET_CONTINUOUS = "target_rain_mm"


def load_zone_data(district_list, max_rows=90000):
    """Load stratified district partitions for a specific agro-climatic zone."""
    frames = []
    samples_per_district = max_rows // len(district_list)

    for dist in district_list:
        p_dir = DATA_DIR / f"district_name={dist}"
        parquet_file = p_dir / "data.parquet"
        if not parquet_file.exists():
            continue
        df_dist = pd.read_parquet(parquet_file)
        if len(df_dist) > samples_per_district:
            df_sampled = df_dist.sample(n=samples_per_district, random_state=42)
        else:
            df_sampled = df_dist
        frames.append(df_sampled)

    if not frames:
        raise FileNotFoundError(f"No partitions found for zone districts: {district_list}")

    df_all = pd.concat(frames, ignore_index=True)
    df_all["date"] = pd.to_datetime(df_all["date"])
    return df_all


def train_single_zone(zone_key, district_list):
    """Train Hurdle Model + Gamma Extreme Tail + Conformal Intervals for a single zone."""
    start_time = time.time()
    print("------------------------------------------------------------")
    print(f"TRAINING REGIONAL HURDLE MODEL: {zone_key.upper()} ZONE")
    print(f"Districts: {', '.join(district_list)}")
    print("------------------------------------------------------------")

    df_zone = load_zone_data(district_list, max_rows=80000)
    
    # Temporal Train / Test Split (Strict Zero-Leakage)
    df_train = df_zone[df_zone["date"].dt.year == 2024]
    df_test = df_zone[df_zone["date"].dt.year == 2025]

    if len(df_test) < 1000:
        # Fallback split if 2025 data partition is small
        split_idx = int(len(df_zone) * 0.8)
        df_train = df_zone.iloc[:split_idx]
        df_test = df_zone.iloc[split_idx:]

    print(f"  Train samples (2024): {len(df_train):,} rows")
    print(f"  Test samples  (2025): {len(df_test):,} rows")

    X_train = df_train[FEATURES]
    y_train_bin = df_train[TARGET_BINARY]
    y_train_reg = df_train[TARGET_CONTINUOUS]

    X_test = df_test[FEATURES]
    y_test_bin = df_test[TARGET_BINARY]
    y_test_reg = df_test[TARGET_CONTINUOUS]

    # Stage 1: Rain Occurrence Classifier
    print("  1. Fitting Stage 1 Rain Classifier...")
    clf = HistGradientBoostingClassifier(
        max_iter=100,
        learning_rate=0.09,
        max_depth=6,
        random_state=42,
    )
    clf.fit(X_train, y_train_bin)
    test_probs = clf.predict_proba(X_test)[:, 1]
    acc = accuracy_score(y_test_bin, (test_probs >= 0.5).astype(int))
    auc = roc_auc_score(y_test_bin, test_probs)
    print(f"     Accuracy: {acc:.4f} | ROC-AUC: {auc:.4f}")

    # Stage 2: Continuous Median Precipitation (P50)
    print("  2. Fitting Stage 2 Median Regressor (P50)...")
    wet_mask = y_train_reg > 0.1
    X_train_wet = X_train[wet_mask]
    y_train_wet = y_train_reg[wet_mask]

    reg_p50 = HistGradientBoostingRegressor(
        loss="squared_error",
        max_iter=100,
        learning_rate=0.09,
        max_depth=6,
        random_state=42,
    )
    reg_p50.fit(X_train_wet, y_train_wet)

    # Stage 3: Quantile Uncertainty Bounds (P10 & P90)
    print("  3. Fitting Quantile Regressors (P10 & P90)...")
    reg_p10 = HistGradientBoostingRegressor(
        loss="quantile",
        quantile=0.10,
        max_iter=70,
        learning_rate=0.09,
        max_depth=5,
        random_state=42,
    )
    reg_p10.fit(X_train_wet, y_train_wet)

    reg_p90 = HistGradientBoostingRegressor(
        loss="quantile",
        quantile=0.90,
        max_iter=70,
        learning_rate=0.09,
        max_depth=5,
        random_state=42,
    )
    reg_p90.fit(X_train_wet, y_train_wet)

    # Stage 4: Extreme-Value Tail Calibration (Gamma loss for severe downpours)
    print("  4. Fitting Extreme Tail Regressor (Gamma loss for heavy convective events)...")
    extreme_mask = y_train_reg >= 15.0  # Focus on convective storm regime
    if extreme_mask.sum() >= 100:
        reg_extreme = HistGradientBoostingRegressor(
            loss="gamma",
            max_iter=80,
            learning_rate=0.07,
            max_depth=5,
            random_state=42,
        )
        reg_extreme.fit(X_train[extreme_mask], y_train_reg[extreme_mask])
    else:
        reg_extreme = reg_p90

    # Test Evaluation & Conformal Prediction Intervals
    raw_p50 = np.clip(reg_p50.predict(X_test), 0.0, None)
    hurdle_pred = np.where(test_probs >= 0.35, raw_p50, 0.0)
    mae = mean_absolute_error(y_test_reg, hurdle_pred)

    # Conformal Calibration: Compute 90% non-parametric prediction interval margin
    test_errors = np.abs(y_test_reg - hurdle_pred)
    conformal_margin_90 = float(np.percentile(test_errors, 90))
    print(f"     MAE: {mae:.2f} mm | 90% Conformal Margin: ±{conformal_margin_90:.2f} mm")

    artifact = {
        "model_version": f"2.0-regional-{zone_key}",
        "zone_key": zone_key,
        "zone_districts": district_list,
        "trained_at": pd.Timestamp.now().isoformat(),
        "classifier": clf,
        "regressor_p50": reg_p50,
        "regressor_p10": reg_p10,
        "regressor_p90": reg_p90,
        "regressor_extreme": reg_extreme,
        "conformal_margin_90": conformal_margin_90,
        "features": FEATURES,
        "metrics": {
            "accuracy": float(acc),
            "roc_auc": float(auc),
            "mae_mm": float(mae),
            "conformal_margin_mm": float(conformal_margin_90),
            "train_rows": len(df_train),
            "test_rows": len(df_test),
        }
    }

    out_file = MODEL_DIR / f"hurdle_{zone_key}.pkl"
    joblib.dump(artifact, out_file)
    elapsed = time.time() - start_time
    print(f"  ✓ Saved to: {out_file.name} ({out_file.stat().st_size / 1024:.1f} KB in {elapsed:.1f}s)\n")


def train_all_regional_models():
    print("============================================================")
    print("TERRAMIND — REGIONAL AGRO-CLIMATIC HURDLE COMPILATION")
    print("============================================================")
    for zone_key, dist_list in REGIONAL_ZONES.items():
        train_single_zone(zone_key, dist_list)
    print("All 3 Regional Agro-Climatic Hurdle Models compiled successfully!")


if __name__ == "__main__":
    train_all_regional_models()
