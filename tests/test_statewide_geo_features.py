"""
tests/test_statewide_geo_features.py
====================================
Comprehensive Unit Test Suite for Milestone M2: Statewide Geospatial Feature Enrichment.
Target Artifact: data_pipeline/features/statewide_static_features.parquet

Verifies:
  - Artifact existence, exact row count (3,339) and column schema
  - Key uniqueness and alignment with LGD statewide registry
  - 0% missing / NaN values across all columns
  - Mandatory edaphic texture invariant: (sand_pct + clay_pct + silt_pct).round(2) == 100.0
  - Categorical soil_type strictly in {'sandy', 'non_sandy'} and sandy dominance logic
  - Topographic bounds (elevation, slope, aspect sin/cos identity, roughness, relative elevation)
  - Hydrology bounds (distance_to_river_m >= 0.0, valid non-empty river names)
  - Exact preservation of Amdanga pilot surveyed features (LGD 107777..107784)
  - Standalone generation engine function and USDA texture classification helper
"""

import math
import unittest
from pathlib import Path
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PARQUET = PROJECT_ROOT / "data_pipeline" / "metadata" / "statewide_panchayats.parquet"
REGISTRY_CSV = PROJECT_ROOT / "data_pipeline" / "csv" / "metadata" / "statewide_panchayats.csv"
STATIC_FEATURES_PARQUET = PROJECT_ROOT / "data_pipeline" / "features" / "statewide_static_features.parquet"

PILOT_TERRAIN_PARQUET = PROJECT_ROOT / "data_pipeline" / "raw" / "panchayat_terrain_features.parquet"
PILOT_RIVER_PARQUET = PROJECT_ROOT / "data_pipeline" / "raw" / "panchayat_river_features.parquet"
PILOT_SOIL_PARQUET = PROJECT_ROOT / "data_pipeline" / "raw" / "panchayat_soil_context.parquet"

MANDATORY_14_COLUMNS = [
    "gp_code", "panchayat_id",
    "elevation_dem_m", "slope_deg", "aspect_sin", "aspect_cos",
    "terrain_roughness_m", "relative_elevation_m",
    "nearest_river", "distance_to_river_m",
    "sand_pct", "clay_pct", "silt_pct", "soil_type"
]

USDA_12_CLASSES = {
    "Clay", "Silty Clay", "Sandy Clay", "Clay Loam", "Silty Clay Loam",
    "Sandy Clay Loam", "Loam", "Silt Loam", "Silt", "Sandy Loam",
    "Loamy Sand", "Sand"
}

AMDANGA_GP_CODES = list(range(107777, 107785))


