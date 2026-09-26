"""
Automated Test Suite for Live Agromet Advisory Source Fetching & Crop-Specific Invariants.
Verifies:
1. Strict crop-specific advisory generation across all 5 staple West Bengal crops (Paddy, Potato, Mustard, Jute, Vegetables).
2. Authoritative source resolution (ICAR-NRRI, ICAR-CPRI, ICAR-DRMR, ICAR-CRIJAF, ICAR-IIHR, IMD AAS / GKMS).
3. District-level AMFU mapping across West Bengal (BCKV Mohanpur, UBKV Pundibari, AMFU Chinsurah, Visva-Bharati Sriniketan, Kakdwip).
4. Live Agromet Bulletin API endpoint (/v1/crops/live-bulletin).
5. Seamless integration in /v1/forecast with live_agromet_bulletin and crop-strict advisories.
"""

import sys
import json
from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "backend"))

from backend.agromet_source_fetcher import (
    fetch_live_agromet_bulletin,
    REQUIRED_CROP_INSTITUTES,
    DISTRICT_AMFU_REGISTRY,
    _get_amfu_for_district,
    _compute_biweekly_cycle,
)
from backend.advisory_context import AdvisoryContext
from backend.advisory_engine import build_advisory_response, evaluate_advisories
from backend.forecast_engine_v2 import forecast_panchayat_v2
from backend.api import get_live_bulletin_endpoint, get_forecast


