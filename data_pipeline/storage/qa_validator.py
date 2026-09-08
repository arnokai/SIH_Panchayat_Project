#!/usr/bin/env python3
"""
=============================================================================
SIH26074 — Statewide Parquet Data Lake QA Validator
=============================================================================
Purpose:
  Validates data integrity, completeness, and schema conformance across all
  district-partitioned Parquet files in data_pipeline/processed/statewide/.
=============================================================================
"""

import sys
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STATEWIDE_LAKE_DIR = PROJECT_ROOT / "data_pipeline" / "processed" / "statewide"
REPORTS_DIR = PROJECT_ROOT / "data_pipeline" / "reports"
QA_REPORT = REPORTS_DIR / "statewide_qa_report.md"

def validate_lake() -> int:
    print("=" * 60)
    print("TERRAMIND STATEWIDE DATA LAKE QA VALIDATION")
    print("=" * 60)
    
    if not STATEWIDE_LAKE_DIR.exists():
        print(f"ERROR: Statewide directory not found: {STATEWIDE_LAKE_DIR}")
        return 1
        
    partitions = sorted([p for p in STATEWIDE_LAKE_DIR.iterdir() if p.is_dir() and p.name.startswith("district_name=")])
    print(f"Found {len(partitions)} district partitions.")
    
    if len(partitions) == 0:
        print("ERROR: No district partitions found.")
        return 1
        
    total_rows = 0
    all_gps = set()
    all_dates = set()
    errors = 0
    
    for p in partitions:
        parquet_file = p / "data.parquet"
        if not parquet_file.exists():
            print(f"ERROR: Missing data.parquet in {p.name}")
            errors += 1
            continue
            
        df = pd.read_parquet(parquet_file)
        n_rows = len(df)
        total_rows += n_rows
        all_gps.update(df["panchayat_id"].unique())
        all_dates.update(df["date"].unique())
        
        # Check nulls in static features
        static_cols = ["elevation_dem_m", "slope_deg", "sand_pct", "clay_pct", "silt_pct", "distance_to_river_m"]
        null_count = df[static_cols].isnull().sum().sum()
        if null_count > 0:
            print(f"ERROR: {p.name} contains {null_count} nulls in static columns")
            errors += 1
            
        # Check non-negative rainfall
        neg_rain = (df["target_rain_mm"] < 0).sum()
        if neg_rain > 0:
            print(f"ERROR: {p.name} contains {neg_rain} negative rain values")
            errors += 1
            
        # Check hurdle consistency
        expected_binary = (df["target_rain_mm"] >= 0.5).astype(int)
        hurdle_mismatch = (df["target_rain_binary"] != expected_binary).sum()
        if hurdle_mismatch > 0:
            print(f"ERROR: {p.name} contains {hurdle_mismatch} hurdle mismatches")
            errors += 1
            
        # Check soil sum
        soil_sum = (df["sand_pct"] + df["clay_pct"] + df["silt_pct"]).round(1)
        soil_invalid = (soil_sum != 100.0).sum()
        if soil_invalid > 0:
            print(f"ERROR: {p.name} contains {soil_invalid} invalid soil sums")
            errors += 1

    print(f"Total Rows: {total_rows:,}")
    print(f"Total Unique Panchayats: {len(all_gps):,}")
    print(f"Total Unique Dates: {len(all_dates)}")
    
    if errors == 0:
        print("\nALL INTEGRITY CHECKS PASSED (Code 0)")
        return 0
    else:
        print(f"\n{errors} INTEGRITY ERRORS FOUND")
        return 1

if __name__ == "__main__":
    sys.exit(validate_lake())
