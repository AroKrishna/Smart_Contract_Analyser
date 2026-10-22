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
from typing import Dict, Any, List, Optional

import tempfile
import shutil

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
    """Hash password using SHA-256 with salt."""
    salt = "sca_saas_platform_salt_2026"
    return hashlib.sha256((password + salt).encode("utf-8")).hexdigest()


def get_connection():
    """Returns a connection to the SQLite database with row factory."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
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

    # 3. System & Audit Logs table
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

    # Check if default admin exists
    cursor.execute("SELECT id FROM users WHERE email = 'admin@legal-ai.io'")
    if not cursor.fetchone():
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
    cursor.execute("SELECT id FROM users WHERE email = 'auditor@enterprise.com'")
    if not cursor.fetchone():
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


def insert_analysis(record: Dict[str, Any]) -> str:
    """Persists a new contract analysis into the database."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    analysis_id = record.get("analysisId") or record.get("id")
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    cursor.execute("""
        INSERT OR REPLACE INTO analyses (
            id, contract_name, contract_type, solidity_code, solidity_version,
            status, risk_score, risk_level, risk_breakdown, categories,
            findings, shap_values, lime_explanations, recommendations,
            compliance_matrix, summary, model_engine, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        analysis_id,
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
        "system",
        f"Analysis {analysis_id} for contract {record.get('contractName', 'Contract')} saved.",
        now_iso
    ))

    conn.commit()
    conn.close()
    return analysis_id


def get_analysis_by_id(analysis_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves an analysis by its ID and decodes JSON fields."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM analyses WHERE id = ?", (analysis_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "analysisId": row["id"],
        "id": row["id"],
        "contractName": row["contract_name"],
        "name": row["contract_name"],
        "contractType": row["contract_type"],
        "solidityCode": row["solidity_code"],
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


def list_analyses(query: str = "", risk_level: str = "All", limit: int = 50) -> List[Dict[str, Any]]:
    """Lists saved analyses with optional keyword and risk-level filters."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    sql = "SELECT * FROM analyses WHERE 1=1"
    params = []

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
            "contractName": row["contract_name"],
            "name": row["contract_name"],
            "contractType": row["contract_type"],
            "status": row["status"],
            "riskScore": row["risk_score"],
            "riskLevel": row["risk_level"],
            "overallRiskScore": row["risk_score"],
            "overallRiskLevel": row["risk_level"],
            "summary": row["summary"],
            "auditDate": row["created_at"],
            "created_at": row["created_at"]
        })
    return results


def get_admin_metrics() -> Dict[str, Any]:
    """Computes summary statistics for the Admin Control Panel."""
    init_db()
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
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, full_name, organization, role, created_at FROM users ORDER BY created_at DESC")
    users = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return users


def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    """Verifies user credentials."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    p_hash = hash_password(password)
    cursor.execute("SELECT id, email, full_name, organization, role, created_at FROM users WHERE email = ? AND password_hash = ?", (email, p_hash))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None


def register_user(email: str, password: str, full_name: str, organization: str = "General") -> Dict[str, Any]:
    """Registers a new user account."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    if cursor.fetchone():
        conn.close()
        raise ValueError(f"Account with email '{email}' already exists.")

    user_id = f"usr-{hashlib.sha256(email.encode('utf-8')).hexdigest()[:8]}"
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    p_hash = hash_password(password)

    cursor.execute("""
        INSERT INTO users (id, email, password_hash, full_name, organization, role, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, email, p_hash, full_name, organization, "auditor", now_iso))

    cursor.execute("""
        INSERT INTO audit_logs (event_type, user_email, details, created_at)
        VALUES (?, ?, ?, ?)
    """, ("USER_REGISTERED", email, f"User {full_name} registered.", now_iso))

    conn.commit()
    conn.close()

    return {
        "id": user_id,
        "email": email,
        "fullName": full_name,
        "organization": organization,
        "role": "auditor",
        "createdAt": now_iso
    }
