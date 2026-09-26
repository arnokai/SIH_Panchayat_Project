"""
Unit and Integration Tests for Machine 2: PMFBY Insurance & Dynamic Phenology.
"""

import pytest
from datetime import date
from backend.api import get_insurance_certificate
from backend.phenology_engine import get_crop_phenology, calculate_daily_gdd
from backend.insurance_engine import (
    evaluate_parametric_triggers,
    generate_pmfby_certificate,
    resolve_agro_climatic_zone,
)


def test_gdd_calculation():
    """Verify standard GDD calculation."""
    # Base 10, Tmax 34, Tmin 24 -> Tavg 29 -> GDD 19
    gdd = calculate_daily_gdd(tmax=34.0, tmin=24.0, t_base=10.0)
    assert gdd == 19.0

    # Cold day below base -> 0
    cold_gdd = calculate_daily_gdd(tmax=8.0, tmin=4.0, t_base=10.0)
    assert cold_gdd == 0.0


def test_crop_phenology_paddy():
    """Verify dynamic phenology mapping for Paddy."""
    pheno = get_crop_phenology("paddy", target_date=date(2026, 9, 26), tmax=32.0, tmin=24.0)
    assert pheno["crop"] == "paddy"
    assert pheno["t_base_c"] == 10.0
    assert pheno["accumulated_gdd"] > 0
    assert pheno["current_stage"] in ["vegetative", "tillering", "flowering", "harvest"]
    assert pheno["current_stage_bn"] != ""
    assert pheno["critical_risk_factor"] != ""


def test_agro_climatic_zone_classification():
    """Verify district classification into 3 distinct zones."""
    assert "Delta" in resolve_agro_climatic_zone("North 24 Parganas")
    assert "Delta" in resolve_agro_climatic_zone("South 24 Parganas")
    assert "Laterite" in resolve_agro_climatic_zone("Purulia")
    assert "Laterite" in resolve_agro_climatic_zone("Bankura")
    assert "Terai" in resolve_agro_climatic_zone("Darjeeling")
    assert "Terai" in resolve_agro_climatic_zone("Jalpaiguri")


def test_pmfby_excess_rain_trigger():
    """Verify excess rain (>60mm) fires insurance trigger."""
    forecast_days = [
        {"rain_mm": {"p50": 10.0}, "tmax_c": {"p50": 31.0}},
        {"rain_mm": {"p50": 72.0}, "tmax_c": {"p50": 29.0}}, # >60mm
        {"rain_mm": {"p50": 15.0}, "tmax_c": {"p50": 30.0}},
    ]
    cert = generate_pmfby_certificate(
        panchayat_id="WB_107778",
        panchayat_name="AMDANGA",
        block_name="AMDANGA",
        district_name="North 24 Parganas",
        forecast_days=forecast_days,
        crop="paddy",
        dry_days=2,
    )

    assert cert["claim_eligible"] is True
    assert cert["verification_hash"] != ""
    assert len(cert["verification_hash"]) == 64 # SHA-256


def test_api_insurance_certificate_endpoint():
    """Test get_insurance_certificate returns valid certificate."""
    data = get_insurance_certificate(panchayat_id="WB_107778", crop="paddy")
    assert data["panchayat_id"] == "WB_107778"
    assert "verification_hash" in data
    assert "phenology" in data
    assert len(data["triggers_evaluated"]) == 4
