import sys
from pathlib import Path

# Ensure project root and backend are on sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "backend"))

from advisory_context import AdvisoryContext, validate_context


def test_context(
    name,
    context
):
    validate_context(context)

    print(
        f"PASS: {name}"
    )

    print(
        context
    )

    print()


# ============================================================
# 1. HEAVY RAIN
# ============================================================

test_context(
    "Heavy rain",
    AdvisoryContext(
        rain_mm=25.0,
        tmax_c=30.0,
        crop="paddy",
        crop_stage="vegetative",
        harvest_window=False,
    )
)


# ============================================================
# 2. FLOWERING HEAT STRESS
# ============================================================

test_context(
    "Flowering heat stress",
    AdvisoryContext(
        rain_mm=2.0,
        tmax_c=39.0,
        crop="paddy",
        crop_stage="flowering",
        harvest_window=False,
    )
)


# ============================================================
# 3. HIGH HUMIDITY / BLAST RISK
# ============================================================

test_context(
    "Paddy blast risk",
    AdvisoryContext(
        rain_mm=5.0,
        tmax_c=31.0,
        humidity=88.0,
        humidity_days=3,
        crop="paddy",
        crop_stage="vegetative",
        harvest_window=False,
    )
)


# ============================================================
# 4. SANDY-SOIL DRY SPELL
# ============================================================

test_context(
    "Sandy soil dry spell",
    AdvisoryContext(
        rain_mm=0.0,
        tmax_c=30.0,
        dry_days=7,
        soil_type="sandy",
        crop="paddy",
        crop_stage="vegetative",
        harvest_window=False,
    )
)


# ============================================================
# 5. HARVEST RAIN
# ============================================================

test_context(
    "Harvest rain",
    AdvisoryContext(
        rain_mm=8.0,
        tmax_c=30.0,
        crop="paddy",
        crop_stage="harvest",
        harvest_window=True,
    )
)


print(
    "========================================"
)

print(
    "ADVISORY CONTEXT TEST COMPLETE"
)

print(
    "========================================"
)