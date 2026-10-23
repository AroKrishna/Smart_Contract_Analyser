"""
tests/test_ownership.py - Verification for Part 3: Persistent saved analyses & user ownership

Tests:
1. Analysis persistence and user association:
   - Authenticated POST /api/v1/analyze associates analysis with user_id and persists to SQLite.
   - Analysis can be retrieved by the owner.
2. Cross-user access denial (403 Forbidden):
   - User B attempting to view User A's private analysis receives 403.
   - User B attempting to chat with User A's private contract assistant receives 403.
   - User B attempting to download User A's private report (PDF/DOCX) receives 403.
   - User B attempting to delete User A's private analysis receives 403.
3. Unauthenticated access denial (401 Unauthorized):
   - Anonymous caller accessing private analysis receives 401.
   - Anonymous caller listing analysis history receives 401.
   - Anonymous caller accessing private chat or reports receives 401.
4. User history isolation:
   - User A sees only User A's analyses in GET /api/v1/analyses.
   - User B sees only User B's analyses in GET /api/v1/analyses.
5. Personal dashboard metrics:
   - GET /api/v1/user/stats returns user-scoped metrics and recent analyses.
6. Job persistence and server reboot reconciliation:
   - Analysis jobs are persisted into SQLite 'jobs' table.
   - Background progress updates write to SQLite.
   - Re-running init_db() reconciles in-flight (queued/running) jobs as interrupted without data loss.
   - Cross-user polling of another user's job returns 403 Forbidden.
7. Safe database migration:
   - Calling init_db() is idempotent and safely adds user_id column without corrupting or deleting existing records.
"""

import pytest
import sqlite3
import json
import uuid
import datetime
from fastapi.testclient import TestClient
from backend.main import app
import backend.analysis.db as db

SAMPLE_SOL = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract SimpleVault {
    address public owner;
    mapping(address => uint256) public balances;

    constructor() {
        owner = msg.sender;
    }

    function deposit() external payable {
        balances[msg.sender] += msg.value;
    }
}
"""


def get_user_client(email: str, password: str) -> TestClient:
    """Helper to create an authenticated TestClient with isolated session cookies."""
    c = TestClient(app)
    res = c.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    token = res.json()["token"]
    c.headers["Authorization"] = f"Bearer {token}"
    return c


@pytest.fixture(autouse=True)
def setup_test_users():
    """Ensure two distinct users exist in the database for ownership testing."""
    db.init_db()

    # User A: default auditor
    # usr-auditor-02: auditor@enterprise.com / AuditorPass2026!

    # User B: create a distinct auditor
    user_b_email = "auditor_b@auditfirm.com"
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE email = ?", (user_b_email,))
    row = cur.fetchone()
    if not row:
        db.register_user(
            email=user_b_email,
            password="AuditorBPass2026!",
            full_name="Bob Auditor",
            organization="Independent Security LLC"
        )
    conn.close()


def test_authenticated_analysis_persistence_and_association():
    """Verify that an authenticated analysis is associated with the user_id and saved to SQLite."""
    client_a = get_user_client("auditor@enterprise.com", "AuditorPass2026!")

    # Submit analysis with User A auth
    res = client_a.post(
        "/api/v1/analyze",
        json={"sourceCode": SAMPLE_SOL, "contractName": "VaultA.sol", "description": "Vault A test"}
    )
    assert res.status_code == 200
    data = res.json()
    analysis_id = data["analysisId"]
    assert data["userId"] == "usr-auditor-02"

    # Verify directly in SQLite database
    db_record = db.get_analysis_by_id(analysis_id)
    assert db_record is not None
    assert db_record["userId"] == "usr-auditor-02"
    assert db_record["contractName"] in ("VaultA.sol", "SimpleVault")

    # Verify owner can retrieve the analysis via endpoint
    get_res = client_a.get(f"/api/v1/analyze/{analysis_id}")
    assert get_res.status_code == 200
    assert get_res.json()["analysisId"] == analysis_id


def test_cross_user_access_denial():
    """Verify that User B is denied access (403 Forbidden) to User A's private analysis."""
    client_a = get_user_client("auditor@enterprise.com", "AuditorPass2026!")
    client_b = get_user_client("auditor_b@auditfirm.com", "AuditorBPass2026!")

    # User A creates a private analysis
    res_a = client_a.post(
        "/api/v1/analyze",
        json={"sourceCode": SAMPLE_SOL, "contractName": "PrivateA.sol"}
    )
    assert res_a.status_code == 200
    analysis_id = res_a.json()["analysisId"]

    # 1. User B tries to view User A's analysis -> 403 Forbidden
    res_b_view = client_b.get(f"/api/v1/analyze/{analysis_id}")
    assert res_b_view.status_code == 403
    assert res_b_view.json()["detail"]["code"] == "ACCESS_DENIED"

    # 2. User B tries to query chat assistant on User A's contract -> 403 Forbidden
    res_b_chat = client_b.post(
        f"/api/v1/analyze/{analysis_id}/chat",
        json={"message": "What does this contract do?"}
    )
    assert res_b_chat.status_code == 403
    assert res_b_chat.json()["detail"]["code"] == "ACCESS_DENIED"

    # 3. User B tries to export User A's PDF report -> 403 Forbidden
    res_b_pdf = client_b.get(f"/api/v1/reports/{analysis_id}/pdf")
    assert res_b_pdf.status_code == 403
    assert res_b_pdf.json()["detail"]["code"] == "ACCESS_DENIED"

    # 4. User B tries to export User A's DOCX report -> 403 Forbidden
    res_b_docx = client_b.get(f"/api/v1/reports/{analysis_id}/docx")
    assert res_b_docx.status_code == 403
    assert res_b_docx.json()["detail"]["code"] == "ACCESS_DENIED"

    # 5. User B tries to delete User A's analysis -> 403 Forbidden
    res_b_del = client_b.delete(f"/api/v1/analyze/{analysis_id}")
    assert res_b_del.status_code == 403
    assert res_b_del.json()["detail"]["code"] == "ACCESS_DENIED"

    # Verify User A can still access their analysis
    res_a_view = client_a.get(f"/api/v1/analyze/{analysis_id}")
    assert res_a_view.status_code == 200


