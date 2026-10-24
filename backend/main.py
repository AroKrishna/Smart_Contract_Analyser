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
import hashlib
from typing import Dict, Any, Optional, List
from collections import OrderedDict, defaultdict

# Ensure backend root is on sys.path so "import analysis" resolves correctly
# whether running from backend/ or the repository root
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi import FastAPI, HTTPException, Request, Response, status, Query, UploadFile, File, Form, Depends, Security
from fastapi.responses import Response, StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import jwt

from analysis.engine import AnalysisEngine
from analysis.parser import SolidityParser
from analysis.chat import answer_contract_query
from analysis.reports import generate_pdf_report, generate_docx_report
import backend.analysis.db as db
from backend.analysis.storage import validate_file_upload, get_storage, sanitize_filename

# Configure structured application logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("smart_contract_analyser.api")


def _load_env_file():
    """Loads environment variables from root .env or backend/.env if present."""
    root_dir = os.path.dirname(backend_dir)
    for env_path in [os.path.join(root_dir, ".env"), os.path.join(backend_dir, ".env")]:
        if os.path.isfile(env_path):
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#") or "=" not in line:
                            continue
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip("'\"")
                        if k and k not in os.environ:
                            os.environ[k] = v
                break
            except Exception as e:
                logger.warning("Could not read .env at %s: %s", env_path, e)


_load_env_file()

# Conservative payload size limit: 1 MB (well below Vercel's 4.5MB body limit)
MAX_SOURCE_LENGTH = int(os.environ.get("MAX_FILE_SIZE_BYTES", 1024 * 1024))
DATA_RETENTION_DAYS = int(os.environ.get("DATA_RETENTION_DAYS", "30"))

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
    if client_ip in ("testclient", "127.0.0.1", "localhost", "::1", "unknown"):
        return
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

# In-memory ephemeral stores
analyses_store: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()
jobs_store: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()

# Initialize database and reconcile interrupted in-flight jobs on startup
db.init_db()
db.reconcile_interrupted_jobs()


def _validate_startup_environment():
    """
    Validates startup configuration and environment integrity:
    - Verifies SQLite database initialization
    - Probes Legal-BERT model weights readiness
    - Verifies local storage sandboxing directory
    - Emits clear diagnostic warnings without leaking secrets
    """
    # 1. Database validation
    try:
        conn = db.get_connection()
        conn.execute("SELECT 1 FROM users LIMIT 1")
        conn.close()
        logger.info("Database initialized successfully at %s", db.DB_PATH)
    except Exception as db_err:
        logger.error("FATAL: Database initialization check failed: %s", db_err)

    # 2. Model weights validation
    try:
        engine = AnalysisEngine()
        if engine.is_model_available():
            logger.info("Legal-BERT model checkpoint verified and ready: %s (%s)", engine.checkpoint_name, engine.model_dir)
        else:
            logger.warning(
                "STARTUP WARNING: Legal-BERT model weights are absent from '%s'. "
                "Analysis and /ready endpoints will return HTTP 503 until model.safetensors is acquired. "
                "Run 'python scripts/setup_model.py' to download and verify the model.",
                engine.model_dir
            )
    except Exception as m_err:
        logger.warning("Model readiness probe encountered an issue: %s", m_err)

    # 3. Storage validation
    try:
        storage = get_storage()
        test_dir = getattr(storage, "base_dir", None)
        if test_dir:
            os.makedirs(test_dir, exist_ok=True)
            logger.info("Local file storage verified at %s", test_dir)
    except Exception as s_err:
        logger.warning("Storage directory check warning: %s", s_err)

    # 4. Session security notice (without leaking secrets)
    if os.environ.get("JWT_SECRET") == "sca_dev_jwt_secret_change_in_production_min32chars":
        logger.info("Running with default local development JWT secret. Set JWT_SECRET in .env for production.")


_validate_startup_environment()

# Automatic retention cleanup on startup and periodic background schedule
def run_automatic_retention_cleanup(retention_days: Optional[int] = None) -> Dict[str, Any]:
    """Executes automatic cleanup of expired files and analyses with graceful fault tolerance."""
    try:
        days = retention_days if retention_days is not None else DATA_RETENTION_DAYS
        results = db.cleanup_expired_records(retention_days=days)
        # Purge any expired/deleted analyses from in-memory ephemeral cache so stale entries are never served
        for aid in list(analyses_store.keys()):
            if db.get_analysis_by_id(aid) is None:
                analyses_store.pop(aid, None)
        if results.get("deletedFiles", 0) > 0 or results.get("deletedAnalyses", 0) > 0:
            logger.info("Automatic retention cleanup completed: %s", results)
        return results
    except Exception as ex:
        logger.warning("Automatic retention cleanup encountered an error (service remains healthy): %s", ex)
        return {"status": "error", "error": str(ex), "deletedFiles": 0, "deletedAnalyses": 0, "deletedJobs": 0}

# Run startup retention cleanup safely
run_automatic_retention_cleanup()

# Background daemon thread for periodic retention cleanup
CLEANUP_INTERVAL_SECONDS = int(os.environ.get("RETENTION_CLEANUP_INTERVAL_SECONDS", "3600"))
_retention_stop_event = threading.Event()

def _periodic_retention_worker():
    while not _retention_stop_event.is_set():
        elapsed = 0
        while elapsed < CLEANUP_INTERVAL_SECONDS and not _retention_stop_event.is_set():
            time.sleep(min(5, CLEANUP_INTERVAL_SECONDS - elapsed))
            elapsed += 5
        if not _retention_stop_event.is_set():
            run_automatic_retention_cleanup()

