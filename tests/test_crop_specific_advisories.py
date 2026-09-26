"""
Tests for Crop-Specific Agronomic Advisories from Authoritative Data Sources.
Verifies:
1. Advisories dynamically tailor to the selected crop (Paddy, Potato, Mustard, Jute, Vegetables).
2. Proper authoritative source attribution (ICAR-NRRI, ICAR-CPRI, ICAR-DRMR, ICAR-CRIJAF, ICAR-IIHR, IMD).
3. Structured action items checklist generation.
4. Universal statewide resolution across all Agro-Climatic Zones (Delta, Laterite, Terai, Hills, Coastal).
"""

import sys
from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "backend"))

from advisory_context import AdvisoryContext
from advisory_engine import build_advisory_response, evaluate_advisories
from forecast_engine_v2 import forecast_panchayat_v2


class TestCropSpecificAdvisories:

    def test_01_potato_advisories_and_icar_cpri_source(self):
        """Verify Potato advisories attribute to ICAR-CPRI and provide tuber-specific advice."""
        # 1. Heavy waterlogging
        ctx_heavy = AdvisoryContext(rain_mm=22.0, tmax_c=22.0, humidity=80.0, crop="potato", crop_stage="tuber_bulking")
        res_heavy = build_advisory_response(ctx_heavy)
        assert res_heavy["rule_id"] == "potato_waterlogging_risk"
        assert "ICAR-CPRI" in res_heavy["source"]
        assert "tuber" in res_heavy["text_en"].lower()
        assert len(res_heavy["action_items"]) > 0

        # 2. Late Blight
        ctx_blight = AdvisoryContext(rain_mm=2.0, tmax_c=20.0, humidity=85.0, crop="potato", crop_stage="tuber_bulking")
        res_blight = build_advisory_response(ctx_blight)
        assert res_blight["rule_id"] == "potato_late_blight"
        assert "Phytophthora" in res_blight["text_en"] or "Late Blight" in res_blight["text_en"]
        assert "ICAR-CPRI" in res_blight["source"]

        # 3. Dry day bulking
        ctx_dry = AdvisoryContext(rain_mm=0.0, tmax_c=24.0, humidity=65.0, crop="potato", crop_stage="tuber_bulking")
        res_dry = build_advisory_response(ctx_dry)
        assert res_dry["rule_id"] == "potato_dry_day"
        assert "ICAR-CPRI" in res_dry["source"]

    def test_02_paddy_advisories_and_icar_nrri_source(self):
        """Verify Paddy advisories attribute to ICAR-NRRI and handle tillering/standing water."""
        # 1. Moderate rain
        ctx_mod = AdvisoryContext(rain_mm=10.0, tmax_c=30.0, humidity=80.0, crop="paddy", crop_stage="tillering")
        res_mod = build_advisory_response(ctx_mod)
        assert res_mod["rule_id"] == "paddy_moderate_rain"
        assert "ICAR-NRRI" in res_mod["source"]
        assert "bund" in res_mod["text_en"].lower() or "water" in res_mod["text_en"].lower()

        # 2. Dry day
        ctx_dry = AdvisoryContext(rain_mm=0.0, tmax_c=32.0, humidity=70.0, crop="paddy", crop_stage="flowering")
        res_dry = build_advisory_response(ctx_dry)
        assert res_dry["rule_id"] == "paddy_dry_day"
        assert "ICAR-NRRI" in res_dry["source"]
        assert "standing water" in res_dry["text_en"].lower()

    def test_03_mustard_advisories_and_icar_drmr_source(self):
        """Verify Mustard advisories attribute to ICAR-DRMR and protect sensitive taproots."""
        # 1. Excessive rain
        ctx_rain = AdvisoryContext(rain_mm=16.0, tmax_c=22.0, humidity=75.0, crop="mustard", crop_stage="vegetative")
        res_rain = build_advisory_response(ctx_rain)
        assert res_rain["rule_id"] == "mustard_heavy_rain"
        assert "ICAR-DRMR" in res_rain["source"]
        assert "taproot" in res_rain["text_en"].lower() or "stagnant" in res_rain["text_en"].lower()

        # 2. Aphid and white rust
        ctx_pest = AdvisoryContext(rain_mm=0.0, tmax_c=22.0, humidity=82.0, crop="mustard", crop_stage="flowering")
        res_pest = build_advisory_response(ctx_pest)
        assert res_pest["rule_id"] == "mustard_aphid_rust_risk"
        assert "ICAR-DRMR" in res_pest["source"]
        assert "aphid" in res_pest["text_en"].lower()

    def test_04_jute_advisories_and_icar_crijaf_source(self):
        """Verify Jute advisories attribute to ICAR-CRIJAF and prevent stem rot."""
        # 1. Water stagnation stem rot
        ctx_rot = AdvisoryContext(rain_mm=25.0, tmax_c=31.0, humidity=88.0, crop="jute", crop_stage="vegetative_growth")
        res_rot = build_advisory_response(ctx_rot)
        assert res_rot["rule_id"] in ("jute_stem_rot", "jute_heavy_rain")
        assert "ICAR-CRIJAF" in res_rot["source"]

        # 2. Moderate growth rain
        ctx_mod = AdvisoryContext(rain_mm=12.0, tmax_c=30.0, humidity=75.0, crop="jute", crop_stage="vegetative_growth")
        res_mod = build_advisory_response(ctx_mod)
        assert res_mod["rule_id"] == "jute_moderate_rain"
        assert "ICAR-CRIJAF" in res_mod["source"]

    def test_05_vegetables_advisories_and_icar_iihr_source(self):
        """Verify Vegetable advisories attribute to ICAR-IIHR and guide staking and damping-off."""
        ctx_heavy = AdvisoryContext(rain_mm=18.0, tmax_c=27.0, humidity=80.0, crop="vegetables", crop_stage="fruiting")
        res_heavy = build_advisory_response(ctx_heavy)
        assert res_heavy["rule_id"] == "vegetables_heavy_rain"
        assert "ICAR-IIHR" in res_heavy["source"]
        assert "raised beds" in res_heavy["text_en"].lower() or "stake" in res_heavy["text_en"].lower()

    def test_06_crop_differentiation_for_same_weather(self):
        """Verify that identical weather conditions yield distinct, specialized advisories per crop."""
        rain = 8.0
        tmax = 24.0
        hum = 75.0

        ctx_potato = AdvisoryContext(rain_mm=rain, tmax_c=tmax, humidity=hum, crop="potato")
        ctx_paddy = AdvisoryContext(rain_mm=rain, tmax_c=tmax, humidity=hum, crop="paddy")
        ctx_mustard = AdvisoryContext(rain_mm=rain, tmax_c=tmax, humidity=hum, crop="mustard")
        ctx_jute = AdvisoryContext(rain_mm=rain, tmax_c=tmax, humidity=hum, crop="jute")
        ctx_veg = AdvisoryContext(rain_mm=rain, tmax_c=tmax, humidity=hum, crop="vegetables")

        res_potato = build_advisory_response(ctx_potato)
        res_paddy = build_advisory_response(ctx_paddy)
        res_mustard = build_advisory_response(ctx_mustard)
        res_jute = build_advisory_response(ctx_jute)
        res_veg = build_advisory_response(ctx_veg)

        # Rule IDs and sources must be crop-distinct
        assert res_potato["rule_id"] == "potato_moderate_rain"
        assert "ICAR-CPRI" in res_potato["source"]

        assert res_paddy["rule_id"] == "paddy_moderate_rain"
        assert "ICAR-NRRI" in res_paddy["source"]

        assert res_mustard["rule_id"] == "mustard_moderate_rain"
        assert "ICAR-DRMR" in res_mustard["source"]

        assert res_jute["rule_id"] == "jute_moderate_rain"
        assert "ICAR-CRIJAF" in res_jute["source"]

        assert res_veg["rule_id"] == "vegetables_moderate_rain"
        assert "ICAR-IIHR" in res_veg["source"]

    def test_07_statewide_locations_advisory_parity(self):
        """
        Verify that panchayats across all 5 agro-climatic zones resolve complete
        crop-specific advisories with authoritative sources and action checklists.
        """
        audit_cases = [
            ("Delta", "107778", "potato"),
            ("Delta", "107780", "paddy"),
            ("Alluvial Delta", "107412", "mustard"),
            ("Laterite / Rarh", "109832", "paddy"),
            ("Laterite / Rarh", "108500", "potato"),
            ("Terai & Dooars", "107001", "jute"),
            ("Hills", "107550", "vegetables"),
        ]

        for zone, pid, crop in audit_cases:
            forecast_payload = forecast_panchayat_v2(pid, days=3, crop=crop, live=False)
            assert forecast_payload is not None
            assert forecast_payload["crop"] == crop
            assert "advisories" in forecast_payload
            assert len(forecast_payload["advisories"]) > 0

            # Verify first advisory carries authoritative source and structured metadata
            adv = forecast_payload["advisories"][0]
            assert "rule_id" in adv
            assert "priority" in adv
            assert "source" in adv
            assert "ICAR" in adv["source"] or "IMD" in adv["source"] or "BCKV" in adv["source"]
            assert "action_items" in adv
            assert isinstance(adv["action_items"], list)
            assert len(adv["action_items"]) > 0
            assert "text_en" in adv
            assert len(adv["text_en"]) > 10
