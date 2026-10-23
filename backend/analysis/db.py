"""
analysis/db.py - Persistent Database Storage for Smart Contract Analyser SaaS Platform

Implements SQLite persistence for:
- Users & Authentication (Phase 1, Phase 11, Phase 13)
- Contract Analysis Results (Phase 4, Phase 5, Phase 8)
- Audit & System Event Logs (Phase 13)
"""

import os
import sqlite3
import json
import datetime
import hashlib
import hmac
import re
import logging
from typing import Dict, Any, List, Optional, Tuple

import bcrypt
import tempfile
import shutil

logger = logging.getLogger("smart_contract_analyser.db")

def _get_db_path() -> str:
    # On Vercel, AWS Lambda, or containerized serverless runtimes,
    # the deployment root filesystem is read-only.
    # Phase 1 requirement: strictly transient, no permanent storage of user contracts or results.
    if os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
        return os.path.join(tempfile.gettempdir(), "transient_smart_contract_analyser.db")

    backend_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    local_dir = os.path.join(backend_base, "data")
    os.makedirs(local_dir, exist_ok=True)
    return os.path.join(local_dir, "transient_smart_contract_analyser.db")


DB_PATH = _get_db_path()
DB_DIR = os.path.dirname(DB_PATH)


def hash_password(password: str) -> str:
    """Hash password using modern bcrypt with 12 salt rounds."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, stored_hash: str) -> Tuple[bool, bool]:
    """
    Verifies a plain password against the stored hash.
    Returns (is_valid, needs_rehash).
    - For modern bcrypt hashes ($2b$ or $2a$), returns (valid, False).
    - For legacy single-round SHA-256 hashes (64 hex chars), verifies legacy hash
      and returns (True, True) on match so the caller can rehash to bcrypt.
    """
    if not stored_hash or not plain_password:
        return False, False

    # 1. Check modern bcrypt hash
    if stored_hash.startswith("$2b$") or stored_hash.startswith("$2a$"):
        try:
            valid = bcrypt.checkpw(plain_password.encode("utf-8"), stored_hash.encode("utf-8"))
            return valid, False
        except Exception:
            return False, False

    # 2. Check legacy static-salt SHA-256 format
    legacy_salt = "sca_saas_platform_salt_2026"
    legacy_candidate = hashlib.sha256((plain_password + legacy_salt).encode("utf-8")).hexdigest()
    if hmac.compare_digest(stored_hash, legacy_candidate):
        return True, True

    return False, False


def update_user_password(user_id: str, new_password_hash: str):
    """Updates stored password hash for an existing user account."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_password_hash, user_id))
    conn.commit()
    conn.close()


def get_connection():
    """Returns a connection to the SQLite database with row factory."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def revoke_token(token: str, user_id: Optional[str] = None, expires_at: Optional[int] = None) -> None:
    """Revokes a session token to ensure it cannot access protected endpoints after logout."""
    if not token:
        return
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    exp = expires_at or int(datetime.datetime.now(datetime.timezone.utc).timestamp() + 86400)
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO revoked_tokens (token_hash, user_id, revoked_at, expires_at)
        VALUES (?, ?, ?, ?)
    """, (token_hash, user_id, now_iso, exp))
    conn.commit()
    conn.close()


def is_token_revoked(token: str) -> bool:
    """Checks whether a session token has been revoked."""
    if not token:
        return False
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM revoked_tokens WHERE token_hash = ?", (token_hash,))
    row = cursor.fetchone()
    conn.close()
    return row is not None