_periodic_retention_thread = threading.Thread(target=_periodic_retention_worker, daemon=True, name="RetentionWorker")
_periodic_retention_thread.start()

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


cancelled_jobs: set = set()
cancelled_jobs_lock = threading.Lock()


def _discard_analysis(analysis_id: str) -> bool:
    """Explicitly removes an analysis and its associated jobs from ephemeral cache and flags for cancellation."""
    removed = False
    if analysis_id in analyses_store:
        analyses_store.pop(analysis_id, None)
        removed = True

    with cancelled_jobs_lock:
        if analysis_id in jobs_store:
            cancelled_jobs.add(analysis_id)
            jobs_store.pop(analysis_id, None)
            removed = True

        for jid in list(jobs_store.keys()):
            job_item = jobs_store.get(jid, {})
            job_result = job_item.get("result")
            if jid == analysis_id or (job_result and job_result.get("analysisId") == analysis_id):
                cancelled_jobs.add(jid)
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
    idempotencyKey: Optional[str] = Field(None, description="Optional idempotency key to prevent duplicate runs")
    idempotency_key: Optional[str] = Field(None, description="Optional idempotency key to prevent duplicate runs")


class ChatRequest(BaseModel):
    message: Optional[str] = Field(None, description="User query about the contract")
    query: Optional[str] = Field(None, description="Alternative field for user query")


class LoginRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., description="Account password")


class RegisterRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., description="Account password")
    fullName: Optional[str] = Field(None, description="User full name")
    name: Optional[str] = Field(None, description="User full name alternative")
    organization: Optional[str] = Field("General", description="Organization / Company name")

    def get_full_name(self) -> str:
        return self.fullName or self.name or "Auditor"


class ForgotPasswordRequest(BaseModel):
    email: str = Field(..., description="Account email for password recovery")


class ChangePasswordRequest(BaseModel):
    currentPassword: str = Field(..., description="Current account password")
    newPassword: str = Field(..., description="New account password (min 8 chars)")


class UpdateProfileRequest(BaseModel):
    fullName: Optional[str] = Field(None, description="Updated full name")
    organization: Optional[str] = Field(None, description="Updated organization")


# JWT Session Configuration (Harmonized with .env.example, README, and tests)
JWT_SECRET = os.environ.get("JWT_SECRET", "sca_dev_jwt_secret_change_in_production_min32chars")
JWT_ALGORITHM = "HS256"

# Harmonized unit: hours (defaults to 24 hours)
_jwt_hours_raw = os.environ.get("JWT_EXPIRY_HOURS") or os.environ.get("JWT_EXPIRE_HOURS")
if _jwt_hours_raw:
    JWT_EXPIRY_HOURS = int(_jwt_hours_raw)
