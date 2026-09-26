import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "backend"))

import terramind
from backend.api import get_forecast, get_nearest_panchayat, get_panchayat_boundaries
from terramind import (
    __cli_name__,
    __title__,
    __ui_title__,
    __version__,
    app,
    compute_nwp_coarse_centroid,
    forecast_panchayat_v2,
    haversine_distance_km,
    resolve_panchayat_meta,
)


class TestSystemIdentifiers(unittest.TestCase):
    """Verify package, UI, and CLI metadata meet specification."""

    def test_01_package_metadata(self):
        self.assertEqual(
            __title__,
            "TerraMind: Panchayat-Scale Micro-Climate & Agro-Advisory Intelligence System",
        )
        self.assertEqual(
            __ui_title__,
            "TerraMind | Gram Panchayat Climate Intelligence",
        )
        self.assertEqual(__version__, "2.1.0")
        self.assertEqual(__cli_name__, "terramind-engine")

    def test_02_fastapi_metadata(self):
        self.assertEqual(app.title, __title__)
        self.assertEqual(app.version, __version__)

    def test_03_cli_binary_version(self):
        res = subprocess.run(
            [sys.executable, "-m", "terramind.cli", "--version"],
            cwd=str(ROOT_DIR),
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn(__title__, res.stdout)
        self.assertIn(__version__, res.stdout)

    def test_04_cli_status(self):
        res = subprocess.run(
            [sys.executable, "-m", "terramind.cli", "status"],
            cwd=str(ROOT_DIR),
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn("Statewide Registry", res.stdout)
        self.assertIn("3,339 Gram Panchayats", res.stdout)

    def test_05_cli_nearest(self):
        res = subprocess.run(
            [sys.executable, "-m", "terramind.cli", "nearest", "22.805", "88.510", "--limit", "2"],
            cwd=str(ROOT_DIR),
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn("AMDANGA", res.stdout)
        self.assertIn("WB_107778", res.stdout)

    def test_06_cli_search(self):
        res = subprocess.run(
            [sys.executable, "-m", "terramind.cli", "search", "Amdanga", "--limit", "3"],
            cwd=str(ROOT_DIR),
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn("AMDANGA", res.stdout)


class TestMapAndLocationAccuracy(unittest.TestCase):
    """Verify exact Gram Panchayat coordinates and regional grid downscaling geometry."""

    def test_01_pilot_panchayat_exact_coordinates(self):
        # Amdanga pilot (WB_107778)
        meta = resolve_panchayat_meta("WB_107778")
        self.assertIsNotNone(meta)
        self.assertAlmostEqual(meta["latitude"], 22.804947, places=4)
        self.assertAlmostEqual(meta["longitude"], 88.509614, places=4)

    def test_02_statewide_panchayats_exact_coordinates(self):
        # Banchukamari in Alipurduar (WB_107001)
        meta_north = resolve_panchayat_meta("WB_107001")
        self.assertIsNotNone(meta_north)
        self.assertAlmostEqual(meta_north["latitude"], 26.527425, places=4)
        self.assertAlmostEqual(meta_north["longitude"], 89.496956, places=4)
        self.assertEqual(meta_north["district_name"], "Alipurduar")

        # Baragram in Purulia (WB_109832)
        meta_west = resolve_panchayat_meta("WB_109832")
        self.assertIsNotNone(meta_west)
        self.assertAlmostEqual(meta_west["latitude"], 23.440528, places=4)
        self.assertAlmostEqual(meta_west["longitude"], 86.222848, places=4)
        self.assertEqual(meta_west["district_name"], "Purulia")

    def test_03_coarse_nwp_grid_centroid_calculation(self):
        # Test 0.25° NWP atmospheric grid calculation
        grid_lat, grid_lon = compute_nwp_coarse_centroid(22.804947, 88.509614)
        self.assertAlmostEqual(grid_lat, 22.75, places=2)
        self.assertAlmostEqual(grid_lon, 88.50, places=2)

        # Distance should be positive and under ~30km (representing ~25km NWP grid resolution)
        dist = haversine_distance_km(22.804947, 88.509614, grid_lat, grid_lon)
        self.assertGreater(dist, 0.5)
        self.assertLess(dist, 25.0)

    def test_04_forecast_engine_returns_exact_coordinates(self):
        res = forecast_panchayat_v2("WB_107778", days=3, live=False)
        self.assertIn("latitude", res)
        self.assertIn("longitude", res)
        self.assertIn("panchayat_lat", res)
        self.assertIn("panchayat_lon", res)
        self.assertIn("grid_distance_km", res)
        self.assertIn("coarse_coordinate", res)

        self.assertAlmostEqual(res["latitude"], 22.804947, places=4)
        self.assertAlmostEqual(res["longitude"], 88.509614, places=4)
        self.assertGreater(res["grid_distance_km"], 0.0)

    def test_05_api_forecast_payload_coordinates(self):
        resp = get_forecast(panchayat_id="WB_107778", days=3, live=False)
        data = json.loads(resp.body.decode("utf-8"))

        self.assertIn("latitude", data)
        self.assertIn("longitude", data)
        self.assertIn("panchayat_lat", data)
        self.assertIn("panchayat_lon", data)
        self.assertIn("grid_distance_km", data)
        self.assertIn("coarse_coordinate", data)

        self.assertAlmostEqual(data["latitude"], 22.804947, places=4)
        self.assertAlmostEqual(data["longitude"], 88.509614, places=4)
        self.assertAlmostEqual(data["coarse_coordinate"]["latitude"], 22.75, places=2)
        self.assertAlmostEqual(data["coarse_coordinate"]["longitude"], 88.50, places=2)
        self.assertGreater(data["grid_distance_km"], 0.0)

    def test_06_statewide_api_forecast_payload_coordinates(self):
        # Purulia GP through API
        resp = get_forecast(panchayat_id="WB_109832", days=2, live=False)
        data = json.loads(resp.body.decode("utf-8"))

        self.assertEqual(data["district_name"], "Purulia")
        self.assertAlmostEqual(data["latitude"], 23.4405, places=3)
        self.assertAlmostEqual(data["longitude"], 86.2228, places=3)
        # Verify coarse coordinate is in Purulia, NOT stuck at Amdanga!
        self.assertAlmostEqual(data["coarse_coordinate"]["latitude"], 23.50, places=2)
        self.assertAlmostEqual(data["coarse_coordinate"]["longitude"], 86.25, places=2)
        self.assertLess(data["grid_distance_km"], 15.0)

    def test_07_gps_nearest_panchayat_resolution(self):
        """Verify modern GPS coordinate detection resolves to the accurate nearest Gram Panchayat."""
        # Test GPS fix near Amdanga GP centroid (22.805, 88.510)
        res = get_nearest_panchayat(lat=22.805, lon=88.510, limit=3)
        self.assertEqual(res["status"], "ok")
        nearest = res["nearest_panchayat"]
        self.assertEqual(nearest["panchayat_name"], "AMDANGA")
        self.assertEqual(nearest["gp_code"], 107778)
        self.assertLess(nearest["distance_km"], 0.2)
        self.assertEqual(len(res["nearby_panchayats"]), 3)

        # Test GPS fix near Purulia / Balarampur (23.10, 86.22)
        res_purulia = get_nearest_panchayat(lat=23.10, lon=86.22, limit=1)
        self.assertEqual(res_purulia["status"], "ok")
        nearest_p = res_purulia["nearest_panchayat"]
        self.assertEqual(nearest_p["district_name"], "Purulia")
        self.assertLess(nearest_p["distance_km"], 10.0)

    def test_08_statewide_boundaries_endpoint(self):
        """Verify /v1/statewide/boundaries generates contiguous Voronoi polygons across districts."""
        # Purulia
        res_purulia = get_panchayat_boundaries(panchayat_id="WB_109832")
        self.assertEqual(res_purulia["type"], "FeatureCollection")
        self.assertEqual(res_purulia["selected_panchayat_id"], "WB_109832")
        self.assertGreater(len(res_purulia["features"]), 5)
        for f in res_purulia["features"]:
            self.assertEqual(f["geometry"]["type"], "Polygon")
            self.assertGreater(len(f["geometry"]["coordinates"][0]), 3)
            self.assertGreater(f["properties"]["area_sqkm"], 0.0)

        # Alipurduar
        res_alipur = get_panchayat_boundaries(panchayat_id="WB_107001")
        self.assertEqual(res_alipur["selected_panchayat_id"], "WB_107001")
        self.assertGreater(len(res_alipur["features"]), 5)

    def test_09_amdanga_surveyed_boundaries(self):
        """Verify Amdanga pilot block returns 100% official surveyed cadastral boundaries."""
        res_amdanga = get_panchayat_boundaries(panchayat_id="WB_107778")
        self.assertEqual(res_amdanga["selected_panchayat_id"], "WB_107778")
        self.assertEqual(len(res_amdanga["features"]), 8)
        amdanga_feat = next(f for f in res_amdanga["features"] if f["properties"]["gp_code"] == 107778)
        self.assertEqual(amdanga_feat["properties"]["geometry_source"], "official_cadastral_survey")
        self.assertGreater(amdanga_feat["properties"]["area_sqkm"], 5.0)


if __name__ == "__main__":
    unittest.main()