def init_db(reconcile: bool = True):
    """Initializes the SQLite database tables and default admin/user records."""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            organization TEXT DEFAULT 'General',
            role TEXT DEFAULT 'auditor',
            created_at TEXT NOT NULL
        )
    """)

    # 2. Analyses table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            file_id TEXT,
            contract_name TEXT NOT NULL,
            contract_type TEXT DEFAULT 'Solidity Smart Contract',
            solidity_code TEXT NOT NULL,
            solidity_version TEXT DEFAULT '^0.8.20',
            status TEXT NOT NULL,
            risk_score INTEGER NOT NULL,
            risk_level TEXT NOT NULL,
            risk_breakdown TEXT NOT NULL,
            categories TEXT NOT NULL,
            findings TEXT NOT NULL,
            shap_values TEXT NOT NULL,
            lime_explanations TEXT NOT NULL,
            recommendations TEXT NOT NULL,
            compliance_matrix TEXT NOT NULL,
            summary TEXT NOT NULL,
            model_engine TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    # Safe migration: ensure user_id and file_id columns exist if table pre-existed
    cursor.execute("PRAGMA table_info(analyses)")
    existing_analysis_cols = [r["name"] for r in cursor.fetchall()]
    if "user_id" not in existing_analysis_cols:
        cursor.execute("ALTER TABLE analyses ADD COLUMN user_id TEXT")
    if "file_id" not in existing_analysis_cols:
        cursor.execute("ALTER TABLE analyses ADD COLUMN file_id TEXT")

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_analyses_user_id ON analyses(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_analyses_file_id ON analyses(file_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_analyses_created_at ON analyses(created_at)")

    # 3. Analysis Jobs table (persists background jobs across server reboots)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            contract_name TEXT NOT NULL,
            status TEXT NOT NULL,
            stage TEXT NOT NULL,
            stage_message TEXT,
            progress INTEGER NOT NULL DEFAULT 0,
            result_json TEXT,
            error_json TEXT,
            idempotency_key TEXT,
            source_hash TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    cursor.execute("PRAGMA table_info(jobs)")
    existing_job_cols = [r["name"] for r in cursor.fetchall()]
    if "idempotency_key" not in existing_job_cols:
        cursor.execute("ALTER TABLE jobs ADD COLUMN idempotency_key TEXT")
    if "source_hash" not in existing_job_cols:
        cursor.execute("ALTER TABLE jobs ADD COLUMN source_hash TEXT")

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_user_id ON jobs(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_idempotency ON jobs(user_id, idempotency_key)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_source_hash ON jobs(user_id, source_hash)")

    # 4. System & Audit Logs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            user_email TEXT,
            details TEXT,
            ip_address TEXT,
            created_at TEXT NOT NULL
        )
    """)

    # 5. Revoked / Invalidated session tokens table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS revoked_tokens (
            token_hash TEXT PRIMARY KEY,
            user_id TEXT,
            revoked_at TEXT NOT NULL,
            expires_at INTEGER NOT NULL
        )
    """)

    # 6. Uploaded / Stored Files Metadata table (Part 4)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stored_files (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            analysis_id TEXT,
            original_filename TEXT NOT NULL,
            safe_filename TEXT NOT NULL,
            storage_path TEXT NOT NULL,
            storage_backend TEXT NOT NULL DEFAULT 'local',
            file_size INTEGER NOT NULL,
            mime_type TEXT NOT NULL DEFAULT 'text/x-solidity',
            sha256_hash TEXT NOT NULL,
            retention_days INTEGER DEFAULT 30,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_stored_files_user_id ON stored_files(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_stored_files_analysis_id ON stored_files(analysis_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_stored_files_created_at ON stored_files(created_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_stored_files_expires_at ON stored_files(expires_at)")

    # Development Seed Accounts
    # Controlled by SEED_DEV_ACCOUNTS environment variable (enabled by default in dev,
    # strictly disabled in production environments).
    is_prod = os.environ.get("ENVIRONMENT") == "production" or os.environ.get("VERCEL_ENV") == "production"
    seed_dev = os.environ.get("SEED_DEV_ACCOUNTS", "false" if is_prod else "true").lower() in ("true", "1", "yes")

    if seed_dev:
        # Check if default admin exists
        cursor.execute("SELECT id, password_hash FROM users WHERE email = 'admin@legal-ai.io'")
        admin_row = cursor.fetchone()
        if not admin_row:
            cursor.execute("""
                INSERT INTO users (id, email, password_hash, full_name, organization, role, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                "usr-admin-01",
                "admin@legal-ai.io",
                hash_password("AdminPass2026!"),
                "System Administrator",
                "Legal AI Security Lab",
                "admin",
                datetime.datetime.now(datetime.timezone.utc).isoformat()
            ))

        # Check if default demo user exists
        cursor.execute("SELECT id, password_hash FROM users WHERE email = 'auditor@enterprise.com'")
        auditor_row = cursor.fetchone()
        if not auditor_row:
            cursor.execute("""
                INSERT INTO users (id, email, password_hash, full_name, organization, role, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                "usr-auditor-02",
                "auditor@enterprise.com",
                hash_password("AuditorPass2026!"),
                "Jane Doe",
                "Web3 Compliance Partners",
                "auditor",
                datetime.datetime.now(datetime.timezone.utc).isoformat()
            ))

    conn.commit()
    conn.close()

    if reconcile:
        reconcile_interrupted_jobs()


def insert_analysis(record: Dict[str, Any], user_id: Optional[str] = None) -> str:
    """Persists a new contract analysis into the database, associating it with the submitting user."""
    init_db(reconcile=False)
    conn = get_connection()
    cursor = conn.cursor()

    analysis_id = record.get("analysisId") or record.get("id")
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    effective_user_id = user_id or record.get("userId") or record.get("user_id")
    file_id = record.get("fileId") or record.get("file_id")

    cursor.execute("""
        INSERT OR REPLACE INTO analyses (
            id, user_id, file_id, contract_name, contract_type, solidity_code, solidity_version,
            status, risk_score, risk_level, risk_breakdown, categories,
            findings, shap_values, lime_explanations, recommendations,
            compliance_matrix, summary, model_engine, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        analysis_id,
        effective_user_id,
        file_id,
        record.get("contractName") or record.get("name") or "Contract.sol",
        record.get("contractType") or "Solidity Smart Contract",
        record.get("solidityCode") or "",
        record.get("solidityVersion") or "^0.8.20",
        record.get("status") or "completed",
        record.get("riskScore", 0),
        record.get("riskLevel", "Low"),
        json.dumps(record.get("riskBreakdown", {})),
        json.dumps(record.get("categories", [])),
        json.dumps(record.get("findings", [])),
        json.dumps(record.get("shapValues", [])),
        json.dumps(record.get("limeExplanations", [])),
        json.dumps(record.get("recommendations", [])),
        json.dumps(record.get("complianceMatrix", [])),
        record.get("summary", ""),
        record.get("metadata", {}).get("engineType", "legal_bert_ml_engine"),
        record.get("timestamp") or now_iso
    ))

    # Log the audit creation
    cursor.execute("""
        INSERT INTO audit_logs (event_type, user_email, details, created_at)
        VALUES (?, ?, ?, ?)
    """, (
        "ANALYSIS_SAVED",
        effective_user_id or "anonymous",
        f"Analysis {analysis_id} for contract {record.get('contractName', 'Contract')} saved.",
        now_iso
    ))

    conn.commit()
    conn.close()
    return analysis_id