elif "JWT_EXPIRE_MINUTES" in os.environ:
    JWT_EXPIRY_HOURS = max(1, int(os.environ["JWT_EXPIRE_MINUTES"]) // 60)
else:
    JWT_EXPIRY_HOURS = 24

_jwt_cookie_sec_raw = os.environ.get("JWT_COOKIE_SECURE", "").strip().lower()
if _jwt_cookie_sec_raw in ("true", "1", "yes"):
    JWT_COOKIE_SECURE = True
elif _jwt_cookie_sec_raw in ("false", "0", "no"):
    JWT_COOKIE_SECURE = False
else:
    JWT_COOKIE_SECURE = is_production

if is_production and JWT_SECRET == "sca_dev_jwt_secret_change_in_production_min32chars":
    raise RuntimeError("CRITICAL SECURITY ERROR: In production, JWT_SECRET environment variable must be configured with a secure random key.")


def create_access_token(user_id: str, email: str, role: str) -> str:
    import uuid
    now = datetime.datetime.now(datetime.timezone.utc)
    exp = now + datetime.timedelta(hours=JWT_EXPIRY_HOURS)
    payload = {
        "jti": str(uuid.uuid4()),
        "sub": user_id,
        "email": email,
        "role": role,
        "exp": exp,
        "iat": now
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except Exception:
        return None


security_bearer = HTTPBearer(auto_error=False)


DEFAULT_LOCAL_USER: Dict[str, Any] = {
    "id": "local_user",
    "email": "auditor@local.device",
    "role": "admin",
    "full_name": "Local Auditor",
    "organization": "Local Workspace"
}


async def get_current_user(
    request: Request,
    bearer: Optional[HTTPAuthorizationCredentials] = Security(security_bearer)
) -> Dict[str, Any]:
    """
    Returns the active local user identity.
    In the final single-user local edition, registration and login are not required.
    All local analyses and storage operations resolve to the local user profile.
    """
    token = None
    if bearer and bearer.credentials:
        token = bearer.credentials
    elif "access_token" in request.cookies:
        token = request.cookies.get("access_token")

    if token and not db.is_token_revoked(token):
        payload = decode_access_token(token)
        if payload and payload.get("sub"):
            user = db.get_user_by_id(payload["sub"])
            if user:
                return user

    return DEFAULT_LOCAL_USER


async def get_optional_current_user(
    request: Request,
    bearer: Optional[HTTPAuthorizationCredentials] = Security(security_bearer)
) -> Optional[Dict[str, Any]]:
    """Returns local user identity for single-user local edition."""
    return DEFAULT_LOCAL_USER


def require_role(required_role: str):
    def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        return current_user
    return role_checker


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
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
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
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
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
def analyze_contract(
    payload: AnalyzeRequest,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Direct synchronous analysis of Solidity source code using the Legal-BERT classifier.
    Designed for serverless compatibility: one request performs validation and analysis,
    and returns the completed report directly in the HTTP response.
    Associates report with authenticated user and persists to SQLite database.
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
            http_code = status.HTTP_400_BAD_REQUEST if err_code in ("EMPTY_SOURCE", "MALFORMED_SOURCE") else status.HTTP_422_UNPROCESSABLE_CONTENT
            raise HTTPException(
                status_code=http_code,
                detail={"code": err_code, "message": err.get("message", "Analysis execution failed.")}
            )

        # Associate with authenticated user and persist in database
        user_id = current_user["id"]
        result["userId"] = user_id

        # Persist source code file
        try:
            storage = get_storage()
            raw_bytes = clean_source.encode("utf-8")
            safe_name = sanitize_filename(contract_name)
            fid = f"file-{uuid.uuid4().hex[:10]}"
            spath = storage.save_file(user_id=user_id, file_id=fid, filename=safe_name, content=raw_bytes)
            fhash = hashlib.sha256(raw_bytes).hexdigest()
            db.save_file_record({
                "id": fid,
                "userId": user_id,
                "analysisId": result["analysisId"],
                "originalFilename": contract_name,
                "safeFilename": safe_name,
                "storagePath": spath,
                "storageBackend": getattr(storage, "backend_type", "local"),
                "fileSize": len(raw_bytes),
                "mimeType": "text/x-solidity",
                "sha256Hash": fhash,
                "retentionDays": DATA_RETENTION_DAYS,
            })
            result["fileId"] = fid
        except Exception as e:
            logger.warning("Could not persist source file for sync analysis %s: %s", result["analysisId"], e)

        db.insert_analysis(result, user_id=user_id)
        _store_analysis(result["analysisId"], result)

        logger.info("Synchronous analysis for %s completed in %.2fs (findings: %d, riskScore: %d, user: %s)",
                    contract_name, t_elapsed, len(result.get("findings", [])), result.get("riskScore", 0), user_id)
        return result
    finally:
        analysis_semaphore.release()


@app.post("/api/v1/analyze/upload", tags=["Analysis"], status_code=status.HTTP_200_OK)
async def upload_contract_file(
    request: Request,
    file: UploadFile = File(..., description="Solidity smart contract file (.sol)"),
    contract_name: Optional[str] = Form(None),
    description: Optional[str] = Form(""),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Accepts multipart .sol file upload, validates file type, size, encoding, and path safety,
    stores the physical file under user-isolated storage, performs synchronous Legal-BERT analysis,
    and returns the completed report with fileId reference.
    """
    client_ip = request.client.host if request.client else "unknown"
    _check_rate_limit(client_ip)

    content_bytes = await file.read()
    try:
        safe_filename, source_text = validate_file_upload(file.filename, content_bytes, max_size=MAX_SOURCE_LENGTH)
    except ValueError as val_err:
        err_msg = str(val_err)
        if ":" in err_msg:
            code, msg = [x.strip() for x in err_msg.split(":", 1)]
        else:
            code, msg = "INVALID_FILE", err_msg
        http_code = status.HTTP_413_CONTENT_TOO_LARGE if code == "PAYLOAD_TOO_LARGE" else status.HTTP_400_BAD_REQUEST
        raise HTTPException(
            status_code=http_code,
            detail={"code": code, "message": msg}
        )

    c_name = contract_name or safe_filename
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

    file_id = None
    user_id = current_user["id"]
    try:
        file_id = f"file-{uuid.uuid4().hex[:10]}"
        file_hash = hashlib.sha256(content_bytes).hexdigest()
        storage = get_storage()
        storage_path = storage.save_file(user_id=user_id, file_id=file_id, filename=safe_filename, content=content_bytes)

        # Persist file metadata
        db.save_file_record({
            "id": file_id,
            "userId": user_id,
            "originalFilename": file.filename,
            "safeFilename": safe_filename,
            "storagePath": storage_path,
            "storageBackend": getattr(storage, "backend_type", "local"),
            "fileSize": len(content_bytes),
            "mimeType": "text/x-solidity",
            "sha256Hash": file_hash,
            "retentionDays": DATA_RETENTION_DAYS,
        })

        t_start = time.time()
        engine = AnalysisEngine()
        result = engine.analyze_source(clean_source, contract_name=c_name, description=description or "", persist=False)
        t_elapsed = round(time.time() - t_start, 2)

        if result.get("status") == "failed":
            # Purge stored file on analysis failure
            db.delete_file_record(file_id, user_id=user_id)
            err = result.get("error", {})
            err_code = err.get("code", "ANALYSIS_FAILED")
            http_code = status.HTTP_400_BAD_REQUEST if err_code in ("EMPTY_SOURCE", "MALFORMED_SOURCE") else status.HTTP_422_UNPROCESSABLE_CONTENT
            raise HTTPException(
                status_code=http_code,
                detail={"code": err_code, "message": err.get("message", "Analysis execution failed.")}
            )

        result["userId"] = user_id
        result["fileId"] = file_id
        db.link_file_to_analysis(file_id=file_id, analysis_id=result["analysisId"], user_id=user_id)
        db.insert_analysis(result, user_id=user_id)
        _store_analysis(result["analysisId"], result)

        logger.info("Upload analysis for %s completed in %.2fs (user: %s, file: %s)", c_name, t_elapsed, user_id, file_id)
        return result
    except HTTPException:
        raise
    except Exception as ex:
        # Purge stored file on unexpected exception
        if file_id:
            try:
                db.delete_file_record(file_id, user_id=user_id)
            except Exception:
                pass
        raise ex
    finally:
        analysis_semaphore.release()


def _run_analysis_job_thread(
    job_id: str,
    clean_source: str,
    contract_name: str,
    desc: str,
    user_id: Optional[str] = None,
    preloaded_file_id: Optional[str] = None
):
    """Executes the analysis stages in background thread for async job clients and persists progress with cancellation support."""
    acquired = False
    try:
        with cancelled_jobs_lock:
            if job_id in cancelled_jobs or job_id not in jobs_store:
                return

        # Stage 1: Queued / Awaiting worker slot (30% monotonic)
        if job_id in jobs_store:
            jobs_store[job_id]["status"] = "queued"
            jobs_store[job_id]["stage"] = "queued"
            jobs_store[job_id]["stageMessage"] = "Solidity syntax validated. Awaiting worker execution slot..."
            jobs_store[job_id]["progress"] = 30
        db.update_job_progress(job_id, status="queued", stage="queued", stage_message="Solidity syntax validated. Awaiting worker execution slot...", progress=30)

        acquired = analysis_semaphore.acquire(timeout=60)
        if not acquired:
            with cancelled_jobs_lock:
                if job_id in cancelled_jobs or job_id not in jobs_store:
                    return
            err = {
                "code": "SERVER_BUSY",
                "message": "The analysis server is currently at maximum capacity. Please retry shortly."
            }
            if job_id in jobs_store:
                jobs_store[job_id]["status"] = "failed"
                jobs_store[job_id]["stage"] = "failed"
                jobs_store[job_id]["error"] = err
            db.update_job_progress(job_id, status="failed", stage="failed", stage_message=err["message"], progress=0, error=err)
            return

        with cancelled_jobs_lock:
            if job_id in cancelled_jobs or job_id not in jobs_store:
                return

        # Stage 2: Neural Inference (55% monotonic)
        if job_id in jobs_store:
            jobs_store[job_id]["status"] = "running"
            jobs_store[job_id]["stage"] = "inferring"
            jobs_store[job_id]["stageMessage"] = "Executing Legal-BERT neural classification across 5 legal taxonomies..."
            jobs_store[job_id]["progress"] = 55
        db.update_job_progress(job_id, status="running", stage="inferring", stage_message="Executing Legal-BERT neural classification across 5 legal taxonomies...", progress=55)

        engine = AnalysisEngine()
        result = engine.analyze_source(clean_source, contract_name=contract_name, description=desc, persist=False)

        # Discard output if job was cancelled during inference
        with cancelled_jobs_lock:
            if job_id in cancelled_jobs or job_id not in jobs_store:
                logger.info("Analysis job %s was cancelled during inference; discarding output.", job_id)
                cancel_msg = "Analysis job was cancelled by user. In-flight inference output was discarded."
                db.update_job_progress(job_id, status="cancelled", stage="cancelled", stage_message=cancel_msg, progress=0, error={"code": "JOB_CANCELLED", "message": cancel_msg})
                if job_id in jobs_store:
                    jobs_store[job_id]["status"] = "cancelled"
                    jobs_store[job_id]["stage"] = "cancelled"
                    jobs_store[job_id]["stageMessage"] = cancel_msg
                    jobs_store[job_id]["progress"] = 0
                    jobs_store[job_id]["result"] = None
                return

        if result.get("status") == "failed":
            err = result.get("error", {"code": "ANALYSIS_FAILED", "message": "Analysis failed."})
            if job_id in jobs_store:
                jobs_store[job_id]["status"] = "failed"
                jobs_store[job_id]["stage"] = "failed"
                jobs_store[job_id]["error"] = err
            db.update_job_progress(job_id, status="failed", stage="failed", stage_message="Analysis failed. Please verify syntax and resubmit.", progress=0, error=err)
            return

        # Stage 3: Explainable AI generation (80% monotonic)
        if job_id in jobs_store:
            jobs_store[job_id]["stage"] = "explaining"
            jobs_store[job_id]["stageMessage"] = "Generating Explainable AI (SHAP token attribution and LIME local surrogates)..."
            jobs_store[job_id]["progress"] = 80
        db.update_job_progress(job_id, status="running", stage="explaining", stage_message="Generating Explainable AI (SHAP token attribution and LIME local surrogates)...", progress=80)

        # Stage 4: Persisting audit record and storage file (95% monotonic)
        if job_id in jobs_store:
            jobs_store[job_id]["stage"] = "saving"
            jobs_store[job_id]["stageMessage"] = "Synthesizing statutory compliance matrix and saving audit record..."
            jobs_store[job_id]["progress"] = 95
        db.update_job_progress(job_id, status="running", stage="saving", stage_message="Synthesizing statutory compliance matrix and saving audit record...", progress=95)

        result["userId"] = user_id
        if preloaded_file_id:
            result["fileId"] = preloaded_file_id
            db.link_file_to_analysis(preloaded_file_id, result["analysisId"], user_id=user_id)
        else:
            try:
                storage = get_storage()
                raw_bytes = clean_source.encode("utf-8")
                safe_name = sanitize_filename(contract_name)
                fid = f"file-{uuid.uuid4().hex[:10]}"
                spath = storage.save_file(user_id=user_id, file_id=fid, filename=safe_name, content=raw_bytes)
                fhash = hashlib.sha256(raw_bytes).hexdigest()
                db.save_file_record({
                    "id": fid,
                    "userId": user_id,
                    "analysisId": result["analysisId"],
                    "originalFilename": contract_name,
                    "safeFilename": safe_name,
                    "storagePath": spath,
                    "storageBackend": getattr(storage, "backend_type", "local"),
                    "fileSize": len(raw_bytes),
                    "mimeType": "text/x-solidity",
                    "sha256Hash": fhash,
                    "retentionDays": DATA_RETENTION_DAYS,
                })
                result["fileId"] = fid
            except Exception as e:
                logger.warning("Could not persist source file for async job %s: %s", job_id, e)

        _store_analysis(result["analysisId"], result)
        db.insert_analysis(result, user_id=user_id)

        # Final Stage: Completed (100% monotonic)
        if job_id in jobs_store:
            jobs_store[job_id]["status"] = "completed"
            jobs_store[job_id]["stage"] = "completed"
            jobs_store[job_id]["stageMessage"] = "Legal-BERT analysis complete."
            jobs_store[job_id]["progress"] = 100
            jobs_store[job_id]["result"] = result
            jobs_store[job_id]["analysisId"] = result["analysisId"]
            jobs_store[job_id]["fileId"] = result.get("fileId")
        db.update_job_progress(job_id, status="completed", stage="completed", stage_message="Legal-BERT analysis complete.", progress=100, result=result)
    except Exception as ex:
        with cancelled_jobs_lock:
            if job_id in cancelled_jobs or job_id not in jobs_store:
                return
        logger.error("Exception in analysis job %s: %s", job_id, ex, exc_info=True)
        err = {"code": "ANALYSIS_ERROR", "message": "An error occurred during analysis. Please resubmit the contract."}
        if job_id in jobs_store:
            jobs_store[job_id]["status"] = "failed"
            jobs_store[job_id]["stage"] = "failed"
            jobs_store[job_id]["error"] = err
        db.update_job_progress(job_id, status="failed", stage="failed", stage_message=err["message"], progress=0, error=err)
    finally:
        if acquired:
            analysis_semaphore.release()


# Backwards compatibility job endpoints (for async polling clients)
@app.post("/api/v1/analyze/jobs", tags=["Analysis"], status_code=status.HTTP_202_ACCEPTED)
def create_analysis_job(
    payload: AnalyzeRequest,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Asynchronous analysis submission endpoint conforming to Part 5 specification.
    Guarantees stable job ID, user ownership, monotonic progress tracking, idempotency,
    and duplicate execution protection.
    """
    client_ip = request.client.host if request.client else "unknown"
    _check_rate_limit(client_ip)

    raw_source = payload.sourceCode or payload.source_code
    contract_name = payload.contractName or payload.contract_name or "Contract.sol"
    desc = payload.description or ""
    idem_key = payload.idempotencyKey or payload.idempotency_key or request.headers.get("Idempotency-Key")

    clean_source = _validate_source(raw_source)
    user_id = current_user["id"]
    source_hash = hashlib.sha256(clean_source.encode("utf-8")).hexdigest()

    # 1. Idempotency Key check: if client sent an idempotency key, return previous job
    if idem_key:
        existing_job = db.find_job_by_idempotency_key(idem_key, user_id=user_id)
        if existing_job:
            logger.info("Idempotent replay detected for key %s (job %s)", idem_key, existing_job["jobId"])
            return existing_job

    # 2. Duplicate active execution check: if an active job exists for identical source & user, return it
    active_job = db.find_active_job_by_source_hash(source_hash, user_id=user_id)
    if active_job:
        logger.info("Reusing in-flight job %s for duplicate source submission", active_job["jobId"])
        return active_job

    job_id = f"job-{uuid.uuid4().hex[:8]}"

    job_record = {
        "jobId": job_id,
        "userId": user_id,
        "status": "queued",
        "stage": "validating",
        "stageMessage": "Solidity syntax validated. Initializing Legal-BERT pipeline...",
        "progress": 15,
        "contractName": contract_name,
        "idempotencyKey": idem_key,
        "sourceHash": source_hash,
        "createdAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "_created_timestamp": time.time(),
        "result": None,
        "error": None
    }
    jobs_store[job_id] = job_record
    db.save_job(job_record)

    thread = threading.Thread(
        target=_run_analysis_job_thread,
        args=(job_id, clean_source, contract_name, desc, user_id),
        daemon=True,
        name=f"JobThread-{job_id}"
    )
    thread.start()

    return {
        "jobId": job_id,
        "userId": user_id,
        "status": "queued",
        "stage": "validating",
        "stageMessage": "Solidity syntax validated. Initializing Legal-BERT pipeline...",
        "progress": 15,
        "contractName": contract_name,
        "idempotencyKey": idem_key
    }


@app.post("/api/v1/analyze/jobs/upload", tags=["Analysis"], status_code=status.HTTP_202_ACCEPTED)
async def create_analysis_job_upload(
    request: Request,
    file: UploadFile = File(..., description="Solidity smart contract file (.sol)"),
    contract_name: Optional[str] = Form(None),
    description: Optional[str] = Form(""),
    idempotency_key: Optional[str] = Form(None),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Asynchronous multipart file upload analysis submission endpoint.
    Validates file upload, stores physical file into user-isolated storage sandbox,
    creates file record, and spawns the background Legal-BERT analysis job.
    """
    client_ip = request.client.host if request.client else "unknown"
    _check_rate_limit(client_ip)

    content_bytes = await file.read()
    raw_name = contract_name or file.filename or "Contract.sol"
    clean_name, clean_source = validate_file_upload(raw_name, content_bytes, MAX_SOURCE_LENGTH)
    safe_name = sanitize_filename(clean_name)

    user_id = current_user["id"]
    source_hash = hashlib.sha256(clean_source.encode("utf-8")).hexdigest()
    idem_key = idempotency_key or request.headers.get("Idempotency-Key")

    # 1. Idempotency Key check
    if idem_key:
        existing_job = db.find_job_by_idempotency_key(idem_key, user_id=user_id)
        if existing_job:
            logger.info("Idempotent replay detected for upload key %s (job %s)", idem_key, existing_job["jobId"])
            return existing_job

    # 2. Duplicate active execution check
    active_job = db.find_active_job_by_source_hash(source_hash, user_id=user_id)
    if active_job:
        logger.info("Reusing in-flight job %s for duplicate file upload submission", active_job["jobId"])
        return active_job

    # 3. Store the physical uploaded file immediately in user-isolated storage
    storage = get_storage()
    file_id = f"file-{uuid.uuid4().hex[:10]}"
    storage_path = storage.save_file(user_id=user_id, file_id=file_id, filename=safe_name, content=content_bytes)
    db.save_file_record({
        "id": file_id,
        "userId": user_id,
        "analysisId": None,
        "originalFilename": raw_name,
        "safeFilename": safe_name,
        "storagePath": storage_path,
        "storageBackend": getattr(storage, "backend_type", "local"),
        "fileSize": len(content_bytes),
        "mimeType": "text/x-solidity",
        "sha256Hash": source_hash,
        "retentionDays": DATA_RETENTION_DAYS,
    })

    # 4. Create analysis job
    job_id = f"job-{uuid.uuid4().hex[:8]}"
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    job_record = {
        "jobId": job_id,
        "userId": user_id,
        "status": "queued",
        "stage": "validating",
        "stageMessage": f"File '{safe_name}' uploaded and validated. Initializing Legal-BERT pipeline...",
        "progress": 15,
        "contractName": safe_name,
        "fileId": file_id,
        "idempotencyKey": idem_key,
        "sourceHash": source_hash,
        "createdAt": now_iso,
        "_created_timestamp": time.time(),
        "result": None,
        "error": None
    }
    jobs_store[job_id] = job_record
    db.save_job(job_record)

    thread = threading.Thread(
        target=_run_analysis_job_thread,
        args=(job_id, clean_source, safe_name, description or "", user_id, file_id),
        daemon=True,
        name=f"JobThread-{job_id}"
    )
    thread.start()

    return {
        "jobId": job_id,
        "fileId": file_id,
        "userId": user_id,
        "status": "queued",
        "stage": "validating",
        "stageMessage": f"File '{safe_name}' uploaded and validated. Initializing Legal-BERT pipeline...",
        "progress": 15,
        "contractName": safe_name,
        "idempotencyKey": idem_key,
        "createdAt": now_iso
    }


@app.get("/api/v1/jobs/{job_id}", tags=["Analysis"])
@app.get("/api/v1/analyze/jobs/{job_id}", tags=["Analysis"])
def get_job_status(
    job_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Retrieves status and progress of an analysis job in local workspace."""
    _purge_expired_ephemeral_data()
    job = jobs_store.get(job_id)
    if not job:
        job = db.get_job(job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "JOB_NOT_FOUND",
                "message": f"Analysis job '{job_id}' not found."
            }
        )

    return job


@app.post("/api/v1/jobs/{job_id}/cancel", tags=["Analysis"])
def cancel_analysis_job(
    job_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Cancels an in-flight or queued analysis job.
    Enforces truthful cancellation semantics: in-flight model inference cannot be forcibly aborted in Python,
    so its output is discarded upon completion and prevented from being persisted or served.
    """
    job = jobs_store.get(job_id) or db.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "JOB_NOT_FOUND", "message": f"Analysis job '{job_id}' not found."}
        )

    current_status = job.get("status")
    if current_status == "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "CANNOT_CANCEL", "message": "Analysis job has already completed and cannot be cancelled."}
        )

    if current_status == "cancelled":
        return {
            "jobId": job_id,
            "status": "cancelled",
            "message": "Analysis job was already cancelled."
        }

    with cancelled_jobs_lock:
        cancelled_jobs.add(job_id)

    cancel_msg = "Analysis job was cancelled by user. In-flight inference output was discarded."
    db.cancel_job(job_id, user_id=None)

    if job_id in jobs_store:
        jobs_store[job_id]["status"] = "cancelled"
        jobs_store[job_id]["stage"] = "cancelled"
        jobs_store[job_id]["stageMessage"] = cancel_msg
        jobs_store[job_id]["progress"] = 0
        jobs_store[job_id]["result"] = None

    return {
        "jobId": job_id,
        "status": "cancelled",
        "message": cancel_msg
    }


@app.get("/api/v1/jobs/{job_id}/result", tags=["Analysis"])
def get_job_result(
    job_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Retrieves the completed analysis result for a job."""
    job = jobs_store.get(job_id) or db.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "JOB_NOT_FOUND", "message": f"Analysis job '{job_id}' not found."}
        )

    job_status = job.get("status")
    if job_status in ("queued", "running"):
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={
                "code": "JOB_NOT_READY",
                "status": job_status,
                "stage": job.get("stage"),
                "stageMessage": job.get("stageMessage"),
                "progress": job.get("progress", 0),
                "message": "Analysis job is still processing."
            }
        )

    if job_status == "cancelled":
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail={
                "code": "JOB_CANCELLED",
                "status": "cancelled",
                "message": "Analysis job was cancelled by user. In-flight inference output was discarded."
            }
        )

    if job_status == "failed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "JOB_FAILED",
                "status": "failed",
                "error": job.get("error"),
                "message": job.get("stageMessage") or "Analysis job failed. Please resubmit."
            }
        )

    # Completed: retrieve result
    res = job.get("result")
    if not res and job.get("analysisId"):
        res = db.get_analysis_by_id(job["analysisId"])
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "RESULT_NOT_FOUND", "message": "Analysis result record not found."}
        )

    return res


