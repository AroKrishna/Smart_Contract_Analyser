"""
analysis/api.py - Re-export from canonical backend location (backend.main)
Ensures a single source of truth for the FastAPI application and analysis endpoints.
"""

import sys
import os

backend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from backend.main import (
    app,
    MAX_SOURCE_LENGTH,
    AnalyzeRequest,
    ChatRequest,
    LoginRequest,
    RegisterRequest,
    ForgotPasswordRequest,
    _validate_source,
    _store_analysis,
    _discard_analysis
)
