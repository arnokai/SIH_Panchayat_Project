"""
Unit and Integration Tests for Machine 3: Delivery (SMS, IVR) & Trust Verification.
"""

import pytest
from datetime import date
from backend.api import (
    get_delivery_sms,
    get_delivery_ivr,
    get_trust_yesterday,
)
from backend.delivery_engine import (
    generate_160char_sms,
    generate_ivr_payload,
    calculate_yesterday_trust_metrics,
)


def test_sms_generation_constraints():
    """Verify English and Bengali SMS obey the <=160 character single-segment constraint."""
    advisory = {
        "text_en": "Do not spray today. Heavy rainfall expected (45mm).",
        "text_bn": "আজ কীটনাশক স্প্রে করবেন না। ভারী বৃষ্টির সম্ভাবনা রয়েছে (৪৫মিমি)।",
        "priority": "high",
    }
    sms = generate_160char_sms(
        panchayat_name="Amdanga",
        target_date=date(2026, 9, 26),
        rain_p50=45.0,
        tmax=31.5,
        advisory=advisory,
        crop="paddy"
    )

    assert sms["char_count_en"] <= 160
    assert sms["char_count_bn"] <= 160
    assert sms["is_standard_sms"] is True
    assert sms["disaster_warning"] is True
    assert "18001801551" in sms["message_en"]
    assert "১৮০০১৮০১৫৫১" in sms["message_bn"]


def test_ivr_payload_structure():
    """Verify IVR script contains dialpad menu and toll-free hotline."""
    advisory = {
        "text_en": "Optimal spray window open from 7 AM to 10 AM.",
        "text_bn": "সকাল ৭টা থেকে ১০টার মধ্যে স্প্রে করার উপযুক্ত সময়।",
        "priority": "optimal",
    }
    ivr = generate_ivr_payload(
        panchayat_name="Amdanga",
        target_date=date(2026, 9, 26),
        rain_p50=0.0,
        tmax=32.0,
        advisory=advisory,
        crop="paddy"
    )

    assert ivr["toll_free_number"] == "1800-TERRAMIND"
    assert len(ivr["dialpad_menu"]) >= 3
    assert "Amdanga" in ivr["script_en"]
    assert "আমডাঙ্গা" in ivr["script_bn"] or "Amdanga" in ivr["script_bn"]


def test_trust_metrics_calculation():
    """Verify yesterday's prediction vs actual trust evaluation."""
    metrics = calculate_yesterday_trust_metrics(
        panchayat_id="WB_107778",
        panchayat_name="AMDANGA",
        district_name="North 24 Parganas",
        evaluation_date=date(2026, 9, 25),
    )

    assert "predicted_rain_p50" in metrics
    assert "actual_rain_recorded" in metrics
    assert metrics["calibration_score_pct"] >= 80.0
    assert metrics["verification_status"] in ["WITHIN_SPREAD", "SLIGHT_OVERPREDICTION", "EXTREME_EVENT_OBSERVED"]
    assert metrics["badge_text"] != ""


def test_api_delivery_sms_endpoint():
    """Test get_delivery_sms returns valid data."""
    data = get_delivery_sms(panchayat_id="WB_107778", crop="paddy")
    assert data["panchayat_id"] == "WB_107778"
    assert data["char_count_en"] <= 160
    assert data["char_count_bn"] <= 160


def test_api_delivery_ivr_endpoint():
    """Test get_delivery_ivr returns valid data."""
    data = get_delivery_ivr(panchayat_id="WB_107778", crop="paddy")
    assert data["toll_free_number"] == "1800-TERRAMIND"
    assert len(data["dialpad_menu"]) > 0


def test_api_trust_yesterday_endpoint():
    """Test get_trust_yesterday returns valid data."""
    data = get_trust_yesterday(panchayat_id="WB_107778")
    assert data["panchayat_id"] == "WB_107778"
    assert "calibration_score_pct" in data
