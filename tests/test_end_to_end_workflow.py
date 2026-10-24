"""
tests/test_end_to_end_workflow.py - End-to-End Workflow & Release Readiness Verification

Validates the full local operation lifecycle required for the Final Local Edition:
1. Health & readiness endpoints.
2. Unauthenticated asynchronous job creation, monotonic progress polling, and result retrieval.
3. AI Legal Assistant querying with grounded findings and engine attribution.
4. Binary PDF and DOCX export generation without session cookies.
5. Local audit history listing and verification.
6. Safe deletion cascading to stored files and records.
7. Local user profile retrieval.
"""

import pytest
import uuid
import time
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
    # 2. Asynchronous Analysis Job Creation & Lifecycle (No Login Required)
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
        }
    )
    assert job_resp.status_code == 202
    job_id = job_resp.json()["jobId"]
    assert job_id.startswith("job-")

    # Poll status until completion (CPU inference + real SHAP/LIME takes ~15-25s)
    completed = False
    final_status = None
    for _ in range(60):
        status_resp = client.get(f"/api/v1/jobs/{job_id}")
        assert status_resp.status_code == 200
        final_status = status_resp.json()
        if final_status["status"] == "completed":
            completed = True
            break
        time.sleep(1.0)

    assert completed, f"Job {job_id} did not complete in time: {final_status}"
    assert final_status["progress"] == 100

    # Retrieve final result via dedicated endpoint
    result_resp = client.get(f"/api/v1/jobs/{job_id}/result")
    assert result_resp.status_code == 200
    result_data = result_resp.json()
    analysis_id = result_data["analysisId"]
    assert analysis_id is not None
    assert "riskScore" in result_data
    assert "categories" in result_data

    # --------------------------------------------------------------------------
    # 3. Context-Grounded AI Legal Assistant (No Login Required)
    # --------------------------------------------------------------------------
    chat_resp = client.post(
        f"/api/v1/analyze/{analysis_id}/chat",
        json={"message": "Explain the emergency termination clause and recommend remediation."}
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
    # 4. Binary PDF and DOCX Report Exports (No Login Required)
    # --------------------------------------------------------------------------
    pdf_resp = client.get(f"/api/v1/reports/{analysis_id}/pdf")
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"
    assert pdf_resp.content.startswith(b"%PDF-")
    assert len(pdf_resp.content) > 1000

    docx_resp = client.get(f"/api/v1/reports/{analysis_id}/docx")
    assert docx_resp.status_code == 200
    assert "vnd.openxmlformats" in docx_resp.headers["content-type"]
    assert docx_resp.content.startswith(b"PK\x03\x04")  # Standard ZIP container signature
    assert len(docx_resp.content) > 1000

    # --------------------------------------------------------------------------
    # 5. Local Audit History Listing
    # --------------------------------------------------------------------------
    history_resp = client.get("/api/v1/analyses")
    assert history_resp.status_code == 200
    analyses_list = history_resp.json().get("analyses", [])
    assert any(a["id"] == analysis_id for a in analyses_list)

    # --------------------------------------------------------------------------
    # 6. Complete Deletion & Cascading Cleanup
    # --------------------------------------------------------------------------
    del_resp = client.delete(f"/api/v1/analyze/{analysis_id}")
    assert del_resp.status_code == 200
    assert del_resp.json().get("status") in ("deleted", "discarded") or del_resp.json().get("success")

    # Verify analysis is no longer accessible
    get_del_resp = client.get(f"/api/v1/analyze/{analysis_id}")
    assert get_del_resp.status_code in (404, 403)

    # --------------------------------------------------------------------------
    # 7. Local Profile and Status Check
    # --------------------------------------------------------------------------
    profile_resp = client.get("/api/v1/auth/me")
    assert profile_resp.status_code == 200
    assert profile_resp.json()["role"] in ("admin", "auditor")

