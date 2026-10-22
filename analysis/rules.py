"""
analysis/rules.py - Re-export from canonical backend location (backend.analysis.rules)
"""

import sys
import os

backend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from backend.analysis.rules import *
