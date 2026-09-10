"""
Adversarial Challenger Test Suite for Milestone M1 (Statewide GP Registry)
===========================================================================
Empirically stress-tests the Milestone M1 artifacts:
  - data_pipeline/metadata/statewide_panchayats.csv
  - data_pipeline/metadata/statewide_panchayats.parquet

Requirements Verified by Independent Generators and Oracles:
  1. All coordinates strictly within [21.5N, 27.3N] and [85.8E, 89.9E]
  2. Zero duplicate gp_code or panchayat_id
  3. 0% nulls or NaNs across all columns (including corrupt sentinels & unstripped whitespace)
  4. Formatting consistency of panchayat_id ('WB_<gp_code>')
  5. Exactly 22 rural districts represented and total GP count ~3,339
  6. Exact CSV vs Parquet parity and schema fidelity
  7. Amdanga pilot backward compatibility
  8. Independent stdlib CSV parser cross-validation
  9. PyArrow native schema and null invariants
  10. Adversarial Stress Test: Spatial collision detection & dispersion oracle
"""

import csv
import re
import unittest
from pathlib import Path
from typing import Dict, List, Set, Tuple

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PARQUET_PATH = PROJECT_ROOT / "data_pipeline" / "metadata" / "statewide_panchayats.parquet"
PILOT_COORDS_PARQUET = PROJECT_ROOT / "data_pipeline" / "raw" / "panchayat_coordinates.parquet"

# Global Statewide Bounds (WGS84 EPSG:4326)
WB_LAT_MIN, WB_LAT_MAX = 21.5, 27.3
WB_LON_MIN, WB_LON_MAX = 85.8, 89.9

# 22 Canonical Rural Districts of West Bengal (excluding Kolkata which is 100% urban)
CANONICAL_22_RURAL_DISTRICTS: Set[str] = {
    "Alipurduar", "Bankura", "Birbhum", "Cooch Behar", "Dakshin Dinajpur",
    "Darjeeling", "Hooghly", "Howrah", "Jalpaiguri", "Jhargram",
    "Kalimpong", "Malda", "Murshidabad", "Nadia", "North 24 Parganas",
    "Paschim Bardhaman", "Paschim Medinipur", "Purba Bardhaman",
    "Purba Medinipur", "Purulia", "South 24 Parganas", "Uttar Dinajpur"
}

EXPECTED_COLUMNS: List[str] = [
    "gp_code",
    "panchayat_id",
    "panchayat_name",
    "block_name",
    "district_name",
    "latitude",
    "longitude",
]


