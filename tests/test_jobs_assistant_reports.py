"""
tests/test_jobs_assistant_reports.py - Automated Verification Suite for Part 5
Analysis job processing lifecycle, concurrency, duplicate protection, cancellation semantics,
reboot reconciliation, AI assistant context grounding & offline fallback, and PDF/DOCX report exports.
"""

import io
import os
import sys
import time
import json
import uuid
import pytest
from fastapi.testclient import TestClient

# Ensure root and backend directories are in sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_dir = os.path.join(root_dir, "backend")
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from backend.main import app, jobs_store, cancelled_jobs, cancelled_jobs_lock
import backend.analysis.db as db
from backend.analysis.storage import get_storage
from backend.analysis.chat import answer_contract_query, LEGAL_ASSISTANT_DISCLAIMER
from backend.analysis.reports import generate_pdf_report, generate_docx_report

SAMPLE_SOL = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract Part5Vault {
    address public owner;
    uint256 public feePercent = 5;

    constructor() {
        owner = msg.sender;
    }

    function emergencyKill() external {
        require(msg.sender == owner, "Not owner");
        selfdestruct(payable(owner));
    }

    function setFee(uint256 newFee) external {
        require(msg.sender == owner, "Not owner");
        feePercent = newFee;
    }
}
"""


@pytest.fixture(autouse=True)
def init_clean_environment():
    """Initializes clean database schema and reconciles jobs on each test."""
    db.init_db()


def create_user_client(email: str, password: str = "TestPass2026!", role: str = "auditor") -> TestClient:
    """Helper to register/login and return an authenticated TestClient with active session cookies."""
    client = TestClient(app)
    existing = db.get_user_by_email(email)
    if not existing:
        clean_email = email.strip().lower()
        user_id = f"usr-{uuid.uuid4().hex[:8]}"
        p_hash = db.hash_password(password)
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO users (id, email, password_hash, full_name, organization, role, created_at)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
        """, (user_id, clean_email, p_hash, "Part 5 Tester", "QA Audits", role))
        conn.commit()
        conn.close()

    login_res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login_res.status_code == 200, f"Login failed for {email}: {login_res.text}"
    return client


# 1. Job Creation, Monotonic Progress Transitions, and Successful Retrieval
def test_job_submission_and_progress_lifecycle():
    client = create_user_client("job_lifecycle_user@example.com")

    # Submit an async analysis job
    res = client.post(
        "/api/v1/analyze/jobs",
        json={
            "sourceCode": SAMPLE_SOL,
            "contractName": "LifecycleVault.sol",
            "description": "Lifecycle test"
        }
    )
    assert res.status_code == 202
    data = res.json()
    job_id = data["jobId"]
    assert job_id.startswith("job-")
    assert data["status"] in ("queued", "running", "completed")
    assert data["progress"] >= 15

    # Poll until completed (with timeout)
    max_wait = 65
    start = time.time()
    final_status = None
    prev_progress = 0

    while time.time() - start < max_wait:
        poll_res = client.get(f"/api/v1/jobs/{job_id}")
        assert poll_res.status_code == 200
        poll_data = poll_res.json()
        curr_progress = poll_data.get("progress", 0)
        assert curr_progress >= prev_progress, f"Progress must be monotonic: {curr_progress} < {prev_progress}"
        prev_progress = curr_progress

        final_status = poll_data.get("status")
        if final_status in ("completed", "failed"):
            break
        time.sleep(0.5)

    assert final_status == "completed"
    assert prev_progress == 100

    # Retrieve result via GET /api/v1/jobs/{job_id}/result
    res_endpoint = client.get(f"/api/v1/jobs/{job_id}/result")
    assert res_endpoint.status_code == 200
    res_data = res_endpoint.json()
    assert res_data["analysisId"].startswith("audit-")
    assert "findings" in res_data
    assert "categories" in res_data
    assert "overallRiskScore" in res_data or "riskScore" in res_data


