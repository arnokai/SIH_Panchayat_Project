"""
tests/test_challenger_m2.py
===========================
Adversarial Empirical Challenger Test Suite for Milestone M2
(Bulk Geospatial Feature Enrichment).

Artifact under test:
  data_pipeline/features/statewide_static_features.parquet

Challenger Invariant & Stress Tests:
  1. Parquet artifact existence, readability, and PyArrow schema fidelity
  2. Row count exact match (3,339) and exact 14 mandatory columns
  3. Primary key 1-to-1 bijective match with statewide_panchayats.parquet
  4. 0% nulls, NaNs, Infs across all 14 columns, no sentinel strings or unstripped whitespace
  5. Strict soil sum closure: (sand_pct + clay_pct + silt_pct).round(2) == 100.0 for all 3,339 rows
  6. Float precision check: raw soil sum abs diff from 100.0 < 1e-12
  7. soil_type strictly in {'sandy', 'non_sandy'}
  8. Sandy dominance logic bi-directional verification
  9. Orography and terrain bounds and aspect trigonometric identity
  10. Hydrology bounds (distance_to_river_m >= 0.0, non-empty nearest_river)
  11. Relative elevation zero-mean per community development block
  12. Amdanga pilot surveyed features preservation (LGD 107777..107784)
  13. Standalone generator deterministic reproducibility
"""

import math
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PARQUET = PROJECT_ROOT / "data_pipeline" / "metadata" / "statewide_panchayats.parquet"
REGISTRY_CSV = PROJECT_ROOT / "data_pipeline" / "csv" / "metadata" / "statewide_panchayats.csv"
STATIC_FEATURES_PARQUET = PROJECT_ROOT / "data_pipeline" / "features" / "statewide_static_features.parquet"

PILOT_TERRAIN_PARQUET = PROJECT_ROOT / "data_pipeline" / "raw" / "panchayat_terrain_features.parquet"
PILOT_TERRAIN_CSV = PROJECT_ROOT / "data_pipeline" / "csv" / "raw" / "panchayat_terrain_features.csv"
PILOT_RIVER_PARQUET = PROJECT_ROOT / "data_pipeline" / "raw" / "panchayat_river_features.parquet"
PILOT_RIVER_CSV = PROJECT_ROOT / "data_pipeline" / "csv" / "raw" / "panchayat_river_features.csv"
PILOT_SOIL_PARQUET = PROJECT_ROOT / "data_pipeline" / "raw" / "panchayat_soil_context.parquet"
PILOT_SOIL_CSV = PROJECT_ROOT / "data_pipeline" / "csv" / "raw" / "panchayat_soil_context.csv"

MANDATORY_14_COLUMNS = [
    "gp_code", "panchayat_id",
    "elevation_dem_m", "slope_deg", "aspect_sin", "aspect_cos",
    "terrain_roughness_m", "relative_elevation_m",
    "nearest_river", "distance_to_river_m",
    "sand_pct", "clay_pct", "silt_pct", "soil_type"
]


