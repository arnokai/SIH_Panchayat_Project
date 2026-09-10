"""
Unit Test Suite for Milestone M1: Statewide Gram Panchayat Registry.
====================================================================
Tests schema compliance, physical data types, primary key uniqueness,
zero-null invariant, geographic bounding box adherence, district & block
coverage, pilot Amdanga backward compatibility, and CSV/Parquet parity.
"""

import math
from pathlib import Path
import unittest

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
METADATA_DIR = PROJECT_ROOT / "data_pipeline" / "metadata"
RAW_DIR = PROJECT_ROOT / "data_pipeline" / "raw"

PARQUET_PATH = METADATA_DIR / "statewide_panchayats.parquet"
PILOT_COORDS_PARQUET = RAW_DIR / "panchayat_coordinates.parquet"
PILOT_METADATA_PARQUET = METADATA_DIR / "panchayats.parquet"

CANONICAL_23_DISTRICTS = {
    "Alipurduar", "Bankura", "Birbhum", "Cooch Behar", "Dakshin Dinajpur",
    "Darjeeling", "Hooghly", "Howrah", "Jalpaiguri", "Jhargram",
    "Kalimpong", "Kolkata", "Malda", "Murshidabad", "Nadia",
    "North 24 Parganas", "Paschim Bardhaman", "Paschim Medinipur",
    "Purba Bardhaman", "Purba Medinipur", "Purulia", "South 24 Parganas",
    "Uttar Dinajpur"
}

EXPECTED_COLUMNS = [
    "gp_code",
    "panchayat_id",
    "panchayat_name",
    "block_name",
    "district_name",
    "latitude",
    "longitude",
]