def test_unauthenticated_access_denial_to_private_analysis():
    """Verify that unauthenticated callers are denied access (401 Unauthorized) to private analyses."""
    client_a = get_user_client("auditor@enterprise.com", "AuditorPass2026!")
    anon_client = TestClient(app)

    # User A creates a private analysis
    res_a = client_a.post(
        "/api/v1/analyze",
        json={"sourceCode": SAMPLE_SOL, "contractName": "ConfidentialA.sol"}
    )
    assert res_a.status_code == 200
    analysis_id = res_a.json()["analysisId"]

    # 1. Anonymous GET /api/v1/analyze/{analysis_id} -> 401
    anon_view = anon_client.get(f"/api/v1/analyze/{analysis_id}")
    assert anon_view.status_code == 401
    assert anon_view.json()["detail"]["code"] == "UNAUTHORIZED"

    # 2. Anonymous GET /api/v1/analyses -> 401
    anon_list = anon_client.get("/api/v1/analyses")
    assert anon_list.status_code == 401
    assert anon_list.json()["detail"]["code"] == "UNAUTHORIZED"

    # 3. Anonymous POST /api/v1/analyze/{analysis_id}/chat -> 401
    anon_chat = anon_client.post(f"/api/v1/analyze/{analysis_id}/chat", json={"message": "Query"})
    assert anon_chat.status_code == 401

    # 4. Anonymous GET /api/v1/reports/{analysis_id}/pdf -> 401
    anon_pdf = anon_client.get(f"/api/v1/reports/{analysis_id}/pdf")
    assert anon_pdf.status_code == 401

    # 5. Anonymous DELETE /api/v1/analyze/{analysis_id} -> 401
    anon_del = anon_client.delete(f"/api/v1/analyze/{analysis_id}")
    assert anon_del.status_code == 401


