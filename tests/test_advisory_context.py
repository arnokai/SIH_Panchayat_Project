import sys
from pathlib import Path
import pytest

# Ensure project root and backend are on sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "backend"))

from advisory_context import AdvisoryContext, validate_context


def test_heavy_rain_context():
    ctx = AdvisoryContext(
        rain_mm=25.0,
        tmax_c=30.0,
        crop="paddy",
        crop_stage="vegetative",
        harvest_window=False,
    )
    validate_context(ctx)
    assert ctx.rain_mm == 25.0
    assert ctx.crop == "paddy"


def test_flowering_heat_stress_context():
    ctx = AdvisoryContext(
        rain_mm=2.0,
        tmax_c=39.0,
        crop="paddy",
        crop_stage="flowering",
        harvest_window=False,
    )
    validate_context(ctx)
    assert ctx.tmax_c == 39.0
    assert ctx.crop_stage == "flowering"


def test_high_humidity_blast_risk_context():
    ctx = AdvisoryContext(
        rain_mm=5.0,
        tmax_c=31.0,
        humidity=88.0,
        humidity_days=3,
        crop="paddy",
        crop_stage="vegetative",
        harvest_window=False,
    )
    validate_context(ctx)
    assert ctx.humidity == 88.0
    assert ctx.humidity_days == 3


def test_sandy_soil_dry_spell_context():
    ctx = AdvisoryContext(
        rain_mm=0.0,
        tmax_c=30.0,
        dry_days=7,
        soil_type="sandy",
        crop="paddy",
        crop_stage="vegetative",
        harvest_window=False,
    )
    validate_context(ctx)
    assert ctx.dry_days == 7
    assert ctx.soil_type == "sandy"


def test_harvest_rain_context():
    ctx = AdvisoryContext(
        rain_mm=8.0,
        tmax_c=30.0,
        crop="paddy",
        crop_stage="harvest",
        harvest_window=True,
    )
    validate_context(ctx)
    assert ctx.harvest_window is True
    assert ctx.crop_stage == "harvest"