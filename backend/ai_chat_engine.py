"""
TerraMind AI Agro-Climatic Chatbot Engine
Dual-mode conversational agent for Gram Panchayat micro-climate and agricultural intelligence:
1. Google Gemini Generative AI (when GEMINI_API_KEY is available)
2. Built-in Local Expert Agro-Climatic Reasoner (Zero-Key, deterministic fallback)

Grounds responses in:
- Selected Gram Panchayat metadata (elevation, soil type, river proximity)
- 5-day downscaled quantile rainfall (P10/P50/P90), temperature, humidity, wind
- Active crop & phenological growth stage
- Authoritative institutional advisories (ICAR-NRRI, ICAR-CPRI, ICAR-DRMR, ICAR-CRIJAF, ICAR-IIHR, IMD)
- Synoptic Bay of Bengal tropical storm & cyclone alerts
"""

import os
import re
import json
import logging
from typing import Dict, Any, List, Optional
import urllib.request
import urllib.error

logger = logging.getLogger(__name__)

# Known authoritative institutions mapping
INSTITUTION_MAP = {
    "potato": "ICAR-CPRI (Central Potato Research Institute) & BCKV Mohanpur",
    "paddy": "ICAR-NRRI (National Rice Research Institute) & BCKV Agromet Field Unit",
    "mustard": "ICAR-DRMR (Directorate of Rapeseed-Mustard Research) & District KVKs",
    "jute": "ICAR-CRIJAF (Central Research Institute for Jute and Allied Fibres, Barrackpore)",
    "vegetables": "ICAR-IIHR (Indian Institute of Horticultural Research) & Dept. of Agriculture, GoWB",
    "general": "IMD Gramin Krishi Mausam Sewa (GKMS) & MoES",
}


def _try_gemini_api(
    query: str,
    history: List[Dict[str, str]],
    context: Dict[str, Any],
    api_key: str,
) -> Optional[Dict[str, Any]]:
    """
    Attempt inference using Google Gemini REST API.
    Returns structured dict if successful, None if failed.
    """
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        
        system_instruction = (
            "You are TerraMind AI, an elite agro-meteorological advisory intelligence assistant "
            "specialized in West Bengal's 3,339 Gram Panchayats. "
            "You provide practical, scientifically rigorous, and empathetic advice to farmers and field officers. "
            "STRICT CONSTRAINTS:\n"
            "1. ALWAYS speak 100% in clear English.\n"
            "2. Ground every answer in the provided Gram Panchayat micro-climate telemetry (exact rainfall P10/P50/P90, temperatures, soil type, elevation, and river distance).\n"
            "3. Ground all crop practices in authoritative bodies: ICAR-NRRI (Paddy), ICAR-CPRI (Potato), ICAR-DRMR (Mustard), ICAR-CRIJAF (Jute), ICAR-IIHR (Vegetables), and IMD GKMS (General/Severe).\n"
            "4. Structure your response with: (a) Direct Answer / Assessment, (b) Local Weather & Soil Telemetry, (c) Operational Field Checklist (bullet points with concrete actions), (d) Institutional Reference.\n"
            "5. Never hallucinate weather data outside the provided context."
        )

        context_str = json.dumps(context, indent=2)
        
        # Build contents from history and current prompt
        contents = []
        for msg in history[-6:]:  # Keep recent context
            role = "user" if msg.get("role") == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": msg.get("content", "")}]
            })
        
        current_prompt = (
            f"### REAL-TIME GRAM PANCHAYAT CONTEXT:\n{context_str}\n\n"
            f"### USER INQUIRY:\n{query}\n\n"
            "Provide a comprehensive, actionable response adhering to the system instructions."
        )
        contents.append({
            "role": "user",
            "parts": [{"text": current_prompt}]
        })

        payload = {
            "system_instruction": {
                "parts": [{"text": system_instruction}]
            },
            "contents": contents,
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 800,
            }
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=7) as resp:
            res_data = json.loads(resp.read().decode("utf-8"))
            candidate = res_data.get("candidates", [{}])[0]
            text = candidate.get("content", {}).get("parts", [{}])[0].get("text", "")
            if text:
                crop = (context.get("crop") or "general").lower()
                source = INSTITUTION_MAP.get(crop, INSTITUTION_MAP["general"])
                
                # Extract bullet points as action items
                action_items = []
                for line in text.split("\n"):
                    clean = line.strip()
                    if clean.startswith(("-", "*", "•")) and len(clean) > 8:
                        action_items.append(clean.lstrip("-*• ").strip())
                
                return {
                    "reply": text,
                    "sources": [source, "IMD GKMS Weather Feed", "TerraMind Hurdle Downscaling Model"],
                    "action_items": action_items[:4] if action_items else ["Follow local field extension guidance"],
                    "suggested_questions": _generate_suggested_questions(context, query),
                    "engine": "gemini",
                }
    except Exception as e:
        logger.warning(f"Gemini API request failed or timed out: {e}. Falling back to Local Expert Reasoner.")
    
    return None