def test_user_history_isolation():
    """Verify that User A and User B see only their own respective analyses in history."""
    client_a = get_user_client("auditor@enterprise.com", "AuditorPass2026!")
    client_b = get_user_client("auditor_b@auditfirm.com", "AuditorBPass2026!")

    tag_a = f"VaultA_{uuid.uuid4().hex[:6]}"
    code_a = SAMPLE_SOL.replace("SimpleVault", tag_a)
    res_a = client_a.post(
        "/api/v1/analyze",
        json={"sourceCode": code_a, "contractName": f"{tag_a}.sol"}
    )
    assert res_a.status_code == 200

    tag_b = f"VaultB_{uuid.uuid4().hex[:6]}"
    code_b = SAMPLE_SOL.replace("SimpleVault", tag_b)
    res_b = client_b.post(
        "/api/v1/analyze",
        json={"sourceCode": code_b, "contractName": f"{tag_b}.sol"}
    )
    assert res_b.status_code == 200

    # User A list history
    list_a = client_a.get("/api/v1/analyses").json()
    names_a = [item["contractName"] for item in list_a["analyses"]]
    assert any(tag_a in name for name in names_a), f"Expected {tag_a} in {names_a}"
    assert not any(tag_b in name for name in names_a), f"User A saw User B's contract {tag_b}!"

    # User B list history
    list_b = client_b.get("/api/v1/analyses").json()
    names_b = [item["contractName"] for item in list_b["analyses"]]
    assert any(tag_b in name for name in names_b), f"Expected {tag_b} in {names_b}"
    assert not any(tag_a in name for name in names_b), f"User B saw User A's contract {tag_a}!"


def test_user_dashboard_stats():
    """Verify that GET /api/v1/user/stats returns user-scoped metrics."""
    client_b = get_user_client("auditor_b@auditfirm.com", "AuditorBPass2026!")

    res = client_b.get("/api/v1/user/stats")
    assert res.status_code == 200
    data = res.json()
    assert "totalAnalyzed" in data
    assert "averageRiskScore" in data
    assert "highRiskCount" in data
    assert "lowRiskCount" in data
    assert "recentAnalyses" in data
    assert isinstance(data["recentAnalyses"], list)


def test_job_persistence_and_cross_user_denial():
    """Verify analysis jobs persist in SQLite and enforce ownership."""
    client_a = get_user_client("auditor@enterprise.com", "AuditorPass2026!")
    client_b = get_user_client("auditor_b@auditfirm.com", "AuditorBPass2026!")
    anon_client = TestClient(app)

    # Create job under User A
    create_res = client_a.post(
        "/api/v1/analyze/jobs",
        json={"sourceCode": SAMPLE_SOL, "contractName": "JobVaultA.sol"}
    )
    assert create_res.status_code == 202
    job_id = create_res.json()["jobId"]
    assert create_res.json()["userId"] == "usr-auditor-02"

    # Verify job exists in SQLite DB immediately
    db_job = db.get_job(job_id)
    assert db_job is not None
    assert db_job["jobId"] == job_id
    assert db_job["userId"] == "usr-auditor-02"

    # User B trying to check User A's job -> 403 Forbidden
    poll_b = client_b.get(f"/api/v1/jobs/{job_id}")
    assert poll_b.status_code == 403
    assert poll_b.json()["detail"]["code"] == "ACCESS_DENIED"

    # Unauthenticated caller checking User A's job -> 401 Unauthorized
    poll_anon = anon_client.get(f"/api/v1/jobs/{job_id}")
    assert poll_anon.status_code == 401
    assert poll_anon.json()["detail"]["code"] in ("UNAUTHORIZED", "AUTHENTICATION_REQUIRED")

    # User A checking their job -> 200 OK
    poll_a = client_a.get(f"/api/v1/jobs/{job_id}")
    assert poll_a.status_code == 200
    assert poll_a.json()["jobId"] == job_id


