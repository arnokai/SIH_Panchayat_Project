"""
Unit and integration tests for TerraMind Crop Advisory Intelligence Engine.
Tests:
1. Smart Fertilizer & NPK Dosage Calculator (Acres, Bighas, Commercial Bags, Rain Leaching Alert)
2. Agrochemical Spray Advisor (Delta-T, Wind Speed Drift, Rainfastness Lead Time, WALES Mixing Order)
3. Crop Water Requirement & Irrigation Budget (FAO-56 Hargreaves ET0, Kc, Effective Rain, 5HP Pumping Hours)
4. Pest & Disease Doctor Catalog (Symptoms, Active Formulations, Dilutions, PHI, Bio-Control)
5. Stage-Wise Package of Practices (POP Operations, Water, Nutrient Timing, Scouting)
6. APMC Mandi Market Intelligence & Storage Criteria
7. Full API Endpoint Integration (/v1/crops/advisory-dossier)
"""

import json
import pytest
from backend.crop_advisory_intelligence import (
    calculate_fertilizer_dosage,
    evaluate_spray_suitability,
    calculate_crop_water_balance,
    get_crop_advisory_dossier,
    PEST_AND_DISEASE_DB,
    POP_CATALOG,
    MANDI_PRICE_DATA,
)
from backend.api import get_crop_advisory_dossier_endpoint


def test_fertilizer_dosage_acre_vs_bigha_equivalence():
    """Verify that 1 Acre equals 3 Bighas in nutrient calculations."""
    res_acre = calculate_fertilizer_dosage(crop="paddy", field_size=1.0, unit="acre", rain_next_24h_mm=0.0)
    res_bigha = calculate_fertilizer_dosage(crop="paddy", field_size=3.0, unit="bigha", rain_next_24h_mm=0.0)

    # Required nutrients in kg must match within floating precision
    assert abs(res_acre["nutrients_required_kg"]["nitrogen_n"] - res_bigha["nutrients_required_kg"]["nitrogen_n"]) < 0.2
    assert abs(res_acre["nutrients_required_kg"]["phosphorus_p2o5"] - res_bigha["nutrients_required_kg"]["phosphorus_p2o5"]) < 0.2
    assert abs(res_acre["nutrients_required_kg"]["potassium_k2o"] - res_bigha["nutrients_required_kg"]["potassium_k2o"]) < 0.2

    # Commercial bags must be calculated
    assert len(res_acre["commercial_fertilizers"]) == 3
    assert res_acre["commercial_fertilizers"][0]["name"].startswith("Urea")
    assert res_acre["commercial_fertilizers"][1]["name"].startswith("DAP")
    assert res_acre["commercial_fertilizers"][2]["name"].startswith("MOP")


def test_fertilizer_rain_leaching_risk_alert():
    """Verify that heavy rainfall forecast triggers the nitrogen leaching risk alert."""
    # Under dry forecast: no leaching risk
    dry_res = calculate_fertilizer_dosage(crop="paddy", field_size=1.0, unit="acre", rain_next_24h_mm=2.0)
    assert not dry_res["leaching_risk"]
    assert "Low Leaching Risk" in dry_res["leaching_alert"]

    # Under heavy rainfall (>10 mm): high leaching risk triggered
    wet_res = calculate_fertilizer_dosage(crop="paddy", field_size=1.0, unit="acre", rain_next_24h_mm=18.0)
    assert wet_res["leaching_risk"]
    assert "POSTPONE all urea" in wet_res["leaching_alert"]


def test_spray_suitability_evaluator():
    """Verify spray safety assessment across various meteorological thresholds."""
    # Ideal conditions: 24°C, 70% RH, 8 km/h wind, 0 rain
    ideal = evaluate_spray_suitability(
        temp_c=24.0, humidity_pct=70.0, wind_kmh=8.0, rain_prob=0.1, rain_mm_24h=0.0
    )
    assert ideal["status"] == "Optimal"
    assert ideal["score_pct"] >= 85
    assert "WALES" in ideal["tank_mixing_order_rule"]

    # High wind condition (>16 km/h drift threshold)
    windy = evaluate_spray_suitability(
        temp_c=24.0, humidity_pct=70.0, wind_kmh=20.0, rain_prob=0.1, rain_mm_24h=0.0
    )
    assert windy["status"] == "Unfavorable"
    assert any("wind speed" in r.lower() for r in windy["advisory_reasons"])

    # High rain probability / washout risk
    rainy = evaluate_spray_suitability(
        temp_c=24.0, humidity_pct=70.0, wind_kmh=8.0, rain_prob=0.85, rain_mm_24h=15.0
    )
    assert rainy["status"] == "Unfavorable"
    assert any("rain" in r.lower() for r in rainy["advisory_reasons"])


