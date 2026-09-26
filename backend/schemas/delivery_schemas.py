"""
Pydantic Schemas for TerraMind Machine 3: Multimodal Delivery & Trust Verification
Includes 160-char SMS Broadcast, Missed-Call IVR, and Yesterday vs Actual Trust Panel.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SMSDeliveryResponse(BaseModel):
    panchayat_id: str = Field(..., description="Unique Panchayat Identifier")
    panchayat_name: str = Field(..., description="Gram Panchayat Name")
    district_name: Optional[str] = Field(None, description="District Name")
    date: str = Field(..., description="Forecast date (ISO string)")
    crop: str = Field(..., description="Target crop")
    message_en: str = Field(..., description="160-character action SMS in English")
    message_bn: str = Field(..., description="160-character action SMS in Bengali")
    char_count_en: int = Field(..., description="Character count in English")
    char_count_bn: int = Field(..., description="Character count in Bengali")
    is_standard_sms: bool = Field(True, description="Whether message fits within standard single SMS limit")
    disaster_warning: bool = Field(False, description="Whether alert is an urgent disaster/heavy rain warning")
    toll_free_helpline: str = Field("1800-180-1551", description="Kisan Call Center / MoES Helpline")


class DialpadMenuItem(BaseModel):
    key: str = Field(..., description="Keypad digit (e.g. '1', '2', '3')")
    label_en: str = Field(..., description="Menu label in English")
    label_bn: str = Field(..., description="Menu label in Bengali")


class IVRDeliveryResponse(BaseModel):
    panchayat_id: str = Field(..., description="Unique Panchayat Identifier")
    panchayat_name: str = Field(..., description="Gram Panchayat Name")
    toll_free_number: str = Field("1800-TERRAMIND", description="Toll-free missed-call hotline")
    script_en: str = Field(..., description="Voice script for text-to-speech in English")
    script_bn: str = Field(..., description="Voice script for text-to-speech in Bengali")
    estimated_duration_sec: int = Field(..., description="Estimated audio playback duration in seconds")
    dialpad_menu: List[DialpadMenuItem] = Field(..., description="Interactive Voice Response telephone keypad options")


class TrustVerificationResponse(BaseModel):
    panchayat_id: str = Field(..., description="Unique Panchayat Identifier")
    panchayat_name: str = Field(..., description="Gram Panchayat Name")
    district_name: Optional[str] = Field(None, description="District Name")
    evaluation_date: str = Field(..., description="Yesterday's evaluation date")
    predicted_rain_p10: float = Field(..., description="Yesterday's predicted P10 rainfall (mm)")
    predicted_rain_p50: float = Field(..., description="Yesterday's predicted P50 rainfall (mm)")
    predicted_rain_p90: float = Field(..., description="Yesterday's predicted P90 rainfall (mm)")
    actual_rain_recorded: float = Field(..., description="Actual observed rain recorded yesterday (mm)")
    verification_status: str = Field(..., description="Status (e.g. 'VERIFIED_ACCURATE', 'WITHIN_SPREAD')")
    badge_text: str = Field(..., description="Human-readable verification badge")
    badge_text_bn: str = Field(..., description="Human-readable verification badge in Bengali")
    error_margin_mm: float = Field(..., description="Absolute error difference in mm")
    calibration_score_pct: float = Field(..., description="Historical 30-day calibration confidence percentage")
    observation_source: str = Field(..., description="Ground truth observation source")
