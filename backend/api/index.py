"""
backend/api/index.py - Vercel Serverless Function entry point for FastAPI backend
Exposes the FastAPI application 'app' to Vercel's Python runtime.
"""

import sys
import os

# Add backend directory to sys.path so "import analysis" and "import main" work seamlessly
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from main import app
