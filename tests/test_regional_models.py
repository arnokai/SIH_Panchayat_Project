"""
Unit and Integration Tests for Machine 1: Regional Agro-Climatic Zone Hurdle Models.
Tests Delta, Laterite, and Terai regional models, conformal prediction margins, and extreme tail calibration.
"""

from pathlib import Path
import joblib
import pytest
from backend.forecast_engine_v2 import forecast_panchayat_v2

ROOT_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = ROOT_DIR / "ml" / "models"


def test_regional_model_files_exist():
    """Verify all 3 regional model binaries are compiled and present."""
    assert (MODEL_DIR / "hurdle_delta.pkl").exists(), "hurdle_delta.pkl is missing"
    assert (MODEL_DIR / "hurdle_laterite.pkl").exists(), "hurdle_laterite.pkl is missing"
    assert (MODEL_DIR / "hurdle_terai.pkl").exists(), "hurdle_terai.pkl is missing"


def test_delta_model_artifact_contents():
    """Verify Delta model contains extreme tail regressor and conformal prediction margin."""
    art = joblib.load(MODEL_DIR / "hurdle_delta.pkl")
    assert art["zone_key"] == "delta"
    assert "classifier" in art
    assert "regressor_p50" in art
    assert "regressor_extreme" in art
    assert "conformal_margin_90" in art
    assert art["conformal_margin_90"] > 0.0


def test_laterite_model_artifact_contents():
    """Verify Laterite model contains extreme tail regressor and conformal prediction margin."""
    art = joblib.load(MODEL_DIR / "hurdle_laterite.pkl")
    assert art["zone_key"] == "laterite"
    assert "regressor_extreme" in art
    assert "conformal_margin_90" in art


def test_terai_model_artifact_contents():
    """Verify Terai model contains extreme tail regressor and conformal prediction margin."""
    art = joblib.load(MODEL_DIR / "hurdle_terai.pkl")
    assert art["zone_key"] == "terai"
    assert "regressor_extreme" in art
    assert "conformal_margin_90" in art


def test_delta_forecast_execution():
    """Verify Delta GP forecast resolves to Delta Regional Hurdle model."""
    res = forecast_panchayat_v2("WB_107778", days=3, crop="paddy", live=False)
    assert "Delta" in res["agro_climatic_zone"]
    assert "Delta Zone" in res["model_version"]
    assert len(res["forecast"]) == 3


def test_laterite_forecast_execution():
    """Verify Laterite GP forecast resolves to Laterite Regional Hurdle model."""
    # WB_114321 is in Bankura or Purulia
    import pandas as pd
    reg = pd.read_parquet(ROOT_DIR / "data_pipeline" / "metadata" / "statewide_panchayats.parquet")
    purulia_gp = reg[reg["district_name"] == "Purulia"].iloc[0]["panchayat_id"]
    res = forecast_panchayat_v2(purulia_gp, days=2, crop="mustard", live=False)
    assert "Laterite" in res["agro_climatic_zone"]
    assert "Laterite Zone" in res["model_version"]


def test_terai_forecast_execution():
    """Verify Terai GP forecast resolves to Terai Regional Hurdle model."""
    import pandas as pd
    reg = pd.read_parquet(ROOT_DIR / "data_pipeline" / "metadata" / "statewide_panchayats.parquet")
    darjeeling_gp = reg[reg["district_name"] == "Darjeeling"].iloc[0]["panchayat_id"]
    res = forecast_panchayat_v2(darjeeling_gp, days=2, crop="vegetables", live=False)
    assert "Terai" in res["agro_climatic_zone"]
    assert "Terai Zone" in res["model_version"]