class TestStatewideStaticFeaturesContract(unittest.TestCase):
    """Test contract compliance of statewide_static_features.parquet."""

    @classmethod
    def setUpClass(cls):
        if not STATIC_FEATURES_PARQUET.exists():
            raise unittest.SkipTest(f"Artifact {STATIC_FEATURES_PARQUET} does not exist.")
        cls.df = pd.read_parquet(STATIC_FEATURES_PARQUET)
        if REGISTRY_PARQUET.exists():
            cls.registry = pd.read_parquet(REGISTRY_PARQUET)
        else:
            cls.registry = pd.read_csv(REGISTRY_CSV)

    def test_file_exists_and_readable(self):
        """Parquet artifact must exist and be loadable as DataFrame."""
        self.assertTrue(STATIC_FEATURES_PARQUET.exists())
        self.assertGreater(STATIC_FEATURES_PARQUET.stat().st_size, 0)
        self.assertIsInstance(self.df, pd.DataFrame)

    def test_row_count_exact_match_3339(self):
        """Must have exactly 3,339 Gram Panchayats matching statewide registry."""
        self.assertEqual(len(self.df), 3339)
        self.assertEqual(len(self.df), len(self.registry))

    def test_schema_mandatory_columns_present(self):
        """All 14 mandatory columns must be present."""
        for col in MANDATORY_14_COLUMNS:
            self.assertIn(col, self.df.columns, f"Mandatory column '{col}' missing from static features table")

    def test_key_uniqueness_and_alignment(self):
        """Zero duplicate gp_codes, zero duplicate panchayat_ids, exactly matches registry."""
        self.assertEqual(self.df["gp_code"].nunique(), 3339)
        self.assertEqual(self.df["panchayat_id"].nunique(), 3339)
        self.assertEqual(set(self.df["gp_code"]), set(self.registry["gp_code"]))
        expected_ids = set("WB_" + self.df["gp_code"].astype(str))
        self.assertEqual(set(self.df["panchayat_id"]), expected_ids)

    def test_zero_nulls_and_nans(self):
        """0% nulls, NaNs, or Infs across all columns in static features."""
        for col in self.df.columns:
            null_count = self.df[col].isnull().sum()
            self.assertEqual(null_count, 0, f"Column '{col}' has {null_count} nulls")
            if pd.api.types.is_numeric_dtype(self.df[col]):
                inf_count = np.isinf(self.df[col]).sum()
                self.assertEqual(inf_count, 0, f"Column '{col}' has {inf_count} infinite values")

    def test_edaphic_exact_100_percent_sum_invariant(self):
        """Mandatory Invariant: (sand_pct + clay_pct + silt_pct).round(2) == 100.0 across all 3,339 rows."""
        soil_sums = (self.df["sand_pct"] + self.df["clay_pct"] + self.df["silt_pct"]).round(2)
        mismatches = (soil_sums != 100.0).sum()
        self.assertEqual(mismatches, 0, f"Found {mismatches} records where sand+clay+silt != 100.0%")

    def test_edaphic_fraction_bounds(self):
        """Sand, clay, and silt percentages must strictly fall within [0.0, 100.0]."""
        for col in ["sand_pct", "clay_pct", "silt_pct"]:
            self.assertTrue((self.df[col] >= 0.0).all(), f"Negative values found in {col}")
            self.assertTrue((self.df[col] <= 100.0).all(), f"Values > 100.0 found in {col}")

    def test_edaphic_soil_type_categories(self):
        """soil_type must be strictly in {'sandy', 'non_sandy'}."""
        unique_types = set(self.df["soil_type"].unique())
        self.assertTrue(unique_types.issubset({"sandy", "non_sandy"}), f"Invalid soil_type categories: {unique_types}")
        self.assertIn("non_sandy", unique_types)

    def test_edaphic_sandy_dominance_rule(self):
        """soil_type == 'sandy' strictly requires sand_pct > 50.0, sand > clay, and sand > silt."""
        sandy_rows = self.df[self.df["soil_type"] == "sandy"]
        if len(sandy_rows) > 0:
            self.assertTrue((sandy_rows["sand_pct"] > 50.0).all(), "Sandy soil with sand <= 50%")
            self.assertTrue((sandy_rows["sand_pct"] > sandy_rows["clay_pct"]).all(), "Sandy soil with sand <= clay")
            self.assertTrue((sandy_rows["sand_pct"] > sandy_rows["silt_pct"]).all(), "Sandy soil with sand <= silt")

        non_sandy = self.df[self.df["soil_type"] == "non_sandy"]
        violators = non_sandy[
            (non_sandy["sand_pct"] > 50.0) &
            (non_sandy["sand_pct"] > non_sandy["clay_pct"]) &
            (non_sandy["sand_pct"] > non_sandy["silt_pct"])
        ]
        self.assertEqual(len(violators), 0, f"Found {len(violators)} rows that should be sandy but labeled non_sandy")

    def test_orography_elevation_bounds(self):
        """elevation_dem_m must fall within [-5.0m, 3700.0m]."""
        self.assertTrue((self.df["elevation_dem_m"] >= -5.0).all(), "Elevation below -5.0m found")
        self.assertTrue((self.df["elevation_dem_m"] <= 3700.0).all(), "Elevation above 3700.0m found")

    def test_orography_slope_bounds(self):
        """slope_deg must fall within [0.0, 90.0]."""
        self.assertTrue((self.df["slope_deg"] >= 0.0).all(), "Negative slope found")
        self.assertTrue((self.df["slope_deg"] <= 90.0).all(), "Slope > 90 degrees found")

    def test_orography_aspect_bounds_and_trigonometry(self):
        """aspect_sin and aspect_cos must fall in [-1.0, 1.0] and satisfy sin^2 + cos^2 == 1.0."""
        self.assertTrue((self.df["aspect_sin"] >= -1.0).all() and (self.df["aspect_sin"] <= 1.0).all())
        self.assertTrue((self.df["aspect_cos"] >= -1.0).all() and (self.df["aspect_cos"] <= 1.0).all())
        trig_sum = (self.df["aspect_sin"] ** 2 + self.df["aspect_cos"] ** 2).round(3)
        self.assertTrue(((trig_sum >= 0.99) & (trig_sum <= 1.01)).all(), "Aspect sin^2 + cos^2 != 1.0")

    def test_orography_terrain_roughness_non_negative(self):
        """terrain_roughness_m must be strictly non-negative (>= 0.0m)."""
        self.assertTrue((self.df["terrain_roughness_m"] >= 0.0).all(), "Negative terrain roughness found")

    def test_orography_relative_elevation_bounds(self):
        """relative_elevation_m must fall within [-2000.0m, 2000.0m]."""
        self.assertTrue((self.df["relative_elevation_m"] >= -2000.0).all())
        self.assertTrue((self.df["relative_elevation_m"] <= 2000.0).all())

    def test_hydrology_nearest_river_non_empty(self):
        """nearest_river must be a non-empty string."""
        river_lengths = self.df["nearest_river"].astype(str).str.strip().str.len()
        self.assertTrue((river_lengths > 0).all(), "Empty river name detected")
        unique_rivers = self.df["nearest_river"].nunique()
        self.assertGreaterEqual(unique_rivers, 5, f"Expected multiple major rivers, got {unique_rivers}")

    def test_hydrology_distance_to_river_non_negative(self):
        """distance_to_river_m must be strictly non-negative (>= 0.0m)."""
        self.assertTrue((self.df["distance_to_river_m"] >= 0.0).all(), "Negative river distance detected")
        self.assertLess(self.df["distance_to_river_m"].max(), 200000.0, "Unreasonable river distance > 200km")

    def test_optional_soil_texture_class_nomenclature(self):
        """If soil_texture_class is present, it must be in the 12 USDA classes."""
        if "soil_texture_class" in self.df.columns:
            unique_classes = set(self.df["soil_texture_class"].unique())
            self.assertTrue(unique_classes.issubset(USDA_12_CLASSES), f"Invalid USDA classes: {unique_classes}")

    def test_amdanga_pilot_preservation(self):
        """The 8 Amdanga pilot Panchayats must preserve surveyed features."""
        amdanga = self.df[self.df["gp_code"].isin(AMDANGA_GP_CODES)]
        self.assertEqual(len(amdanga), 8, f"Expected 8 Amdanga pilot records, found {len(amdanga)}")

        # Soil check
        self.assertTrue((amdanga["soil_type"] == "non_sandy").all())
        soil_sums = (amdanga["sand_pct"] + amdanga["clay_pct"] + amdanga["silt_pct"]).round(2)
        self.assertTrue((soil_sums == 100.0).all())

        # River check: Amdanga pilot points are closest to Ganges
        self.assertTrue((amdanga["nearest_river"] == "Ganges").all())

        # Check against pilot terrain Parquet if available
        if PILOT_TERRAIN_PARQUET.exists():
            pilot_t = pd.read_parquet(PILOT_TERRAIN_PARQUET)
            id_map = {"A1": 107777, "A2": 107778, "A3": 107779, "A4": 107780,
                      "A5": 107781, "A6": 107782, "A7": 107783, "A8": 107784}
            pilot_t["gp_code"] = pilot_t["panchayat_id"].map(id_map)
            merged = pd.merge(amdanga, pilot_t, on="gp_code", suffixes=("_state", "_pilot"))
            for col in ["elevation_dem_m", "slope_deg", "aspect_sin", "aspect_cos", "terrain_roughness_m", "relative_elevation_m"]:
                diff = (merged[f"{col}_state"] - merged[f"{col}_pilot"]).abs().max()
                self.assertLess(diff, 1e-4, f"Amdanga terrain feature '{col}' diverged from pilot: max diff {diff}")


