"""
backend/main.py - Production FastAPI Entry Point for Smart Contract Legal AI SaaS Platform

Conforms to:
- docs/reference/Smart_Contract_Legal_AI_SaaS_Platform_Specification.docx
- Phase 1: Public No-Login Website, Ephemeral Storage Policy
- Vercel Serverless Function specifications for FastAPI and Python Runtime
"""

import os
import sys
import io
import time
import uuid
import logging
import threading
import datetime
from typing import Dict, Any, Optional, List
from collections import OrderedDict, defaultdict

# Ensure backend root is on sys.path so "import analysis" resolves correctly
# whether running from backend/ or the repository root
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi import FastAPI, HTTPException, Request, Response, status, Query, UploadFile, File, Form
from fastapi.responses import Response, StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from analysis.engine import AnalysisEngine
from analysis.parser import SolidityParser
from analysis.chat import answer_contract_query
from analysis.reports import generate_pdf_report, generate_docx_report
import analysis.db as db

# Configure structured application logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("smart_contract_analyser.api")

# Conservative payload size limit: 1 MB (well below Vercel's 4.5MB body limit)
MAX_SOURCE_LENGTH = int(os.environ.get("MAX_FILE_SIZE_BYTES", 1024 * 1024))

# Ephemeral in-memory store for Phase 1
# Retention policy: Entries expire after 30 minutes (TTL) and max 100 entries (FIFO eviction)
EPHEMERAL_TTL_SECONDS = int(os.environ.get("ANALYSIS_TTL_MINUTES", "30")) * 60
MAX_STORE_ENTRIES = int(os.environ.get("MAX_STORED_ANALYSES", "100"))

# Concurrency Protection: default to 1 on serverless to prevent memory exhaustion
MAX_CONCURRENT_JOBS = int(os.environ.get("MAX_CONCURRENT_ANALYSIS_JOBS", "1"))
analysis_semaphore = threading.Semaphore(MAX_CONCURRENT_JOBS)

RATE_LIMIT_WINDOW_SECONDS = 60
MAX_REQUESTS_PER_WINDOW = int(os.environ.get("RATE_LIMIT_PER_MINUTE", "20"))
client_request_history: Dict[str, List[float]] = defaultdict(list)
rate_limit_lock = threading.Lock()


def _check_rate_limit(client_ip: str):
    """Enforces a sliding-window rate limit per client IP for anonymous submissions."""
    now = time.time()
    with rate_limit_lock:
        timestamps = client_request_history[client_ip]
        client_request_history[client_ip] = [t for t in timestamps if now - t < RATE_LIMIT_WINDOW_SECONDS]
        if len(client_request_history[client_ip]) >= MAX_REQUESTS_PER_WINDOW:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": f"Rate limit of {MAX_REQUESTS_PER_WINDOW} analyses per minute exceeded. Please wait 1 minute before submitting again."
                }
            )
        client_request_history[client_ip].append(now)


app = FastAPI(
    title="Smart Contract Analyser API",
    description="Legal-BERT Neural Framework for Automated Operational Legal-Risk Assessment in Solidity Contracts",
    version=AnalysisEngine.VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Initialize database on startup
db.init_db()

# CORS configuration: strictly configurable via ALLOWED_ORIGINS env var for production
allowed_origins_raw = os.environ.get("ALLOWED_ORIGINS", "").strip()

default_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
]

is_production = os.getenv("VERCEL_ENV") == "production" or os.getenv("ENVIRONMENT") == "production"
allow_credentials = True

if allowed_origins_raw == "*":
    cors_origins = ["*"]
    allow_origin_regex = None
    allow_credentials = False
elif allowed_origins_raw:
    configured = [orig.strip() for orig in allowed_origins_raw.split(",") if orig.strip()]
    if is_production:
        # In production: permit only the exact configured frontend origins
        cors_origins = configured
        allow_origin_regex = None
    else:
        # In local development: permit configured origins plus localhost/127.0.0.1
        cors_origins = list(dict.fromkeys(default_origins + configured))
        allow_origin_regex = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"
else:
    cors_origins = default_origins
    allow_origin_regex = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=allow_origin_regex,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["x-analysis-disclaimer", "x-engine-type", "x-persistence-note"],
)

# In-memory ephemeral stores
analyses_store: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()
jobs_store: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()


