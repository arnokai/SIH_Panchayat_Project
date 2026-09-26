"""
Tests for TerraMind Agro-Climatic Seasonal Crop Selection & Off-Season Avoidance.
Verifies that:
1. Crop auto-selection maps accurately to West Bengal cropping seasons (Kharif, Rabi, Zaid).
2. Unnecessary out-of-season crops (e.g. potato/mustard in September) are identified and avoided.
3. /v1/crops/seasonal endpoint returns the full seasonal catalog.
4. /v1/forecast supports crop='auto' and attaches seasonal_info in response payload.
"""

from datetime import date
import pytest
from backend.phenology_engine import (
    get_agricultural_season,
    resolve_seasonal_crop,
    get_seasonal_crop_catalog,
)
from backend.forecast_engine_v2 import forecast_panchayat_v2
from backend.api import app, get_forecast, get_seasonal_crops_endpoint


def test_kharif_season_resolution():
    """Verify Kharif season (June - October) auto-selects Paddy and avoids Potato/Mustard."""
    # Test September 26 (current monsoon/autumn Kharif)
    target = date(2026, 9, 26)
    season = get_agricultural_season(target)
    
    assert season["season_id"] == "kharif"
    assert "Kharif" in season["season_name"]
    assert season["primary_crop"] == "paddy"
    assert "paddy" in season["active_crops"]
    assert "jute" in season["active_crops"]
    assert "vegetables" in season["active_crops"]
    
    # Verify unseasonal crops are flagged with agronomic avoidance rationale
    assert "potato" in season["inactive_crops"]
    assert "mustard" in season["inactive_crops"]
    assert "Rabi" in season["inactive_crops"]["potato"]
    assert "Rabi" in season["inactive_crops"]["mustard"]

    # Auto resolution should yield paddy
    assert resolve_seasonal_crop("auto", target_date=target) == "paddy"
    assert resolve_seasonal_crop(None, target_date=target) == "paddy"
    assert resolve_seasonal_crop("", target_date=target) == "paddy"


def test_rabi_season_resolution():
    """Verify Rabi season (November - March) auto-selects Potato and avoids Jute."""
    # Test January 15 (Winter Rabi)
    target = date(2026, 1, 15)
    season = get_agricultural_season(target)
    
    assert season["season_id"] == "rabi"
    assert "Rabi" in season["season_name"]
    assert season["primary_crop"] == "potato"
    assert "potato" in season["active_crops"]
    assert "mustard" in season["active_crops"]
    assert "jute" in season["inactive_crops"]

    # Auto resolution should yield potato
    assert resolve_seasonal_crop("auto", target_date=target) == "potato"


def test_zaid_season_resolution():
    """Verify Zaid season (April - May) auto-selects Jute and avoids Potato/Mustard."""
    # Test May 5 (Pre-monsoon summer)
    target = date(2026, 5, 5)
    season = get_agricultural_season(target)
    
    assert season["season_id"] == "zaid"
    assert "Zaid" in season["season_name"]
    assert season["primary_crop"] == "jute"
    assert "jute" in season["active_crops"]
    assert "potato" in season["inactive_crops"]

    # Auto resolution should yield jute
    assert resolve_seasonal_crop("auto", target_date=target) == "jute"


def test_strict_seasonal_crop_avoidance():
    """Verify strict seasonal mode prevents out-of-season crops."""
    september_date = date(2026, 9, 26)
    
    # In September (Kharif), requesting potato under strict avoidance should revert to paddy
    reverted = resolve_seasonal_crop("potato", target_date=september_date, strict_seasonal=True)
    assert reverted == "paddy"

    # Non-strict mode preserves user preference if recognized
    preserved = resolve_seasonal_crop("potato", target_date=september_date, strict_seasonal=False)
    assert preserved == "potato"


def test_seasonal_crop_catalog_endpoint():
    """Verify /v1/crops/seasonal endpoint returns complete metadata."""
    res = get_seasonal_crops_endpoint(target_date="2026-09-26")
    body = res.body.decode("utf-8")
    import json
    data = json.loads(body)

    assert data["season_id"] == "kharif"
    assert data["auto_selected_crop"] == "paddy"
    assert len(data["active_crops"]) >= 3
    assert any(c["id"] == "paddy" and c["is_primary"] is True for c in data["active_crops"])
    assert any(c["id"] == "potato" for c in data["inactive_crops"])
    assert any(c["id"] == "mustard" for c in data["inactive_crops"])


def test_forecast_auto_crop_resolution():
    """Verify /v1/forecast?crop=auto resolves to seasonal crop and attaches seasonal_info."""
    res = get_forecast(panchayat_id="WB_107778", crop="auto", days=3, live=False)
    body = res.body.decode("utf-8")
    import json
    data = json.loads(body)

    assert data["crop"] == "paddy"
    assert "seasonal_info" in data
    assert data["seasonal_info"] is not None
    assert data["seasonal_info"]["season_id"] == "kharif"
    assert data["seasonal_info"]["primary_crop"] == "paddy"
    assert "potato" in data["seasonal_info"]["inactive_crops"]