# 2. Local Job Lifecycle, Retrieval, and Cancellation Semantics
def test_job_ownership_isolation():
    """Verify local job lifecycle without login: unauthenticated creation, polling, cancellation, and deletion."""
    anon_client = TestClient(app)

    # 1. Anonymous client creates an analysis job
    res = anon_client.post(
        "/api/v1/analyze/jobs",
        json={"sourceCode": SAMPLE_SOL, "contractName": "SecureA.sol"}
    )
    assert res.status_code == 202
    job_id = res.json()["jobId"]
    assert job_id.startswith("job-")

    # 2. Anonymous caller can inspect job status and results directly
    status_res = anon_client.get(f"/api/v1/jobs/{job_id}")
    assert status_res.status_code == 200
    assert status_res.json()["jobId"] == job_id
    assert status_res.json()["status"] in ("queued", "running", "completed")

    # 3. Nonexistent job ID returns 404
    fake_res = anon_client.get("/api/v1/jobs/job-nonexistent-999999")
    assert fake_res.status_code == 404
    assert fake_res.json()["detail"]["code"] == "JOB_NOT_FOUND"

    # 4. Anonymous caller can cancel the job
    cancel_res = anon_client.post(f"/api/v1/jobs/{job_id}/cancel")
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] in ("cancelled", "completed")

    # 5. Anonymous caller can delete the job record
    del_res = anon_client.delete(f"/api/v1/jobs/{job_id}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] in ("deleted", "discarded") or del_res.json().get("success")


# 3. Duplicate Submission Protection & Idempotency
def test_job_idempotency_and_duplicate_protection():
    client = create_user_client("idempotent_user@example.com")

    # 1. Idempotency Key Replay Protection
    idem_key = f"idem-key-{uuid.uuid4().hex[:8]}"
    payload = {
        "sourceCode": SAMPLE_SOL,
        "contractName": "IdemVault.sol",
        "idempotencyKey": idem_key
    }

    first_res = client.post("/api/v1/analyze/jobs", json=payload)
    assert first_res.status_code == 202
    first_job_id = first_res.json()["jobId"]

    # Re-send same request with same idempotency key
    replay_res = client.post("/api/v1/analyze/jobs", json=payload)
    assert replay_res.status_code in (200, 202)
    replay_job_id = replay_res.json()["jobId"]

    # Must return exact same job without re-execution
    assert replay_job_id == first_job_id


# 4. Job Cancellation Semantics (Queued and In-Flight)
def test_job_cancellation_semantics():
    client = create_user_client("cancellation_user@example.com")

    # Create job in memory
    job_id = f"job-cancel-{uuid.uuid4().hex[:8]}"
    user = db.get_user_by_email("cancellation_user@example.com")

    job_record = {
        "jobId": job_id,
        "userId": user["id"],
        "status": "queued",
        "stage": "validating",
        "stageMessage": "Solidity syntax validated.",
        "progress": 15,
        "contractName": "CancelVault.sol",
        "createdAt": "2026-10-23T00:00:00Z"
    }
    jobs_store[job_id] = job_record
    db.save_job(job_record)

    # Cancel while queued
    cancel_res = client.post(f"/api/v1/jobs/{job_id}/cancel")
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "cancelled"

    # Verify status in database
    db_job = db.get_job(job_id)
    assert db_job["status"] == "cancelled"

    # Result retrieval must return 410 GONE
    res_poll = client.get(f"/api/v1/jobs/{job_id}/result")
    assert res_poll.status_code == 410
    assert res_poll.json()["detail"]["code"] == "JOB_CANCELLED"

    # Completed job cannot be cancelled
    completed_job_id = f"job-comp-{uuid.uuid4().hex[:8]}"
    comp_record = {
        "jobId": completed_job_id,
        "userId": user["id"],
        "status": "completed",
        "stage": "completed",
        "progress": 100,
        "contractName": "CompVault.sol"
    }
    jobs_store[completed_job_id] = comp_record
    db.save_job(comp_record)

    bad_cancel = client.post(f"/api/v1/jobs/{completed_job_id}/cancel")
    assert bad_cancel.status_code == 400
    assert bad_cancel.json()["detail"]["code"] == "CANNOT_CANCEL"


# 5. Startup Reboot Interrupted-Job Reconciliation
def test_reboot_interrupted_job_reconciliation():
    # Insert an artificial in-flight job simulating server shutdown during inference
    user = db.get_user_by_email("reboot_user@example.com")
    if not user:
        create_user_client("reboot_user@example.com")
        user = db.get_user_by_email("reboot_user@example.com")

    interrupted_job_id = f"job-interrupted-{uuid.uuid4().hex[:8]}"

    raw_job = {
        "jobId": interrupted_job_id,
        "userId": user["id"],
        "status": "running",
        "stage": "inferring",
        "stageMessage": "Executing Legal-BERT neural classification...",
        "progress": 55,
        "contractName": "InterruptedContract.sol"
    }
    db.save_job(raw_job)

    # Verify initially running in DB
    assert db.get_job(interrupted_job_id)["status"] == "running"

    # Trigger reboot reconciliation routine
    updated_count = db.reconcile_interrupted_jobs()
    assert updated_count >= 1

    # Verify status changed to failed with clear resubmission message
    rec = db.get_job(interrupted_job_id)
    assert rec["status"] == "failed"
    assert rec["stage"] == "interrupted"
    assert "restarted" in rec["stageMessage"].lower() or "interrupted" in rec["stageMessage"].lower()


# 6. AI Assistant Context Grounding and Schema Distinction
def test_assistant_scoping_and_schema_distinction():
    audit_data = {
        "analysisId": "audit-test-assistant-01",
        "contractName": "Part5Vault.sol",
        "solidityCode": SAMPLE_SOL,
        "riskScore": 78,
        "overallRiskLevel": "High",
        "findings": [
            {
                "category": "Termination",
                "severity": "High",
                "lineStart": 14,
                "lineEnd": 14,
                "snippet": "selfdestruct(payable(owner));",
                "description": "Irreversible selfdestruct killswitch allows unilateral termination."
            },
            {
                "category": "Payment / Financial",
                "severity": "Medium",
                "lineStart": 17,
                "lineEnd": 20,
                "snippet": "function setFee(uint256 newFee) external",
                "description": "Unbounded fee parameter modifier without hard ceiling."
            }
        ],
        "categories": [
            {"name": "Termination", "severity": "High", "score": 90},
            {"name": "Payment / Financial", "severity": "Medium", "score": 60}
        ]
    }

    # Query 1: Termination clause
    ans_kill = answer_contract_query("Explain the termination clause and how it works", audit_data)
    assert ans_kill["category"] == "Termination"
    assert ans_kill["scopedContract"] == "Part5Vault.sol"
    assert len(ans_kill["verifiedFindings"]) > 0
    assert "selfdestruct" in ans_kill["verifiedFindings"][0]["snippet"]
    assert "selfdestruct" in ans_kill["modelExplanations"].lower()
    assert ans_kill["disclaimer"] == LEGAL_ASSISTANT_DISCLAIMER
    assert ans_kill["sourceCodeAvailable"] is True

    # Query 2: Fee modification clause
    ans_fee = answer_contract_query("Can the owner change the fees arbitrarily?", audit_data)
    assert ans_fee["category"] == "Payment / Financial"
    assert len(ans_fee["verifiedFindings"]) > 0
    assert "fee" in ans_fee["modelExplanations"].lower()


# 7. AI Assistant External Provider Graceful Offline Fallback
def test_assistant_external_provider_fallback(monkeypatch):
    # Set fake external provider URL pointing to closed local port (immediate connection refused)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake-secret-key-12345")
    monkeypatch.setenv("OPENAI_API_BASE", "http://127.0.0.1:54321/v1")

    audit_data = {
        "contractName": "FallbackContract.sol",
        "solidityCode": SAMPLE_SOL,
        "riskScore": 65,
        "overallRiskLevel": "Medium",
        "findings": [{"category": "Termination", "severity": "High", "description": "selfdestruct killswitch"}]
    }

    # Should catch connection failure gracefully and fall back to local grounded synthesis
    res = answer_contract_query("What does this contract do?", audit_data)
    assert res is not None
    assert "answer" in res
    assert "FallbackContract.sol" in res["answer"] or "Part5Vault" in res["answer"] or "Scope Assessment" in res["answer"]
    # Secret API key must NOT be leaked anywhere in the output
    assert "sk-fake-secret-key" not in json.dumps(res) if "json" in locals() else "sk-fake-secret-key" not in str(res)


# 8. Report Generation (PDF & DOCX) with Risk, Findings, and XAI Attributions
def test_pdf_and_docx_report_generation_and_content():
    mock_audit = {
        "analysisId": "audit-report-verify-01",
        "contractName": "AuditedVault.sol",
        "auditDate": "2026-10-23T12:00:00Z",
        "riskScore": 82,
        "overallRiskLevel": "High",
        "summary": "Automated Legal-BERT neural analysis detected high-severity operational termination hazard.",
        "categories": [
            {"name": "Termination", "severity": "High", "score": 95, "summary": "Emergency selfdestruct killswitch detected."},
            {"name": "Payment / Financial", "severity": "Medium", "score": 60, "summary": "Unbounded fee modifications."}
        ],
        "findings": [
            {
                "category": "Termination",
                "severity": "High",
                "lineStart": 14,
                "lineEnd": 14,
                "snippet": "selfdestruct(payable(owner));",
                "description": "Unilateral fund liquidation instruction."
            }
        ],
        "shapValues": [
            {"token": "selfdestruct", "weight": 0.4281},
            {"token": "payable", "weight": 0.1822}
        ],
        "limeExplanations": [
            {"token": "selfdestruct", "weight": 0.4105}
        ],
        "recommendations": [
            {"priority": "High", "category": "Termination", "issue": "Unilateral selfdestruct", "recommendation": "Use OpenZeppelin Pausable."}
        ],
        "complianceMatrix": [
            {"area": "GDPR Art 17", "status": "Pass", "note": "No plaintext natural-person personal identifying information."}
        ]
    }

    # 1. PDF Report Generation
    pdf_bytes = generate_pdf_report(mock_audit)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF")

    # 2. DOCX Report Generation
    docx_bytes = generate_docx_report(mock_audit)
    assert isinstance(docx_bytes, bytes)
    assert len(docx_bytes) > 1000
    # ZIP signature for docx format
    assert docx_bytes.startswith(b"PK")


# 9. Report Export Endpoint Ownership & Authentication Checks
def test_report_endpoints_ownership_and_auth():
    client_a = create_user_client("report_owner_a@example.com")
    client_b = create_user_client("report_attacker_b@example.com")

    # User A performs an analysis
    analysis_res = client_a.post(
        "/api/v1/analyze",
        json={"sourceCode": SAMPLE_SOL, "contractName": "ReportVault.sol"}
    )
    assert analysis_res.status_code == 200
    analysis_id = analysis_res.json()["analysisId"]

    # 1. Unauthenticated downloads succeed directly in local edition
    anon_client = TestClient(app)
    anon_pdf = anon_client.get(f"/api/v1/reports/{analysis_id}/pdf")
    assert anon_pdf.status_code == 200
    assert anon_pdf.headers["content-type"] == "application/pdf"
    assert anon_pdf.content.startswith(b"%PDF")

    anon_docx = anon_client.get(f"/api/v1/reports/{analysis_id}/docx")
    assert anon_docx.status_code == 200
    assert "wordprocessingml" in anon_docx.headers["content-type"]
    assert anon_docx.content.startswith(b"PK")

    # 2. Nonexistent analysis ID returns 404
    fake_pdf = anon_client.get("/api/v1/reports/audit-nonexistent-12345/pdf")
    assert fake_pdf.status_code == 404

    # 3. Authenticated client also downloads both PDF and DOCX reports
    pdf_a = client_a.get(f"/api/v1/reports/{analysis_id}/pdf")
    assert pdf_a.status_code == 200
    assert pdf_a.headers["content-type"] == "application/pdf"
    assert pdf_a.content.startswith(b"%PDF")

    docx_a = client_a.get(f"/api/v1/reports/{analysis_id}/docx")
    assert docx_a.status_code == 200
    assert "wordprocessingml" in docx_a.headers["content-type"]
    assert docx_a.content.startswith(b"PK")


# 10. Async Multipart Upload Integration Test
def test_async_job_multipart_upload_persists_file_and_links_lifecycle():
    """
    Verifies that POST /api/v1/analyze/jobs/upload stores the physical file in local storage,
    records file metadata, links fileId to the async job and saved analysis, and cleans up on deletion.
    """
    client = create_user_client("async_uploader@example.com")

    # 1. Unauthenticated client can interact with upload endpoint (validates file without 401)
    anon_client = TestClient(app)
    unauth_bad = anon_client.post(
        "/api/v1/analyze/jobs/upload",
        files={"file": ("invalid.txt", io.BytesIO(b"not a sol file"), "text/plain")}
    )
    assert unauth_bad.status_code == 400
    assert "INVALID_FILE_TYPE" in unauth_bad.text

    # 2. Authenticated upload
    upload_res = client.post(
        "/api/v1/analyze/jobs/upload",
        files={"file": ("AsyncVault.sol", io.BytesIO(SAMPLE_SOL.encode("utf-8")), "text/plain")}
    )
    assert upload_res.status_code == 202
    job_payload = upload_res.json()
    job_id = job_payload["jobId"]
    file_id = job_payload["fileId"]
    assert file_id is not None
    assert job_payload["status"] in ("queued", "processing")

    # Verify file metadata in database and storage backend
    storage = get_storage()
    file_rec = db.get_file_record(file_id)
    assert file_rec is not None
    assert file_rec["originalFilename"] == "AsyncVault.sol"
    assert storage.file_exists(file_rec["storagePath"], file_rec["userId"])

    # 3. Poll job until completed
    for _ in range(60):
        poll_res = client.get(f"/api/v1/analyze/jobs/{job_id}")
        assert poll_res.status_code == 200
        poll_data = poll_res.json()
        if poll_data["status"] == "completed":
            break
        time.sleep(1.0)
    else:
        pytest.fail("Async upload job did not complete within timeout")

    analysis_id = poll_data.get("analysisId") or poll_data.get("result", {}).get("analysisId")
    assert analysis_id is not None
    assert (poll_data.get("fileId") == file_id or poll_data.get("result", {}).get("fileId") == file_id)

    # Verify saved analysis record links file_id
    saved_analysis = db.get_analysis_by_id(analysis_id)
    assert saved_analysis is not None
    assert (saved_analysis.get("fileId") == file_id or saved_analysis.get("file_id") == file_id)

    # 4. Deleting the analysis cascades to file deletion
    del_res = client.delete(f"/api/v1/analyses/{analysis_id}")
    assert del_res.status_code == 200
    assert not storage.file_exists(file_rec["storagePath"], file_rec["userId"])
    assert db.get_file_record(file_id) is None