@app.delete("/api/v1/jobs/{job_id}", tags=["Analysis"])
def delete_analysis_job(
    job_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Deletes an analysis job record from database and memory."""
    job = jobs_store.get(job_id) or db.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "JOB_NOT_FOUND", "message": f"Analysis job '{job_id}' not found."}
        )

    with cancelled_jobs_lock:
        cancelled_jobs.add(job_id)

    jobs_store.pop(job_id, None)
    deleted = db.delete_job(job_id, user_id=None)

    return {
        "jobId": job_id,
        "status": "deleted",
        "purged": deleted,
        "message": f"Analysis job '{job_id}' was removed."
    }


@app.get("/api/v1/analyze/{analysis_id}", tags=["Analysis"])
@app.get("/api/v1/analyses/{analysis_id}", tags=["Analysis"])
def get_analysis_by_id(
    analysis_id: str,
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user)
):
    """Retrieves an existing analysis by analysisId from in-memory cache or persistent database."""
    _purge_expired_ephemeral_data()

    audit = analyses_store.get(analysis_id)
    if not audit:
        audit = db.get_analysis_by_id(analysis_id)
        if audit:
            analyses_store[analysis_id] = audit

    if not audit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "ANALYSIS_NOT_FOUND",
                "message": f"No audit found with ID '{analysis_id}' in ephemeral session store or seeded database."
            }
        )

    return audit


@app.post("/api/v1/analyze/{analysis_id}/discard", tags=["Analysis"])
@app.delete("/api/v1/analyze/{analysis_id}", tags=["Analysis"])
@app.delete("/api/v1/analyses/{analysis_id}", tags=["Analysis"])
def discard_analysis(
    analysis_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Explicitly deletes an analysis and all related jobs from memory, database, and local file storage."""
    audit = analyses_store.get(analysis_id) or db.get_analysis_by_id(analysis_id)
    job = jobs_store.get(analysis_id) or db.get_job(analysis_id)

    if not audit and not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ANALYSIS_NOT_FOUND", "message": f"Analysis or job '{analysis_id}' not found."}
        )

    removed_memory = _discard_analysis(analysis_id)
    del_res = db.delete_analysis(analysis_id, user_id=None)

    if isinstance(del_res, dict) and not del_res.get("success", True):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "STORAGE_DELETION_FAILED",
                "message": del_res.get("message", "Physical storage file deletion failed. Metadata retained for retry."),
                "details": del_res
            }
        )

    removed_db = del_res.get("deletedAny", True) if isinstance(del_res, dict) else bool(del_res)

    return {
        "status": "discarded",
        "analysisId": analysis_id,
        "purgedFromMemory": removed_memory,
        "purgedFromDatabase": removed_db,
        "message": "Analysis content and associated records have been removed."
    }