def test_job_reboot_reconciliation():
    """Verify that backend restart marks in-flight jobs as interrupted gracefully."""
    # Simulate a job left in 'running' state in SQLite
    fake_job_id = f"job-reboot-{uuid.uuid4().hex[:6]}"
    db.save_job({
        "jobId": fake_job_id,
        "userId": "usr-auditor-02",
        "contractName": "RebootContract.sol",
        "status": "running",
        "stage": "inferring",
        "stageMessage": "Executing inference...",
        "progress": 50,
        "createdAt": datetime.datetime.now(datetime.timezone.utc).isoformat()
    })

    # Trigger restart simulation via init_db()
    db.init_db()

    # Verify the job was safely transitioned to interrupted/failed
    reconciled_job = db.get_job(fake_job_id)
    assert reconciled_job is not None
    assert reconciled_job["status"] == "failed"
    assert reconciled_job["stage"] == "interrupted"
    assert "restarted" in reconciled_job["stageMessage"].lower()


def test_safe_schema_migration_idempotence():
    """Verify database schema migration runs idempotently without losing existing data."""
    # Insert a sample analysis
    sample_id = f"migr-{uuid.uuid4().hex[:6]}"
    db.insert_analysis({
        "analysisId": sample_id,
        "contractName": "MigrationTest.sol",
        "contractType": "Solidity Smart Contract",
        "solidityCode": SAMPLE_SOL,
        "status": "completed",
        "riskScore": 40,
        "riskLevel": "Low",
        "riskBreakdown": {},
        "categories": [],
        "findings": [],
        "shapValues": [],
        "limeExplanations": [],
        "recommendations": [],
        "complianceMatrix": [],
        "summary": "Migration test summary"
    }, user_id="usr-auditor-02")

    # Run init_db multiple times
    db.init_db()
    db.init_db()

    # Verify record still intact
    record = db.get_analysis_by_id(sample_id)
    assert record is not None
    assert record["analysisId"] == sample_id
    assert record["userId"] == "usr-auditor-02"
    assert record["contractName"] == "MigrationTest.sol"


def test_unauthenticated_analysis_submission_rejected():
    """Verify that unauthenticated callers cannot submit contracts or jobs and receive 401."""
    anon_client = TestClient(app)

    # Direct Analysis
    r1 = anon_client.post("/api/v1/analyze", json={"sourceCode": SAMPLE_SOL, "contractName": "Test.sol"})
    assert r1.status_code == 401
    assert r1.json()["detail"]["code"] == "AUTHENTICATION_REQUIRED"

    # File Upload
    r2 = anon_client.post("/api/v1/analyze/upload", files={"file": ("Test.sol", SAMPLE_SOL.encode("utf-8"), "text/plain")})
    assert r2.status_code == 401
    assert r2.json()["detail"]["code"] == "AUTHENTICATION_REQUIRED"

    # Async Job
    r3 = anon_client.post("/api/v1/analyze/jobs", json={"sourceCode": SAMPLE_SOL, "contractName": "Test.sol"})
    assert r3.status_code == 401
    assert r3.json()["detail"]["code"] == "AUTHENTICATION_REQUIRED"