def get_analysis_by_id(analysis_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves an analysis by its ID and decodes JSON fields."""
    init_db(reconcile=False)
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM analyses WHERE id = ?", (analysis_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    code = row["solidity_code"] or ""
    file_id = row["file_id"] if "file_id" in row.keys() else None
    if not code and file_id:
        try:
            from .storage import get_storage
            f_record = get_file_record(file_id)
            if f_record:
                storage = get_storage()
                code_bytes = storage.get_file(f_record["storagePath"], f_record["userId"])
                code = code_bytes.decode("utf-8")
        except Exception:
            pass

    return {
        "analysisId": row["id"],
        "id": row["id"],
        "userId": row["user_id"],
        "user_id": row["user_id"],
        "fileId": file_id,
        "file_id": file_id,
        "contractName": row["contract_name"],
        "name": row["contract_name"],
        "contractType": row["contract_type"],
        "solidityCode": code,
        "solidityVersion": row["solidity_version"],
        "status": row["status"],
        "riskScore": row["risk_score"],
        "overallRiskScore": row["risk_score"],
        "riskLevel": row["risk_level"],
        "overallRiskLevel": row["risk_level"],
        "riskBreakdown": json.loads(row["risk_breakdown"]),
        "categories": json.loads(row["categories"]),
        "findings": json.loads(row["findings"]),
        "shapValues": json.loads(row["shap_values"]),
        "shapExplanations": json.loads(row["shap_values"]),
        "limeExplanations": json.loads(row["lime_explanations"]),
        "recommendations": json.loads(row["recommendations"]),
        "complianceMatrix": json.loads(row["compliance_matrix"]),
        "summary": row["summary"],
        "auditDate": row["created_at"],
        "timestamp": row["created_at"],
        "metadata": {
            "engineType": row["model_engine"],
            "analysisModelVersion": "legal-bert-multi-label-v1.0"
        }
    }


def list_analyses(user_id: Optional[str] = None, query: str = "", risk_level: str = "All", limit: int = 50) -> List[Dict[str, Any]]:
    """Lists saved analyses with optional ownership (user_id), keyword, and risk-level filters."""
    init_db(reconcile=False)
    conn = get_connection()
    cursor = conn.cursor()

    sql = "SELECT * FROM analyses WHERE 1=1"
    params = []

    if user_id:
        sql += " AND user_id = ?"
        params.append(user_id)

    if query and query.strip():
        sql += " AND (contract_name LIKE ? OR summary LIKE ?)"
        term = f"%{query.strip()}%"
        params.extend([term, term])

    if risk_level and risk_level.lower() != "all":
        sql += " AND risk_level = ?"
        params.append(risk_level)

    sql += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()

    results = []
    for row in rows:
        results.append({
            "analysisId": row["id"],
            "id": row["id"],
            "userId": row["user_id"],
            "user_id": row["user_id"],
            "fileId": row["file_id"] if "file_id" in row.keys() else None,
            "file_id": row["file_id"] if "file_id" in row.keys() else None,
            "contractName": row["contract_name"],
            "name": row["contract_name"],
            "contractType": row["contract_type"],
            "status": row["status"],
            "riskScore": row["risk_score"],
            "riskLevel": row["risk_level"],
            "overallRiskScore": row["risk_score"],
            "overallRiskLevel": row["risk_level"],
            "summary": row["summary"],
            "description": row["summary"],
            "auditDate": row["created_at"],
            "created_at": row["created_at"]
        })
    return results


def delete_analysis(analysis_id: str, user_id: Optional[str] = None) -> bool:
    """
    Permanently deletes an analysis record, associated uploaded files, and all related jobs,
    strictly scoped to the owner's user_id.
    """
    init_db(reconcile=False)
    conn = get_connection()
    cursor = conn.cursor()

    related_ids = {analysis_id}
    # Check if analysis_id is a job id that contains an analysisId in result_json
    if user_id:
        cursor.execute("SELECT result_json FROM jobs WHERE id = ? AND user_id = ?", (analysis_id, user_id))
    else:
        cursor.execute("SELECT result_json FROM jobs WHERE id = ?", (analysis_id,))
    job_row = cursor.fetchone()
    if job_row and job_row["result_json"]:
        try:
            res_obj = json.loads(job_row["result_json"])
            if isinstance(res_obj, dict) and res_obj.get("analysisId"):
                related_ids.add(res_obj["analysisId"])
        except Exception:
            pass

    # 1. Identify all associated files to remove physical storage and DB metadata
    files_to_delete = []
    for target_id in list(related_ids):
        if user_id:
            cursor.execute("SELECT id, user_id, storage_path FROM stored_files WHERE user_id = ? AND (analysis_id = ? OR id = ?)", (user_id, target_id, target_id))
        else:
            cursor.execute("SELECT id, user_id, storage_path FROM stored_files WHERE analysis_id = ? OR id = ?", (target_id, target_id))
        for r in cursor.fetchall():
            files_to_delete.append(dict(r))

        if user_id:
            cursor.execute("SELECT file_id, user_id FROM analyses WHERE user_id = ? AND id = ?", (user_id, target_id))
        else:
            cursor.execute("SELECT file_id, user_id FROM analyses WHERE id = ?", (target_id,))
        a_row = cursor.fetchone()
        if a_row and "file_id" in a_row.keys() and a_row["file_id"]:
            f_id = a_row["file_id"]
            cursor.execute("SELECT id, user_id, storage_path FROM stored_files WHERE id = ?", (f_id,))
            f_row = cursor.fetchone()
            if f_row:
                files_to_delete.append(dict(f_row))

    # Safely delete physical files from storage backend
    failed_file_ids = set()
    failed_errors = []

    from .storage import get_storage
    try:
        storage = get_storage()
    except Exception as ex:
        storage = None
        failed_errors.append(f"Storage backend unavailable: {ex}")

    for f_meta in files_to_delete:
        if storage:
            try:
                if storage.file_exists(f_meta["storage_path"], f_meta["user_id"]):
                    removed = storage.delete_file(f_meta["storage_path"], f_meta["user_id"])
                    if not removed:
                        failed_file_ids.add(f_meta["id"])
                        failed_errors.append(f"Physical file removal returned False for {f_meta['storage_path']}")
            except Exception as e:
                failed_file_ids.add(f_meta["id"])
                failed_errors.append(f"Error removing physical file {f_meta['storage_path']}: {e}")
        else:
            failed_file_ids.add(f_meta["id"])

    # If physical deletion failed for any file, do NOT falsely report complete deletion!
    # Retain metadata for failed files so they can be retried.
    if failed_file_ids:
        logger.error("Physical storage deletion failed for files: %s. Retaining metadata for retry.", failed_file_ids)
        conn.close()
        return {
            "success": False,
            "error": "STORAGE_DELETION_FAILED",
            "message": f"Physical storage file deletion failed for {len(failed_file_ids)} file(s). Metadata retained for retry.",
            "failedFiles": list(failed_file_ids),
            "errors": failed_errors
        }

    # Purge file metadata rows
    deleted_any = False
    for f_meta in files_to_delete:
        cursor.execute("DELETE FROM stored_files WHERE id = ?", (f_meta["id"],))
        deleted_any = True

    # 2. Delete analyses and jobs records
    for target_id in related_ids:
        pattern = f'%"{target_id}"%'
        if user_id:
            cursor.execute("DELETE FROM analyses WHERE id = ? AND user_id = ?", (target_id, user_id))
            if cursor.rowcount > 0:
                deleted_any = True
            cursor.execute(
                """DELETE FROM jobs
                   WHERE user_id = ?
                     AND (id = ? OR result_json LIKE ?)""",
                (user_id, target_id, pattern)
            )
            if cursor.rowcount > 0:
                deleted_any = True
        else:
            cursor.execute("DELETE FROM analyses WHERE id = ?", (target_id,))
            if cursor.rowcount > 0:
                deleted_any = True
            cursor.execute(
                """DELETE FROM jobs
                   WHERE id = ? OR result_json LIKE ?""",
                (target_id, pattern)
            )
            if cursor.rowcount > 0:
                deleted_any = True

    conn.commit()
    conn.close()
    return {
        "success": True,
        "deletedAny": deleted_any,
        "purgedFiles": len(files_to_delete)
    }


def save_file_record(record: Dict[str, Any]) -> str:
    """Persists uploaded file metadata into stored_files table."""
    init_db(reconcile=False)
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.datetime.now(datetime.timezone.utc)
    now_iso = now.isoformat()
    retention_days = int(record.get("retentionDays") or record.get("retention_days") or 30)
    expires_at = (now + datetime.timedelta(days=retention_days)).isoformat()

    file_id = record["id"]
    cursor.execute("""
        INSERT OR REPLACE INTO stored_files (
            id, user_id, analysis_id, original_filename, safe_filename,
            storage_path, storage_backend, file_size, mime_type, sha256_hash,
            retention_days, created_at, expires_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        file_id,
        record["userId"] or record["user_id"],
        record.get("analysisId") or record.get("analysis_id"),
        record.get("originalFilename") or record.get("original_filename") or "Contract.sol",
        record.get("safeFilename") or record.get("safe_filename") or "Contract.sol",
        record["storagePath"] or record["storage_path"],
        record.get("storageBackend") or record.get("storage_backend") or "local",
        int(record.get("fileSize") or record.get("file_size") or 0),
        record.get("mimeType") or record.get("mime_type") or "text/x-solidity",
        record.get("sha256Hash") or record.get("sha256_hash") or "",
        retention_days,
        record.get("createdAt") or record.get("created_at") or now_iso,
        record.get("expiresAt") or record.get("expires_at") or expires_at
    ))
    conn.commit()
    conn.close()
    return file_id


