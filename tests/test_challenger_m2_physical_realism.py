"""
tests/test_challenger_m2_physical_realism.py
============================================
Adversarial Empirical Challenger 2 Test Suite for Milestone M2
(Bulk Geospatial Feature Enrichment).

Empirically stress-tests:
1. Amdanga pilot preservation: delta < 1e-6 across all features.
   (Detailed audit of raw CSV vs normalized pilot training table).
2. Physical bounds:
   - distance_to_river_m >= 0.0
   - slope_deg in [0.0, 90.0]
   - aspect_sin and aspect_cos in [-1.0, 1.0] and unit circle identity
   - terrain_roughness_m >= 0.0
   - elevation_dem_m in [-5.0, 3700.0]
   - relative_elevation_m in [-2000.0, 2000.0] and block zero-mean
   - soil fractions sum == 100.0% exactly
3. Regional elevation sanity:
   - Darjeeling & Kalimpong GPs > 500m
   - Coastal / Sunderbans (South 24 Parganas, Purba Medinipur, Howrah) < 15m
   - Physical orographic gradient ordering (Himalayan > Western Rarh > Coastal Delta)
4. River distribution plausibility across all 22 rural districts:
   - Northern rivers in northern districts
   - Western rivers in western districts
   - Deltaic rivers in coastal / delta districts
   - Plausible geodesic distances (min >= 0, max < 100 km)
"""

import math
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATIC_FEATURES_PARQUET = PROJECT_ROOT / "data_pipeline" / "features" / "statewide_static_features.parquet"
REGISTRY_PARQUET = PROJECT_ROOT / "data_pipeline" / "metadata" / "statewide_panchayats.parquet"
REGISTRY_CSV = PROJECT_ROOT / "data_pipeline" / "metadata" / "statewide_panchayats.csv"

PILOT_TERRAIN_CSV = PROJECT_ROOT / "data_pipeline" / "raw" / "panchayat_terrain_features.csv"
PILOT_RIVER_CSV = PROJECT_ROOT / "data_pipeline" / "raw" / "panchayat_river_features.csv"
PILOT_SOIL_CSV = PROJECT_ROOT / "data_pipeline" / "raw" / "panchayat_soil_context.csv"
PILOT_TRAINING_PARQUET = PROJECT_ROOT / "data_pipeline" / "processed" / "training_table.parquet"


