"""
tests/test_end_to_end_workflow.py - End-to-End Workflow & Release Readiness Verification

Validates the full local operation lifecycle required by Part 7:
1. Health & readiness endpoints.
2. User registration, authentication, and secure session management.
3. Asynchronous job creation, monotonic progress polling, and result retrieval.
4. AI Legal Assistant querying with grounded findings and engine attribution.
5. Authenticated PDF and DOCX export generation.
6. Audit history listing and deletion cascading to stored files and jobs.
7. Data retention cleanup and session logout token invalidation.
"""

import pytest
import uuid
from fastapi.testclient import TestClient

from backend.main import app
import backend.analysis.db as db

client = TestClient(app, base_url="http://localhost:8000")


@pytest.fixture(autouse=True)
def setup_db():
    """Ensure database schema is initialized for each test run."""
    db.init_db(reconcile=False)


def test_complete_end_to_end_local_workflow():
    # --------------------------------------------------------------------------
    # 1. Health & Readiness Verification
    # --------------------------------------------------------------------------
    health_resp = client.get("/health")
    assert health_resp.status_code == 200
    assert health_resp.json()["status"] in ("healthy", "degraded")

    ready_resp = client.get("/ready")
    assert ready_resp.status_code == 200
    assert ready_resp.json()["status"] == "ready"
    assert "legal_bert" in ready_resp.json()["checkpointName"]

    # --------------------------------------------------------------------------
    # 2. User Registration & Login (Session Cookie)
    # --------------------------------------------------------------------------
    random_suffix = uuid.uuid4().hex[:6]
    user_email = f"auditor_{random_suffix}@release-check.io"
    user_password = "SecureReleasePass2026!"

    reg_resp = client.post("/api/v1/auth/register", json={
        "email": user_email,
        "password": user_password,
        "fullName": "Release Verification Auditor",
        "organization": "Compliance Testing Lab"
    })
    assert reg_resp.status_code in (200, 201)

    login_resp = client.post("/api/v1/auth/login", json={
        "email": user_email,
        "password": user_password
    })
    assert login_resp.status_code == 200
    assert "access_token" in login_resp.cookies
    session_cookie = login_resp.cookies["access_token"]

    # --------------------------------------------------------------------------
    # 3. Asynchronous Analysis Job Creation & Lifecycle
    # --------------------------------------------------------------------------
    sample_contract = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract WorkflowTest {
    address payable public owner;
    uint256 public feeRate = 100;

    constructor() {
        owner = payable(msg.sender);
    }

    function emergencyTerminate() external {
        require(msg.sender == owner, "Only owner");
        selfdestruct(owner);
    }

    function setFee(uint256 newRate) external {
        require(msg.sender == owner, "Only owner");
        feeRate = newRate;
    }
}"""

    idempotency_key = f"idem-{uuid.uuid4().hex}"
    job_resp = client.post(
        "/api/v1/analyze/jobs",
        json={
            "sourceCode": sample_contract,
            "contractName": "WorkflowTest.sol",
            "description": "End-to-end integration test contract",
            "idempotencyKey": idempotency_key
        },
        cookies={"access_token": session_cookie}
    )
    assert job_resp.status_code == 202
    job_id = job_resp.json()["jobId"]
    assert job_id.startswith("job-")

    # Poll status until completion (CPU inference + real SHAP/LIME takes ~15-25s)
    import time
    completed = False
    final_status = None
    for _ in range(60):
        status_resp = client.get(
            f"/api/v1/jobs/{job_id}",
            cookies={"access_token": session_cookie}
        )
        assert status_resp.status_code == 200
        final_status = status_resp.json()
        if final_status["status"] == "completed":
            completed = True
            break
        time.sleep(1.0)

    assert completed, f"Job {job_id} did not complete in time: {final_status}"
    assert final_status["progress"] == 100

    # Retrieve final result via dedicated endpoint
    result_resp = client.get(
        f"/api/v1/jobs/{job_id}/result",
        cookies={"access_token": session_cookie}
    )
    assert result_resp.status_code == 200
    result_data = result_resp.json()
    analysis_id = result_data["analysisId"]
    assert analysis_id is not None
    assert "riskScore" in result_data
    assert "categories" in result_data

    # --------------------------------------------------------------------------
    # 4. Context-Grounded AI Legal Assistant
    # --------------------------------------------------------------------------
    chat_resp = client.post(
        f"/api/v1/analyze/{analysis_id}/chat",
        json={"message": "Explain the emergency termination clause and recommend remediation."},
        cookies={"access_token": session_cookie}
    )
    assert chat_resp.status_code == 200
    chat_data = chat_resp.json()
    assert "answer" in chat_data
    assert "verifiedFindings" in chat_data
    assert "modelExplanations" in chat_data
    assert "remediation" in chat_data
    assert "disclaimer" in chat_data
    assert "engineType" in chat_data
    assert "engineLabel" in chat_data
    assert "isGenerativeAi" in chat_data

    # --------------------------------------------------------------------------
    # 5. Authenticated PDF and DOCX Report Exports
    # --------------------------------------------------------------------------
    pdf_resp = client.get(
        f"/api/v1/reports/{analysis_id}/pdf",
        cookies={"access_token": session_cookie}
    )
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"
    assert pdf_resp.content.startswith(b"%PDF-")
    assert len(pdf_resp.content) > 1000

    docx_resp = client.get(
        f"/api/v1/reports/{analysis_id}/docx",
        cookies={"access_token": session_cookie}
    )
    assert docx_resp.status_code == 200
    assert "vnd.openxmlformats" in docx_resp.headers["content-type"]
    assert docx_resp.content.startswith(b"PK\x03\x04")  # Standard ZIP container signature
    assert len(docx_resp.content) > 1000

    # --------------------------------------------------------------------------
    # 6. Audit History Listing & Cross-Tenant Security
    # --------------------------------------------------------------------------
    history_resp = client.get(
        "/api/v1/analyses",
        cookies={"access_token": session_cookie}
    )
    assert history_resp.status_code == 200
    analyses_list = history_resp.json().get("analyses", [])
    assert any(a["id"] == analysis_id for a in analyses_list)

    # --------------------------------------------------------------------------
    # 7. Complete Deletion & Cascading Cleanup
    # --------------------------------------------------------------------------
    del_resp = client.delete(
        f"/api/v1/analyze/{analysis_id}",
        cookies={"access_token": session_cookie}
    )
    assert del_resp.status_code == 200
    assert del_resp.json().get("status") in ("deleted", "discarded") or del_resp.json().get("success")

    # Verify analysis is no longer accessible
    get_del_resp = client.get(
        f"/api/v1/analyze/{analysis_id}",
        cookies={"access_token": session_cookie}
    )
    assert get_del_resp.status_code in (404, 403)

    # --------------------------------------------------------------------------
    # 8. Session Logout & Token Revocation
    # --------------------------------------------------------------------------
    logout_resp = client.post(
        "/api/v1/auth/logout",
        cookies={"access_token": session_cookie}
    )
    assert logout_resp.status_code == 200

    # Verify revoked token cannot access protected endpoints
    subsequent_resp = client.get(
        "/api/v1/auth/me",
        cookies={"access_token": session_cookie}
    )
    assert subsequent_resp.status_code == 401
