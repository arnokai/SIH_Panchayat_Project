"""
Root Entrypoint Shim — TerraMind API
=====================================
Provides backward compatibility for deployment environments (such as Render)
and CLI runners executing `uvicorn api:app` from the project root.
Delegates to `backend.api.app`.
"""

import sys
from pathlib import Path

# Add project root and backend/ to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = PROJECT_ROOT / "backend"

for path in [PROJECT_ROOT, BACKEND_DIR]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from backend.api import app  # noqa: E402

__all__ = ["app"]