def test_crop_water_requirement_fao56():
    """Verify Hargreaves-Samani ET0 and FAO-56 crop water balance."""
    # Active tillering paddy on a dry hot day (34°C max, 24°C min, 0 rain)
    dry_day = calculate_crop_water_balance(
        crop="paddy", stage_name="tillering", tmax=34.0, tmin=24.0, rh=65.0, wind_kmh=10.0, rain_mm=0.0
    )
    assert dry_day["reference_et0_mm_day"] > 2.5
    assert dry_day["crop_coefficient_kc"] >= 1.05
    assert dry_day["crop_evapotranspiration_etc_mm_day"] > 3.0
    assert dry_day["net_irrigation_requirement_mm"] > 0.0
    assert dry_day["water_volume_liters_per_acre"] > 0

    # Wet day with 25 mm rain (should result in rain surplus, net irrigation = 0)
    wet_day = calculate_crop_water_balance(
        crop="paddy", stage_name="tillering", tmax=30.0, tmin=25.0, rh=85.0, wind_kmh=12.0, rain_mm=25.0
    )
    assert wet_day["net_irrigation_requirement_mm"] == 0.0
    assert "Rain Surplus" in wet_day["irrigation_status"]


def test_disease_doctor_catalog_completeness():
    """Verify diagnostic catalog for all 5 crops has required clinical fields."""
    for crop_name in ["paddy", "potato", "mustard", "jute", "vegetables"]:
        assert crop_name in PEST_AND_DISEASE_DB
        diseases = PEST_AND_DISEASE_DB[crop_name]
        assert len(diseases) >= 2

        for d in diseases:
            assert "name" in d
            assert "symptoms" in d and len(d["symptoms"]) > 0
            assert "weather_triggers" in d
            assert "chemical_control" in d
            cc = d["chemical_control"]
            assert "active_ingredient" in cc
            assert "dilution_per_liter" in cc
            assert "phi_days" in cc
            assert "biological_control" in d
            assert "cultural_prevention" in d
            assert "source" in d


def test_package_of_practices_stages():
    """Verify stage-wise POP catalog exists for all crops."""
    for crop_name in ["paddy", "potato", "mustard", "jute", "vegetables"]:
        assert crop_name in POP_CATALOG
        stages = POP_CATALOG[crop_name]
        assert len(stages) >= 3

        for s in stages:
            assert "stage_name" in s
            assert "duration_days" in s
            assert "key_operations" in s and len(s["key_operations"]) > 0
            assert "water_management" in s
            assert "nutrient_advice" in s
            assert "pest_scouting" in s


def test_mandi_market_intelligence():
    """Verify APMC mandi market data for all crops."""
    for crop_name in ["paddy", "potato", "mustard", "jute", "vegetables"]:
        assert crop_name in MANDI_PRICE_DATA
        mandi = MANDI_PRICE_DATA[crop_name]
        assert "commodity" in mandi
        assert "modal_price_inr" in mandi
        assert mandi["modal_price_inr"] > 0
        assert "weekly_trend" in mandi
        assert "post_harvest_advice" in mandi
        assert "storage_standard" in mandi


def test_api_crop_advisory_dossier_endpoint():
    """Integration test verifying full /v1/crops/advisory-dossier API endpoint."""
    resp = get_crop_advisory_dossier_endpoint(
        crop="potato",
        panchayat_id="WB_107778",
        field_size=2.5,
        unit="bigha",
    )
    data = json.loads(resp.body.decode("utf-8"))

    assert data["crop"] == "potato"
    assert data["panchayat_id"] == "WB_107778"
    assert "phenology_summary" in data
    assert "package_of_practices" in data
    assert "pest_and_disease_doctor" in data
    assert "fertilizer_calculator" in data
    assert "spray_advisor" in data
    assert "water_irrigation_budget" in data
    assert "mandi_market_intelligence" in data

    # Verify fertilizer calculations for 2.5 Bigha
    fert = data["fertilizer_calculator"]
    assert fert["unit"] == "bigha"
    assert fert["field_size_input"] == 2.5
    assert len(fert["commercial_fertilizers"]) == 3
    assert len(fert["split_schedule"]) >= 2

    # Verify spray advisor
    spray = data["spray_advisor"]
    assert spray["status"] in ["Optimal", "Caution", "Unfavorable"]
    assert len(spray["tank_mix_matrix"]) >= 3

    # Verify water irrigation budget
    water = data["water_irrigation_budget"]
    assert water["crop"] == "potato"
    assert "net_irrigation_requirement_mm" in water
