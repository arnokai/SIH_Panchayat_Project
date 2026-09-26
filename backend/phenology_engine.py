"""
TerraMind Dynamic Phenology Engine
Calculates Growing Degree Days (GDD) and dynamic growth stages for staple West Bengal crops.
Grounded in handbook 'From Block to Panchayat' (SIH26074).
"""

from __future__ import annotations
from datetime import date
from typing import Dict, Any, Optional

CROP_GDD_CONFIG = {
    "paddy": {
        "t_base": 10.0,
        "stages": [
            {"name": "vegetative", "name_bn": "অঙ্গজ বৃদ্ধি পর্যায়", "min_gdd": 0.0, "max_gdd": 300.0, "risk": "Waterlogging & Submergence"},
            {"name": "tillering", "name_bn": "কুশি গজানো পর্যায়", "min_gdd": 300.0, "max_gdd": 650.0, "risk": "Nutrient deficiency & Blast"},
            {"name": "flowering", "name_bn": "ফুল ও শিষ বের হওয়া পর্যায়", "min_gdd": 650.0, "max_gdd": 1150.0, "risk": "Extreme Heat (>38°C) Sterility & Rain Lodging"},
            {"name": "harvest", "name_bn": "পাকা ধান কাটা পর্যায়", "min_gdd": 1150.0, "max_gdd": 9999.0, "risk": "Rain wash-out & Grain Sprouting"},
        ],
        "default_sowing_day_of_year": 196, # ~July 15 Aman season
    },
    "potato": {
        "t_base": 7.0,
        "stages": [
            {"name": "planting", "name_bn": "বীজ রোপণ পর্যায়", "min_gdd": 0.0, "max_gdd": 200.0, "risk": "Soil crusting & tuber rot"},
            {"name": "tuber_bulking", "name_bn": "আলু ফোলা পর্যায়", "min_gdd": 200.0, "max_gdd": 850.0, "risk": "Late Blight fungal blight (high humidity >80%)"},
            {"name": "harvest", "name_bn": "আলু তোলা পর্যায়", "min_gdd": 850.0, "max_gdd": 9999.0, "risk": "Wet soil rotting during lifting"},
        ],
        "default_sowing_day_of_year": 305, # ~November 1
    },
    "mustard": {
        "t_base": 5.0,
        "stages": [
            {"name": "vegetative", "name_bn": "চারা বৃদ্ধি পর্যায়", "min_gdd": 0.0, "max_gdd": 350.0, "risk": "Aphid infestation & dry spell"},
            {"name": "flowering", "name_bn": "হলুদ ফুল ফোটা পর্যায়", "min_gdd": 350.0, "max_gdd": 750.0, "risk": "Hailstorm shattering & cloudy weather aphids"},
            {"name": "harvest", "name_bn": "শুঁটি পাকা পর্যায়", "min_gdd": 750.0, "max_gdd": 9999.0, "risk": "Rain shatter of siliquae"},
        ],
        "default_sowing_day_of_year": 298, # ~October 25
    },
    "jute": {
        "t_base": 15.0,
        "stages": [
            {"name": "seedling", "name_bn": "পাট চারা পর্যায়", "min_gdd": 0.0, "max_gdd": 300.0, "risk": "Drought desiccation & flea beetle"},
            {"name": "vegetative_growth", "name_bn": "দ্রুত কাণ্ড বৃদ্ধি পর্যায়", "min_gdd": 300.0, "max_gdd": 1200.0, "risk": "Early flowering induction & stem rot"},
            {"name": "harvest_retting", "name_bn": "পাট কাটা ও জাগ দেওয়া", "min_gdd": 1200.0, "max_gdd": 9999.0, "risk": "Water scarcity in retting ponds"},
        ],
        "default_sowing_day_of_year": 105, # ~April 15
    },
    "vegetables": {
        "t_base": 10.0,
        "stages": [
            {"name": "vegetative", "name_bn": "শাখা-প্রশাখা বৃদ্ধি", "min_gdd": 0.0, "max_gdd": 400.0, "risk": "Damping off & leaf curl virus"},
            {"name": "fruiting", "name_bn": "ফুল ও ফল ধরা পর্যায়", "min_gdd": 400.0, "max_gdd": 900.0, "risk": "Heavy rain fruit dropping & fungal wilt"},
            {"name": "harvest", "name_bn": "সবজি তোলা পর্যায়", "min_gdd": 900.0, "max_gdd": 9999.0, "risk": "Post-harvest rot & market transport delay"},
        ],
        "default_sowing_day_of_year": 180,
    }
}

