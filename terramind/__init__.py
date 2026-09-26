"""
TerraMind: Panchayat-Scale Micro-Climate & Agro-Advisory Intelligence System
============================================================================
Official Python package and high-performance meteorological engine for
3,339 Gram Panchayats across West Bengal's 22 districts.

Application UI Title: TerraMind | Gram Panchayat Climate Intelligence
CLI / Microservice:   terramind-engine
"""

from pathlib import Path
import sys

# Ensure backend modules are available on path
_ROOT_DIR = Path(__file__).resolve().parent.parent
_BACKEND_DIR = _ROOT_DIR / "backend"
for _p in [_ROOT_DIR, _BACKEND_DIR]:
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from backend.api import app
from backend.forecast_engine_v2 import (
    forecast_panchayat_v2,
    resolve_panchayat_meta,
    compute_nwp_coarse_centroid,
    haversine_distance_km,
)
from backend.delivery_engine import (
    generate_160char_sms,
    generate_ivr_payload,
    calculate_yesterday_trust_metrics,
)
from backend.insurance_engine import (
    generate_pmfby_certificate,
    resolve_agro_climatic_zone,
)

__version__ = "2.1.0"
__title__ = "TerraMind: Panchayat-Scale Micro-Climate & Agro-Advisory Intelligence System"
__ui_title__ = "TerraMind | Gram Panchayat Climate Intelligence"
__cli_name__ = "terramind-engine"

__all__ = [
    "__version__",
    "__title__",
    "__ui_title__",
    "__cli_name__",
    "app",
    "forecast_panchayat_v2",
    "resolve_panchayat_meta",
    "compute_nwp_coarse_centroid",
    "haversine_distance_km",
    "generate_160char_sms",
    "generate_ivr_payload",
    "calculate_yesterday_trust_metrics",
    "generate_pmfby_certificate",
    "resolve_agro_climatic_zone",
]