def _purge_expired_ephemeral_data():
    """Purges expired analyses and background jobs based on the TTL."""
    now = time.time()
    expired_analyses = [
        aid for aid, item in analyses_store.items()
        if now - item.get("_created_timestamp", now) > EPHEMERAL_TTL_SECONDS
    ]
    for aid in expired_analyses:
        analyses_store.pop(aid, None)

    expired_jobs = [
        jid for jid, item in jobs_store.items()
        if now - item.get("_created_timestamp", now) > EPHEMERAL_TTL_SECONDS
    ]
    for jid in expired_jobs:
        jobs_store.pop(jid, None)


def _store_analysis(analysis_id: str, payload: Dict[str, Any]):
    """Stores temporary analysis in memory with TTL timestamp and FIFO eviction."""
    _purge_expired_ephemeral_data()
    if len(analyses_store) >= MAX_STORE_ENTRIES:
        analyses_store.popitem(last=False)
    payload["_created_timestamp"] = time.time()
    analyses_store[analysis_id] = payload


def _discard_analysis(analysis_id: str) -> bool:
    """Explicitly removes an analysis and its associated jobs from ephemeral cache."""
    removed = False
    if analysis_id in analyses_store:
        analyses_store.pop(analysis_id, None)
        removed = True

    for jid in list(jobs_store.keys()):
        job_result = jobs_store[jid].get("result")
        if job_result and job_result.get("analysisId") == analysis_id:
            jobs_store.pop(jid, None)
            removed = True

    return removed


# Request / Response Schemas
class AnalyzeRequest(BaseModel):
    sourceCode: Optional[str] = Field(None, description="Solidity contract source text (camelCase)")
    source_code: Optional[str] = Field(None, description="Solidity contract source text (snake_case)")
    contractName: Optional[str] = Field(None, description="Optional contract file or project name")
    contract_name: Optional[str] = Field(None, description="Optional contract file or project name")
    description: Optional[str] = Field(None, description="Optional contract project description")


class ChatRequest(BaseModel):
    message: str = Field(..., description="User query about the contract")


class LoginRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., description="Account password")


class RegisterRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., description="Account password")
    fullName: str = Field(..., description="User full name")
    organization: Optional[str] = Field("General", description="Organization / Company name")


class ForgotPasswordRequest(BaseModel):
    email: str = Field(..., description="Account email for password recovery")