# ============================================================
# AGRO-CLIMATIC SEASONS OF WEST BENGAL & EASTERN INDIA
# ============================================================
SEASONS_CONFIG: Dict[str, Dict[str, Any]] = {
    "kharif": {
        "name": "Kharif Season (Monsoon & Autumn)",
        "name_bn": "খরিফ মরশুম (বর্ষা ও শরৎকালীন)",
        "months": [6, 7, 8, 9, 10],  # June to October
        "primary_crop": "paddy",
        "active_crops": ["paddy", "jute", "vegetables"],
        "inactive_crops": {
            "potato": "Rabi winter crop. Planting in monsoon heat (>30°C) causes seed rot and 100% crop loss.",
            "mustard": "Rabi winter crop. Requires night temperatures <18°C; rainfall destroys young seedlings.",
        },
        "description": "Monsoon cropping season dominated by Aman & Aus paddy, late jute harvesting, and kharif vegetables.",
    },
    "rabi": {
        "name": "Rabi Season (Winter)",
        "name_bn": "রবি মরশুম (শীতকালীন)",
        "months": [11, 12, 1, 2, 3],  # November to March
        "primary_crop": "potato",
        "active_crops": ["potato", "mustard", "vegetables", "paddy"],
        "inactive_crops": {
            "jute": "Warm-season fiber crop. Seeds cannot germinate and plants die in winter temperatures <15°C.",
        },
        "description": "Winter cropping season featuring potato tubers, oilseed mustard, winter greens, and boro paddy nursery.",
    },
    "zaid": {
        "name": "Zaid / Pre-Kharif Season (Summer)",
        "name_bn": "জায়েদ / প্রাক-খরিফ মরশুম (গ্রীষ্মকালীন)",
        "months": [4, 5],  # April to May
        "primary_crop": "jute",
        "active_crops": ["jute", "vegetables", "paddy"],
        "inactive_crops": {
            "potato": "Rabi tuber crop. Extreme summer heat (>35°C) and dry winds prevent tuber initiation.",
            "mustard": "Rabi winter crop. Heat causes premature drying and flower sterility.",
        },
        "description": "Pre-monsoon summer season with convective showers, ideal for jute fiber sowing and summer gourds.",
    },
}


def get_agricultural_season(target_date: Optional[date] = None) -> Dict[str, Any]:
    """
    Resolve the agricultural cropping season (Kharif, Rabi, Zaid) for West Bengal.
    Enables automatic selection of current seasonal crops and avoidance of unnecessary ones.
    """
    if target_date is None:
        target_date = date.today()

    month = target_date.month

    for season_id, cfg in SEASONS_CONFIG.items():
        if month in cfg["months"]:
            return {
                "season_id": season_id,
                "season_name": cfg["name"],
                "season_name_bn": cfg["name_bn"],
                "month": month,
                "target_date": target_date.isoformat(),
                "primary_crop": cfg["primary_crop"],
                "active_crops": list(cfg["active_crops"]),
                "inactive_crops": dict(cfg["inactive_crops"]),
                "description": cfg["description"],
            }

    # Default fallback to kharif
    cfg = SEASONS_CONFIG["kharif"]
    return {
        "season_id": "kharif",
        "season_name": cfg["name"],
        "season_name_bn": cfg["name_bn"],
        "month": month,
        "target_date": target_date.isoformat(),
        "primary_crop": cfg["primary_crop"],
        "active_crops": list(cfg["active_crops"]),
        "inactive_crops": dict(cfg["inactive_crops"]),
        "description": cfg["description"],
    }


def resolve_seasonal_crop(
    crop: Optional[str],
    target_date: Optional[date] = None,
    strict_seasonal: bool = False,
) -> str:
    """
    Resolves the target crop against the current agricultural season.
    - If crop is 'auto', None, or empty: auto-selects the primary seasonal crop.
    - If strict_seasonal is True and crop is out-of-season: reverts to primary seasonal crop.
    - Otherwise, preserves valid recognized crops.
    """
    season_info = get_agricultural_season(target_date)
    if not crop or str(crop).strip().lower() in ("auto", "seasonal", "default", "none"):
        return season_info["primary_crop"]

    clean_crop = str(crop).strip().lower()
    if clean_crop not in CROP_GDD_CONFIG:
        return season_info["primary_crop"]

    if strict_seasonal and clean_crop not in season_info["active_crops"]:
        return season_info["primary_crop"]

    return clean_crop


