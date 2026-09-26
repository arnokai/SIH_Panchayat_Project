"""
TerraMind Parametric Weather-Index Insurance Engine (Machine 2)
Evaluates policy triggers under Pradhan Mantri Fasal Bima Yojana (PMFBY) Weather-Based Crop Insurance.
Produces verifiable, cryptographically sealed loss certificates for Gram Panchayats.
"""

from __future__ import annotations
from datetime import datetime, timezone, date
from typing import Dict, Any, List, Optional
import hashlib

from backend.phenology_engine import get_crop_phenology

# Agro-Climatic Zone Mapping for West Bengal Districts
AGRO_ZONES = {
    "delta": [
        "South_24_Parganas", "North_24_Parganas", "Purba_Medinipur",
        "Howrah", "Hooghly", "Nadia", "Murshidabad"
    ],
    "laterite": [
        "Bankura", "Birbhum", "Purulia", "Jhargram",
        "Paschim_Medinipur", "Paschim_Bardhaman", "Purba_Bardhaman"
    ],
    "terai": [
        "Darjeeling", "Kalimpong", "Jalpaiguri", "Alipurduar",
        "Cooch_Behar", "Uttar_Dinajpur", "Dakshin_Dinajpur", "Malda"
    ]
}


def resolve_agro_climatic_zone(district_name: Optional[str]) -> str:
    """Classify district into Delta, Laterite, or Terai zone."""
    if not district_name:
        return "Delta (Coastal & Gangetic Alluvium)"
    
    clean_dist = str(district_name).strip().replace(" ", "_")
    for d in AGRO_ZONES["laterite"]:
        if d.lower() in clean_dist.lower():
            return "Laterite (Western Undulating Uplands)"
    for d in AGRO_ZONES["terai"]:
        if d.lower() in clean_dist.lower():
            return "Terai (Sub-Himalayan & Foothills)"
    return "Delta (Coastal & Gangetic Alluvium)"