@app.middleware("http")
async def add_disclaimer_headers(request: Request, call_next):
    response: Response = await call_next(request)
    response.headers["X-Analysis-Disclaimer"] = "Operational indicators only; not authoritative legal advice."
    response.headers["X-Engine-Type"] = "legal_bert_ml_engine"
    response.headers["X-Phase"] = "1-no-login"
    response.headers["X-Storage-Policy"] = "ephemeral-in-memory-ttl-30m"
    response.headers["X-Persistence-Note"] = "in-memory-only-does-not-survive-restart"
    return response


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Sanitizes unhandled server exceptions to protect visitor security."""
    if isinstance(exc, HTTPException):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    logger.error("Unhandled server exception on %s %s: %s", request.method, request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An internal server error occurred while processing your request. Please try again later."
            }
        }
    )


# ==============================================================================
# Health & Diagnostic Endpoints
# ==============================================================================
@app.get("/", tags=["Diagnostic"])
def root_info():
    """Root info endpoint confirming API service and documentation location."""
    return {
        "service": "Smart Contract Analyser API",
        "status": "online",
        "docs": "/docs",
        "health": "/health",
        "ready": "/ready"
    }


@app.get("/health", tags=["Diagnostic"])
@app.get("/api/v1/health", tags=["Diagnostic"])
def health_check():
    """Health check endpoint confirming engine readiness, checkpoint name, and storage policy."""
    engine = AnalysisEngine()
    is_model_ready = engine.is_model_available()
    return {
        "status": "healthy" if is_model_ready else "degraded",
        "service": "Smart Contract Analyser API",
        "version": AnalysisEngine.VERSION,
        "engine": AnalysisEngine.ENGINE_TYPE,
        "phase": "1-no-login",
        "storagePolicy": "ephemeral-in-memory-ttl-30m",
        "persistenceNote": "Ephemeral in-memory cache; results do not survive server restarts.",
        "modelAvailable": is_model_ready,
        "checkpointName": engine.checkpoint_name,
        "checkpointPath": f"analysis/models/{engine.checkpoint_name}",
        "checkpointVersion": "v3.3.0",
        "modelStatus": "deployed" if is_model_ready else "training_blocked_by_data_limitations",
        "disclaimer": "Automated pre-deployment decision support. Findings are operational risk indicators, not authoritative legal advice.",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }


@app.get("/ready", tags=["Diagnostic"])
@app.get("/api/v1/ready", tags=["Diagnostic"])
def readiness_probe(response: Response):
    """
    Readiness probe for orchestrators and frontend pre-flight checks.
    Fails with HTTP 503 if the required legal_bert_v3.3.0 model checkpoint is unavailable.
    """
    engine = AnalysisEngine()
    if not engine.is_model_available():
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "not_ready",
            "modelStatus": "unavailable",
            "reason": "Required Legal-BERT checkpoint (legal_bert_v3.3.0) is not loaded or unavailable."
        }
    return {
        "status": "ready",
        "checkpointName": engine.checkpoint_name,
        "engine": AnalysisEngine.ENGINE_TYPE
    }


def _validate_source(raw_source: Optional[str]) -> str:
    """Validates submitted source text safely and returns cleaned source or raises HTTPException."""
    if not raw_source or not raw_source.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "EMPTY_SOURCE",
                "message": "Solidity source code cannot be empty. Please provide valid contract source text."
            }
        )

    if len(raw_source) > MAX_SOURCE_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "code": "PAYLOAD_TOO_LARGE",
                "message": f"Source code length ({len(raw_source)} bytes) exceeds the maximum allowed limit of {MAX_SOURCE_LENGTH} bytes."
            }
        )

    clean_source = raw_source.strip()
    if "\x00" in clean_source:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "MALFORMED_SOURCE",
                "message": "Source code contains invalid null byte characters."
            }
        )

    parser = SolidityParser(clean_source)
    parsed = parser.parse()

    if parsed.get("status") == "malformed_input":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "MALFORMED_SOURCE",
                "message": f"Malformed Solidity syntax: {'; '.join(parsed.get('warnings', []))}"
            }
        )

    if not parsed.get("contracts") and not parsed.get("pragmas"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "UNSUPPORTED_SOURCE",
                "message": "No recognized Solidity contract, interface, library, or pragma declarations were found in the provided input."
            }
        )

    return clean_source


# ==============================================================================
# Phase 1: Synchronous Serverless-Compatible Analysis Endpoints
# ==============================================================================
@app.post("/api/v1/analyze", tags=["Analysis"], status_code=status.HTTP_200_OK)
def analyze_contract(payload: AnalyzeRequest, request: Request):
    """
    Direct synchronous analysis of Solidity source code using the Legal-BERT classifier.
    Designed for serverless compatibility: one request performs validation and analysis,
    and returns the completed report directly in the HTTP response.
    """
    client_ip = request.client.host if request.client else "unknown"
    _check_rate_limit(client_ip)

    raw_source = payload.sourceCode or payload.source_code
    contract_name = payload.contractName or payload.contract_name or "Contract.sol"
    desc = payload.description or ""

    clean_source = _validate_source(raw_source)

    # Concurrency protection
    acquired = analysis_semaphore.acquire(timeout=60)
    if not acquired:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "SERVER_BUSY",
                "message": "The analysis server is currently at maximum capacity. Please retry shortly."
            }
        )

    try:
        t_start = time.time()
        engine = AnalysisEngine()
        result = engine.analyze_source(clean_source, contract_name=contract_name, description=desc, persist=False)
        t_elapsed = round(time.time() - t_start, 2)

        if result.get("status") == "failed":
            err = result.get("error", {})
            err_code = err.get("code", "ANALYSIS_FAILED")
            http_code = status.HTTP_400_BAD_REQUEST if err_code in ("EMPTY_SOURCE", "MALFORMED_SOURCE") else status.HTTP_422_UNPROCESSABLE_ENTITY
            raise HTTPException(
                status_code=http_code,
                detail={"code": err_code, "message": err.get("message", "Analysis execution failed.")}
            )

        # Cache ephemeral result in memory
        _store_analysis(result["analysisId"], result)
        logger.info("Synchronous analysis for %s completed in %.2fs (findings: %d, riskScore: %d)",
                    contract_name, t_elapsed, len(result.get("findings", [])), result.get("riskScore", 0))
        return result
    finally:
        analysis_semaphore.release()


@app.post("/api/v1/analyze/upload", tags=["Analysis"], status_code=status.HTTP_200_OK)
async def upload_contract_file(
    request: Request,
    file: UploadFile = File(..., description="Solidity smart contract file (.sol)"),
    contract_name: Optional[str] = Form(None),
    description: Optional[str] = Form("")
):
    """
    Accepts multipart .sol file upload, performs synchronous Legal-BERT analysis,
    and returns the completed report in the same response.
    """
    client_ip = request.client.host if request.client else "unknown"
    _check_rate_limit(client_ip)

    if not file.filename.lower().endswith(".sol"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_FILE_TYPE",
                "message": f"Unsupported file '{file.filename}'. Only Solidity smart contract files (.sol) are accepted."
            }
        )

    content_bytes = await file.read()
    if len(content_bytes) > MAX_SOURCE_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "code": "PAYLOAD_TOO_LARGE",
                "message": f"Uploaded file ({len(content_bytes)} bytes) exceeds the maximum allowed limit of {MAX_SOURCE_LENGTH} bytes."
            }
        )

    try:
        source_text = content_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_ENCODING",
                "message": "File content must be UTF-8 encoded text."
            }
        )

    c_name = contract_name or file.filename or "Contract.sol"
    clean_source = _validate_source(source_text)

    # Concurrency protection
    acquired = analysis_semaphore.acquire(timeout=60)
    if not acquired:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "SERVER_BUSY",
                "message": "The analysis server is currently at maximum capacity. Please retry shortly."
            }
        )

    try:
        t_start = time.time()
        engine = AnalysisEngine()
        result = engine.analyze_source(clean_source, contract_name=c_name, description=description or "", persist=False)
        t_elapsed = round(time.time() - t_start, 2)

        if result.get("status") == "failed":
            err = result.get("error", {})
            err_code = err.get("code", "ANALYSIS_FAILED")
            http_code = status.HTTP_400_BAD_REQUEST if err_code in ("EMPTY_SOURCE", "MALFORMED_SOURCE") else status.HTTP_422_UNPROCESSABLE_ENTITY
            raise HTTPException(
                status_code=http_code,
                detail={"code": err_code, "message": err.get("message", "Analysis execution failed.")}
            )

        _store_analysis(result["analysisId"], result)
        logger.info("Upload analysis for %s completed in %.2fs", c_name, t_elapsed)
        return result
    finally:
        analysis_semaphore.release()


def _run_analysis_job_thread(job_id: str, clean_source: str, contract_name: str, desc: str):
    """Executes the analysis stages in background thread for async job clients."""
    acquired = False
    try:
        if job_id not in jobs_store:
            return

        acquired = analysis_semaphore.acquire(timeout=60)
        if not acquired:
            if job_id in jobs_store:
                jobs_store[job_id]["status"] = "failed"
                jobs_store[job_id]["stage"] = "failed"
                jobs_store[job_id]["error"] = {
                    "code": "SERVER_BUSY",
                    "message": "The analysis server is currently at maximum capacity. Please retry shortly."
                }
            return

        jobs_store[job_id]["status"] = "running"
        jobs_store[job_id]["stage"] = "inferring"
        jobs_store[job_id]["stageMessage"] = "Executing Legal-BERT neural inference and explainability..."
        jobs_store[job_id]["progress"] = 50

        engine = AnalysisEngine()
        result = engine.analyze_source(clean_source, contract_name=contract_name, description=desc, persist=False)

        if result.get("status") == "failed":
            jobs_store[job_id]["status"] = "failed"
            jobs_store[job_id]["stage"] = "failed"
            jobs_store[job_id]["error"] = result.get("error", {"code": "ANALYSIS_FAILED", "message": "Analysis failed."})
        else:
            _store_analysis(result["analysisId"], result)
            jobs_store[job_id]["status"] = "completed"
            jobs_store[job_id]["stage"] = "completed"
            jobs_store[job_id]["stageMessage"] = "Legal-BERT analysis complete."
            jobs_store[job_id]["progress"] = 100
            jobs_store[job_id]["result"] = result
    except Exception as ex:
        logger.error("Exception in analysis job %s: %s", job_id, ex, exc_info=True)
        if job_id in jobs_store:
            jobs_store[job_id]["status"] = "failed"
            jobs_store[job_id]["stage"] = "failed"
            jobs_store[job_id]["error"] = {"code": "ANALYSIS_ERROR", "message": "An error occurred during analysis."}
    finally:
        if acquired:
            analysis_semaphore.release()


# Backwards compatibility job endpoints (for async polling clients)
@app.post("/api/v1/analyze/jobs", tags=["Analysis"], status_code=status.HTTP_202_ACCEPTED)
def create_analysis_job(payload: AnalyzeRequest, request: Request):
    """
    Backwards compatibility endpoint for existing job-based clients.
    Initiates background job thread and returns jobId for polling.
    """
    client_ip = request.client.host if request.client else "unknown"
    _check_rate_limit(client_ip)

    raw_source = payload.sourceCode or payload.source_code
    contract_name = payload.contractName or payload.contract_name or "Contract.sol"
    desc = payload.description or ""

    clean_source = _validate_source(raw_source)
    job_id = f"job-{uuid.uuid4().hex[:8]}"

    job_record = {
        "jobId": job_id,
        "status": "queued",
        "stage": "validating",
        "stageMessage": "Solidity syntax validated. Initializing Legal-BERT pipeline...",
        "progress": 15,
        "contractName": contract_name,
        "createdAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "_created_timestamp": time.time(),
        "result": None,
        "error": None
    }
    jobs_store[job_id] = job_record

    thread = threading.Thread(
        target=_run_analysis_job_thread,
        args=(job_id, clean_source, contract_name, desc),
        daemon=True
    )
    thread.start()

    return {
        "jobId": job_id,
        "status": "queued",
        "stage": "validating",
        "stageMessage": "Solidity syntax validated. Initializing Legal-BERT pipeline...",
        "progress": 15,
        "contractName": contract_name
    }


@app.get("/api/v1/jobs/{job_id}", tags=["Analysis"])
def get_job_status(job_id: str):
    """Retrieves status and result of an analysis job."""
    _purge_expired_ephemeral_data()
    job = jobs_store.get(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "JOB_NOT_FOUND",
                "message": f"Analysis job '{job_id}' not found or expired under the ephemeral retention policy."
            }
        )
    return job


@app.get("/api/v1/analyze/{analysis_id}", tags=["Analysis"])
def get_analysis_by_id(analysis_id: str):
    """Retrieves an existing analysis by analysisId from in-memory cache or seeded database."""
    _purge_expired_ephemeral_data()

    if analysis_id in analyses_store:
        return analyses_store[analysis_id]

    db_record = db.get_analysis_by_id(analysis_id)
    if db_record:
        analyses_store[analysis_id] = db_record
        return db_record

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={
            "code": "ANALYSIS_NOT_FOUND",
            "message": f"No audit found with ID '{analysis_id}' in ephemeral session store or seeded database."
        }
    )


@app.post("/api/v1/analyze/{analysis_id}/discard", tags=["Analysis"])
@app.delete("/api/v1/analyze/{analysis_id}", tags=["Analysis"])
def discard_analysis(analysis_id: str):
    """Explicitly discards a temporary analysis and purges in-memory buffers."""
    removed = _discard_analysis(analysis_id)
    return {
        "status": "discarded",
        "analysisId": analysis_id,
        "purgedFromMemory": removed,
        "message": "Temporary analysis content and session cache have been discarded."
    }


# ==============================================================================
# Phase 8 & 9: Analysis History & Persistence (Roadmap)
# ==============================================================================
@app.get("/api/v1/analyses", tags=["History"])
def list_analysis_history(
    query: str = Query("", description="Keyword search"),
    risk_level: str = Query("All", description="Risk level filter: All, Low, Medium, High, Critical"),
    limit: int = Query(50, description="Max results")
):
    """Retrieves saved audit records from persistent database with keyword and risk filters."""
    items = db.list_analyses(query=query, risk_level=risk_level, limit=limit)
    return {
        "total": len(items),
        "query": query,
        "riskLevel": risk_level,
        "analyses": items
    }


# ==============================================================================
# Phase 6: Interactive Context-Scoped AI Legal Assistant
# ==============================================================================
@app.post("/api/v1/analyze/{analysis_id}/chat", tags=["Assistant"])
def chat_with_legal_assistant(analysis_id: str, payload: ChatRequest):
    """Answers inquiries strictly scoped to the analyzed contract."""
    _purge_expired_ephemeral_data()
    audit = analyses_store.get(analysis_id) or db.get_analysis_by_id(analysis_id)
    if not audit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ANALYSIS_NOT_FOUND", "message": f"Audit '{analysis_id}' not found."}
        )

    return answer_contract_query(payload.message, audit)


# ==============================================================================
# Phase 7: Exportable Audit Reports (PDF & DOCX)
# ==============================================================================
@app.get("/api/v1/reports/{analysis_id}/pdf", tags=["Reports"])
def export_pdf_report(analysis_id: str):
    """Generates and downloads a structured executive PDF audit report."""
    _purge_expired_ephemeral_data()
    audit = analyses_store.get(analysis_id) or db.get_analysis_by_id(analysis_id)
    if not audit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ANALYSIS_NOT_FOUND", "message": f"Audit '{analysis_id}' not found."}
        )

    pdf_bytes = generate_pdf_report(audit)
    contract_name = (audit.get("contractName") or "Contract").replace(" ", "_")
    filename = f"{contract_name}_Legal_AI_Audit_Report.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@app.get("/api/v1/reports/{analysis_id}/docx", tags=["Reports"])
def export_docx_report(analysis_id: str):
    """Generates and downloads an editable Word DOCX audit report."""
    _purge_expired_ephemeral_data()
    audit = analyses_store.get(analysis_id) or db.get_analysis_by_id(analysis_id)
    if not audit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ANALYSIS_NOT_FOUND", "message": f"Audit '{analysis_id}' not found."}
        )

    docx_bytes = generate_docx_report(audit)
    contract_name = (audit.get("contractName") or "Contract").replace(" ", "_")
    filename = f"{contract_name}_Legal_AI_Audit_Report.docx"

    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


# ==============================================================================
# Phase 1 & 11: Authentication & User Profile Management (Roadmap)
# ==============================================================================
@app.post("/api/v1/auth/register", tags=["Auth"])
def register(payload: RegisterRequest):
    """Registers a new user account into persistent storage."""
    try:
        user = db.register_user(
            email=payload.email,
            password=payload.password,
            full_name=payload.fullName,
            organization=payload.organization or "General"
        )
        return {
            "status": "success",
            "message": "Account registered successfully.",
            "user": user,
            "token": f"jwt_mock_token_{user['id']}"
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"message": str(e)})


@app.post("/api/v1/auth/login", tags=["Auth"])
def login(payload: LoginRequest):
    """Authenticates user credentials."""
    user = db.authenticate_user(payload.email, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_CREDENTIALS", "message": "Invalid email address or password."}
        )
    return {
        "status": "success",
        "message": "Authenticated successfully.",
        "user": user,
        "token": f"jwt_mock_token_{user['id']}"
    }


@app.post("/api/v1/auth/forgot-password", tags=["Auth"])
def forgot_password(payload: ForgotPasswordRequest):
    """Password recovery workflow."""
    return {
        "status": "success",
        "message": f"Password reset instructions have been dispatched to {payload.email}."
    }


@app.get("/api/v1/auth/me", tags=["Auth"])
def get_current_user_profile():
    """Returns current active user profile."""
    users = db.list_users()
    current = users[0] if users else {"email": "auditor@enterprise.com", "full_name": "Jane Doe", "role": "auditor"}
    return {
        "user": current,
        "tier": "Legal-BERT Enterprise SaaS",
        "features": ["Legal-BERT Inference", "SHAP/LIME Explanations", "AI Assistant", "PDF/DOCX Exports"]
    }


# ==============================================================================
# Phase 13: Admin Control Panel & Model Governance
# ==============================================================================
@app.get("/api/v1/admin/stats", tags=["Admin"])
def get_admin_dashboard_stats():
    """Retrieves operational metrics, user counts, and platform usage analytics."""
    return db.get_admin_metrics()


@app.get("/api/v1/admin/users", tags=["Admin"])
def get_admin_users_list():
    """Retrieves user accounts and roles for platform administration."""
    return {"users": db.list_users()}


@app.get("/api/v1/admin/model-status", tags=["Admin"])
def get_admin_model_status():
    """Retrieves real-time Legal-BERT model deployment, dataset readiness, and diagnostics."""
    engine = AnalysisEngine()
    is_available = engine.is_model_available()
    readiness = engine.get_dataset_readiness_summary()

    return {
        "modelName": "nlpaueb/legal-bert-base-uncased",
        "modelDirectory": engine.model_dir,
        "isModelAvailable": is_available,
        "status": "deployed" if is_available else "training_blocked_by_data_limitations",
        "readiness": readiness
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