class TestM2ChallengerEmpirical(unittest.TestCase):
    """Adversarial stress-test harness for Milestone M2."""

    @classmethod
    def setUpClass(cls):
        if not STATIC_FEATURES_PARQUET.exists():
            raise unittest.SkipTest(f"Artifact {STATIC_FEATURES_PARQUET} does not exist.")
        cls.static_df = pd.read_parquet(STATIC_FEATURES_PARQUET)
        if REGISTRY_PARQUET.exists():
            cls.registry_df = pd.read_parquet(REGISTRY_PARQUET)
        else:
            cls.registry_df = pd.read_csv(REGISTRY_CSV)

    def test_01_parquet_exists_and_non_empty(self):
        """Parquet artifact must exist, be non-empty, and loadable via PyArrow."""
        self.assertTrue(STATIC_FEATURES_PARQUET.exists())
        size_bytes = STATIC_FEATURES_PARQUET.stat().st_size
        self.assertGreater(size_bytes, 100_000, f"File size {size_bytes} bytes is suspiciously small.")

        table = pq.read_table(STATIC_FEATURES_PARQUET)
        self.assertEqual(table.num_rows, 3339)
        self.assertEqual(table.num_columns, 14)

    def test_02_schema_exact_14_columns(self):
        """Exactly 14 mandatory columns must be present in canonical order."""
        self.assertEqual(list(self.static_df.columns), MANDATORY_14_COLUMNS)

    def test_03_primary_key_bijective_alignment(self):
        """Primary key 1-to-1 match with statewide_panchayats.parquet on gp_code and panchayat_id."""
        # Row count match
        self.assertEqual(len(self.static_df), 3339)
        self.assertEqual(len(self.static_df), len(self.registry_df))

        # Uniqueness
        self.assertEqual(self.static_df["gp_code"].nunique(), 3339)
        self.assertEqual(self.static_df["panchayat_id"].nunique(), 3339)

        # Exact set equality
        self.assertEqual(set(self.static_df["gp_code"]), set(self.registry_df["gp_code"]))
        self.assertEqual(set(self.static_df["panchayat_id"]), set(self.registry_df["panchayat_id"]))

        # Bijective ID formatting
        expected_ids = "WB_" + self.static_df["gp_code"].astype(str)
        self.assertTrue((self.static_df["panchayat_id"] == expected_ids).all())

        # Exact row-by-row order alignment
        self.assertTrue((self.static_df["gp_code"].values == self.registry_df["gp_code"].values).all())

    def test_04_zero_nulls_nans_infs_and_clean_strings(self):
        """0% nulls, NaNs, Infs across all 14 columns; no empty or unstripped strings."""
        # Check nulls
        null_counts = self.static_df.isnull().sum()
        self.assertEqual(null_counts.sum(), 0, f"Detected null values: {null_counts[null_counts > 0].to_dict()}")

        # Check numeric Infs and NaNs
        num_cols = self.static_df.select_dtypes(include=[np.number]).columns
        for col in num_cols:
            self.assertFalse(np.isnan(self.static_df[col]).any(), f"NaN found in numeric column {col}")
            self.assertFalse(np.isinf(self.static_df[col]).any(), f"Inf found in numeric column {col}")

        # Check string columns for clean formatting (no leading/trailing whitespace, no empty strings)
        str_cols = ["panchayat_id", "nearest_river", "soil_type"]
        for col in str_cols:
            s = self.static_df[col].astype(str)
            self.assertTrue((s == s.str.strip()).all(), f"Leading/trailing whitespace found in column {col}")
            self.assertFalse((s.str.strip() == "").any(), f"Empty string found in column {col}")
            # Sentinels
            bad_sentinels = {"null", "none", "nan", "na", "undefined", "?"}
            self.assertFalse(s.str.lower().isin(bad_sentinels).any(), f"Sentinel null string found in column {col}")

    def test_05_strict_soil_sum_closure_invariant(self):
        """Strict soil sum (sand_pct + clay_pct + silt_pct).round(2) == 100.0 for all 3,339 rows."""
        rounded_sums = (self.static_df["sand_pct"] + self.static_df["clay_pct"] + self.static_df["silt_pct"]).round(2)
        mismatches = (rounded_sums != 100.0).sum()
        self.assertEqual(mismatches, 0, f"Found {mismatches} rows failing the 100.0% soil sum invariant!")

        # Check raw float precision: max drift from 100.0 must be < 1e-12 (IEEE 754 precision)
        raw_sums = self.static_df["sand_pct"] + self.static_df["clay_pct"] + self.static_df["silt_pct"]
        max_abs_drift = (raw_sums - 100.0).abs().max()
        self.assertLess(max_abs_drift, 1e-12, f"Float drift {max_abs_drift} exceeds tolerance 1e-12")

        # Fractions within [0.0, 100.0]
        for col in ["sand_pct", "clay_pct", "silt_pct"]:
            self.assertTrue((self.static_df[col] >= 0.0).all(), f"Negative percentage in {col}")
            self.assertTrue((self.static_df[col] <= 100.0).all(), f"Percentage > 100.0 in {col}")

    def test_06_soil_type_categories_and_bidirectional_sandy_dominance(self):
        """soil_type strictly in {'sandy', 'non_sandy'} and bidirectional sandy dominance logic."""
        # 1. Strict categorical domain
        unique_types = set(self.static_df["soil_type"].unique())
        self.assertEqual(unique_types, {"sandy", "non_sandy"})

        # 2. Forward direction: sandy => sand > 50 AND sand > clay AND sand > silt
        sandy_rows = self.static_df[self.static_df["soil_type"] == "sandy"]
        self.assertGreater(len(sandy_rows), 0, "No sandy rows found in dataset!")
        self.assertTrue((sandy_rows["sand_pct"] > 50.0).all(), "Found sandy row with sand_pct <= 50.0")
        self.assertTrue((sandy_rows["sand_pct"] > sandy_rows["clay_pct"]).all(), "Found sandy row with sand_pct <= clay_pct")
        self.assertTrue((sandy_rows["sand_pct"] > sandy_rows["silt_pct"]).all(), "Found sandy row with sand_pct <= silt_pct")

        # 3. Reverse direction: non_sandy => NOT (sand > 50 AND sand > clay AND sand > silt)
        non_sandy = self.static_df[self.static_df["soil_type"] == "non_sandy"]
        self.assertGreater(len(non_sandy), 0, "No non_sandy rows found in dataset!")
        violators = non_sandy[
            (non_sandy["sand_pct"] > 50.0) &
            (non_sandy["sand_pct"] > non_sandy["clay_pct"]) &
            (non_sandy["sand_pct"] > non_sandy["silt_pct"])
        ]
        self.assertEqual(len(violators), 0, f"Found {len(violators)} rows that meet sandy criteria but labeled non_sandy")

    def test_07_topography_physical_ranges_and_aspect_trigonometry(self):
        """Topography features fall within physical bounds and satisfy trigonometric identities."""
        # Elevation
        self.assertTrue((self.static_df["elevation_dem_m"] >= -5.0).all())
        self.assertTrue((self.static_df["elevation_dem_m"] <= 3700.0).all())
        # Slope
        self.assertTrue((self.static_df["slope_deg"] >= 0.0).all())
        self.assertTrue((self.static_df["slope_deg"] <= 90.0).all())
        # Roughness
        self.assertTrue((self.static_df["terrain_roughness_m"] >= 0.0).all())
        # Aspect sin & cos
        self.assertTrue((self.static_df["aspect_sin"] >= -1.0).all())
        self.assertTrue((self.static_df["aspect_sin"] <= 1.0).all())
        self.assertTrue((self.static_df["aspect_cos"] >= -1.0).all())
        self.assertTrue((self.static_df["aspect_cos"] <= 1.0).all())

        # Trigonometric identity: sin^2 + cos^2 == 1.0 (within float rounding)
        trig = (self.static_df["aspect_sin"]**2 + self.static_df["aspect_cos"]**2).round(3)
        self.assertTrue(((trig >= 0.99) & (trig <= 1.01)).all())

    def test_08_relative_elevation_block_balance(self):
        """Relative elevation is within [-2000, 2000] and balances to ~0.0 mean across all 341 non-pilot blocks."""
        merged = pd.merge(self.static_df, self.registry_df[["gp_code", "block_name"]], on="gp_code")
        self.assertTrue((merged["relative_elevation_m"] >= -2000.0).all())
        self.assertTrue((merged["relative_elevation_m"] <= 2000.0).all())

        # Group by block and check mean for all non-pilot blocks
        non_amdanga = merged[merged["block_name"] != "AMDANGA"]
        block_means = non_amdanga.groupby("block_name")["relative_elevation_m"].mean()
        self.assertEqual(len(block_means), 341)
        # Each non-pilot block mean should be within +/- 0.01 due to 2-decimal rounding
        self.assertTrue((block_means.abs() < 0.01).all(), f"Non-pilot block relative elevation mean deviated: max abs {block_means.abs().max()}")

        # For Amdanga, verify it preserves the exact surveyed pilot mean (-0.8118m)
        amdanga = merged[merged["block_name"] == "AMDANGA"]
        self.assertAlmostEqual(amdanga["relative_elevation_m"].mean(), -0.81178976, places=4)

    def test_09_hydrology_bounds_and_river_names(self):
        """Hydrology features are strictly non-negative with valid river names."""
        self.assertTrue((self.static_df["distance_to_river_m"] >= 0.0).all())
        self.assertLess(self.static_df["distance_to_river_m"].max(), 200000.0)

        rivers = self.static_df["nearest_river"].unique()
        self.assertGreaterEqual(len(rivers), 10, f"Expected at least 10 major river channels, got {len(rivers)}")
        for r in rivers:
            self.assertGreater(len(r.strip()), 0)

    def test_10_amdanga_pilot_surveyed_preservation(self):
        """Exact preservation of Amdanga pilot surveyed features for LGD 107777..107784."""
        amdanga = self.static_df[self.static_df["gp_code"].isin(range(107777, 107785))].sort_values("gp_code")
        self.assertEqual(len(amdanga), 8)

        # Soil: strictly non_sandy and 100.0% sum
        self.assertTrue((amdanga["soil_type"] == "non_sandy").all())
        self.assertTrue(((amdanga["sand_pct"] + amdanga["clay_pct"] + amdanga["silt_pct"]).round(2) == 100.0).all())

        # Nearest river: Ganges
        self.assertTrue((amdanga["nearest_river"] == "Ganges").all())

        # Check against terrain pilot Parquet/CSV
        if PILOT_TERRAIN_PARQUET.exists():
            pt = pd.read_parquet(PILOT_TERRAIN_PARQUET)
        elif PILOT_TERRAIN_CSV.exists():
            pt = pd.read_csv(PILOT_TERRAIN_CSV)
        else:
            pt = None

        if pt is not None:
            id_map = {f"A{i}": 107776 + i for i in range(1, 9)}
            pt["gp_code"] = pt["panchayat_id"].map(id_map)
            merged = pd.merge(amdanga, pt, on="gp_code", suffixes=("_static", "_pilot"))
            for col in ["elevation_dem_m", "slope_deg", "aspect_sin", "aspect_cos", "terrain_roughness_m", "relative_elevation_m"]:
                max_diff = (merged[f"{col}_static"] - merged[f"{col}_pilot"]).abs().max()
                self.assertLess(max_diff, 1e-4, f"Amdanga feature '{col}' diverged from surveyed pilot: {max_diff}")

    def test_11_generator_deterministic_reproducibility(self):
        """Re-running generate_statewide_static_features in-memory matches disk artifact exactly."""
        from data_pipeline.features.statewide_geo_features import generate_statewide_static_features
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".parquet", delete=True) as tmp:
            generated_df = generate_statewide_static_features(output_path=tmp.name)
            self.assertEqual(len(generated_df), 3339)
            self.assertEqual(list(generated_df.columns), MANDATORY_14_COLUMNS)

            # Compare all numeric columns with static_df
            for col in MANDATORY_14_COLUMNS:
                if pd.api.types.is_numeric_dtype(self.static_df[col]):
                    max_diff = (self.static_df[col] - generated_df[col]).abs().max()
                    self.assertLess(max_diff, 1e-6, f"Generator output differed on column {col}: {max_diff}")
                else:
                    mismatches = (self.static_df[col] != generated_df[col]).sum()
                    self.assertEqual(mismatches, 0, f"Generator output differed on string column {col}: {mismatches} mismatches")


if __name__ == "__main__":
    unittest.main()
