import unittest
import pandas as pd
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent.parent / "data_pipeline" / "processed" / "training_table.parquet"
CSV_PATH = Path(__file__).resolve().parent.parent / "data_pipeline" / "processed" / "training_table.csv"
QA_REPORT = Path(__file__).resolve().parent.parent / "data_pipeline" / "reports" / "qa_report.md"

class TestDataPipeline(unittest.TestCase):

    def test_files_exist(self):
        self.assertTrue(DATA_PATH.exists(), f"Missing Parquet dataset: {DATA_PATH}")
        self.assertTrue(CSV_PATH.exists(), f"Missing CSV dataset: {CSV_PATH}")
        self.assertTrue(QA_REPORT.exists(), f"Missing QA report: {QA_REPORT}")

    def test_parquet_schema_and_shape(self):
        df = pd.read_parquet(DATA_PATH)
        self.assertEqual(len(df), 5848, f"Expected 5,848 rows, found {len(df)}")
        self.assertEqual(df['panchayat_id'].nunique(), 8, "Expected 8 Panchayats in Amdanga Block")
        self.assertEqual(df['date'].nunique(), 731, "Expected 731 continuous days (2024-2025)")

    def test_key_uniqueness(self):
        df = pd.read_parquet(DATA_PATH)
        duplicates = df.duplicated(subset=['date', 'panchayat_id']).sum()
        self.assertEqual(duplicates, 0, f"Found {duplicates} duplicate (date, panchayat_id) entries!")

    def test_no_nulls_in_critical_features(self):
        df = pd.read_parquet(DATA_PATH)
        critical_features = [
            'date', 'panchayat_id', 'coarse_rain_mm', 'coarse_tmax_c', 'coarse_tmin_c',
            'elevation_dem_m', 'slope_deg', 'aspect_sin', 'aspect_cos',
            'distance_to_river_m', 'sand_pct', 'clay_pct', 'silt_pct',
            'day_of_year_sin', 'day_of_year_cos', 'target_rain_binary', 'target_rain_mm'
        ]
        for col in critical_features:
            null_count = df[col].isnull().sum()
            self.assertEqual(null_count, 0, f"Feature '{col}' contains {null_count} nulls!")

    def test_physical_validity_bounds(self):
        df = pd.read_parquet(DATA_PATH)
        self.assertTrue((df['target_rain_mm'] >= 0).all(), "Negative rainfall values detected!")
        self.assertTrue((df['coarse_tmax_c'] >= 0).all() and (df['coarse_tmax_c'] <= 55).all(), "Coarse tmax out of bounds!")
        self.assertTrue((df['coarse_tmin_c'] >= 0).all() and (df['coarse_tmin_c'] <= 45).all(), "Coarse tmin out of bounds!")
        soil_sums = (df['sand_pct'] + df['clay_pct'] + df['silt_pct']).round(1)
        self.assertTrue((soil_sums == 100.0).all(), "Soil texture percentages do not sum to 100%!")

    def test_hurdle_target_consistency(self):
        df = pd.read_parquet(DATA_PATH)
        expected_binary = (df['target_rain_mm'] >= 0.5).astype(int)
        self.assertTrue((df['target_rain_binary'] == expected_binary).all(), "Mismatch between target_rain_binary and target_rain_mm!")

if __name__ == "__main__":
    unittest.main()