class TestAgrometSourceFetcher:

    def test_01_mandatory_crop_authoritative_sources(self):
        """Verify each crop is strictly mapped to its designated national ICAR institute."""
        assert "ICAR-NRRI" in REQUIRED_CROP_INSTITUTES["paddy"]["institute"]
        assert "BCKV" in REQUIRED_CROP_INSTITUTES["paddy"]["institute"]

        assert "ICAR-CPRI" in REQUIRED_CROP_INSTITUTES["potato"]["institute"]
        assert "BCKV" in REQUIRED_CROP_INSTITUTES["potato"]["institute"]

        assert "ICAR-DRMR" in REQUIRED_CROP_INSTITUTES["mustard"]["institute"]

        assert "ICAR-CRIJAF" in REQUIRED_CROP_INSTITUTES["jute"]["institute"]
        assert "Barrackpore" in REQUIRED_CROP_INSTITUTES["jute"]["institute"]

        assert "ICAR-IIHR" in REQUIRED_CROP_INSTITUTES["vegetables"]["institute"]

    def test_02_district_amfu_registry_resolution(self):
        """Verify proper resolution of designated Agromet Field Units (AMFUs) across Bengal districts."""
        # Nadia / North 24 Parganas -> AMFU Mohanpur (BCKV)
        amfu_nadia = _get_amfu_for_district("Nadia")
        assert "Mohanpur" in amfu_nadia["nodal_center"]
        assert "BCKV" in amfu_nadia["university"]

        # Hooghly -> AMFU Chinsurah
        amfu_hooghly = _get_amfu_for_district("Hooghly")
        assert "Chinsurah" in amfu_hooghly["nodal_center"]

        # Jalpaiguri / Cooch Behar -> AMFU Pundibari (UBKV)
        amfu_jalp = _get_amfu_for_district("Jalpaiguri")
        assert "Pundibari" in amfu_jalp["nodal_center"]
        assert "UBKV" in amfu_jalp["university"]

        # Birbhum -> AMFU Sriniketan (Visva-Bharati)
        amfu_birbhum = _get_amfu_for_district("Birbhum")
        assert "Sriniketan" in amfu_birbhum["nodal_center"]
        assert "Visva-Bharati" in amfu_birbhum["university"]

        # South 24 Parganas -> Coastal Station Kakdwip / Nimpith
        amfu_s24p = _get_amfu_for_district("South 24 Parganas")
        assert "Kakdwip" in amfu_s24p["nodal_center"] or "Nimpith" in amfu_s24p["nodal_center"]

    def test_03_live_agromet_bulletin_payload_structure(self):
        """Verify bulletin compilation returns a verified IMD/GKMS structure with full metadata."""
        bulletin = fetch_live_agromet_bulletin(district="Hooghly", crop="potato")
        assert bulletin["status"] == "success"
        assert bulletin["verification_status"] == "OFFICIAL_IMD_GKMS_VERIFIED"
        assert bulletin["bulletin_number"].startswith("IMD/AAS/WB/")
        assert "ICAR-CPRI" in bulletin["required_source"]
        assert "Chinsurah" in bulletin["amfu_center"]
        assert len(bulletin["synoptic_weather_overview"]) > 20
        assert "advisory_summary" in bulletin["crop_advisory"]
        assert len(bulletin["crop_advisory"]["action_checklist"]) > 0

    def test_04_api_live_bulletin_endpoint(self):
        """Verify GET /v1/crops/live-bulletin endpoint returns valid bulletin data."""
        crops = ["paddy", "potato", "mustard", "jute", "vegetables"]
        for crop in crops:
            resp = get_live_bulletin_endpoint(district="Nadia", crop=crop)
            data = json.loads(resp.body.decode("utf-8"))
            assert data["selected_crop"] == crop
            assert data["verification_status"] == "OFFICIAL_IMD_GKMS_VERIFIED"
            assert "bulletin_number" in data
            assert len(data["issuing_bodies"]) >= 3

    def test_05_forecast_endpoint_crop_strict_advisories_and_bulletin(self):
        """Verify /v1/forecast embeds live_agromet_bulletin and tailors advisories strictly to crop."""
        test_cases = [
            ("paddy", "ICAR-NRRI"),
            ("potato", "ICAR-CPRI"),
            ("mustard", "ICAR-DRMR"),
            ("jute", "ICAR-CRIJAF"),
            ("vegetables", "ICAR-IIHR"),
        ]

        for crop, expected_inst in test_cases:
            res = forecast_panchayat_v2("WB_107778", days=5, crop=crop, live=False)
            assert res["crop"] == crop
            assert "live_agromet_bulletin" in res
            bulletin = res["live_agromet_bulletin"]
            assert expected_inst in bulletin["required_source"]
            assert bulletin["bulletin_number"].startswith("IMD/AAS/WB/")

            advs = res["advisories"]
            assert len(advs) > 0
            for a in advs:
                # Every single advisory must strictly match the selected crop
                assert a["crop"] == crop
                # Every advisory must attribute to the required authoritative source
                assert expected_inst in a["source"] or expected_inst in a.get("required_source", "")
                assert a.get("bulletin_ref") is not None

    def test_06_paddy_heavy_rain_rule_grounded_in_nrri(self):
        """Verify paddy heavy rainfall (>20mm) specifically triggers paddy_heavy_rain citing ICAR-NRRI."""
        ctx = AdvisoryContext(rain_mm=26.0, tmax_c=30.0, humidity=85.0, crop="paddy", crop_stage="tillering")
        res = build_advisory_response(ctx)
        assert res["rule_id"] == "paddy_heavy_rain"
        assert "ICAR-NRRI" in res["source"]
        assert "submergence" in res["text_en"].lower() or "spraying" in res["text_en"].lower()
        assert len(res["action_items"]) >= 2

    def test_07_crop_specific_sandy_soil_dry_spell_rules(self):
        """Verify each of the 5 crops has its dedicated dry spell rule on sandy soil citing its required institute."""
        crop_rules = [
            ("paddy", "paddy_sandy_soil_dry_spell", "ICAR-NRRI"),
            ("potato", "potato_sandy_soil_dry_spell", "ICAR-CPRI"),
            ("mustard", "mustard_sandy_soil_dry_spell", "ICAR-DRMR"),
            ("jute", "jute_sandy_soil_dry_spell", "ICAR-CRIJAF"),
            ("vegetables", "vegetables_sandy_soil_dry_spell", "ICAR-IIHR"),
        ]

        for crop, expected_rule, expected_source in crop_rules:
            ctx = AdvisoryContext(
                rain_mm=0.0,
                tmax_c=31.0,
                dry_days=8,
                soil_type="sandy",
                crop=crop,
                crop_stage="vegetative",
            )
            res = build_advisory_response(ctx)
            assert res["rule_id"] == expected_rule
            assert expected_source in res["source"]
            assert len(res["action_items"]) >= 2