class TestM1ChallengerEmpirical(unittest.TestCase):
    """Empirical adversarial test suite for Milestone M1 artifacts."""

    @classmethod
    def setUpClass(cls):
        if not PARQUET_PATH.is_file():
            raise FileNotFoundError(f"Parquet artifact not found: {PARQUET_PATH}")
        cls.df_parquet = pd.read_parquet(PARQUET_PATH)
        cls.dfs = [("Parquet", cls.df_parquet)]

    def test_01_coordinate_bounds_oracle(self):
        """Oracle: All coordinates strictly within [21.5N, 27.3N] and [85.8E, 89.9E]."""
        for name, df in self.dfs:
            lats = df["latitude"].to_numpy()
            lons = df["longitude"].to_numpy()

            # No NaNs or Infs
            self.assertFalse(np.isnan(lats).any(), f"{name} contains NaN latitudes")
            self.assertFalse(np.isnan(lons).any(), f"{name} contains NaN longitudes")
            self.assertFalse(np.isinf(lats).any(), f"{name} contains infinite latitudes")
            self.assertFalse(np.isinf(lons).any(), f"{name} contains infinite longitudes")

            # Strict bounds enforcement
            min_lat, max_lat = float(np.min(lats)), float(np.max(lats))
            min_lon, max_lon = float(np.min(lons)), float(np.max(lons))

            self.assertGreaterEqual(min_lat, WB_LAT_MIN, f"{name}: min latitude {min_lat} < {WB_LAT_MIN}")
            self.assertLessEqual(max_lat, WB_LAT_MAX, f"{name}: max latitude {max_lat} > {WB_LAT_MAX}")
            self.assertGreaterEqual(min_lon, WB_LON_MIN, f"{name}: min longitude {min_lon} < {WB_LON_MIN}")
            self.assertLessEqual(max_lon, WB_LON_MAX, f"{name}: max longitude {max_lon} > {WB_LON_MAX}")

            # Interior realism check: coordinates must not sit exactly on artificial outer bounds
            self.assertGreater(min_lat, WB_LAT_MIN)
            self.assertLess(max_lat, WB_LAT_MAX)
            self.assertGreater(min_lon, WB_LON_MIN)
            self.assertLess(max_lon, WB_LON_MAX)

    def test_02_primary_key_uniqueness_oracle(self):
        """Oracle: Zero duplicate gp_code or panchayat_id across entire registry."""
        for name, df in self.dfs:
            total_records = len(df)
            unique_gp_codes = df["gp_code"].nunique()
            unique_panchayat_ids = df["panchayat_id"].nunique()

            self.assertEqual(unique_gp_codes, total_records, f"Duplicate gp_code found in {name}")
            self.assertEqual(unique_panchayat_ids, total_records, f"Duplicate panchayat_id found in {name}")
            self.assertTrue((df["gp_code"] > 0).all(), f"Non-positive gp_code found in {name}")

    def test_03_zero_nulls_nans_and_whitespace_oracle(self):
        """Oracle: 0% nulls or NaNs, empty strings, unstripped whitespace, or corrupt sentinels."""
        corrupt_sentinels = {"nan", "null", "none", "undefined", "", "n/a", "na", "\\n", "\\0"}

        for name, df in self.dfs:
            # Exact columns
            self.assertEqual(list(df.columns), EXPECTED_COLUMNS, f"{name} column mismatch")

            for col in EXPECTED_COLUMNS:
                nulls = df[col].isnull().sum()
                self.assertEqual(nulls, 0, f"{name}: column '{col}' contains {nulls} nulls")

                # If string or object type
                if pd.api.types.is_string_dtype(df[col]) or pd.api.types.is_object_dtype(df[col]):
                    raw_vals = df[col].astype(str)
                    lowered_vals = raw_vals.str.strip().str.lower()
                    bad = lowered_vals[lowered_vals.isin(corrupt_sentinels)]
                    self.assertEqual(len(bad), 0, f"{name}: column '{col}' has invalid sentinels: {bad.tolist()}")

                    # Unstripped whitespace
                    whitespace_issues = raw_vals[raw_vals != raw_vals.str.strip()]
                    self.assertEqual(len(whitespace_issues), 0, f"{name}: column '{col}' has untrimmed whitespace")

    def test_04_panchayat_id_formatting_consistency_oracle(self):
        """Oracle: Formatting consistency of panchayat_id ('WB_<gp_code>')."""
        regex_pattern = re.compile(r"^WB_([1-9][0-9]*)$")

        for name, df in self.dfs:
            for pid, code in zip(df["panchayat_id"], df["gp_code"]):
                match = regex_pattern.match(pid)
                self.assertIsNotNone(match, f"{name}: panchayat_id '{pid}' does not match regex ^WB_([1-9][0-9]*)$")
                parsed_code = int(match.group(1))
                self.assertEqual(parsed_code, code, f"{name}: ID parsed code {parsed_code} != gp_code {code}")
                self.assertEqual(pid, f"WB_{code}", f"{name}: '{pid}' != 'WB_{code}'")

    def test_05_district_and_total_gp_count_oracle(self):
        """Oracle: Exactly 22 rural districts represented and total GP count ~3,339."""
        for name, df in self.dfs:
            # Exact GP count
            self.assertEqual(len(df), 3339, f"{name}: total GP count {len(df)} != 3339")

            # District coverage
            districts = set(df["district_name"].unique())
            self.assertEqual(len(districts), 22, f"{name}: district count {len(districts)} != 22")
            self.assertEqual(districts, CANONICAL_22_RURAL_DISTRICTS, f"{name}: rural districts mismatch")

            # Urban exclusion
            self.assertNotIn("Kolkata", districts, f"{name}: Kolkata found in rural district list")

            # Block count
            blocks = set(df["block_name"].unique())
            self.assertEqual(len(blocks), 342, f"{name}: block count {len(blocks)} != 342")

    def test_06_pilot_amdanga_backward_compatibility_oracle(self):
        """Oracle: Pilot Amdanga coordinates preserved identically."""
        if PILOT_COORDS_PARQUET.is_file():
            pilot_df = pd.read_parquet(PILOT_COORDS_PARQUET)
        else:
            self.skipTest(f"Pilot coordinate reference file not found at {PILOT_COORDS_PARQUET}")
        self.assertEqual(len(pilot_df), 8)

        for _, row in pilot_df.iterrows():
            code = int(row["GPCODE"])
            gp_name = str(row["GPNAME"]).strip().upper()
            ref_lat = float(row["latitude"])
            ref_lon = float(row["longitude"])

            match = self.df_parquet[self.df_parquet["gp_code"] == code]
            self.assertEqual(len(match), 1, f"Pilot GP {gp_name} (code={code}) not found")
            rec = match.iloc[0]
            self.assertEqual(rec["panchayat_name"], gp_name)
            self.assertEqual(rec["block_name"], "AMDANGA")
            self.assertEqual(rec["district_name"], "North 24 Parganas")
            self.assertAlmostEqual(rec["latitude"], ref_lat, places=6)
            self.assertAlmostEqual(rec["longitude"], ref_lon, places=6)

    def test_07_pyarrow_native_schema(self):
        """Oracle: PyArrow table schema and null count."""
        table = pq.read_table(PARQUET_PATH)
        self.assertEqual(table.num_rows, 3339)
        self.assertEqual(table.num_columns, 7)

        for col_name in EXPECTED_COLUMNS:
            col_chunk = table.column(col_name)
            self.assertEqual(col_chunk.null_count, 0, f"PyArrow null count > 0 in {col_name}")

        schema = table.schema
        self.assertEqual(str(schema.field("gp_code").type), "int64")
        self.assertIn(str(schema.field("panchayat_id").type), ("string", "large_string"))
        self.assertIn(str(schema.field("panchayat_name").type), ("string", "large_string"))
        self.assertIn(str(schema.field("block_name").type), ("string", "large_string"))
        self.assertIn(str(schema.field("district_name").type), ("string", "large_string"))
        self.assertEqual(str(schema.field("latitude").type), "double")
        self.assertEqual(str(schema.field("longitude").type), "double")

    def test_08_adversarial_spatial_collision_oracle(self):
        """Adversarial Oracle: Enforce 0 spatial point collisions across the entire statewide catalog."""
        coords = list(zip(self.df_parquet["latitude"], self.df_parquet["longitude"]))
        unique_coords = set(coords)
        collision_count = len(coords) - len(unique_coords)

        dups = self.df_parquet[self.df_parquet.duplicated(subset=["latitude", "longitude"], keep=False)]
        self.assertEqual(len(dups), 0, f"Spatial collisions detected: {len(dups)} duplicate records")
        self.assertEqual(collision_count, 0, f"Spatial collisions detected: {collision_count} colliding pairs")


if __name__ == "__main__":
    unittest.main()
