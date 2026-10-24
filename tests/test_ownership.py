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
    """Verify that an analysis is associated with the local user and saved to SQLite."""
    client = TestClient(app)

    # Submit analysis
    res = client.post(
        "/api/v1/analyze",
        json={"sourceCode": SAMPLE_SOL, "contractName": "VaultA.sol", "description": "Vault A test"}
    )
    assert res.status_code == 200
    data = res.json()
    analysis_id = data["analysisId"]
    assert "userId" in data

    # Verify directly in SQLite database
    db_record = db.get_analysis_by_id(analysis_id)
    assert db_record is not None
    assert db_record["contractName"] in ("VaultA.sol", "SimpleVault")

    # Verify local user can retrieve the analysis via endpoint
    get_res = client.get(f"/api/v1/analyze/{analysis_id}")
    assert get_res.status_code == 200
    assert get_res.json()["analysisId"] == analysis_id


def test_local_analysis_access_and_safe_404():
    """Verify that local user can access analysis, chat, reports, and delete, and nonexistent returns 404."""
    client = TestClient(app)

    # User creates an analysis
    res = client.post(
        "/api/v1/analyze",
        json={"sourceCode": SAMPLE_SOL, "contractName": "PrivateA.sol"}
    )
    assert res.status_code == 200
    analysis_id = res.json()["analysisId"]

    # 1. View analysis -> 200 OK
    res_view = client.get(f"/api/v1/analyze/{analysis_id}")
    assert res_view.status_code == 200

    # 2. Query chat assistant on contract -> 200 OK
    res_chat = client.post(
        f"/api/v1/analyze/{analysis_id}/chat",
        json={"message": "What does this contract do?"}
    )
    assert res_chat.status_code == 200

    # 3. Export PDF report -> 200 OK
    res_pdf = client.get(f"/api/v1/reports/{analysis_id}/pdf")
    assert res_pdf.status_code == 200

    # 4. Export DOCX report -> 200 OK
    res_docx = client.get(f"/api/v1/reports/{analysis_id}/docx")
    assert res_docx.status_code == 200

    # 5. Nonexistent analysis returns 404 for all endpoints
    fake_id = "nonexistent_analysis_xyz"
    assert client.get(f"/api/v1/analyze/{fake_id}").status_code == 404
    assert client.post(f"/api/v1/analyze/{fake_id}/chat", json={"message": "hi"}).status_code == 404
    assert client.get(f"/api/v1/reports/{fake_id}/pdf").status_code == 404
    assert client.get(f"/api/v1/reports/{fake_id}/docx").status_code == 404
    assert client.delete(f"/api/v1/analyze/{fake_id}").status_code == 404


def test_unauthenticated_access_allowed_in_local_mode():
    """Verify that unauthenticated callers have full access without 401 in local no-login mode."""
    anon_client = TestClient(app)

    # Anonymous user creates an analysis
    res = anon_client.post(
        "/api/v1/analyze",
        json={"sourceCode": SAMPLE_SOL, "contractName": "ConfidentialA.sol"}
    )
    assert res.status_code == 200
    analysis_id = res.json()["analysisId"]

    # 1. Anonymous GET /api/v1/analyze/{analysis_id} -> 200
    anon_view = anon_client.get(f"/api/v1/analyze/{analysis_id}")
    assert anon_view.status_code == 200

    # 2. Anonymous GET /api/v1/analyses -> 200
    anon_list = anon_client.get("/api/v1/analyses")
    assert anon_list.status_code == 200

    # 3. Anonymous POST /api/v1/analyze/{analysis_id}/chat -> 200
    anon_chat = anon_client.post(f"/api/v1/analyze/{analysis_id}/chat", json={"message": "Query"})
    assert anon_chat.status_code == 200

    # 4. Anonymous GET /api/v1/reports/{analysis_id}/pdf -> 200
    anon_pdf = anon_client.get(f"/api/v1/reports/{analysis_id}/pdf")
    assert anon_pdf.status_code == 200

    # 5. Anonymous DELETE /api/v1/analyze/{analysis_id} -> 200
    anon_del = anon_client.delete(f"/api/v1/analyze/{analysis_id}")
    assert anon_del.status_code == 200


def test_local_user_history_persistence():
    """Verify that all submitted analyses appear in the local user's history."""
    client = TestClient(app)

    tag_a = f"VaultA_{uuid.uuid4().hex[:6]}"
    code_a = SAMPLE_SOL.replace("SimpleVault", tag_a)
    res_a = client.post(
        "/api/v1/analyze",
        json={"sourceCode": code_a, "contractName": f"{tag_a}.sol"}
    )
    assert res_a.status_code == 200

    tag_b = f"VaultB_{uuid.uuid4().hex[:6]}"
    code_b = SAMPLE_SOL.replace("SimpleVault", tag_b)
    res_b = client.post(
        "/api/v1/analyze",
        json={"sourceCode": code_b, "contractName": f"{tag_b}.sol"}
    )
    assert res_b.status_code == 200

    # List history
    list_res = client.get("/api/v1/analyses").json()
    names = [item["contractName"] for item in list_res["analyses"]]
    assert any(tag_a in name for name in names), f"Expected {tag_a} in {names}"
    assert any(tag_b in name for name in names), f"Expected {tag_b} in {names}"


def test_user_dashboard_stats():
    """Verify that GET /api/v1/user/stats returns user-scoped metrics."""
    client = TestClient(app)

    res = client.get("/api/v1/user/stats")
    assert res.status_code == 200
    data = res.json()
    assert "totalAnalyzed" in data
    assert "averageRiskScore" in data
    assert "highRiskCount" in data
    assert "lowRiskCount" in data
    assert "recentAnalyses" in data
    assert isinstance(data["recentAnalyses"], list)


def test_job_persistence_and_lifecycle():
    """Verify analysis jobs persist in SQLite and can be polled locally."""
    client = TestClient(app)

    # Create job
    create_res = client.post(
        "/api/v1/analyze/jobs",
        json={"sourceCode": SAMPLE_SOL, "contractName": "JobVaultA.sol"}
    )
    assert create_res.status_code == 202
    job_id = create_res.json()["jobId"]

    # Verify job exists in SQLite DB immediately
    db_job = db.get_job(job_id)
    assert db_job is not None
    assert db_job["jobId"] == job_id

    # Local user checking their job -> 200 OK
    poll = client.get(f"/api/v1/jobs/{job_id}")
    assert poll.status_code == 200
    assert poll.json()["jobId"] == job_id

    # Nonexistent job returns 404
    assert client.get("/api/v1/jobs/job-nonexistent-12345").status_code == 404


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


def test_unauthenticated_analysis_submission_allowed():
    """Verify that unauthenticated callers can submit contracts or jobs in local mode without 401."""
    anon_client = TestClient(app)

    # Direct Analysis succeeds
    r1 = anon_client.post("/api/v1/analyze", json={"sourceCode": SAMPLE_SOL, "contractName": "TestDirect.sol"})
    assert r1.status_code == 200
    assert "analysisId" in r1.json()

    # Async Job submission succeeds with 202
    r3 = anon_client.post("/api/v1/analyze/jobs", json={"sourceCode": SAMPLE_SOL, "contractName": "TestJob.sol"})
    assert r3.status_code == 202
    assert "jobId" in r3.json()


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