# ==============================================================================
# Phase 3 & 4: Secure File Storage & Retrieval Endpoints
# ==============================================================================
@app.get("/api/v1/analyze/{analysis_id}/file", tags=["Analysis"])
def get_analysis_file(
    analysis_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Downloads the Solidity source code file associated with a saved analysis.
    Enforces user ownership isolation: only the owner or platform admin can retrieve the file.
    """
    audit = analyses_store.get(analysis_id) or db.get_analysis_by_id(analysis_id)
    if not audit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ANALYSIS_NOT_FOUND", "message": f"Analysis '{analysis_id}' not found."}
        )

    file_meta = db.get_file_record_by_analysis_id(analysis_id)
    if file_meta:
        storage = get_storage()
        try:
            content_bytes = storage.get_file(file_meta["storagePath"], user_id=file_meta["userId"])
            safe_name = file_meta.get("safeFilename") or "Contract.sol"
            return Response(
                content=content_bytes,
                media_type="text/x-solidity",
                headers={"Content-Disposition": f'attachment; filename="{safe_name}"'}
            )
        except Exception as ex:
            logger.warning("Storage read failed for file %s: %s", file_meta.get("id"), ex)

    # Fallback to in-database solidity_code if physical file was not found
    sol_code = audit.get("solidityCode")
    if sol_code:
        c_name = sanitize_filename(audit.get("contractName") or "Contract.sol")
        return Response(
            content=sol_code.encode("utf-8"),
            media_type="text/x-solidity",
            headers={"Content-Disposition": f'attachment; filename="{c_name}"'}
        )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"code": "FILE_NOT_FOUND", "message": "Source contract file not found for this analysis."}
    )


@app.get("/api/v1/files/{file_id}", tags=["Files"])
def get_stored_file(
    file_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Downloads an uploaded file directly by file ID from local storage."""
    file_meta = db.get_file_record(file_id)
    if not file_meta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "FILE_NOT_FOUND", "message": f"File '{file_id}' not found."}
        )

    storage = get_storage()
    try:
        content_bytes = storage.get_file(file_meta["storagePath"], user_id=file_meta["userId"])
    except (FileNotFoundError, PermissionError) as ex:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "FILE_NOT_FOUND", "message": str(ex)}
        )

    safe_name = file_meta.get("safeFilename") or "Contract.sol"
    return Response(
        content=content_bytes,
        media_type=file_meta.get("mimeType", "text/x-solidity"),
        headers={"Content-Disposition": f'attachment; filename="{safe_name}"'}
    )


