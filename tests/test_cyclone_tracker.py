import json
import unittest
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "backend"))

from backend.cyclone_engine import (
    haversine_km,
    get_bearing,
    get_active_cyclone_telemetry,
    fetch_live_radar_timestamps,
    ACTIVE_STORM_SYSTEM,
)
from backend.api import get_cyclone_tracker, get_radar_timestamps


class TestCycloneAndStormTracker(unittest.TestCase):
    """Verify cyclone tracking telemetry, distance calculations, and API contracts."""

    def test_01_haversine_and_bearing_math(self):
        # Kolkata (22.57, 88.36) to Digha (21.62, 87.50) is ~140-150 km
        dist = haversine_km(22.57, 88.36, 21.62, 87.50)
        self.assertGreater(dist, 130.0)
        self.assertLess(dist, 160.0)

        bearing = get_bearing(22.57, 88.36, 21.62, 87.50)
        self.assertIn(bearing, ["SW", "SSW", "WSW"])

    def test_02_active_cyclone_telemetry_structure(self):
        telemetry = get_active_cyclone_telemetry(22.804947, 88.509614)
        self.assertEqual(telemetry["status"], "active_system")
        self.assertTrue(telemetry["has_active_system"])

        storm = telemetry["storm"]
        self.assertEqual(storm["system_id"], "BOB-2026-DD01")
        self.assertIn("Bay of Bengal Deep Depression", storm["name"])
        self.assertEqual(storm["classification"], "Depression")
        self.assertEqual(storm["peak_classification"], "Deep Depression")
        self.assertIn("Kalingapatnam", storm["landfall"]["location"])

        # Intensity and wind checks
        self.assertEqual(storm["intensity"]["sustained_wind_kmh"], 45)
        self.assertEqual(storm["intensity"]["gusts_kmh"], 65)
        self.assertFalse(storm["intensity"]["is_cyclone_intensity"])
        self.assertIn("Arnab", storm["intensity"]["naming_explanation"])

        # Relative to GP metrics
        relative = storm["relative_to_gp"]
        self.assertGreater(relative["distance_km"], 600.0)
        self.assertLess(relative["distance_km"], 750.0)
        self.assertIn(relative["threat_level"], ["ADVISORY", "MONITORING"])

    def test_03_marine_and_port_warnings(self):
        storm = ACTIVE_STORM_SYSTEM
        ports = [p["port"] for p in storm["marine_warnings"]["port_signals"]]
        self.assertTrue(any("Kolkata" in p for p in ports))
        self.assertTrue(any("Haldia" in p for p in ports))
        self.assertIn("LC3", storm["marine_warnings"]["port_signals"][0]["signal"])

        # High risk coastal districts
        districts = storm["regional_rain_threat"]["high_risk_districts"]
        self.assertIn("South 24 Parganas", districts)
        self.assertIn("East Midnapore", districts)

    def test_04_api_cyclone_tracker_endpoint(self):
        resp = get_cyclone_tracker(panchayat_id="WB_107778")
        self.assertEqual(resp["status"], "active_system")
        self.assertTrue(resp["has_active_system"])
        self.assertIn("relative_to_gp", resp["storm"])
        self.assertGreater(resp["storm"]["relative_to_gp"]["distance_km"], 0)

    def test_05_api_radar_timestamps_endpoint(self):
        resp = get_radar_timestamps()
        self.assertIn(resp["status"], ["ok", "fallback"])
        self.assertIn("host", resp)
        self.assertTrue(resp["host"].startswith("http"))


if __name__ == "__main__":
    unittest.main()