def get_seasonal_crop_catalog(target_date: Optional[date] = None) -> Dict[str, Any]:
    """
    Returns full seasonal crop metadata with UI icons, Bengali translations,
    active vs inactive classifications, and agronomic explanations.
    """
    season_info = get_agricultural_season(target_date)

    crop_meta = {
        "paddy": {"name": "Paddy", "name_bn": "ধান", "icon": "🌾", "category": "Cereal"},
        "potato": {"name": "Potato", "name_bn": "আলু", "icon": "🥔", "category": "Tuber Cash Crop"},
        "mustard": {"name": "Mustard", "name_bn": "সরিষা", "icon": "🌼", "category": "Oilseed"},
        "jute": {"name": "Jute", "name_bn": "পাট", "icon": "🌿", "category": "Commercial Fiber"},
        "vegetables": {"name": "Vegetables", "name_bn": "শাকসবজি", "icon": "🥬", "category": "Horticulture"},
    }

    active_list = []
    for c_id in season_info["active_crops"]:
        info = crop_meta.get(c_id, {"name": c_id.title(), "name_bn": c_id, "icon": "🌱", "category": "Crop"})
        active_list.append({
            "id": c_id,
            "name": info["name"],
            "name_bn": info["name_bn"],
            "icon": info["icon"],
            "category": info["category"],
            "is_primary": (c_id == season_info["primary_crop"]),
            "is_active": True,
        })

    inactive_list = []
    for c_id, reason in season_info["inactive_crops"].items():
        info = crop_meta.get(c_id, {"name": c_id.title(), "name_bn": c_id, "icon": "🌱", "category": "Crop"})
        inactive_list.append({
            "id": c_id,
            "name": info["name"],
            "name_bn": info["name_bn"],
            "icon": info["icon"],
            "category": info["category"],
            "is_active": False,
            "avoidance_reason": reason,
        })

    return {
        "season_id": season_info["season_id"],
        "season_name": season_info["season_name"],
        "season_name_bn": season_info["season_name_bn"],
        "month": season_info["month"],
        "target_date": season_info["target_date"],
        "auto_selected_crop": season_info["primary_crop"],
        "active_crops": active_list,
        "inactive_crops": inactive_list,
        "description": season_info["description"],
    }



def calculate_daily_gdd(tmax: float, tmin: float, t_base: float) -> float:
    """Calculate daily GDD using standard averaging method with lower base clamp."""
    t_avg = (float(tmax) + float(tmin)) / 2.0
    return max(0.0, t_avg - t_base)


def estimate_accumulated_gdd(crop: str, current_date: date, recent_tmax: float = 32.0, recent_tmin: float = 24.0) -> float:
    """
    Estimate season-accumulated GDD based on crop sowing offset and temperature conditions.
    Provides realistic continuous physiological progress.
    """
    crop_key = crop.lower().strip()
    config = CROP_GDD_CONFIG.get(crop_key, CROP_GDD_CONFIG["paddy"])
    t_base = config["t_base"]
    sowing_doy = config["default_sowing_day_of_year"]
    cur_doy = current_date.timetuple().tm_yday
    
    # Calculate days elapsed since nominal seasonal sowing
    if cur_doy >= sowing_doy:
        days_elapsed = cur_doy - sowing_doy
    else:
        # Wrapped around year (e.g. Rabi season planted in Oct/Nov evaluating in Jan/Feb)
        days_elapsed = (365 - sowing_doy) + cur_doy
    
    # Bound to reasonable biological window (0 to 150 days)
    days_elapsed = max(5, min(140, days_elapsed))
    
    # Representative mean thermal unit per day (~14 to 18 GDD for Aman, ~10 to 14 for Rabi)
    daily_rate = calculate_daily_gdd(recent_tmax, recent_tmin, t_base)
    # Ensure nominal minimum progression
    effective_daily_rate = max(daily_rate, 8.5)
    
    return round(float(days_elapsed * effective_daily_rate), 1)


def get_crop_phenology(
    crop: str,
    target_date: Optional[date] = None,
    tmax: float = 32.0,
    tmin: float = 24.0,
    accumulated_gdd: Optional[float] = None
) -> Dict[str, Any]:
    """
    Resolve crop phenological phase, GDD accumulation, and weather vulnerabilities.
    """
    if target_date is None:
        target_date = date.today()

    crop_key = crop.lower().strip()
    if crop_key not in CROP_GDD_CONFIG:
        crop_key = "paddy"

    config = CROP_GDD_CONFIG[crop_key]
    t_base = config["t_base"]

    if accumulated_gdd is None:
        accumulated_gdd = estimate_accumulated_gdd(crop_key, target_date, tmax, tmin)

    stages = config["stages"]
    current_stage = stages[0]["name"]
    current_stage_bn = stages[0]["name_bn"]
    risk = stages[0]["risk"]
    days_to_next = 14

    for st in stages:
        if st["min_gdd"] <= accumulated_gdd < st["max_gdd"]:
            current_stage = st["name"]
            current_stage_bn = st["name_bn"]
            risk = st["risk"]
            gdd_remaining = st["max_gdd"] - accumulated_gdd
            daily_step = max(5.0, calculate_daily_gdd(tmax, tmin, t_base))
            days_to_next = max(1, int(round(gdd_remaining / daily_step)))
            break

    return {
        "crop": crop_key,
        "t_base_c": t_base,
        "accumulated_gdd": float(accumulated_gdd),
        "current_stage": current_stage,
        "current_stage_bn": current_stage_bn,
        "days_to_next_stage": days_to_next,
        "critical_risk_factor": risk,
    }