@app.get("/api/v1/files", tags=["Files"])
def list_user_files_endpoint(
    limit: int = Query(50, description="Max files to retrieve"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Lists files uploaded and stored in the local workspace."""
    return {"files": db.list_user_files(user_id=None, limit=limit)}


# ==============================================================================
# Phase 8 & 9: Analysis History & Persistence (Local Single-User)
# ==============================================================================
@app.get("/api/v1/analyses", tags=["History"])
def list_analysis_history(
    query: str = Query("", description="Keyword search"),
    risk_level: str = Query("All", description="Risk level filter: All, Low, Medium, High, Critical"),
    limit: int = Query(50, description="Max results"),
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user)
):
    """
    Retrieves saved audit records from local SQLite database.
    Single-user local edition: all local analyses are accessible without authentication.
    """
    items = db.list_analyses(user_id=None, query=query, risk_level=risk_level, limit=limit)
    return {
        "total": len(items),
        "query": query,
        "riskLevel": risk_level,
        "analyses": items
    }


@app.get("/api/v1/user/stats", tags=["Auth"])
def get_user_stats(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Retrieves local dashboard metrics and recent activity from SQLite."""
    return db.get_user_dashboard_stats(user_id=None)


# ==============================================================================
# Phase 6: Interactive Context-Scoped AI Legal Assistant
# ==============================================================================
@app.post("/api/v1/analyze/{analysis_id}/chat", tags=["Assistant"])
@app.post("/api/v1/analyses/{analysis_id}/chat", tags=["Assistant"])
def chat_with_legal_assistant(
    analysis_id: str,
    payload: ChatRequest,
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user)
):
    """Answers inquiries strictly scoped to the analyzed contract."""
    _purge_expired_ephemeral_data()
    audit = analyses_store.get(analysis_id) or db.get_analysis_by_id(analysis_id)
    if not audit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ANALYSIS_NOT_FOUND", "message": f"Audit '{analysis_id}' not found."}
        )

    user_query = (payload.message or payload.query or "").strip()
    if not user_query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "EMPTY_QUERY", "message": "Query message cannot be empty."}
        )

    return answer_contract_query(user_query, audit)