def evaluate_parametric_triggers(
    forecast_days: List[Dict[str, Any]],
    crop: str = "paddy",
    dry_days_count: int = 4,
    phenology_info: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Evaluate 4 PMFBY weather insurance triggers across 5-day downscaled window.
    """
    if phenology_info is None:
        phenology_info = get_crop_phenology(crop)

    stage = phenology_info.get("current_stage", "vegetative").lower()
    
    # 1. Check Excess Rainfall Trigger (> 60 mm in 24 hours)
    max_daily_rain = 0.0
    for day in forecast_days:
        rain_val = 0.0
        r_dict = day.get("rain_mm", {})
        if isinstance(r_dict, dict):
            rain_val = float(r_dict.get("p50", 0.0))
        elif isinstance(r_dict, (int, float)):
            rain_val = float(r_dict)
        if rain_val > max_daily_rain:
            max_daily_rain = rain_val

    excess_triggered = max_daily_rain >= 60.0
    excess_res = {
        "trigger_type": "EXCESS_RAINFALL_24H",
        "threshold": "Precipitation ≥ 60.0 mm in a single 24h meteorological day",
        "observed_value": f"{max_daily_rain:.1f} mm peak forecast",
        "triggered": excess_triggered,
        "risk_severity": "SEVERE" if excess_triggered else ("MODERATE" if max_daily_rain >= 40.0 else "NORMAL"),
        "advisory_recommendation": (
            "Open field drainage bunds immediately to prevent root inundation."
            if excess_triggered
            else "Standard moisture management."
        )
    }

    # 2. Check Continuous Dry Spell Trigger (>= 14 dry days during vegetative/tillering stage)
    # Estimate total dry spell = current observed dry days + forecast consecutive dry days
    forecast_dry_streak = 0
    for day in forecast_days:
        rain_val = day.get("rain_mm", {}).get("p50", 0.0) if isinstance(day.get("rain_mm"), dict) else 0.0
        if rain_val < 2.5:
            forecast_dry_streak += 1
        else:
            break
            
    total_consecutive_dry = dry_days_count + forecast_dry_streak
    dry_spell_triggered = (total_consecutive_dry >= 14) and (stage in ["vegetative", "tillering", "planting"])
    dry_res = {
        "trigger_type": "CONTINUOUS_DRY_SPELL",
        "threshold": "≥ 14 consecutive rainless days (<2.5mm) during vegetative/tillering stage",
        "observed_value": f"{total_consecutive_dry} consecutive dry days",
        "triggered": dry_spell_triggered,
        "risk_severity": "SEVERE" if dry_spell_triggered else ("MODERATE" if total_consecutive_dry >= 10 else "NORMAL"),
        "advisory_recommendation": (
            "Provide emergency life-saving irrigation from farm pond or community tube well."
            if dry_spell_triggered
            else "Soil moisture within tolerable crop range."
        )
    }

    # 3. Check Flowering Heat Shock Trigger (Tmax > 38°C during flowering)
    hot_days = 0
    max_tmax = 0.0
    for day in forecast_days:
        tmax = float(day.get("tmax_c", {}).get("p50", 30.0) if isinstance(day.get("tmax_c"), dict) else day.get("tmax_c", 30.0))
        if tmax > max_tmax:
            max_tmax = tmax
        if tmax >= 38.0:
            hot_days += 1

    heat_triggered = (hot_days >= 2) and (stage in ["flowering", "fruiting"])
    heat_res = {
        "trigger_type": "FLOWERING_HEAT_STRESS",
        "threshold": "Tmax ≥ 38.0°C during sensitive flowering/anthesis phase",
        "observed_value": f"{max_tmax:.1f}°C maximum temperature",
        "triggered": heat_triggered,
        "risk_severity": "SEVERE" if heat_triggered else ("MODERATE" if max_tmax >= 36.5 else "NORMAL"),
        "advisory_recommendation": (
            "Apply light evening irrigation to create microclimate cooling and mitigate floret sterility."
            if heat_triggered
            else "Thermal envelope favorable for pollination."
        )
    }

    # 4. Check Unseasonal Rain at Harvest Trigger (> 10mm rain during harvest)
    harvest_rain_triggered = (stage == "harvest") and (max_daily_rain >= 10.0)
    harvest_res = {
        "trigger_type": "UNSEASONAL_HARVEST_RAIN",
        "threshold": "Rainfall ≥ 10.0 mm during mature crop harvesting window",
        "observed_value": f"{max_daily_rain:.1f} mm rain expected",
        "triggered": harvest_rain_triggered,
        "risk_severity": "SEVERE" if harvest_rain_triggered else "NORMAL",
        "advisory_recommendation": (
            "Expedite crop reaping and move harvested produce to covered shelter or tarpaulin."
            if harvest_rain_triggered
            else "Safe window for harvesting and field drying."
        )
    }

    return [excess_res, dry_res, heat_res, harvest_res]


def generate_pmfby_certificate(
    panchayat_id: str,
    panchayat_name: str,
    block_name: Optional[str],
    district_name: Optional[str],
    forecast_days: List[Dict[str, Any]],
    crop: str = "paddy",
    dry_days: int = 4
) -> Dict[str, Any]:
    """
    Generate official PMFBY Weather-Based Crop Insurance Claim Certificate.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    zone = resolve_agro_climatic_zone(district_name)
    phenology = get_crop_phenology(crop, target_date=date.today())
    triggers = evaluate_parametric_triggers(forecast_days, crop=crop, dry_days_count=dry_days, phenology_info=phenology)

    any_triggered = any(t["triggered"] for t in triggers)
    triggered_names = [t["trigger_type"] for t in triggers if t["triggered"]]

    cert_id = f"PMFBY-WB-{panchayat_id}-{datetime.now().strftime('%Y%m%d%H%M')}"
    
    # Generate cryptographic SHA-256 proof hash
    proof_str = f"{cert_id}|{panchayat_id}|{crop}|{any_triggered}|{now_iso}|TERRAMIND-PMFBY-V2"
    verification_hash = hashlib.sha256(proof_str.encode("utf-8")).hexdigest()

    if any_triggered:
        payout_rec = (
            f"Parametric loss condition confirmed for {', '.join(triggered_names)}. "
            f"Eligible for expedited PMFBY cluster payout under Weather-Based Crop Insurance Scheme (WBCIS)."
        )
    else:
        payout_rec = (
            "No parametric trigger conditions breached during current evaluation window. "
            "Normal agricultural operations recommended."
        )

    return {
        "certificate_id": cert_id,
        "verification_hash": verification_hash,
        "issued_at": now_iso,
        "scheme_name": "PMFBY Weather-Based Crop Insurance Scheme (WBCIS)",
        "panchayat_id": panchayat_id,
        "panchayat_name": panchayat_name,
        "block_name": block_name,
        "district_name": district_name,
        "agro_climatic_zone": zone,
        "crop": crop,
        "phenology": phenology,
        "triggers_evaluated": triggers,
        "claim_eligible": any_triggered,
        "payout_recommendation": payout_rec,
    }
