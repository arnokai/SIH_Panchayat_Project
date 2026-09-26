"""
Unit Test Suite for TerraMind Forecast Engine & Live Ingestion.
==================================================================
Tests:
- Offline coarse forecast downscaling for pilot & statewide GPs
- Dynamic live meteorological data fetching and in-memory TTL caching
- Monotonic quantile constraints (0 <= P10 <= P50 <= P90)
- Agronomic advisory generation in English
- Robust error handling for invalid panchayats, invalid day ranges
- API endpoints /health and /v1/forecast integration
"""

import json
import unittest
from pathlib import Path

import pandas as pd
from fastapi import HTTPException

from backend.api import get_forecast, health
from backend.forecast_engine_v2 import (
    _LIVE_WEATHER_CACHE,
    fetch_live_block_weather,
    forecast_panchayat_v2,
    refine_hourly_weather,
    resolve_panchayat_meta,
)


class TestForecastEngineV2(unittest.TestCase):
    """Authoritative test cases for V2 Hurdle Forecast Engine and Live Connectors."""

    def test_01_pilot_panchayat_offline_downscaling(self):
        """Verify offline forecast downscaling for Amdanga pilot GP A2."""
        res = forecast_panchayat_v2("A2", days=5, live=False)
        self.assertEqual(res["panchayat_name"], "AMDANGA")
        self.assertFalse(res["is_live_dynamic"])
        self.assertFalse(res["degraded"])
        self.assertEqual(len(res["forecast"]), 5)

        for day in res["forecast"]:
            rain = day["rain_mm"]
            self.assertIn("p10", rain)
            self.assertIn("p50", rain)
            self.assertIn("p90", rain)
            # Strict physical monotonicity invariant
            self.assertGreaterEqual(rain["p10"], 0.0)
            self.assertLessEqual(rain["p10"], rain["p50"] + 1e-6)
            self.assertLessEqual(rain["p50"], rain["p90"] + 1e-6)

            # Advisory completeness
            advisory = day["advisory"]
            self.assertIn("rule_id", advisory)
            self.assertIn("priority", advisory)
            self.assertIn("text_en", advisory)
            self.assertIn("text_bn", advisory)

    def test_02_lgd_code_alias_resolution(self):
        """Verify LGD code WB_107778 correctly resolves to Amdanga with equal canonical ID."""
        meta = resolve_panchayat_meta("WB_107778")
        self.assertIsNotNone(meta)
        self.assertEqual(meta["canonical_id"], "WB_107778")
        self.assertEqual(meta["panchayat_name"], "AMDANGA")

        res = forecast_panchayat_v2("WB_107778", days=3, live=False)
        self.assertEqual(res["panchayat_name"], "AMDANGA")
        self.assertEqual(len(res["forecast"]), 3)

    def test_03_statewide_panchayat_offline_resolution(self):
        """Verify arbitrary statewide GP (Darjeeling WB_107901) resolves with elevation features."""
        meta = resolve_panchayat_meta("WB_107901")
        self.assertIsNotNone(meta)
        self.assertEqual(meta["district_name"], "Darjeeling")

        res = forecast_panchayat_v2("WB_107901", days=3, live=False)
        self.assertEqual(res["district_name"], "Darjeeling")
        self.assertFalse(res["is_live_dynamic"])
        self.assertFalse(res["degraded"])
        self.assertEqual(len(res["forecast"]), 3)

    def test_04_invalid_panchayat_raises_error(self):
        """Verify invalid panchayat ID raises ValueError."""
        with self.assertRaises(ValueError):
            forecast_panchayat_v2("NON_EXISTENT_GP_9999", days=3)

    def test_05_invalid_days_range_raises_error(self):
        """Verify day limits (1 to 5) are strictly enforced."""
        with self.assertRaises(ValueError):
            forecast_panchayat_v2("A2", days=0)
        with self.assertRaises(ValueError):
            forecast_panchayat_v2("A2", days=6)

    def test_06_api_health_endpoint(self):
        """Verify API /health returns operational statewide hurdle model status."""
        h = health()
        self.assertEqual(h["status"], "ok")
        self.assertFalse(h["degraded"])
        self.assertTrue(h["live_weather_enabled"])
        self.assertIn("3,339", h["statewide_coverage"])

    def test_07_api_get_forecast_endpoint_offline(self):
        """Verify API /v1/forecast returns valid UTF-8 JSON response."""
        resp = get_forecast("A2", days=3, live=False)
        data = json.loads(resp.body.decode("utf-8"))
        self.assertEqual(data["panchayat_name"], "AMDANGA")
        self.assertFalse(data["is_live_dynamic"])
        self.assertEqual(len(data["forecast"]), 3)

    def test_08_api_get_forecast_statewide_endpoint(self):
        """Verify API /v1/forecast serves statewide panchayats."""
        resp = get_forecast("WB_107901", days=2, live=False)
        data = json.loads(resp.body.decode("utf-8"))
        self.assertEqual(data["district_name"], "Darjeeling")
        self.assertEqual(len(data["forecast"]), 2)

    def test_09_api_invalid_panchayat_404(self):
        """Verify API raises 404 HTTPException for unknown panchayats."""
        with self.assertRaises(HTTPException) as ctx:
            get_forecast("UNKNOWN_GP")
        self.assertEqual(ctx.exception.status_code, 404)

    def test_10_live_weather_cache_ttl(self):
        """Verify live weather fetcher in-memory TTL caching."""
        fake_lat, fake_lon = 22.82, 88.52
        cache_key = (round(fake_lat, 4), round(fake_lon, 4), 5)
        dummy_df = pd.DataFrame([{"dummy": 1}])
        _LIVE_WEATHER_CACHE[cache_key] = (9999999999.0, dummy_df, None)

        fetched_df, fetched_live = fetch_live_block_weather(fake_lat, fake_lon, days=5)
        self.assertIsNotNone(fetched_df)
        self.assertIn("dummy", fetched_df.columns)
        _LIVE_WEATHER_CACHE.pop(cache_key, None)

    def test_11_refine_hourly_weather_spray_safety_and_lapse_rate(self):
        """Verify DEM lapse rate adjustment and agronomic spray safety classification."""
        dummy_live_data = {
            "current": {"temperature_2m": 30.0},
            "hourly": {
                "time": ["2026-09-10T10:00", "2026-09-10T11:00", "2026-09-10T12:00"],
                "temperature_2m": [28.0, 30.0, 32.0],
                "precipitation_probability": [10, 60, 20],
                "precipitation": [0.0, 1.5, 0.0],
                "weather_code": [1, 61, 1],
                "wind_speed_10m": [5.0, 8.0, 18.0],
            },
        }
        dummy_gp_feat = {"relative_elevation_m": 100.0, "elevation_dem_m": 150.0}
        refined = refine_hourly_weather(dummy_live_data, {"panchayat_name": "Test"}, dummy_gp_feat)

        self.assertIsNotNone(refined)
        self.assertEqual(refined["operational_refinement"]["lapse_rate_c"], -0.65)
        self.assertEqual(refined["current"]["temperature_2m"], 29.4)
        self.assertEqual(refined["hourly"]["temperature_2m"], [27.4, 29.4, 31.4])

        records = refined["hourly"]["records"]
        self.assertEqual(len(records), 3)
        self.assertEqual(records[0]["spray_safety"], "optimal")
        self.assertEqual(records[1]["spray_safety"], "unsafe_rain")
        self.assertEqual(records[2]["spray_safety"], "unsafe_wind")
        self.assertTrue(len(refined["operational_insight"]) > 0)


if __name__ == "__main__":
    unittest.main()