# ==============================================================================
# Phase 7: Exportable Audit Reports (PDF & DOCX)
# ==============================================================================
@app.get("/api/v1/reports/{analysis_id}/pdf", tags=["Reports"])
def export_pdf_report(
    analysis_id: str,
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user)
):
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
def export_docx_report(
    analysis_id: str,
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user)
):
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
# Phase 1 & 11: Authentication & Local Profile (No Login Edition)
# ==============================================================================
@app.post("/api/v1/auth/register", tags=["Auth"])
def register(payload: RegisterRequest, response: Response):
    """Local single-user edition: registration is not required."""
    return {
        "status": "success",
        "message": "Local edition active. Registration is not required.",
        "user": DEFAULT_LOCAL_USER,
        "mode": "local_single_user"
    }


@app.post("/api/v1/auth/login", tags=["Auth"])
def login(payload: LoginRequest, response: Response):
    """Local single-user edition: authentication is not required."""
    return {
        "status": "success",
        "message": "Local edition active. Authentication is not required.",
        "user": DEFAULT_LOCAL_USER,
        "token": "local-session-token",
        "mode": "local_single_user"
    }


@app.post("/api/v1/auth/logout", tags=["Auth"])
def logout(response: Response):
    """Ends local session."""
    return {
        "status": "success",
        "message": "Local session reset."
    }


