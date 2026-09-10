"""
Unit Tests for Pydantic v2 API Schemas
Verifies strict validation, schema fidelity, and OpenAPI schema registration.
"""

import unittest
from backend.api import (
    root,
    health,
    get_panchayats,
    get_statewide_districts,
    get_statewide_stats,
    get_nearest_panchayat,
)
from backend.forecast_engine_v2 import forecast_panchayat_v2
from backend.schemas import (
    RootResponse,
    HealthResponse,
    PanchayatListResponse,
    StatewideDistrictsResponse,
    StatewideStatsResponse,
    ForecastResponse,
    NearestPanchayatResponse,
)


class TestAPISchemas(unittest.TestCase):
    """Tests for Pydantic v2 Schema validation."""

    def test_root_schema(self):
        res = root()
        model = RootResponse.model_validate(res)
        self.assertEqual(model.status, "online")

    def test_health_schema(self):
        res = health()
        model = HealthResponse.model_validate(res)
        self.assertEqual(model.status, "ok")
        self.assertFalse(model.degraded)

    def test_panchayats_schema(self):
        res = get_panchayats()
        model = PanchayatListResponse.model_validate(res)
        self.assertGreater(model.count, 0)

    def test_districts_schema(self):
        res = get_statewide_districts()
        model = StatewideDistrictsResponse.model_validate(res)
        self.assertEqual(model.state, "West Bengal")
        self.assertEqual(model.district_count, 22)

    def test_stats_schema(self):
        res = get_statewide_stats()
        model = StatewideStatsResponse.model_validate(res)
        self.assertEqual(model.total_panchayats, 3339)
        self.assertEqual(model.total_districts, 22)

    def test_forecast_schema_offline(self):
        data = forecast_panchayat_v2("A2", days=3, live=False)
        model = ForecastResponse.model_validate(data)
        self.assertEqual(model.panchayat_name, "AMDANGA")
        self.assertEqual(len(model.forecast), 3)
        self.assertIsNotNone(model.forecast[0].rain_mm.p50)

    def test_nearest_schema(self):
        res = get_nearest_panchayat(lat=22.5726, lon=88.3639, limit=3)
        model = NearestPanchayatResponse.model_validate(res)
        self.assertEqual(model.status, "ok")
        self.assertIn("panchayat_name", model.nearest_panchayat)
        self.assertIn("distance_km", model.nearest_panchayat)
        self.assertIsInstance(model.nearest_panchayat["distance_km"], float)
        self.assertEqual(len(model.nearby_panchayats), 3)
        self.assertEqual(model.nearby_panchayats[0]["panchayat_name"], model.nearest_panchayat["panchayat_name"])


if __name__ == "__main__":
    unittest.main()