def link_file_to_analysis(file_id: str, analysis_id: str, user_id: Optional[str] = None) -> bool:
    """Associates an existing file metadata record with an analysis ID."""
    init_db(reconcile=False)
    conn = get_connection()
    cursor = conn.cursor()

    if user_id:
        cursor.execute("UPDATE stored_files SET analysis_id = ? WHERE id = ? AND user_id = ?", (analysis_id, file_id, user_id))
    else:
        cursor.execute("UPDATE stored_files SET analysis_id = ? WHERE id = ?", (analysis_id, file_id))
    updated = cursor.rowcount > 0

    if user_id:
        cursor.execute("UPDATE analyses SET file_id = ? WHERE id = ? AND user_id = ?", (file_id, analysis_id, user_id))
    else:
        cursor.execute("UPDATE analyses SET file_id = ? WHERE id = ?", (file_id, analysis_id))

    conn.commit()
    conn.close()
    return updated


def get_file_record(file_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Retrieves file metadata row by file ID, optionally scoped to owner user_id."""
    init_db(reconcile=False)
    conn = get_connection()
    cursor = conn.cursor()

    if user_id:
        cursor.execute("SELECT * FROM stored_files WHERE id = ? AND user_id = ?", (file_id, user_id))
    else:
        cursor.execute("SELECT * FROM stored_files WHERE id = ?", (file_id,))

    row = cursor.fetchone()
    conn.close()
    if not row:
        return None

    return {
        "id": row["id"],
        "userId": row["user_id"],
        "user_id": row["user_id"],
        "analysisId": row["analysis_id"],
        "analysis_id": row["analysis_id"],
        "originalFilename": row["original_filename"],
        "safeFilename": row["safe_filename"],
        "storagePath": row["storage_path"],
        "storageBackend": row["storage_backend"],
        "fileSize": row["file_size"],
        "mimeType": row["mime_type"],
        "sha256Hash": row["sha256_hash"],
        "retentionDays": row["retention_days"],
        "createdAt": row["created_at"],
        "expiresAt": row["expires_at"]
    }


def get_file_record_by_analysis_id(analysis_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Retrieves file metadata associated with an analysis."""
    init_db(reconcile=False)
    conn = get_connection()
    cursor = conn.cursor()

    if user_id:
        cursor.execute("SELECT * FROM stored_files WHERE analysis_id = ? AND user_id = ?", (analysis_id, user_id))
    else:
        cursor.execute("SELECT * FROM stored_files WHERE analysis_id = ?", (analysis_id,))
    row = cursor.fetchone()

    if not row:
        # Check analyses.file_id
        if user_id:
            cursor.execute("SELECT file_id FROM analyses WHERE id = ? AND user_id = ?", (analysis_id, user_id))
        else:
            cursor.execute("SELECT file_id FROM analyses WHERE id = ?", (analysis_id,))
        a_row = cursor.fetchone()
        if a_row and "file_id" in a_row.keys() and a_row["file_id"]:
            cursor.execute("SELECT * FROM stored_files WHERE id = ?", (a_row["file_id"],))
            row = cursor.fetchone()

    conn.close()
    if not row:
        return None

    return {
        "id": row["id"],
        "userId": row["user_id"],
        "user_id": row["user_id"],
        "analysisId": row["analysis_id"],
        "originalFilename": row["original_filename"],
        "safeFilename": row["safe_filename"],
        "storagePath": row["storage_path"],
        "storageBackend": row["storage_backend"],
        "fileSize": row["file_size"],
        "mimeType": row["mime_type"],
        "sha256Hash": row["sha256_hash"],
        "retentionDays": row["retention_days"],
        "createdAt": row["created_at"],
        "expiresAt": row["expires_at"]
    }


def list_user_files(user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Lists stored files for a user ordered by creation date."""
    init_db(reconcile=False)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM stored_files WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
        (user_id, limit)
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": r["id"],
            "userId": r["user_id"],
            "analysisId": r["analysis_id"],
            "originalFilename": r["original_filename"],
            "safeFilename": r["safe_filename"],
            "storagePath": r["storage_path"],
            "fileSize": r["file_size"],
            "createdAt": r["created_at"],
            "expiresAt": r["expires_at"]
        }
        for r in rows
    ]


def delete_file_record(file_id: str, user_id: Optional[str] = None) -> bool:
    """Deletes physical file and metadata row. If physical deletion fails, retains metadata and returns False."""
    file_meta = get_file_record(file_id, user_id=user_id)
    if not file_meta:
        return False

    from .storage import get_storage
    try:
        storage = get_storage()
        if storage.file_exists(file_meta["storagePath"], file_meta["userId"]):
            success = storage.delete_file(file_meta["storagePath"], file_meta["userId"])
            if not success:
                logger.error("Physical deletion returned False for file %s. Retaining metadata for retry.", file_id)
                return False
    except Exception as e:
        logger.error("Error deleting physical file %s: %s. Retaining metadata for retry.", file_id, e)
        return False

    init_db(reconcile=False)
    conn = get_connection()
    cursor = conn.cursor()
    if user_id:
        cursor.execute("DELETE FROM stored_files WHERE id = ? AND user_id = ?", (file_id, user_id))
    else:
        cursor.execute("DELETE FROM stored_files WHERE id = ?", (file_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def cleanup_expired_records(retention_days: int = 30) -> Dict[str, int]:
    """
    Cleans up stored files and analysis records that have passed their retention period.
    Deletes physical files from storage, purges metadata and database records,
    and logs an audit log entry.
    """
    init_db(reconcile=False)
    conn = get_connection()
    cursor = conn.cursor()
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    cursor.execute("SELECT id, user_id, storage_path FROM stored_files WHERE expires_at <= ?", (now_iso,))
    expired_files = [dict(r) for r in cursor.fetchall()]

    from .storage import get_storage
    try:
        storage = get_storage()
    except Exception:
        storage = None

    deleted_files_count = 0
    for f in expired_files:
        if storage:
            try:
                storage.delete_file(f["storage_path"], f["user_id"])
            except Exception:
                pass
        cursor.execute("DELETE FROM stored_files WHERE id = ?", (f["id"],))
        deleted_files_count += 1

    cutoff = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=retention_days)).isoformat()
    cursor.execute("DELETE FROM analyses WHERE created_at <= ?", (cutoff,))
    deleted_analyses_count = cursor.rowcount

    cursor.execute("DELETE FROM jobs WHERE created_at <= ?", (cutoff,))
    deleted_jobs_count = cursor.rowcount

    if deleted_files_count > 0 or deleted_analyses_count > 0:
        cursor.execute("""
            INSERT INTO audit_logs (event_type, user_email, details, created_at)
            VALUES (?, ?, ?, ?)
        """, (
            "DATA_RETENTION_CLEANUP",
            "system",
            f"Purged {deleted_files_count} expired files, {deleted_analyses_count} analyses, and {deleted_jobs_count} jobs.",
            now_iso
        ))

    conn.commit()
    conn.close()

    return {
        "deletedFiles": deleted_files_count,
        "deletedAnalyses": deleted_analyses_count,
        "deletedJobs": deleted_jobs_count
    }


def get_user_dashboard_stats(user_id: str) -> Dict[str, Any]:
    """Computes summary statistics specifically for the authenticated user's audits."""
    init_db(reconcile=False)
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) AS total, AVG(risk_score) AS avg_score FROM analyses WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    total = row["total"] or 0
    avg_score = round(row["avg_score"] or 0, 1)

    cursor.execute("SELECT COUNT(*) AS high_count FROM analyses WHERE user_id = ? AND risk_level IN ('High', 'Critical')", (user_id,))
    high_count = cursor.fetchone()["high_count"] or 0

    cursor.execute("SELECT COUNT(*) AS low_count FROM analyses WHERE user_id = ? AND risk_level = 'Low'", (user_id,))
    low_count = cursor.fetchone()["low_count"] or 0

    conn.close()

    recent = list_analyses(user_id=user_id, limit=5)

    return {
        "totalAnalyzed": total,
        "averageRiskScore": avg_score,
        "highRiskCount": high_count,
        "lowRiskCount": low_count,
        "recentAnalyses": recent
    }


def save_job(job_dict: Dict[str, Any]) -> None:
    """Persists a new analysis job into SQLite."""
    init_db(reconcile=False)
    conn = get_connection()
    cursor = conn.cursor()
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    cursor.execute("""
        INSERT OR REPLACE INTO jobs (
            id, user_id, contract_name, status, stage, stage_message,
            progress, result_json, error_json, idempotency_key, source_hash, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        job_dict["jobId"],
        job_dict.get("userId") or job_dict.get("user_id"),
        job_dict.get("contractName", "Contract.sol"),
        job_dict.get("status", "queued"),
        job_dict.get("stage", "validating"),
        job_dict.get("stageMessage", ""),
        job_dict.get("progress", 0),
        json.dumps(job_dict.get("result")) if job_dict.get("result") else None,
        json.dumps(job_dict.get("error")) if job_dict.get("error") else None,
        job_dict.get("idempotencyKey") or job_dict.get("idempotency_key"),
        job_dict.get("sourceHash") or job_dict.get("source_hash"),
        job_dict.get("createdAt", now_iso),
        now_iso
    ))
    conn.commit()
    conn.close()


def reconcile_interrupted_jobs() -> int:
    """
    Called upon backend startup to reconcile in-flight jobs interrupted by server restart.
    Marks any jobs left in 'queued' or 'running' states as 'failed' (stage: 'interrupted')
    with honest resubmission instructions.
    """
    init_db(reconcile=False)
    conn = get_connection()
    cursor = conn.cursor()
    now_reboot_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    interrupted_err = json.dumps({
        "code": "JOB_INTERRUPTED",
        "message": "Backend service restarted while analysis was in progress. Please resubmit your contract analysis.",
        "resubmit": True
    })
    cursor.execute("""
        UPDATE jobs
        SET status = 'failed',
            stage = 'interrupted',
            stage_message = 'Backend was restarted while analysis was in progress. Please resubmit the contract.',
            error_json = ?,
            updated_at = ?
        WHERE status IN ('queued', 'running')
    """, (interrupted_err, now_reboot_iso))
    updated = cursor.rowcount
    conn.commit()
    conn.close()
    return updated


def update_job_progress(
    job_id: str,
    status: str,
    stage: str,
    stage_message: str,
    progress: int,
    result: Optional[Dict[str, Any]] = None,
    error: Optional[Dict[str, Any]] = None
) -> None:
    """Updates progress and status of an in-flight analysis job in SQLite."""
    init_db(reconcile=False)
    conn = get_connection()
    cursor = conn.cursor()
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    cursor.execute("""
        UPDATE jobs
        SET status = ?,
            stage = ?,
            stage_message = ?,
            progress = ?,
            result_json = CASE WHEN ? IS NOT NULL THEN ? ELSE result_json END,
            error_json = CASE WHEN ? IS NOT NULL THEN ? ELSE error_json END,
            updated_at = ?
        WHERE id = ?
    """, (
        status, stage, stage_message, progress,
        json.dumps(result) if result else None, json.dumps(result) if result else None,
        json.dumps(error) if error else None, json.dumps(error) if error else None,
        now_iso, job_id
    ))
    conn.commit()
    conn.close()


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves an analysis job from SQLite."""
    init_db(reconcile=False)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    keys = row.keys()
    return {
        "jobId": row["id"],
        "userId": row["user_id"],
        "user_id": row["user_id"],
        "contractName": row["contract_name"],
        "status": row["status"],
        "stage": row["stage"],
        "stageMessage": row["stage_message"],
        "progress": row["progress"],
        "result": json.loads(row["result_json"]) if row["result_json"] else None,
        "error": json.loads(row["error_json"]) if row["error_json"] else None,
        "idempotencyKey": row["idempotency_key"] if "idempotency_key" in keys else None,
        "sourceHash": row["source_hash"] if "source_hash" in keys else None,
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"]
    }


def find_active_job_by_source_hash(source_hash: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Finds an existing in-flight job for the same user and source hash to prevent duplicate execution."""
    init_db(reconcile=False)
    conn = get_connection()
    cursor = conn.cursor()
    if user_id:
        cursor.execute("""
            SELECT * FROM jobs
            WHERE user_id = ?
              AND source_hash = ?
              AND status IN ('queued', 'running')
            ORDER BY created_at DESC
            LIMIT 1
        """, (user_id, source_hash))
    else:
        cursor.execute("""
            SELECT * FROM jobs
            WHERE source_hash = ?
              AND status IN ('queued', 'running')
            ORDER BY created_at DESC
            LIMIT 1
        """, (source_hash,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    keys = row.keys()
    return {
        "jobId": row["id"],
        "userId": row["user_id"],
        "user_id": row["user_id"],
        "contractName": row["contract_name"],
        "status": row["status"],
        "stage": row["stage"],
        "stageMessage": row["stage_message"],
        "progress": row["progress"],
        "result": json.loads(row["result_json"]) if row["result_json"] else None,
        "error": json.loads(row["error_json"]) if row["error_json"] else None,
        "idempotencyKey": row["idempotency_key"] if "idempotency_key" in keys else None,
        "sourceHash": row["source_hash"] if "source_hash" in keys else None,
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"]
    }


def find_job_by_idempotency_key(idempotency_key: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Finds an existing job by idempotency key to prevent duplicate execution on client retries."""
    init_db(reconcile=False)
    conn = get_connection()
    cursor = conn.cursor()
    if user_id:
        cursor.execute("""
            SELECT * FROM jobs
            WHERE user_id = ?
              AND idempotency_key = ?
            ORDER BY created_at DESC
            LIMIT 1
        """, (user_id, idempotency_key))
    else:
        cursor.execute("""
            SELECT * FROM jobs
            WHERE idempotency_key = ?
            ORDER BY created_at DESC
            LIMIT 1
        """, (idempotency_key,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    keys = row.keys()
    return {
        "jobId": row["id"],
        "userId": row["user_id"],
        "user_id": row["user_id"],
        "contractName": row["contract_name"],
        "status": row["status"],
        "stage": row["stage"],
        "stageMessage": row["stage_message"],
        "progress": row["progress"],
        "result": json.loads(row["result_json"]) if row["result_json"] else None,
        "error": json.loads(row["error_json"]) if row["error_json"] else None,
        "idempotencyKey": row["idempotency_key"] if "idempotency_key" in keys else None,
        "sourceHash": row["source_hash"] if "source_hash" in keys else None,
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"]
    }


def cancel_job(job_id: str, user_id: Optional[str] = None) -> bool:
    """Marks a job as cancelled in the database."""
    init_db(reconcile=False)
    conn = get_connection()
    cursor = conn.cursor()
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    if user_id:
        cursor.execute("""
            UPDATE jobs
            SET status = 'cancelled',
                stage = 'cancelled',
                stage_message = 'Analysis job was cancelled by user.',
                updated_at = ?
            WHERE id = ? AND user_id = ? AND status IN ('queued', 'running')
        """, (now_iso, job_id, user_id))
    else:
        cursor.execute("""
            UPDATE jobs
            SET status = 'cancelled',
                stage = 'cancelled',
                stage_message = 'Analysis job was cancelled by user.',
                updated_at = ?
            WHERE id = ? AND status IN ('queued', 'running')
        """, (now_iso, job_id))
    cancelled = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return cancelled


def delete_job(job_id: str, user_id: Optional[str] = None) -> bool:
    """Deletes a job from the database."""
    init_db(reconcile=False)
    conn = get_connection()
    cursor = conn.cursor()
    if user_id:
        cursor.execute("DELETE FROM jobs WHERE id = ? AND user_id = ?", (job_id, user_id))
    else:
        cursor.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def get_admin_metrics() -> Dict[str, Any]:
    """Computes summary statistics for the Admin Control Panel."""
    init_db(reconcile=False)
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) AS total_users FROM users")
    total_users = cursor.fetchone()["total_users"]

    cursor.execute("SELECT COUNT(*) AS total_analyses, AVG(risk_score) AS avg_score FROM analyses")
    analysis_row = cursor.fetchone()
    total_analyses = analysis_row["total_analyses"]
    avg_score = round(analysis_row["avg_score"] or 0, 1)

    cursor.execute("SELECT risk_level, COUNT(*) AS cnt FROM analyses GROUP BY risk_level")
    risk_dist = {r["risk_level"]: r["cnt"] for r in cursor.fetchall()}

    cursor.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 15")
    logs = [dict(r) for r in cursor.fetchall()]

    conn.close()

    return {
        "totalUsers": total_users,
        "totalAnalyses": total_analyses,
        "averageRiskScore": avg_score,
        "riskDistribution": risk_dist,
        "recentLogs": logs,
        "systemHealth": {
            "database": "online",
            "storagePath": DB_PATH,
            "status": "operational"
        }
    }


def list_users() -> List[Dict[str, Any]]:
    """Returns list of users for Admin user management."""
    init_db(reconcile=False)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, full_name, organization, role, created_at FROM users ORDER BY created_at DESC")
    users = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return users


def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves user profile by ID without exposing password hash."""
    init_db(reconcile=False)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, full_name, organization, role, created_at FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Retrieves user profile by email without exposing password hash."""
    init_db(reconcile=False)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, full_name, organization, role, created_at FROM users WHERE lower(email) = lower(?)", (email.strip(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Verifies user credentials with safe migration from legacy hashes to bcrypt.
    If the account uses a legacy SHA-256 hash, verifies it and transparently
    rehashes to bcrypt on successful login.
    """
    init_db(reconcile=False)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, email, password_hash, full_name, organization, role, created_at FROM users WHERE lower(email) = lower(?)",
        (email.strip(),)
    )
    user_row = cursor.fetchone()
    conn.close()

    if not user_row:
        return None

    is_valid, needs_rehash = verify_password(password, user_row["password_hash"])
    if not is_valid:
        return None

    # Transparent migration: upgrade legacy hash to bcrypt
    if needs_rehash:
        new_bcrypt_hash = hash_password(password)
        update_user_password(user_row["id"], new_bcrypt_hash)

    user_dict = dict(user_row)
    user_dict.pop("password_hash", None)
    return user_dict


def register_user(email: str, password: str, full_name: str, organization: str = "General") -> Dict[str, Any]:
    """
    Registers a new user account with bcrypt password hashing and safe input validation.
    Protects against account enumeration by returning a non-sensitive error message.
    """
    init_db(reconcile=False)
    clean_email = email.strip().lower()
    clean_name = full_name.strip()

    # Input validation
    email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not clean_email or not re.match(email_regex, clean_email):
        raise ValueError("Please provide a valid email address.")

    if not clean_name:
        raise ValueError("Full name cannot be blank.")

    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE lower(email) = ?", (clean_email,))
    if cursor.fetchone():
        conn.close()
        # Non-sensitive error message preventing email enumeration
        raise ValueError("Registration could not be completed with the provided information. If you already have an account, please sign in.")

    user_id = f"usr-{hashlib.sha256(clean_email.encode('utf-8')).hexdigest()[:8]}"
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    p_hash = hash_password(password)

    cursor.execute("""
        INSERT INTO users (id, email, password_hash, full_name, organization, role, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, clean_email, p_hash, clean_name, organization.strip() or "General", "auditor", now_iso))

    cursor.execute("""
        INSERT INTO audit_logs (event_type, user_email, details, created_at)
        VALUES (?, ?, ?, ?)
    """, ("USER_REGISTERED", clean_email, f"User {clean_name} registered.", now_iso))

    conn.commit()
    conn.close()

    return {
        "id": user_id,
        "email": clean_email,
        "fullName": clean_name,
        "organization": organization.strip() or "General",
        "role": "auditor",
        "createdAt": now_iso
    }


def change_user_password(user_id: str, current_password: str, new_password: str) -> Tuple[bool, str]:
    """Changes password for an authenticated user with verification of current password."""
    init_db(reconcile=False)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, password_hash FROM users WHERE id = ?", (user_id,))
    user_row = cursor.fetchone()
    conn.close()

    if not user_row:
        return False, "User account not found."

    is_valid, _ = verify_password(current_password, user_row["password_hash"])
    if not is_valid:
        return False, "Current password is incorrect."

    if len(new_password) < 8:
        return False, "New password must be at least 8 characters long."

    new_hash = hash_password(new_password)
    update_user_password(user_id, new_hash)
    return True, "Password updated successfully."