class TestStatewideGeoFeaturesGenerator(unittest.TestCase):
    """Test the standalone generator module and functions."""

    def test_usda_classification_corners(self):
        """Verify USDA texture classification logic on simplex corners."""
        from data_pipeline.features.statewide_geo_features import classify_usda_texture
        self.assertEqual(classify_usda_texture(100.0, 0.0, 0.0), "Sand")
        self.assertEqual(classify_usda_texture(0.0, 100.0, 0.0), "Clay")
        self.assertEqual(classify_usda_texture(0.0, 0.0, 100.0), "Silt")
        self.assertEqual(classify_usda_texture(40.0, 20.0, 40.0), "Loam")
        self.assertEqual(classify_usda_texture(70.0, 10.0, 20.0), "Sandy Loam")
        self.assertEqual(classify_usda_texture(20.0, 30.0, 50.0), "Silty Clay Loam")

    def test_utm45n_projection_accuracy(self):
        """Verify Snyder UTM 45N projection outputs positive coordinates for West Bengal."""
        from data_pipeline.features.statewide_geo_features import latlon_to_utm45n
        # Kolkata roughly lat 22.57, lon 88.36
        x, y = latlon_to_utm45n(22.5726, 88.3639)
        self.assertGreater(x, 400000.0)
        self.assertLess(x, 700000.0)
        self.assertGreater(y, 2400000.0)
        self.assertLess(y, 2600000.0)


if __name__ == "__main__":
    unittest.main()
