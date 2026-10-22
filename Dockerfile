# syntax=docker/dockerfile:1
# ==============================================================================
# Smart Contract Analyser - Backend Dockerfile (Phase 1)
# ==============================================================================
# IMPORTANT ARCHITECTURAL CONSTRAINT:
# The Phase 1 analysis pipeline uses an in-memory job store (jobs_store)
# and analysis store (analyses_store) with 30-minute ephemeral TTL.
# Therefore, Uvicorn MUST be run with exactly 1 worker process (--workers 1),
# and the hosting platform MUST run exactly 1 container instance (no multi-replica
# round-robin or scale-to-zero during active polling).
# ==============================================================================

FROM python:3.11-slim AS base

# Avoid buffering stdout/stderr and prevent .pyc generation
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Install minimal system dependencies required for building C-extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies using CPU-only wheels for torch
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code and frozen model artifacts
COPY analysis/ ./analysis/
COPY data/ ./data/

# Health check using the backend /ready endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/ready || exit 1

# Expose backend port
EXPOSE 8000

# Launch Uvicorn with a single worker to guarantee shared in-memory job state
CMD ["uvicorn", "analysis.api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
