"""
Automated Test Suite for TerraMind AI Agro-Climatic Chatbot Engine.
Verifies:
- Spraying decision logic (rain vs clear skies)
- Irrigation recommendations on sandy vs non-sandy soils
- Crop disease diagnostics citing authoritative institutions (ICAR-CPRI, ICAR-NRRI, etc.)
- Cyclone & storm threat analysis
- FastAPI POST /v1/ai/chat endpoint integration with automated context enrichment
"""

import pytest
import unittest
from backend.api import handle_ai_chat
from backend.schemas.models import AIChatRequest, AIChatContext
from backend.ai_chat_engine import (
    generate_ai_chat_response,
    _classify_intent,
)


class TestAIChatEngine:

    def test_01_classify_intent(self):
        assert _classify_intent("Can I spray pesticide on my potato crop?") == "spray_pesticide"
        assert _classify_intent("Should I irrigate the fields today?") == "irrigation"
        assert _classify_intent("What diseases should I monitor for paddy?") == "disease_pest"
        assert _classify_intent("Is there any cyclone or storm danger right now?") == "cyclone_storm"
        assert _classify_intent("Give me the 5-day weather forecast") == "weather_forecast"
        assert _classify_intent("Can I apply urea fertilizer tomorrow?") == "fertilizer"

    def test_02_spray_decision_unfavorable_on_rain(self):
        context = {
            "panchayat_name": "Amdanga",
            "crop": "potato",
            "today_weather": {
                "rain_p50": 12.0,
                "prob_rain": 85,
                "wind_speed_kmh": 20.0,
            }
        }
        res = generate_ai_chat_response("Can I spray fungicide on my potato field today?", context=context)
        
        assert "Unfavorable" in res["reply"]
        assert "washout from rainfall" in res["reply"] or "drift" in res["reply"]
        assert any("ICAR-CPRI" in s for s in res["sources"])
        assert len(res["action_items"]) >= 2
        assert len(res["suggested_questions"]) >= 1

    def test_03_spray_decision_favorable_on_dry_day(self):
        context = {
            "panchayat_name": "Singur",
            "crop": "potato",
            "today_weather": {
                "rain_p50": 0.0,
                "prob_rain": 5,
                "wind_speed_kmh": 8.0,
            }
        }
        res = generate_ai_chat_response("Can I spray pesticide today?", context=context)
        
        assert "Favorable" in res["reply"]
        assert any("ICAR-CPRI" in s for s in res["sources"])
        assert any("morning" in a.lower() for a in res["action_items"])

    def test_04_irrigation_on_sandy_soil(self):
        context = {
            "panchayat_name": "Balarampur",
            "crop": "mustard",
            "soil_type": "sandy",
            "today_weather": {
                "rain_p50": 0.2,
                "prob_rain": 10,
            }
        }
        res = generate_ai_chat_response("Should I irrigate my field?", context=context)
        
        assert "Sandy Soil" in res["reply"] or "sandy" in res["reply"].lower()
        assert any("ICAR-DRMR" in s for s in res["sources"])
        assert any("irrigation" in a.lower() for a in res["action_items"])

    def test_05_crop_disease_diagnostics_potato(self):
        context = {
            "panchayat_name": "Memari",
            "crop": "potato",
            "today_weather": {
                "humidity": 88.0,
                "temp_max_c": 22.0,
                "temp_min_c": 15.0,
            }
        }
        res = generate_ai_chat_response("What diseases should I be worried about right now?", context=context)
        
        assert "Late Blight" in res["reply"]
        assert any("Mancozeb" in a for a in res["action_items"])
        assert any("ICAR-CPRI" in s for s in res["sources"])

    def test_06_crop_disease_diagnostics_paddy(self):
        context = {
            "panchayat_name": "Kakdwip",
            "crop": "paddy",
            "today_weather": {
                "humidity": 92.0,
            }
        }
        res = generate_ai_chat_response("Tell me about pest and disease risks.", context=context)
        
        assert "Blast" in res["reply"] or "Sheath Blight" in res["reply"]
        assert any("ICAR-NRRI" in s for s in res["sources"])

    def test_07_cyclone_query_telemetry(self):
        context = {
            "panchayat_name": "Digha",
            "cyclone_alert": {
                "has_active_system": True,
                "name": "Deep Depression (Bay of Bengal)",
                "classification": "Deep Depression",
                "distance_km": 145.2,
                "bearing": "SSW",
                "threat_level": "HIGH",
                "port_signals": "Local Cautionary Signal No. 3 (LC3)",
            }
        }
        res = generate_ai_chat_response("Is there any cyclone warning near my panchayat?", context=context)
        
        assert "Deep Depression" in res["reply"]
        assert "145.2 km" in res["reply"] or "145" in res["reply"]
        assert "LC3" in res["reply"] or "Signal No. 3" in res["reply"]
        assert any("IMD" in s for s in res["sources"])

    def test_08_api_chat_endpoint_with_auto_enrichment(self):
        req = AIChatRequest(
            message="Can I spray my paddy crop today?",
            conversation_history=[],
            context=AIChatContext(
                panchayat_id="WB_107778",
                crop="paddy",
            ),
        )
        data = handle_ai_chat(req)
        
        assert data.reply is not None
        assert len(data.reply) > 50
        assert isinstance(data.sources, list)
        assert len(data.sources) >= 1
        assert isinstance(data.action_items, list)
        assert isinstance(data.suggested_questions, list)
        assert data.engine in ["gemini", "terramind_expert"]
