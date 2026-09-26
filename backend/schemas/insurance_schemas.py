"""
Pydantic Schemas for TerraMind Machine 2: Parametric Weather-Index Insurance & Phenology
Compliant with Pradhan Mantri Fasal Bima Yojana (PMFBY) Weather-Based Crop Insurance.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TriggerRuleResult(BaseModel):
    trigger_type: str = Field(..., description="Trigger Type (e.g. 'EXCESS_RAINFALL', 'DRY_SPELL', 'HEAT_STRESS')")
    threshold: str = Field(..., description="Policy trigger threshold description")
    observed_value: str = Field(..., description="Observed weather value in evaluation window")
    triggered: bool = Field(..., description="Whether threshold condition was breached")
    risk_severity: str = Field(..., description="Severity level: 'NORMAL', 'MODERATE', 'SEVERE'")
    advisory_recommendation: str = Field(..., description="Loss mitigation advice")


class DynamicPhenologyInfo(BaseModel):
    crop: str = Field(..., description="Crop name")
    t_base_c: float = Field(..., description="Base developmental temperature in Celsius")
    accumulated_gdd: float = Field(..., description="Current accumulated Growing Degree Days (°C-days)")
    current_stage: str = Field(..., description="Current developmental phase (e.g. 'Tillering', 'Flowering')")
    current_stage_bn: str = Field(..., description="Phase in Bengali")
    days_to_next_stage: int = Field(..., description="Estimated days until next phenological stage transition")
    critical_risk_factor: str = Field(..., description="Key weather vulnerability for current stage")


class InsuranceCertificateResponse(BaseModel):
    certificate_id: str = Field(..., description="Unique immutable claim verification certificate ID")
    verification_hash: str = Field(..., description="SHA-256 integrity checksum for PMFBY validation")
    issued_at: str = Field(..., description="Issuance timestamp in IST")
    scheme_name: str = Field("PMFBY Weather-Based Crop Insurance Scheme (WBCIS)", description="Insurance scheme")
    panchayat_id: str = Field(..., description="Panchayat ID / LGD Code")
    panchayat_name: str = Field(..., description="Panchayat Name")
    block_name: Optional[str] = Field(None, description="Community Development Block Name")
    district_name: Optional[str] = Field(None, description="District Name")
    agro_climatic_zone: str = Field(..., description="Agro-Climatic Zone (Delta / Laterite / Terai)")
    crop: str = Field(..., description="Crop name")
    phenology: DynamicPhenologyInfo = Field(..., description="Dynamic crop growth phenology state")
    triggers_evaluated: List[TriggerRuleResult] = Field(..., description="List of evaluated parametric triggers")
    claim_eligible: bool = Field(..., description="Whether at least one parametric loss trigger was breached")
    payout_recommendation: str = Field(..., description="Official recommendation for insurance assessor")