def test_complete_deletion_across_all_storage_and_endpoints():
    """
    Verify DELETE /api/v1/analyze/{analysis_id} purges all data across:
    - analyses table in SQLite
    - related jobs rows in SQLite
    - in-memory caches (analyses_store, jobs_store)
    - GET /api/v1/analyze/{id} -> 404
    - GET /api/v1/jobs/{job_id} -> 404
    - GET /api/v1/reports/{id}/pdf -> 404
    - GET /api/v1/reports/{id}/docx -> 404
    - POST /api/v1/analyze/{id}/chat -> 404
    """
    import time
    client_a = get_user_client("auditor@enterprise.com", "AuditorPass2026!")

    # 1. Create analysis directly so completed result exists
    direct_res = client_a.post("/api/v1/analyze", json={"sourceCode": SAMPLE_SOL, "contractName": "PurgeTarget.sol"})
    assert direct_res.status_code == 200
    analysis_data = direct_res.json()
    analysis_id = analysis_data["analysisId"]

    # 2. Register associated completed job in both jobs_store and SQLite jobs table
    from backend.main import jobs_store, analyses_store
    job_id = f"job-{uuid.uuid4().hex[:8]}"
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    job_record = {
        "jobId": job_id,
        "userId": "usr-auditor-02",
        "contractName": "PurgeTarget.sol",
        "status": "completed",
        "stage": "completed",
        "stageMessage": "Legal-BERT analysis complete.",
        "progress": 100,
        "result": analysis_data,
        "error": None,
        "createdAt": now_iso,
        "_created_timestamp": time.time()
    }
    jobs_store[job_id] = job_record
    db.save_job(job_record)

    # 3. Verify all records exist across storage locations before deletion
    assert analysis_id in analyses_store
    assert job_id in jobs_store
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS c FROM analyses WHERE id = ?", (analysis_id,))
    assert cur.fetchone()["c"] >= 1
    cur.execute("SELECT COUNT(*) AS c FROM jobs WHERE id = ?", (job_id,))
    assert cur.fetchone()["c"] >= 1
    conn.close()

    # Verify query and export endpoints work before deletion
    assert client_a.get(f"/api/v1/analyze/{analysis_id}").status_code == 200
    assert client_a.get(f"/api/v1/jobs/{job_id}").status_code == 200
    assert client_a.get(f"/api/v1/reports/{analysis_id}/pdf").status_code == 200
    assert client_a.get(f"/api/v1/reports/{analysis_id}/docx").status_code == 200
    chat_before = client_a.post(f"/api/v1/analyze/{analysis_id}/chat", json={"message": "Is there a killswitch?"})
    assert chat_before.status_code == 200

    # 4. Perform Complete Deletion
    del_res = client_a.delete(f"/api/v1/analyze/{analysis_id}")
    assert del_res.status_code == 200
    del_data = del_res.json()
    assert del_data["status"] == "discarded"
    assert del_data["purgedFromDatabase"] is True

    # 5. Verify SQLite tables are completely purged
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS c FROM analyses WHERE id = ?", (analysis_id,))
    assert cur.fetchone()["c"] == 0
    cur.execute("SELECT COUNT(*) AS c FROM jobs WHERE id = ? OR result_json LIKE ?", (job_id, f'%"{analysis_id}"%'))
    assert cur.fetchone()["c"] == 0
    conn.close()

    # 6. Verify in-memory stores are completely purged
    assert analysis_id not in analyses_store
    assert job_id not in jobs_store

    # 7. Verify all retrieval endpoints return 404 NOT FOUND
    assert client_a.get(f"/api/v1/analyze/{analysis_id}").status_code == 404
    assert client_a.get(f"/api/v1/jobs/{job_id}").status_code == 404
    assert client_a.get(f"/api/v1/reports/{analysis_id}/pdf").status_code == 404
    assert client_a.get(f"/api/v1/reports/{analysis_id}/docx").status_code == 404
    assert client_a.post(f"/api/v1/analyze/{analysis_id}/chat", json={"message": "Any findings?"}).status_code == 404

    # 8. Verify subsequent delete also returns 404
    assert client_a.delete(f"/api/v1/analyze/{analysis_id}").status_code == 404


def test_in_flight_job_cancellation_and_safe_deletion():
    """Verify that deleting a running/queued job cancels background execution and leaves zero traces in storage."""
    client_a = get_user_client("auditor@enterprise.com", "AuditorPass2026!")

    # Submit job
    job_res = client_a.post(
        "/api/v1/analyze/jobs",
        json={"sourceCode": SAMPLE_SOL, "contractName": "CancelTarget.sol"}
    )
    assert job_res.status_code == 202
    job_id = job_res.json()["jobId"]

    # Immediately delete the job while it is queued/running
    del_res = client_a.delete(f"/api/v1/analyze/{job_id}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "discarded"

    # Verify job status endpoint returns 404
    assert client_a.get(f"/api/v1/jobs/{job_id}").status_code == 404

    # Give thread a moment to recognize cancellation and exit
    import time
    time.sleep(1.0)

    # Verify no records remain or were resurrected in SQLite
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS c FROM jobs WHERE id = ?", (job_id,))
    assert cur.fetchone()["c"] == 0
    cur.execute("SELECT COUNT(*) AS c FROM analyses WHERE contract_name = 'CancelTarget.sol'")
    assert cur.fetchone()["c"] == 0
    conn.close()