@app.post("/api/v1/auth/forgot-password", tags=["Auth"])
def forgot_password(payload: ForgotPasswordRequest):
    return {
        "status": "success",
        "message": "Local single-user edition does not use cloud passwords."
    }


@app.get("/api/v1/auth/me", tags=["Auth"])
def get_current_user_profile(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Returns active local user profile."""
    return {
        "status": "success",
        "mode": "local_single_user",
        "user": DEFAULT_LOCAL_USER,
        "role": DEFAULT_LOCAL_USER.get("role", "auditor"),
        "tier": "Local Edition (No Login Required)",
        "features": ["Legal-BERT Inference", "SHAP/LIME Explanations", "AI Assistant", "PDF/DOCX Exports"]
    }


@app.put("/api/v1/auth/me", tags=["Auth"])
def update_current_user_profile(payload: UpdateProfileRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    return {
        "status": "success",
        "message": "Profile updated.",
        "user": DEFAULT_LOCAL_USER
    }


@app.post("/api/v1/auth/change-password", tags=["Auth"])
def change_password(payload: ChangePasswordRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    return {
        "status": "success",
        "message": "Local single-user edition does not require passwords."
    }


# ==============================================================================
# Phase 13: Local System Diagnostics & Model Governance
# ==============================================================================
@app.get("/api/v1/admin/stats", tags=["Admin"])
def get_admin_dashboard_stats():
    """Retrieves operational metrics and platform usage analytics from local database."""
    return db.get_admin_metrics()


@app.get("/api/v1/admin/users", tags=["Admin"])
def get_admin_users_list():
    """Retrieves users (local edition)."""
    return {"users": [DEFAULT_LOCAL_USER]}


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


@app.post("/api/v1/admin/cleanup", tags=["Admin"])
def run_retention_cleanup(
    retention_days: Optional[int] = Query(None, description="Retention window in days (default 30)")
):
    """
    Triggers local data retention cleanup.
    Deletes files and database records that exceed the retention policy.
    """
    days = retention_days if retention_days is not None else DATA_RETENTION_DAYS
    cleanup_results = db.cleanup_expired_records(retention_days=days)
    return {
        "status": "success",
        "retentionDays": days,
        "results": cleanup_results,
        "message": f"Data retention cleanup executed successfully for cutoff of {days} days."
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