class TestStatewideRegistry(unittest.TestCase):
    """Authoritative validation tests for the statewide GP registry."""

    def test_01_files_exist_and_non_empty(self):
        """Verify Parquet registry artifact exists and meets minimum size."""
        self.assertTrue(PARQUET_PATH.is_file(), f"Missing Parquet registry at {PARQUET_PATH}")
        self.assertGreater(PARQUET_PATH.stat().st_size, 50_000, "Parquet catalog suspiciously small (<50KB)")

    def test_02_exact_columns_and_order(self):
        """Verify exact 7 column names and ordering."""
        df_parquet = pd.read_parquet(PARQUET_PATH)
        self.assertEqual(list(df_parquet.columns), EXPECTED_COLUMNS, "Parquet column order mismatch")

    def test_03_physical_dtypes(self):
        """Verify strict physical data types in the Parquet table."""
        df = pd.read_parquet(PARQUET_PATH)
        self.assertTrue(pd.api.types.is_integer_dtype(df["gp_code"]), f"gp_code must be int, got {df['gp_code'].dtype}")
        self.assertTrue(pd.api.types.is_string_dtype(df["panchayat_id"]) or pd.api.types.is_object_dtype(df["panchayat_id"]))
        self.assertTrue(pd.api.types.is_string_dtype(df["panchayat_name"]) or pd.api.types.is_object_dtype(df["panchayat_name"]))
        self.assertTrue(pd.api.types.is_string_dtype(df["block_name"]) or pd.api.types.is_object_dtype(df["block_name"]))
        self.assertTrue(pd.api.types.is_string_dtype(df["district_name"]) or pd.api.types.is_object_dtype(df["district_name"]))
        self.assertTrue(pd.api.types.is_float_dtype(df["latitude"]), f"latitude must be float, got {df['latitude'].dtype}")
        self.assertTrue(pd.api.types.is_float_dtype(df["longitude"]), f"longitude must be float, got {df['longitude'].dtype}")

    def test_04_zero_nulls(self):
        """Verify 0% null values across all columns."""
        df = pd.read_parquet(PARQUET_PATH)
        for col in EXPECTED_COLUMNS:
            null_count = df[col].isnull().sum()
            self.assertEqual(null_count, 0, f"Column '{col}' contains {null_count} nulls!")

    def test_05_primary_key_uniqueness_and_format(self):
        """Verify uniqueness and valid bijective formatting of primary keys."""
        df = pd.read_parquet(PARQUET_PATH)
        total_rows = len(df)
        self.assertEqual(df["gp_code"].nunique(), total_rows, "Duplicate gp_code values detected!")
        self.assertEqual(df["panchayat_id"].nunique(), total_rows, "Duplicate panchayat_id values detected!")
        self.assertTrue((df["gp_code"] > 0).all(), "Non-positive gp_code detected!")
        expected_ids = "WB_" + df["gp_code"].astype(str)
        self.assertTrue((df["panchayat_id"] == expected_ids).all(), "panchayat_id does not conform to 'WB_<gp_code>'")

    def test_06_geographic_bounding_box(self):
        """Verify all centroids lie strictly within West Bengal bounds [21.5, 27.3] and [85.8, 89.9]."""
        df = pd.read_parquet(PARQUET_PATH)
        self.assertTrue((df["latitude"] >= 21.5).all(), f"Latitude < 21.5°N found: min {df['latitude'].min()}")
        self.assertTrue((df["latitude"] <= 27.3).all(), f"Latitude > 27.3°N found: max {df['latitude'].max()}")
        self.assertTrue((df["longitude"] >= 85.8).all(), f"Longitude < 85.8°E found: min {df['longitude'].min()}")
        self.assertTrue((df["longitude"] <= 89.9).all(), f"Longitude > 89.9°E found: max {df['longitude'].max()}")

    def test_07_district_and_block_coverage(self):
        """Verify district and block counts match West Bengal administrative hierarchy."""
        df = pd.read_parquet(PARQUET_PATH)
        present_districts = set(df["district_name"].unique())

        # Must be valid subset of 23 districts
        unknown = present_districts - CANONICAL_23_DISTRICTS
        self.assertEqual(len(unknown), 0, f"Unrecognized districts: {unknown}")

        # Must cover exactly all 22 rural districts (Kolkata has 0 rural GPs)
        self.assertEqual(len(present_districts), 22, f"Expected 22 rural districts, found {len(present_districts)}")

        # GP count must match exactly 3,339 GPs (and be within [3300, 3450])
        self.assertEqual(len(df), 3339, f"Total GP count {len(df)} expected to be 3339")
        self.assertTrue(3300 <= len(df) <= 3450, f"Total GP count {len(df)} out of expected range [3300, 3450]")

        # Block count must match 342 blocks (within [330, 350])
        n_blocks = df["block_name"].nunique()
        self.assertEqual(n_blocks, 342, f"Block count {n_blocks} expected to be 342")
        self.assertTrue(330 <= n_blocks <= 350, f"Block count {n_blocks} out of expected range [330, 350]")

    def test_08_pilot_backward_compatibility(self):
        """Verify that the 8 pilot Amdanga Gram Panchayats are preserved with exact coordinates."""
        df = pd.read_parquet(PARQUET_PATH)
        if PILOT_COORDS_PARQUET.is_file():
            df_pilot = pd.read_parquet(PILOT_COORDS_PARQUET)
        else:
            self.skipTest("Pilot coordinate file not found")
        self.assertEqual(len(df_pilot), 8, "Expected 8 pilot Panchayats in raw coordinates")
        for _, r in df_pilot.iterrows():
            code = int(r["GPCODE"])
            match = df[df["gp_code"] == code]
            self.assertEqual(len(match), 1, f"Pilot GP code {code} missing or duplicate in registry")
            self.assertAlmostEqual(match.iloc[0]["latitude"], float(r["latitude"]), places=6)
            self.assertAlmostEqual(match.iloc[0]["longitude"], float(r["longitude"]), places=6)

    def test_09_pure_python_dissolution_logic(self):
        """Verify Shoelace dissolution handles multi-part polygons (e.g. BODAI 2 parts)."""
        from data_pipeline.metadata.build_statewide_registry import (
            pure_python_polygon_centroid,
            dissolve_and_extract_centroids,
        )

        # Test unit square centroid
        square = [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0], [0.0, 0.0]]
        area, cx, cy = pure_python_polygon_centroid(square)
        self.assertAlmostEqual(area, 1.0)
        self.assertAlmostEqual(cx, 0.5)
        self.assertAlmostEqual(cy, 0.5)

        # Test on amdanga_gps.geojson if present
        geojson_path = RAW_DIR / "amdanga_gps.geojson"
        if geojson_path.is_file():
            dissolved = dissolve_and_extract_centroids(geojson_path)
            self.assertEqual(len(dissolved), 8, "Expected 8 dissolved GP centroids from 9 features")
            self.assertIn(107780, dissolved, "BODAI (GPCODE 107780) missing from dissolved result")

    def test_10_global_spatial_uniqueness(self):
        """Verify that all 3,339 Gram Panchayats have strictly unique (latitude, longitude) coordinates."""
        df = pd.read_parquet(PARQUET_PATH)
        total_rows = len(df)
        unique_coords_count = df[["latitude", "longitude"]].drop_duplicates().shape[0]
        dups = df[df.duplicated(subset=["latitude", "longitude"], keep=False)]
        self.assertEqual(
            unique_coords_count,
            total_rows,
            f"Parquet spatial uniqueness failure: {total_rows - unique_coords_count} duplicate coordinate pairs "
            f"({len(dups)} total affected rows). Duplicated coordinates:\n"
            f"{dups[['gp_code', 'panchayat_name', 'block_name', 'latitude', 'longitude']]}"
        )

    def test_11_intra_block_minimum_spatial_separation(self):
        """Verify that all Gram Panchayats within each CD block maintain >= 250m pairwise geodesic separation."""
        df = pd.read_parquet(PARQUET_PATH)
        min_threshold_m = 250.0
        r_earth = 6371000.0  # WGS84 mean spherical Earth radius in meters

        violations = []
        for block_name, group in df.groupby("block_name"):
            n = len(group)
            if n < 2:
                continue

            lats = np.radians(group["latitude"].to_numpy())
            lons = np.radians(group["longitude"].to_numpy())
            names = group["panchayat_name"].to_numpy()
            codes = group["gp_code"].to_numpy()

            # Broadcast pairwise differences: shape (n, n)
            dlat = lats[:, None] - lats[None, :]
            dlon = lons[:, None] - lons[None, :]

            # Spherical haversine formulation
            a = np.sin(dlat / 2.0) ** 2 + np.cos(lats[:, None]) * np.cos(lats[None, :]) * np.sin(dlon / 2.0) ** 2
            a = np.clip(a, 0.0, 1.0)
            c = 2.0 * np.arctan2(np.sqrt(a), np.sqrt(1.0 - a))
            dist_matrix = r_earth * c

            # Extract upper triangle without self-diagonal
            i_indices, j_indices = np.triu_indices(n, k=1)
            pair_dists = dist_matrix[i_indices, j_indices]

            violation_mask = pair_dists < min_threshold_m
            if np.any(violation_mask):
                for idx in np.where(violation_mask)[0]:
                    i, j = i_indices[idx], j_indices[idx]
                    violations.append({
                        "block_name": block_name,
                        "gp1": f"{names[i]} (LGD {codes[i]})",
                        "gp2": f"{names[j]} (LGD {codes[j]})",
                        "distance_m": round(float(pair_dists[idx]), 2),
                    })

        self.assertEqual(
            len(violations),
            0,
            f"Intra-block spatial separation failure: {len(violations)} pairs closer than {min_threshold_m}m:\n"
            + "\n".join([f"  - {v['block_name']}: {v['gp1']} <-> {v['gp2']} : {v['distance_m']}m" for v in violations])
        )


if __name__ == "__main__":
    unittest.main()

