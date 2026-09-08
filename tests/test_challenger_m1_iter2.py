"""
Milestone M1 Iteration 2 Challenger Adversarial Stress Harness
==============================================================
Independent empirical validation suite by Challenger 1.
Tests every invariant with independent mathematical models, KD-trees,
and standard library parsers.
"""

import csv
import math
import re
import unittest
from pathlib import Path
from typing import Dict, List, Set, Tuple

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from scipy.spatial import cKDTree

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = PROJECT_ROOT / "data_pipeline" / "csv" / "metadata" / "statewide_panchayats.csv"
PARQUET_PATH = PROJECT_ROOT / "data_pipeline" / "metadata" / "statewide_panchayats.parquet"
PILOT_COORDS_PARQUET = PROJECT_ROOT / "data_pipeline" / "raw" / "panchayat_coordinates.parquet"
PILOT_COORDS_CSV = PROJECT_ROOT / "data_pipeline" / "csv" / "raw" / "panchayat_coordinates.csv"

# Global Statewide Bounds (WGS84 EPSG:4326)
WB_LAT_MIN, WB_LAT_MAX = 21.5, 27.3
WB_LON_MIN, WB_LON_MAX = 85.8, 89.9

CANONICAL_22_RURAL_DISTRICTS = {
    "Alipurduar", "Bankura", "Birbhum", "Cooch Behar", "Dakshin Dinajpur",
    "Darjeeling", "Hooghly", "Howrah", "Jalpaiguri", "Jhargram",
    "Kalimpong", "Malda", "Murshidabad", "Nadia", "North 24 Parganas",
    "Paschim Bardhaman", "Paschim Medinipur", "Purba Bardhaman",
    "Purba Medinipur", "Purulia", "South 24 Parganas", "Uttar Dinajpur"
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


def haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in meters between two WGS84 points."""
    R = 6371000.0  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    a = min(1.0, max(0.0, a))
    return 2.0 * R * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))


class TestM1ChallengerStressHarness(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df_parquet = pd.read_parquet(PARQUET_PATH)
        if CSV_PATH.is_file():
            cls.df_csv = pd.read_csv(CSV_PATH)
            cls.dfs = [("Parquet", cls.df_parquet), ("CSV", cls.df_csv)]
        else:
            cls.df_csv = None
            cls.dfs = [("Parquet", cls.df_parquet)]

    def test_01_cardinality_and_administrative_hierarchy(self):
        """Challenger Oracle: Exactly 3,339 GPs, 22 rural districts, 342 blocks, Kolkata excluded."""
        for name, df in self.dfs:
            self.assertEqual(len(df), 3339, f"{name}: Total row count {len(df)} != 3339")
            districts = set(df["district_name"].unique())
            self.assertEqual(len(districts), 22, f"{name}: Expected 22 rural districts, got {len(districts)}")
            self.assertEqual(districts, CANONICAL_22_RURAL_DISTRICTS)
            self.assertNotIn("Kolkata", districts, f"{name}: Kolkata found in rural GP registry")
            blocks = set(df["block_name"].unique())
            self.assertEqual(len(blocks), 342, f"{name}: Expected 342 blocks, got {len(blocks)}")

    def test_02_primary_key_uniqueness_and_bijective_format(self):
        """Challenger Oracle: 100% unique gp_code and panchayat_id with strict bijection."""
        for name, df in self.dfs:
            self.assertEqual(df["gp_code"].nunique(), 3339, f"{name}: gp_code not unique")
            self.assertEqual(df["panchayat_id"].nunique(), 3339, f"{name}: panchayat_id not unique")
            self.assertTrue((df["gp_code"] > 0).all(), f"{name}: Non-positive gp_code detected")

            expected_pids = "WB_" + df["gp_code"].astype(str)
            self.assertTrue((df["panchayat_id"] == expected_pids).all(), f"{name}: panchayat_id format mismatch")

            # Regex check
            p = re.compile(r"^WB_[1-9][0-9]*$")
            for pid in df["panchayat_id"]:
                self.assertTrue(bool(p.match(pid)), f"{name}: Invalid ID pattern {pid}")

    def test_03_zero_nulls_and_corrupt_sentinels(self):
        """Challenger Oracle: Zero nulls, NaNs, infs, whitespace padding, or corrupt sentinels."""
        corrupt = {"nan", "null", "none", "", "n/a", "na", "\\0", "\\n", "undefined"}
        for name, df in self.dfs:
            for col in EXPECTED_COLUMNS:
                self.assertEqual(df[col].isnull().sum(), 0, f"{name}: nulls found in {col}")
                if df[col].dtype == object or pd.api.types.is_string_dtype(df[col]):
                    vals = df[col].astype(str)
                    bad = vals[vals.str.strip().str.lower().isin(corrupt)]
                    self.assertEqual(len(bad), 0, f"{name}: corrupt values in {col}: {bad.tolist()[:5]}")
                    unt = vals[vals != vals.str.strip()]
                    self.assertEqual(len(unt), 0, f"{name}: untrimmed whitespace in {col}: {unt.tolist()[:5]}")

    def test_04_state_bounding_box_compliance_and_margin(self):
        """Challenger Oracle: Coordinates strictly inside West Bengal envelope with non-zero margins."""
        for name, df in self.dfs:
            min_lat = df["latitude"].min()
            max_lat = df["latitude"].max()
            min_lon = df["longitude"].min()
            max_lon = df["longitude"].max()

            self.assertGreaterEqual(min_lat, WB_LAT_MIN, f"{name}: Latitude below {WB_LAT_MIN}")
            self.assertLessEqual(max_lat, WB_LAT_MAX, f"{name}: Latitude above {WB_LAT_MAX}")
            self.assertGreaterEqual(min_lon, WB_LON_MIN, f"{name}: Longitude below {WB_LON_MIN}")
            self.assertLessEqual(max_lon, WB_LON_MAX, f"{name}: Longitude above {WB_LON_MAX}")

            # Margin check: ensure no point sits exactly on the outer envelope edge
            lat_south_margin = min_lat - WB_LAT_MIN
            lat_north_margin = WB_LAT_MAX - max_lat
            lon_west_margin = min_lon - WB_LON_MIN
            lon_east_margin = WB_LON_MAX - max_lon

            self.assertGreater(lat_south_margin, 0.05, f"South boundary margin suspiciously tight: {lat_south_margin}")
            self.assertGreater(lat_north_margin, 0.05, f"North boundary margin suspiciously tight: {lat_north_margin}")
            self.assertGreater(lon_west_margin, 0.05, f"West boundary margin suspiciously tight: {lon_west_margin}")
            self.assertGreater(lon_east_margin, 0.05, f"East boundary margin suspiciously tight: {lon_east_margin}")

    def test_05_zero_spatial_point_collisions(self):
        """Challenger Oracle: Exactly 0 duplicate (lat, lon) pairs across all 3,339 GPs in CSV and Parquet."""
        for name, df in self.dfs:
            dups = df[df.duplicated(subset=["latitude", "longitude"], keep=False)]
            dup_count = len(dups)
            self.assertEqual(dup_count, 0, f"{name}: Found {dup_count} duplicate coordinate records!")

            # Check at 7 decimal places
            rounded_7 = df[["latitude", "longitude"]].round(7)
            dups_7 = rounded_7[rounded_7.duplicated(keep=False)]
            self.assertEqual(len(dups_7), 0, f"{name}: Found {len(dups_7)} duplicates at 7 decimal places (~1.1 cm)!")

            # Check at 6 decimal places (~11 cm)
            rounded_6 = df[["latitude", "longitude"]].round(6)
            dups_6 = rounded_6[rounded_6.duplicated(keep=False)]
            self.assertEqual(len(dups_6), 0, f"{name}: Found {len(dups_6)} duplicates at 6 decimal places (~11 cm)!")

    def test_06_intra_block_minimum_distance_bound(self):
        """Challenger Oracle: All intra-block pairs satisfy geodesic separation >= 250.0m."""
        df = self.df_parquet
        min_distance = float("inf")
        closest_pair = None
        total_intra_pairs = 0

        for block_name, group in df.groupby("block_name"):
            coords = group[["latitude", "longitude"]].values
            names = group["panchayat_name"].values
            n = len(coords)
            for i in range(n):
                for j in range(i + 1, n):
                    total_intra_pairs += 1
                    dist = haversine_distance_m(coords[i, 0], coords[i, 1], coords[j, 0], coords[j, 1])
                    if dist < min_distance:
                        min_distance = dist
                        closest_pair = (block_name, names[i], names[j], dist)
                    self.assertGreaterEqual(
                        dist, 250.0,
                        f"Intra-block violation in {block_name}: {names[i]} <-> {names[j]} distance {dist:.2f}m < 250m"
                    )

        self.assertEqual(total_intra_pairs, 14840, f"Expected 14,840 intra-block pairs, evaluated {total_intra_pairs}")
        self.assertGreaterEqual(min_distance, 500.0, f"Min intra-block distance {min_distance:.2f}m < 500m")

    def test_07_global_nearest_neighbor_distribution(self):
        """Challenger Oracle: Global KD-Tree nearest neighbor analysis across all 3,339 points statewide."""
        df = self.df_parquet
        # Convert lat/lon to geocentric Cartesian coordinates (ECEF approx) for KDTree
        R = 6371000.0
        phi = np.radians(df["latitude"].values)
        lam = np.radians(df["longitude"].values)
        x = R * np.cos(phi) * np.cos(lam)
        y = R * np.cos(phi) * np.sin(lam)
        z = R * np.sin(phi)
        points = np.column_stack([x, y, z])

        tree = cKDTree(points)
        # Query nearest neighbor (k=2, k[0] is self, k[1] is neighbor)
        distances, indices = tree.query(points, k=2)
        nn_distances = distances[:, 1]

        min_nn = np.min(nn_distances)
        p1_nn = np.percentile(nn_distances, 1)
        median_nn = np.median(nn_distances)

        self.assertGreaterEqual(min_nn, 250.0, f"Global minimum nearest neighbor distance {min_nn:.2f}m < 250m")
        self.assertGreater(p1_nn, 500.0, f"1st percentile NN distance {p1_nn:.2f}m < 400m")
        self.assertGreater(median_nn, 750.0, f"Median NN distance {median_nn:.2f}m < 1000m")

    def test_08_csv_vs_parquet_complete_parity(self):
        """Challenger Oracle: Bitwise & semantic parity between CSV and Parquet."""
        if self.df_csv is None:
            self.skipTest("CSV retired - pure Parquet architecture")
        self.assertEqual(len(self.df_csv), len(self.df_parquet))
        self.assertEqual(list(self.df_csv.columns), list(self.df_parquet.columns))

        # Check column types and values
        np.testing.assert_array_equal(self.df_csv["gp_code"].values, self.df_parquet["gp_code"].values)
        self.assertTrue((self.df_csv["panchayat_id"].values == self.df_parquet["panchayat_id"].values).all())
        self.assertTrue((self.df_csv["panchayat_name"].values == self.df_parquet["panchayat_name"].values).all())
        self.assertTrue((self.df_csv["block_name"].values == self.df_parquet["block_name"].values).all())
        self.assertTrue((self.df_csv["district_name"].values == self.df_parquet["district_name"].values).all())

        # Coordinates match within 1e-7 deg (< 1.1 cm)
        np.testing.assert_allclose(self.df_csv["latitude"].values, self.df_parquet["latitude"].values, atol=1e-7)
        np.testing.assert_allclose(self.df_csv["longitude"].values, self.df_parquet["longitude"].values, atol=1e-7)

    def test_09_pilot_amdanga_ground_truth_preservation(self):
        """Challenger Oracle: Exact coordinate preservation for all 8 surveyed pilot Panchayats."""
        if PILOT_COORDS_PARQUET.is_file():
            pilot_df = pd.read_parquet(PILOT_COORDS_PARQUET)
        elif PILOT_COORDS_CSV.is_file():
            pilot_df = pd.read_csv(PILOT_COORDS_CSV)
        else:
            self.skipTest("Pilot coords file missing")
        self.assertEqual(len(pilot_df), 8)

        for _, row in pilot_df.iterrows():
            code = int(row["GPCODE"])
            gp_name = str(row["GPNAME"]).strip().upper()
            ref_lat = float(row["latitude"])
            ref_lon = float(row["longitude"])

            match = self.df_parquet[self.df_parquet["gp_code"] == code]
            self.assertEqual(len(match), 1, f"Missing pilot GP {gp_name} (code={code})")
            p_rec = match.iloc[0]
            self.assertEqual(p_rec["panchayat_name"], gp_name)
            self.assertEqual(p_rec["block_name"], "AMDANGA")
            self.assertEqual(p_rec["district_name"], "North 24 Parganas")
            self.assertAlmostEqual(p_rec["latitude"], ref_lat, places=6)
            self.assertAlmostEqual(p_rec["longitude"], ref_lon, places=6)

    def test_10_stdlib_csv_and_pyarrow_native_parsers(self):
        """Challenger Oracle: Parse CSV with stdlib and Parquet with PyArrow native table reader."""
        # 1. Stdlib CSV
        if CSV_PATH.is_file():
            with open(CSV_PATH, "r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                self.assertEqual(reader.fieldnames, EXPECTED_COLUMNS)
                rows = list(reader)
                self.assertEqual(len(rows), 3339)
                seen_codes = set()
                for r in rows:
                    code = int(r["gp_code"])
                    self.assertNotIn(code, seen_codes)
                    seen_codes.add(code)
                    self.assertEqual(r["panchayat_id"], f"WB_{code}")
                    lat, lon = float(r["latitude"]), float(r["longitude"])
                    self.assertTrue(WB_LAT_MIN <= lat <= WB_LAT_MAX)
                    self.assertTrue(WB_LON_MIN <= lon <= WB_LON_MAX)

        # 2. PyArrow native table
        table = pq.read_table(PARQUET_PATH)
        self.assertEqual(table.num_rows, 3339)
        self.assertEqual(table.num_columns, 7)
        for col_name in EXPECTED_COLUMNS:
            col = table.column(col_name)
            self.assertEqual(col.null_count, 0)


if __name__ == "__main__":
    unittest.main()