def _classify_intent(query: str) -> str:
    """Classifies user intent from inquiry keywords."""
    q = query.lower()
    
    if any(k in q for k in ["spray", "pesticide", "fungicide", "insecticide", "chemical", "mancozeb", "tricyclazole", "chlorpyrifos", "neem"]):
        return "spray_pesticide"
    if any(k in q for k in ["irrigate", "irrigation", "water", "watering", "dry spell", "drought", "canal", "pump", "moisture"]):
        return "irrigation"
    if any(k in q for k in ["fertilizer", "fertiliser", "urea", "nitrogen", "dap", "potash", "npk", "manure", "top dress", "top-dress", "nutrient"]):
        return "fertilizer"
    if any(k in q for k in ["disease", "pest", "blight", "blast", "rust", "rot", "aphid", "caterpillar", "borer", "fungus", "infection", "damage", "yellow", "spot"]):
        return "disease_pest"
    if any(k in q for k in ["cyclone", "storm", "depression", "arnab", "sea", "bay of bengal", "port", "signal", "danger", "gale", "thunderstorm", "lightning"]):
        return "cyclone_storm"
    if any(k in q for k in ["harvest", "cutting", "reaping", "mature", "storage", "yield", "picking"]):
        return "harvesting"
    if any(k in q for k in ["soil", "drainage", "waterlog", "pooling", "slope", "elevation", "sandy", "clay", "loam", "flood", "runoff"]):
        return "soil_drainage"
    if any(k in q for k in ["insurance", "pmfby", "claim", "loss", "certificate", "compensation", "payout"]):
        return "insurance"
    if any(k in q for k in ["rain", "weather", "forecast", "temperature", "temp", "hot", "cold", "humidity", "wind", "cloud", "sun", "tomorrow"]):
        return "weather_forecast"
    
    return "general_crop_advice"


def _generate_suggested_questions(context: Dict[str, Any], current_query: str = "") -> List[str]:
    """Generates context-aware follow-up question chips."""
    crop = (context.get("crop") or "crop").capitalize()
    q = current_query.lower()
    
    today_w = context.get("today_weather") or {}
    rain_p50 = today_w.get("rain_p50") or today_w.get("rainfall_p50_mm") or 0.0
    rain_prob = today_w.get("prob_rain") or today_w.get("prob_rain_pct") or 0
    
    cyclone = context.get("cyclone_alert") or {}
    has_storm = cyclone.get("has_active_system", False)
    
    candidates = []
    
    if "spray" not in q:
        candidates.append(f"Can I spray chemicals or fertilizers on my {crop} today?")
    if "irrigate" not in q and "water" not in q:
        candidates.append(f"Should I irrigate my {crop} field this week?")
    if "rain" not in q and "weather" not in q:
        candidates.append("What is the 3-day rainfall and temperature outlook?")
    if has_storm and "cyclone" not in q and "storm" not in q:
        candidates.append("What is the latest Bay of Bengal cyclone threat level?")
    if "disease" not in q and "pest" not in q:
        candidates.append(f"What diseases and pests should I monitor for {crop} right now?")
    if "soil" not in q and "drainage" not in q:
        candidates.append("How does my panchayat elevation and soil affect water drainage?")
        
    return candidates[:3]


