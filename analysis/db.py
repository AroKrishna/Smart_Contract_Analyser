"""
analysis/db.py - Re-export from canonical backend location (backend.analysis.db)
Aliased directly in sys.modules to resolve duplicate module/import-path issues.
"""

import sys
import os

backend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

import backend.analysis.db as _bad

# Re-export all symbols
from backend.analysis.db import *

# Alias module directly in sys.modules so both import paths share identical module state
sys.modules[__name__] = _bad