class TestM2PhysicalRealismAndPilotCompatibility(unittest.TestCase):
    """Empirical adversarial verification of physical realism and pilot compatibility."""

    @classmethod
    def setUpClass(cls):
        if not STATIC_FEATURES_PARQUET.exists():
            raise unittest.SkipTest(f"Artifact {STATIC_FEATURES_PARQUET} does not exist.")
        cls.df = pd.read_parquet(STATIC_FEATURES_PARQUET)
        
        reg_file = REGISTRY_PARQUET if REGISTRY_PARQUET.exists() else REGISTRY_CSV
        if reg_file.suffix == ".parquet":
            cls.registry = pd.read_parquet(reg_file)
        else:
            cls.registry = pd.read_csv(reg_file)
            
        cls.merged = cls.df.merge(
            cls.registry[["gp_code", "panchayat_name", "block_name", "district_name", "latitude", "longitude"]],
            on="gp_code",
            how="left"
        )
        cls.amdanga = cls.merged[cls.merged["gp_code"].isin(range(107777, 107785))].sort_values("gp_code").copy()

    # -----------------------------------------------------------------
    # DIMENSION 1: Amdanga Pilot Preservation (delta < 1e-6)
    # -----------------------------------------------------------------

    def test_01_amdanga_terrain_preservation_delta(self):
        """All 6 terrain features match panchayat_terrain_features.csv with delta < 1e-6."""
        self.assertTrue(PILOT_TERRAIN_CSV.exists(), "Pilot terrain CSV missing")
        t_csv = pd.read_csv(PILOT_TERRAIN_CSV)
        id_map = {
            "A1": 107777, "A2": 107778, "A3": 107779, "A4": 107780,
            "A5": 107781, "A6": 107782, "A7": 107783, "A8": 107784
        }
        t_csv["gp_code"] = t_csv["panchayat_id"].map(id_map)
        m = self.amdanga.merge(t_csv, on="gp_code", suffixes=("_state", "_pilot"))

        terrain_cols = [
            "elevation_dem_m", "slope_deg", "aspect_sin", "aspect_cos",
            "terrain_roughness_m", "relative_elevation_m"
        ]
        for col in terrain_cols:
            max_delta = (m[f"{col}_state"] - m[f"{col}_pilot"]).abs().max()
            self.assertLess(
                max_delta, 1e-6,
                f"Amdanga terrain feature '{col}' exceeded 1e-6 delta threshold: max delta = {max_delta}"
            )

    def test_02_amdanga_river_preservation_delta(self):
        """Hydrology features match panchayat_river_features.csv with delta < 1e-6."""
        self.assertTrue(PILOT_RIVER_CSV.exists(), "Pilot river CSV missing")
        r_csv = pd.read_csv(PILOT_RIVER_CSV).rename(columns={"GPCODE": "gp_code"})
        m = self.amdanga.merge(r_csv, on="gp_code", suffixes=("_state", "_pilot"))

        # Distance delta < 1e-6
        max_dist_delta = (m["distance_to_river_m_state"] - m["distance_to_river_m_pilot"]).abs().max()
        self.assertLess(
            max_dist_delta, 1e-6,
            f"Amdanga river distance exceeded 1e-6 delta threshold: max delta = {max_dist_delta}"
        )

        # River name identity
        self.assertTrue(
            (m["nearest_river_state"] == m["nearest_river_pilot"]).all(),
            "Amdanga nearest_river names do not match pilot ground truth"
        )
        self.assertTrue((m["nearest_river_state"] == "Ganges").all())

    def test_03_amdanga_soil_preservation_and_normalization_contract(self):
        """
        Soil features preserve surveyed values with delta < 1e-6 against master pilot table.
        Validates the exact mathematical necessity of the 100.0% sum normalization.
        """
        # A. Comparison against pilot training_table.parquet (the normalized gold standard)
        if PILOT_TRAINING_PARQUET.exists():
            pilot_train = pd.read_parquet(PILOT_TRAINING_PARQUET)
            p_sub = pilot_train[["gp_code", "sand_pct", "clay_pct", "silt_pct", "soil_type"]].drop_duplicates()
            m_train = self.amdanga.merge(p_sub, on="gp_code", suffixes=("_state", "_train"))
            self.assertEqual(len(m_train), 8)

            for col in ["sand_pct", "clay_pct", "silt_pct"]:
                delta = (m_train[f"{col}_state"] - m_train[f"{col}_train"]).abs().max()
                self.assertLess(
                    delta, 1e-6,
                    f"Amdanga soil feature '{col}' diverged from training_table: max delta = {delta}"
                )
            self.assertTrue((m_train["soil_type_state"] == m_train["soil_type_train"]).all())

        # B. Comparison against raw panchayat_soil_context.csv
        self.assertTrue(PILOT_SOIL_CSV.exists(), "Pilot soil CSV missing")
        s_csv = pd.read_csv(PILOT_SOIL_CSV).rename(columns={"panchayat_id": "gp_code"})
        m_raw = self.amdanga.merge(s_csv, on="gp_code", suffixes=("_state", "_raw"))

        # sand_pct and clay_pct match raw CSV with delta < 1e-6
        for col in ["sand_pct", "clay_pct"]:
            delta = (m_raw[f"{col}_state"] - m_raw[f"{col}_raw"]).abs().max()
            self.assertLess(delta, 1e-6, f"Amdanga '{col}' diverged from raw soil CSV: max delta = {delta}")

        # Soil type matches raw CSV
        self.assertTrue((m_raw["soil_type_state"] == m_raw["soil_type_raw"]).all())

        # Silt percentage: exactly 7 of 8 GPs match raw CSV with delta 0;
        # LGD 107781 (Chandigarh) was normalized in make_dataset.py from 60.6 to 60.5 to satisfy the 100.0% sum contract
        silt_diffs = (m_raw["silt_pct_state"] - m_raw["silt_pct_raw"]).abs()
        non_chandigarh = m_raw[m_raw["gp_code"] != 107781]
        self.assertLess(
            (non_chandigarh["silt_pct_state"] - non_chandigarh["silt_pct_raw"]).abs().max(), 1e-6,
            "Non-Chandigarh Amdanga GPs diverged in silt_pct from raw CSV"
        )
        chandigarh_raw = m_raw[m_raw["gp_code"] == 107781].iloc[0]
        raw_sum = chandigarh_raw["sand_pct_raw"] + chandigarh_raw["clay_pct_raw"] + chandigarh_raw["silt_pct_raw"]
        self.assertAlmostEqual(raw_sum, 100.1, places=1, msg="Raw CSV Chandigarh sum was expected to be 100.1%")
        norm_sum = chandigarh_raw["sand_pct_state"] + chandigarh_raw["clay_pct_state"] + chandigarh_raw["silt_pct_state"]
        self.assertAlmostEqual(norm_sum, 100.0, places=2, msg="Statewide Chandigarh sum must be 100.00%")

    # -----------------------------------------------------------------
    # DIMENSION 2: Physical Bounds Verification
    # -----------------------------------------------------------------

    def test_04_physical_bounds_hydrology(self):
        """Hydrological distances are strictly non-negative and within plausible bounds."""
        dists = self.df["distance_to_river_m"]
        self.assertTrue((dists >= 0.0).all(), "Found negative distance_to_river_m")
        self.assertGreater(dists.min(), 0.0, "Min river distance should be positive")
        self.assertLess(dists.max(), 100_000.0, "Max river distance exceeded 100 km")

        # River names
        self.assertTrue(self.df["nearest_river"].notna().all(), "Found NaN nearest_river")
        self.assertTrue((self.df["nearest_river"].str.strip() != "").all(), "Found empty nearest_river")

    def test_05_physical_bounds_orography(self):
        """Orography features strictly adhere to physical domain constraints."""
        # Slope: [0.0, 90.0]
        slopes = self.df["slope_deg"]
        self.assertTrue((slopes >= 0.0).all(), "Found slope < 0.0 deg")
        self.assertTrue((slopes <= 90.0).all(), "Found slope > 90.0 deg")

        # Aspect: sin and cos in [-1.0, 1.0]
        sins = self.df["aspect_sin"]
        coss = self.df["aspect_cos"]
        self.assertTrue((sins >= -1.0).all() and (sins <= 1.0).all(), "aspect_sin out of bounds")
        self.assertTrue((coss >= -1.0).all() and (coss <= 1.0).all(), "aspect_cos out of bounds")

        # Aspect unit circle trigonometric identity: sin^2 + cos^2 == 1.0
        unit_dev = (sins**2 + coss**2 - 1.0).abs().max()
        self.assertLess(unit_dev, 1e-3, f"Aspect vector deviates from unit circle: max dev {unit_dev}")

        # Roughness: >= 0.0
        rough = self.df["terrain_roughness_m"]
        self.assertTrue((rough >= 0.0).all(), "Found negative terrain_roughness_m")

        # Elevation: [-5.0, 3700.0]
        elev = self.df["elevation_dem_m"]
        self.assertTrue((elev >= -5.0).all(), "Elevation below West Bengal sea/delta floor (-5m)")
        self.assertTrue((elev <= 3700.0).all(), "Elevation above West Bengal peak Sandakphu (~3636m)")

        # Relative elevation: [-2000.0, 2000.0]
        rel_elev = self.df["relative_elevation_m"]
        self.assertTrue((rel_elev >= -2000.0).all() and (rel_elev <= 2000.0).all())

        # Block zero-mean property: for all 341 non-pilot blocks, mean(relative_elevation_m) == 0.00 (+/- rounding)
        non_amdanga = self.merged[self.merged["block_name"] != "AMDANGA"]
        non_amdanga_means = non_amdanga.groupby("block_name")["relative_elevation_m"].mean()
        self.assertLess(
            non_amdanga_means.abs().max(), 0.01,
            f"Non-Amdanga block mean relative elevation deviated from 0.0: max abs mean {non_amdanga_means.abs().max()}"
        )
        # Amdanga block preserves historical surveyed mean of -0.8118m from pilot terrain CSV
        amdanga_mean = self.merged[self.merged["block_name"] == "AMDANGA"]["relative_elevation_m"].mean()
        self.assertAlmostEqual(amdanga_mean, -0.81178976, places=4)

    def test_06_physical_bounds_edaphic(self):
        """Edaphic soil fractions strictly adhere to [0, 100] and sum to 100.0%."""
        for col in ["sand_pct", "clay_pct", "silt_pct"]:
            vals = self.df[col]
            self.assertTrue((vals >= 0.0).all() and (vals <= 100.0).all(), f"'{col}' outside [0, 100]")

        # Exact 100.0% closure across 100% of rows
        soil_sums = (self.df["sand_pct"] + self.df["clay_pct"] + self.df["silt_pct"]).round(2)
        mismatches = (soil_sums != 100.0).sum()
        self.assertEqual(mismatches, 0, f"Soil sum invariant failed on {mismatches} rows")

        # Binary soil_type classification
        self.assertTrue(set(self.df["soil_type"].unique()).issubset({"sandy", "non_sandy"}))

    # -----------------------------------------------------------------
    # DIMENSION 3: Regional Elevation Sanity
    # -----------------------------------------------------------------

    def test_07_regional_elevation_sanity_himalayan(self):
        """Himalayan districts (Darjeeling, Kalimpong) must have elevations strictly > 500m."""
        darjeeling = self.merged[self.merged["district_name"] == "Darjeeling"]
        self.assertEqual(len(darjeeling), 80)
        self.assertGreater(
            darjeeling["elevation_dem_m"].min(), 500.0,
            f"Darjeeling min elevation {darjeeling['elevation_dem_m'].min()} <= 500m"
        )
        self.assertGreater(
            darjeeling["elevation_dem_m"].max(), 2000.0,
            f"Darjeeling max elevation {darjeeling['elevation_dem_m'].max()} is unrealistically low for alpine ridge"
        )

        kalimpong = self.merged[self.merged["district_name"] == "Kalimpong"]
        self.assertEqual(len(kalimpong), 42)
        self.assertGreater(
            kalimpong["elevation_dem_m"].min(), 500.0,
            f"Kalimpong min elevation {kalimpong['elevation_dem_m'].min()} <= 500m"
        )

    def test_08_regional_elevation_sanity_coastal_and_delta(self):
        """Coastal and low-lying delta districts must have elevations strictly < 15m."""
        coastal_districts = ["South 24 Parganas", "Purba Medinipur", "Howrah"]
        for dist in coastal_districts:
            sub = self.merged[self.merged["district_name"] == dist]
            self.assertGreater(len(sub), 0, f"No records found for {dist}")
            self.assertLess(
                sub["elevation_dem_m"].max(), 15.0,
                f"{dist} max elevation {sub['elevation_dem_m'].max()} >= 15m"
            )
            # Ensure not excessively negative
            self.assertGreaterEqual(
                sub["elevation_dem_m"].min(), -2.0,
                f"{dist} min elevation {sub['elevation_dem_m'].min()} is implausibly below sea level"
            )

    def test_09_regional_orography_ordering(self):
        """
        Physiographic orographic gradient must follow expected macroscopic ordering:
        Himalayan (Darjeeling) > Western Rarh (Purulia) > Coastal Delta (South 24 Parganas).
        """
        darj_elev = self.merged[self.merged["district_name"] == "Darjeeling"]["elevation_dem_m"].mean()
        purulia_elev = self.merged[self.merged["district_name"] == "Purulia"]["elevation_dem_m"].mean()
        s24p_elev = self.merged[self.merged["district_name"] == "South 24 Parganas"]["elevation_dem_m"].mean()

        self.assertGreater(darj_elev, purulia_elev, "Darjeeling mean elevation should exceed Purulia")
        self.assertGreater(purulia_elev, s24p_elev, "Purulia mean elevation should exceed South 24 Parganas")

        darj_slope = self.merged[self.merged["district_name"] == "Darjeeling"]["slope_deg"].mean()
        purulia_slope = self.merged[self.merged["district_name"] == "Purulia"]["slope_deg"].mean()
        s24p_slope = self.merged[self.merged["district_name"] == "South 24 Parganas"]["slope_deg"].mean()

        self.assertGreater(darj_slope, purulia_slope, "Darjeeling mean slope should exceed Purulia")
        self.assertGreater(purulia_slope, s24p_slope, "Purulia mean slope should exceed South 24 Parganas")

        darj_rough = self.merged[self.merged["district_name"] == "Darjeeling"]["terrain_roughness_m"].mean()
        purulia_rough = self.merged[self.merged["district_name"] == "Purulia"]["terrain_roughness_m"].mean()
        s24p_rough = self.merged[self.merged["district_name"] == "South 24 Parganas"]["terrain_roughness_m"].mean()

        self.assertGreater(darj_rough, purulia_rough, "Darjeeling roughness should exceed Purulia")
        self.assertGreater(purulia_rough, s24p_rough, "Purulia roughness should exceed South 24 Parganas")

    # -----------------------------------------------------------------
    # DIMENSION 4: River Distribution Plausibility Across Districts
    # -----------------------------------------------------------------

    def test_10_river_distribution_geographic_plausibility(self):
        """
        Nearest rivers assigned to Gram Panchayats must align with regional hydrological basins:
        - Northern Sub-Himalayan / Terai / Dooars: Teesta, Torsa, Mahananda
        - Western Rarh Plateau / Peneplain: Damodar, Kangsabati, Subarnarekha, Mayurakshi
        - Estuarine Coastal Delta: Vidyadhari, Ichamati, Hooghly/Ganga, Ganges
        """
        # Northern Basin
        northern_districts = ["Jalpaiguri", "Cooch Behar", "Alipurduar", "Kalimpong", "Darjeeling"]
        northern_allowed = {"Teesta", "Torsa", "Mahananda"}
        for dist in northern_districts:
            rivers = set(self.merged[self.merged["district_name"] == dist]["nearest_river"].unique())
            self.assertTrue(
                rivers.issubset(northern_allowed),
                f"District {dist} has implausible northern rivers: {rivers - northern_allowed}"
            )

        # Western Basin (Purulia, Bankura, Jhargram)
        purulia_rivers = set(self.merged[self.merged["district_name"] == "Purulia"]["nearest_river"].unique())
        self.assertTrue(
            purulia_rivers.issubset({"Kangsabati", "Damodar"}),
            f"Purulia has implausible western rivers: {purulia_rivers}"
        )

        bankura_rivers = set(self.merged[self.merged["district_name"] == "Bankura"]["nearest_river"].unique())
        self.assertTrue(
            bankura_rivers.issubset({"Damodar", "Kangsabati"}),
            f"Bankura has implausible western rivers: {bankura_rivers}"
        )

        jhargram_rivers = set(self.merged[self.merged["district_name"] == "Jhargram"]["nearest_river"].unique())
        self.assertTrue(
            jhargram_rivers.issubset({"Subarnarekha", "Kangsabati"}),
            f"Jhargram has implausible western rivers: {jhargram_rivers}"
        )

        # Deltaic Basin (South 24 Parganas)
        s24p_rivers = set(self.merged[self.merged["district_name"] == "South 24 Parganas"]["nearest_river"].unique())
        self.assertTrue(
            s24p_rivers.issubset({"Vidyadhari", "Hooghly/Ganga", "Ichamati"}),
            f"South 24 Parganas has implausible deltaic rivers: {s24p_rivers}"
        )

    def test_11_river_distance_plausibility_across_districts(self):
        """Every district's mean distance to major river is within plausible geodetic limits."""
        for dist, group in self.merged.groupby("district_name"):
            mean_dist = group["distance_to_river_m"].mean()
            self.assertGreater(
                mean_dist, 500.0,
                f"District {dist} mean river distance {mean_dist:.1f}m is suspiciously small"
            )
            self.assertLess(
                mean_dist, 60_000.0,
                f"District {dist} mean river distance {mean_dist:.1f}m is suspiciously large"
            )


if __name__ == "__main__":
    unittest.main()