def _generate_expert_response(
    query: str,
    history: List[Dict[str, str]],
    context: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Built-in Deterministic Agro-Climatic Intelligence Engine.
    Evaluates exact rainfall quantiles, relative humidity, wind speed,
    soil type, elevation, and active ICAR advisories.
    """
    intent = _classify_intent(query)
    
    panchayat_name = context.get("panchayat_name") or "Your Gram Panchayat"
    block_name = context.get("block_name") or "Local Block"
    district_name = context.get("district_name") or "West Bengal"
    elevation_m = context.get("elevation_m", 15.0)
    soil_type = context.get("soil_type") or "non_sandy"
    is_sandy = "sandy" in str(soil_type).lower() and "non" not in str(soil_type).lower()
    
    crop = (context.get("crop") or "paddy").lower()
    crop_display = crop.capitalize()
    crop_stage = context.get("crop_stage") or "Vegetative"
    
    today_w = context.get("today_weather") or {}
    rain_p50 = float(today_w.get("rain_p50") or today_w.get("rainfall_p50_mm") or 0.0)
    rain_p10 = float(today_w.get("rain_p10") or today_w.get("rainfall_p10_mm") or 0.0)
    rain_p90 = float(today_w.get("rain_p90") or today_w.get("rainfall_p90_mm") or 0.0)
    rain_prob = int(today_w.get("prob_rain") or today_w.get("prob_rain_pct") or 0)
    tmax = float(today_w.get("temp_max_c") or today_w.get("tmax") or 31.0)
    tmin = float(today_w.get("temp_min_c") or today_w.get("tmin") or 24.0)
    humidity = float(today_w.get("humidity_pct") or today_w.get("humidity") or 78.0)
    wind_kmh = float(today_w.get("wind_speed_kmh") or today_w.get("wind") or 11.0)
    
    # 5-day horizon aggregates
    forecast_days = context.get("forecast_summary") or []
    total_rain_p50 = sum(float(d.get("rainfall_p50_mm", 0.0)) for d in forecast_days) if forecast_days else rain_p50
    wet_days = sum(1 for d in forecast_days if float(d.get("rainfall_p50_mm", 0.0)) > 2.5)
    
    cyclone = context.get("cyclone_alert") or {}
    advisories = context.get("advisories") or []
    
    primary_source = INSTITUTION_MAP.get(crop, INSTITUTION_MAP["general"])
    sources = [primary_source, "IMD Gramin Krishi Mausam Sewa (GKMS)", "TerraMind 30m Micro-Terrain Engine"]
    
    # =========================================================================
    # INTENT DISPATCH
    # =========================================================================
    
    if intent == "spray_pesticide":
        if rain_prob >= 50 or rain_p50 >= 4.0 or wind_kmh >= 18.0:
            assessment = "❌ **Unfavorable for Spraying Operations**"
            reason = (
                f"Today in **{panchayat_name}**, there is a **{rain_prob}% probability of rain** "
                f"with expected precipitation of **{rain_p50:.1f} mm** (up to {rain_p90:.1f} mm) "
                f"and surface wind speeds around **{wind_kmh:.1f} km/h**."
            )
            guidance = (
                "Applying chemical fungicides, insecticides, or foliar fertilizers today risks **washout from rainfall** "
                "and **chemical drift from wind gusts**. The chemicals will be diluted before reaching effective systemic absorption."
            )
            actions = [
                "Postpone chemical spraying until clear skies and dry foliage prevail",
                "Wait for wind speeds to drop below 15 km/h to prevent spray drift",
                "If preventative fungicide is urgently required, ensure a rain-fast adjuvant or sticker is used on a dry canopy"
            ]
        else:
            assessment = "✅ **Favorable Window for Spraying**"
            reason = (
                f"In **{panchayat_name}**, rainfall probability is low (**{rain_prob}%**, expected rain: **{rain_p50:.1f} mm**) "
                f"with gentle winds of **{wind_kmh:.1f} km/h**."
            )
            guidance = (
                f"Conditions are suitable for pest or disease management in **{crop_display}** ({crop_stage} stage). "
                "Spray early in the morning (7:00 AM – 10:00 AM) or late afternoon to avoid peak evaporation and thermal degradation."
            )
            actions = [
                "Spray during morning hours after dew has evaporated from leaf canopies",
                f"Target {crop_display} specific pests with calibrated nozzle pressure",
                "Wear protective PPE (mask, gloves) during all chemical handling"
            ]

        reply = (
            f"### Spraying & Chemical Application Assessment\n\n"
            f"**Recommendation**: {assessment}\n\n"
            f"{reason}\n\n"
            f"{guidance}\n\n"
            f"#### 📋 Recommended Operations ({primary_source}):\n"
            + "\n".join(f"- ☑ {a}" for a in actions)
        )
        return {
            "reply": reply,
            "sources": sources,
            "action_items": actions,
            "suggested_questions": _generate_suggested_questions(context, query),
            "engine": "terramind_expert",
        }

    elif intent == "irrigation":
        soil_desc = "sandy soil with high percolation and low water retention" if is_sandy else "alluvial/clay loam soil with moderate moisture retention"
        
        if rain_p50 >= 8.0 or total_rain_p50 >= 20.0:
            assessment = "🚫 **Withhold Irrigation**"
            reason = (
                f"Forecast models indicate **{rain_p50:.1f} mm today** (quantile range {rain_p10:.1f}–{rain_p90:.1f} mm) "
                f"and **{total_rain_p50:.1f} mm total rainfall** expected over the 5-day horizon."
            )
            guidance = (
                f"Additional irrigation is unnecessary and will lead to waterlogging. "
                f"In **{panchayat_name}** (elevation: {elevation_m:.1f}m AMSL, {soil_desc}), "
                "excess standing water in ridge furrows can cause root hypoxia and fungal collar rot."
            )
            actions = [
                "Withhold scheduled furrow or sprinkler irrigation",
                "Inspect drainage furrows and ensure unobstructed outlets to field ditches",
                "Monitor lower field corners for water pooling after precipitation events"
            ]
        elif is_sandy and rain_p50 < 3.0:
            assessment = "💧 **Light Irrigation Recommended (Sandy Soil)**"
            reason = (
                f"Your Gram Panchayat features **coarse sandy soil** with rapid drainage. "
                f"With minimal rainfall expected ({rain_p50:.1f} mm, Tmax {tmax:.1f}°C), upper root zone moisture depletes quickly."
            )
            guidance = (
                f"Provide light, frequent irrigation to **{crop_display}** rather than heavy flood irrigation. "
                "Mulching with organic matter will help preserve critical soil moisture."
            )
            actions = [
                "Provide light irrigation during cooler morning or evening hours",
                "Apply paddy straw or organic mulch along crop rows to arrest evaporative loss",
                "Avoid heavy inundation that leaches root-zone nutrients downward"
            ]
        else:
            assessment = "⚖️ **Maintain Normal Soil Moisture**"
            reason = (
                f"Rainfall forecast for **{panchayat_name}** indicates {rain_p50:.1f} mm today. "
                f"Relative humidity is {humidity:.0f}%, and temperatures hover between {tmin:.1f}°C and {tmax:.1f}°C."
            )
            guidance = (
                f"For **{crop_display}** in the {crop_stage} stage on {soil_desc}, "
                "maintain adequate soil moisture without creating standing stagnant water pools."
            )
            actions = [
                "Check moisture depth at 5 cm before operating tube wells or pumps",
                "Maintain uniform bed moisture across the plot",
                "Prioritize moisture conservation if dry spells extend past 4 days"
            ]

        reply = (
            f"### Irrigation & Water Management Guidance\n\n"
            f"**Recommendation**: {assessment}\n\n"
            f"{reason}\n\n"
            f"{guidance}\n\n"
            f"#### 📋 Recommended Operations ({primary_source}):\n"
            + "\n".join(f"- ☑ {a}" for a in actions)
        )
        return {
            "reply": reply,
            "sources": sources,
            "action_items": actions,
            "suggested_questions": _generate_suggested_questions(context, query),
            "engine": "terramind_expert",
        }

    elif intent == "disease_pest":
        disease_notes = {
            "potato": (
                "**Late Blight (*Phytophthora infestans*)** is the critical threat. "
                "When relative humidity exceeds 80% with temperatures between 15°C and 22°C, "
                "fungal sporulation occurs rapidly. Scout lower leaves for water-soaked necrotic lesions with white downy margins underneath."
            ),
            "paddy": (
                "**Rice Blast (*Magnaporthe oryzae*)** and **Sheath Blight** thrive under warm, humid conditions. "
                "Scout upper leaves for spindle-shaped blast lesions and lower leaf sheaths for irregular greyish-green lesions. "
                "Also monitor for Brown Plant Hopper (BPH) at the base of tillers."
            ),
            "mustard": (
                "**White Rust (*Albugo candida*)** and **Mustard Aphids (*Lipaphis erysimi*)** are primary concerns. "
                "Humid overcast weather encourages aphid colonies on inflorescence twigs and white pustules on the undersides of leaves."
            ),
            "jute": (
                "**Stem Rot (*Macrophomina phaseolina*)** and **Damping-Off** occur during prolonged water stagnation. "
                "Scout the collar region of seedlings and young stems for brown necrotic discoloration."
            ),
            "vegetables": (
                "**Damping-Off** in nurseries and **Fruit & Shoot Borers** in Solanaceous crops. "
                "High humidity promotes fungal collar rot. Ensure nursery beds are raised 15 cm above ground."
            ),
        }
        
        disease_text = disease_notes.get(crop, disease_notes["vegetables"])
        
        actions = []
        if crop == "potato":
            actions = [
                "Apply prophylactic Mancozeb 75% WP @ 2.5 g/L on dry foliage before rain showers",
                "If lesions appear, alternate with systemic Cymoxanil + Mancozeb @ 2 g/L",
                "Maintain deep ridge furrows to prevent tuber water contact"
            ]
        elif crop == "paddy":
            actions = [
                "Scout leaf sheaths and collar region for diamond-shaped blast lesions",
                "Withhold excess nitrogenous (urea) fertilizer top-dressing during humid periods",
                "Keep Tricyclazole 75% WP on standby for curative blast management"
            ]
        elif crop == "mustard":
            actions = [
                "Scout inflorescences for early aphid nymph clusters",
                "Apply Azadirachtin (neem oil 1500 ppm) @ 3 ml/L as an eco-friendly barrier",
                "Spray Ridomil MZ @ 2 g/L if white rust pustules appear on leaves"
            ]
        else:
            actions = [
                "Ensure raised planting beds for adequate seedling root aeration",
                "Remove and safely burn virus-infected or heavily infested plants",
                "Install yellow and blue sticky traps to monitor sucking pest vectors"
            ]

        reply = (
            f"### Disease & Pest Intelligence for {crop_display} ({crop_stage} Stage)\n\n"
            f"**Micro-Climate Telemetry in {panchayat_name}**:\n"
            f"- Relative Humidity: **{humidity:.0f}%**\n"
            f"- Max / Min Temperature: **{tmax:.1f}°C / {tmin:.1f}°C**\n"
            f"- Rain Probability: **{rain_prob}%** (Median: {rain_p50:.1f} mm)\n\n"
            f"#### 🔍 Key Pathological Vulnerabilities:\n{disease_text}\n\n"
            f"#### 📋 Recommended Field Operations ({primary_source}):\n"
            + "\n".join(f"- ☑ {a}" for a in actions)
        )
        return {
            "reply": reply,
            "sources": sources,
            "action_items": actions,
            "suggested_questions": _generate_suggested_questions(context, query),
            "engine": "terramind_expert",
        }

    elif intent == "cyclone_storm":
        storm_name = cyclone.get("name") or "Deep Depression (Bay of Bengal)"
        classification = cyclone.get("classification") or "Deep Depression"
        distance_km = cyclone.get("distance_km") or 280.0
        bearing = cyclone.get("bearing") or "SSW"
        threat_level = cyclone.get("threat_level") or "MODERATE"
        port_signals = cyclone.get("port_signals") or "Local Cautionary Signal No. 3 (LC3) at Kolkata and Haldia Ports"
        
        reply = (
            f"### Synoptic Severe Storm & Cyclone Advisory\n\n"
            f"**Active Disturbance**: 🌀 **{storm_name}** ({classification})\n"
            f"- **Threat Level for {panchayat_name}**: **{threat_level} PROXIMITY**\n"
            f"- **Distance from your Gram Panchayat**: **~{distance_km:.1f} km** ({bearing})\n"
            f"- **IMD Maritime Signal**: {port_signals}\n\n"
            f"#### 🌊 Meteorological Impact Analysis:\n"
            f"The disturbance over the Northwest Bay of Bengal and adjoining inland regions continues to pump deep oceanic moisture into South Bengal. "
            f"Wind gusts may reach **{wind_kmh + 15:.0f} km/h** with intermittent squally showers. "
            f"Because sustained wind speeds remain below the 62 km/h cyclonic storm threshold, this system is classified by IMD as a **{classification}**.\n\n"
            f"#### 📋 Emergency Farm Safety Measures (IMD GKMS & NDMA):\n"
            f"- ☑ Secure poly-tunnels, vegetable trellises, and banana/betelvine orchard supports\n"
            f"- ☑ Clear boundary drainage channels immediately to prevent localized field inundation\n"
            f"- ☑ Move harvested crops, grain bags, and electrical pump sets to elevated, covered threshing floors\n"
            f"- ☑ Fishermen are strictly advised not to venture into deep sea or coastal estuaries until signals are lowered"
        )
        actions = [
            "Clear drainage ditches to handle heavy runoff surges",
            "Secure vegetable trellises and bamboo staking supports",
            "Store harvested produce and seed bags on elevated dry platforms",
            "Comply with coastal port LC3 maritime advisories"
        ]
        return {
            "reply": reply,
            "sources": ["IMD RSMC Tropical Cyclones New Delhi", "IMD Regional Met Centre Kolkata", "NDMA Farm Disaster Protocol"],
            "action_items": actions,
            "suggested_questions": _generate_suggested_questions(context, query),
            "engine": "terramind_expert",
        }

    elif intent == "weather_forecast":
        day_bullets = []
        for i, d in enumerate(forecast_days[:5], 1):
            dt = d.get("date", f"Day {i}")
            p50 = float(d.get("rainfall_p50_mm", 0.0))
            p10 = float(d.get("rainfall_p10_mm", 0.0))
            p90 = float(d.get("rainfall_p90_mm", 0.0))
            prob = int(d.get("prob_rain_pct", 0))
            tx = float(d.get("temp_max_c", 30.0))
            day_bullets.append(f"- **{dt}**: Expected Rain **{p50:.1f} mm** (Quantile range: {p10:.1f}–{p90:.1f} mm, Prob: {prob}%), Tmax: **{tx:.1f}°C**")

        if not day_bullets:
            day_bullets = [
                f"- **Today**: Expected Rain **{rain_p50:.1f} mm** (Prob: {rain_prob}%), Tmax: **{tmax:.1f}°C**, Humidity: **{humidity:.0f}%**"
            ]

        reply = (
            f"### Micro-Climate Forecast Horizon for {panchayat_name}\n\n"
            f"**Location Summary**: {block_name} Block, {district_name} District (Elevation: {elevation_m:.1f}m AMSL)\n\n"
            f"#### 📅 5-Day Hurdle Downscaled Forecast:\n"
            + "\n".join(day_bullets) + "\n\n"
            f"#### 📊 Agro-Climatic Synthesis:\n"
            f"- Total expected 5-day rain accumulation: **{total_rain_p50:.1f} mm**\n"
            f"- Prevailing wind speed: **{wind_kmh:.1f} km/h** with relative humidity averaging **{humidity:.0f}%**\n"
            f"- Soil moisture index: {'Rapid drainage expected (Sandy soil)' if is_sandy else 'Good water holding capacity (Alluvial/Clay loam)'}"
        )
        actions = [
            "Plan field labor around the lowest precipitation probability days",
            "Monitor daily quantile shifts (P10 vs P90) for localized thunderstorm spikes",
            "Adjust supplementary irrigation based on real-time rainfall receipts"
        ]
        return {
            "reply": reply,
            "sources": ["TerraMind Hurdle Quantile Model", "IMD Open-Meteo High-Res Stream", "Copernicus 30m DEM"],
            "action_items": actions,
            "suggested_questions": _generate_suggested_questions(context, query),
            "engine": "terramind_expert",
        }

    elif intent == "fertilizer":
        if rain_prob >= 50 or rain_p50 >= 5.0:
            assessment = "⚠️ **Postpone Broadcast Fertilizer Application**"
            reason = (
                f"Rainfall of **{rain_p50:.1f} mm** ({rain_prob}% probability) is forecasted today in **{panchayat_name}**."
            )
            guidance = (
                "Broadcasting top-dressed Urea or soluble NPK fertilizers before moderate-to-heavy rains leads to "
                "**heavy nitrate leaching into groundwater** and surface runoff loss. "
                "Wait for soil to reach field capacity after the rain event before top-dressing."
            )
            actions = [
                "Withhold broadcast Urea top-dressing until showers pass",
                "Ensure standing water is drained to 2–3 cm depth in paddy before nitrogen application",
                "Incorporate basal fertilizers into the soil rather than leaving them on the surface"
            ]
        else:
            assessment = "✅ **Favorable for Targeted Soil Fertilizer Placement**"
            reason = f"Low rain risk ({rain_prob}%) and moderate soil moisture in **{panchayat_name}**."
            guidance = (
                f"Apply fertilizers according to the {crop_stage} stage of **{crop_display}**. "
                "Incorporate fertilizer into the root zone or apply along furrow shoulders followed by light hoeing."
            )
            actions = [
                "Apply recommended dose of nitrogenous fertilizer in split doses",
                "Avoid applying fertilizer directly against tender crop stems",
                "Follow soil health card recommendations for balanced N:P:K ratios"
            ]

        reply = (
            f"### Fertilizer & Nutrient Application Protocol\n\n"
            f"**Recommendation**: {assessment}\n\n"
            f"{reason}\n\n"
            f"{guidance}\n\n"
            f"#### 📋 Recommended Operations ({primary_source}):\n"
            + "\n".join(f"- ☑ {a}" for a in actions)
        )
        return {
            "reply": reply,
            "sources": sources,
            "action_items": actions,
            "suggested_questions": _generate_suggested_questions(context, query),
            "engine": "terramind_expert",
        }

    # Default / General Crop Advice
    adv_text = ""
    if advisories:
        top_adv = advisories[0]
        adv_text = (
            f"\n\n#### 🏛️ Active Agronomic Advisory ({top_adv.get('source', primary_source)}):\n"
            f"**{top_adv.get('rule_id', 'Field Action')}**: {top_adv.get('text_en', '')}\n"
        )
        if top_adv.get("action_items"):
            adv_text += "\n" + "\n".join(f"- ☑ {item}" for item in top_adv["action_items"])

    reply = (
        f"### Agronomic Advisory Overview for {crop_display} ({crop_stage})\n\n"
        f"**Target Gram Panchayat**: **{panchayat_name}**, {block_name} Block, {district_name}\n"
        f"- Elevation: **{elevation_m:.1f} m AMSL** | Soil Type: **{soil_type}**\n"
        f"- Today's Weather: **{rain_p50:.1f} mm rain** ({rain_prob}% prob), **{tmax:.1f}°C max temp**, **{humidity:.0f}% humidity**\n"
        f"{adv_text}\n\n"
        f"#### 🌾 General Crop Management Tips ({primary_source}):\n"
        f"- ☑ Maintain plot cleanliness and weed-free bunds to remove alternate pest hosts\n"
        f"- ☑ Inspect field drainage channels before afternoon convective rain cells\n"
        f"- ☑ Consult your local Krishi Prajukti Sahayak (KPS) or District KVK for farm inputs"
    )
    
    actions = [
        f"Keep drainage furrows clear in {panchayat_name}",
        f"Monitor {crop_display} foliage regularly for pest egg masses",
        "Adopt IPM practices with bio-agents before chemical interventions"
    ]
    
    return {
        "reply": reply,
        "sources": sources,
        "action_items": actions,
        "suggested_questions": _generate_suggested_questions(context, query),
        "engine": "terramind_expert",
    }


def generate_ai_chat_response(
    query: str,
    history: Optional[List[Dict[str, str]]] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Main entry point for generating AI agro-climatic responses.
    Attempts Google Gemini first if GEMINI_API_KEY is present;
    otherwise falls back to the local deterministic expert reasoner.
    """
    if history is None:
        history = []
    if context is None:
        context = {}
        
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    
    # 1. Attempt online LLM if key is configured
    if api_key:
        result = _try_gemini_api(query, history, context, api_key)
        if result:
            return result
            
    # 2. Local Expert Reasoner (Zero-Key Fallback)
    return _generate_expert_response(query, history, context)
