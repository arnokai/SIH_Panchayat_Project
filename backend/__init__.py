import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
ROOT_DIR = BACKEND_DIR.parent

for path in [BACKEND_DIR, ROOT_DIR]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
