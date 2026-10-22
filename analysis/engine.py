"""
analysis/engine.py - Re-export from canonical backend location (backend.analysis.engine)
Ensures a single source of truth for Legal-BERT inference and XAI attribution logic.
"""

import sys
import os

backend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from backend.analysis.engine import (
    CATEGORIES,
    CATEGORY_SEVERITIES,
    CATEGORY_DESCRIPTIONS,
    CATEGORY_SUPPORT_STATUS,
    DEFAULT_MODEL_DIR,
    DEFAULT_CHECKPOINT_NAME,
    MODEL_DIR,
    AnalysisEngine,
    compute_embedding_gradient_saliency,
    compute_genuine_shap,
    compute_genuine_lime,
    locate_category_evidence,
    resolve_default_model_dir,
    download_model_checkpoint_from_url
)
