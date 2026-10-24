"""
tests/test_api.py - Unit and Integration Tests for FastAPI Service

Tests the complete Legal-BERT SaaS API specifications:
- Diagnostic health endpoints with Legal-BERT headers
- Active Legal-BERT analysis path and transparent data-readiness gating
- Persistent history retrieval from SQLite
- Context-scoped AI legal assistant queries
- Real PDF and DOCX report downloads
- Authentication and User profile endpoints
- Admin control panel metrics and model status endpoints
"""

import pytest
from fastapi.testclient import TestClient
from analysis.api import app, MAX_SOURCE_LENGTH
import analysis.db as db

client = TestClient(app)

@pytest.fixture(autouse=True)
def seed_test_audit():
    db.init_db()
    login_res = client.post("/api/v1/auth/login", json={"email": "admin@legal-ai.io", "password": "AdminPass2026!"})
    if login_res.status_code == 200:
        token = login_res.json().get("accessToken") or login_res.json().get("token")
        client.headers["Authorization"] = f"Bearer {token}"
    test_record = {
        "analysisId": "audit-101",
        "contractName": "VulnerableEscrow.sol",
        "contractType": "Solidity Smart Contract",
        "solidityCode": SAMPLE_VALID_CONTRACT,
        "solidityVersion": "^0.8.20",
        "status": "completed",
        "riskScore": 88,
        "riskLevel": "Critical",
        "riskBreakdown": {
            "Privacy": 10,
            "Termination": 95,
            "Legal Compliance": 60,
            "Liability": 40,
            "Payment / Financial": 85
        },
        "categories": [
            {"name": "Privacy", "riskLevel": "Low", "score": 10},
            {"name": "Termination", "riskLevel": "Critical", "score": 95},
            {"name": "Legal Compliance", "riskLevel": "Medium", "score": 60},
            {"name": "Liability", "riskLevel": "Low", "score": 40},
            {"name": "Payment / Financial", "riskLevel": "High", "score": 85}
        ],
        "findings": [
            {
                "findingId": "find-1",
                "category": "Termination",
                "severity": "Critical",
                "title": "Privileged Selfdestruct Routine",
                "description": "Contract contains selfdestruct capable of sweeping balance.",
                "snippet": "selfdestruct(payable(owner));",
                "lineNumbers": [36]
            }
        ],
        "shapValues": [{"token": "selfdestruct", "value": 0.82, "category": "Termination"}],
        "limeExplanations": [{"token": "selfdestruct", "weight": 0.78, "type": "risk"}],
        "recommendations": [{"id": "rec-1", "category": "Termination", "suggestion": "Constrain termination."}],
        "complianceMatrix": [{"area": "Consumer Law", "assessment": "Potential Hazard", "status": "Warning"}],
        "summary": "Legal-BERT analysis identified critical unilateral termination hazards.",
        "metadata": {"engineType": "legal_bert_ml_engine", "analysisModelVersion": "legal-bert-multi-label-v1.0"}
    }
    db.insert_analysis(test_record)

SAMPLE_VALID_CONTRACT = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @notice Two-party commercial settlement escrow.
 */
contract SimpleEscrow {
    address public owner;
    uint256 public feeRate;

    constructor() {
        owner = msg.sender;
    }

    function emergencyKill() external {
        require(msg.sender == owner, "Only owner");
        selfdestruct(payable(owner));
    }

    function setFee(uint256 newFee) external {
        feeRate = newFee;
    }
}
"""


def test_health_endpoints():
    """Verify both /health and /api/v1/health return 200 with Legal-BERT engine metadata."""
    for path in ["/health", "/api/v1/health"]:
        response = client.get(path)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "disclaimer" in data
        assert data["engine"] == "legal_bert_ml_engine"
        assert response.headers.get("x-analysis-disclaimer") is not None
        assert response.headers.get("x-engine-type") == "legal_bert_ml_engine"


def test_analyze_valid_contract_legal_bert_path():
    """
    Verify POST /api/v1/analyze executes the Legal-BERT analysis path.
    When a trained model artifact is not yet present due to dataset volume thresholds,
    verifies it returns model_unavailable status with verified dataset diagnostics
    rather than silently falling back to a deterministic rule engine.
    """
    payload = {
        "sourceCode": SAMPLE_VALID_CONTRACT,
        "contractName": "SimpleEscrow.sol"
    }
    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "analysisId" in data
    assert data["contractName"] == "SimpleEscrow"
    assert data["metadata"]["engineType"] == "legal_bert_ml_engine"
    assert data["metadata"]["ruleEngineSubstituteUsed"] is False
    assert data["metadata"]["mockPredictionsUsed"] is False

    # Check status: either model_unavailable with transparent readiness diagnostics or completed
    assert data["status"] in ("model_unavailable", "completed")
    if data["status"] == "model_unavailable":
        assert data["modelStatus"] == "training_blocked_by_data_limitations"
        assert "readiness" in data
        assert data["readiness"]["totalCanonicalRecords"] == 52
        assert data["readiness"]["trainingEligibleRecords"] == 38
        assert "categorySupport" in data["readiness"]


def test_analyze_empty_source():
    """Verify API returns 400 when source code is empty or whitespace-only."""
    for empty_val in ["", "   ", "\n\t"]:
        response = client.post("/api/v1/analyze", json={"sourceCode": empty_val})
        assert response.status_code == 400
        detail = response.json()["detail"]
        assert detail["code"] == "EMPTY_SOURCE"


def test_analyze_unsupported_non_solidity_source():
    """Verify API returns 422 when source is not Solidity."""
    response = client.post("/api/v1/analyze", json={
        "sourceCode": "def calculate_risk():\n    return 'not a solidity contract'\n",
        "contractName": "script.py"
    })
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["code"] == "UNSUPPORTED_SOURCE"


def test_analyze_payload_too_large():
    """Verify API returns 413 when source code exceeds 2MB limit."""
    oversized = "pragma solidity ^0.8.0;\ncontract Large { " + ("// padding\n" * 200000) + " }"
    assert len(oversized) > MAX_SOURCE_LENGTH
    response = client.post("/api/v1/analyze", json={"sourceCode": oversized})
    assert response.status_code == 413
    detail = response.json()["detail"]
    assert detail["code"] == "PAYLOAD_TOO_LARGE"


def test_analyze_null_byte_malformed():
    """Verify API returns 400 for null byte malformed content."""
    response = client.post("/api/v1/analyze", json={"sourceCode": "contract Bad {\x00 }"})
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["code"] == "MALFORMED_SOURCE"


def test_get_analysis_by_id_seeded():
    """Verify GET /api/v1/analyze/{analysis_id} retrieves seeded audit from persistent database."""
    response = client.get("/api/v1/analyze/audit-101")
    assert response.status_code == 200
    data = response.json()
    assert data["analysisId"] == "audit-101"
    assert data["contractName"] == "VulnerableEscrow.sol"
    assert data["riskLevel"] == "Critical"
    assert "categories" in data
    assert len(data["categories"]) == 5


def test_list_analyses_history():
    """Verify GET /api/v1/analyses retrieves local history without requiring login."""
    # 1. Unauthenticated request retrieves local history directly
    unauth_response = TestClient(app).get("/api/v1/analyses?risk_level=All")
    assert unauth_response.status_code == 200
    data = unauth_response.json()
    assert "total" in data
    assert "analyses" in data

    # 2. Insert an audit record
    sample_analysis = {
        "analysisId": "audit-user-hist",
        "contractName": "HistoryContract.sol",
        "contractType": "Solidity Smart Contract",
        "solidityCode": SAMPLE_VALID_CONTRACT,
        "status": "completed",
        "riskScore": 75,
        "riskLevel": "High",
        "riskBreakdown": {},
        "categories": [],
        "findings": [],
        "shapValues": [],
        "limeExplanations": [],
        "recommendations": [],
        "complianceMatrix": [],
        "summary": "History test contract"
    }
    db.insert_analysis(sample_analysis)

    # 3. Retrieve analyses without authentication
    response = client.get("/api/v1/analyses?risk_level=All")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert data["total"] >= 1
    assert "analyses" in data


def test_ai_legal_assistant_chat():
    """Verify POST /api/v1/analyze/{analysis_id}/chat delivers context-grounded response."""
    payload = {"message": "Explain the termination clause and why it is high risk."}
    response = client.post("/api/v1/analyze/audit-101/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert data["category"] == "Termination"
    assert "selfdestruct" in data["answer"].lower()


def test_export_pdf_report():
    """Verify GET /api/v1/reports/{analysis_id}/pdf generates binary PDF report."""
    response = client.get("/api/v1/reports/audit-101/pdf")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content[:4] == b"%PDF"


def test_export_docx_report():
    """Verify GET /api/v1/reports/{analysis_id}/docx generates binary Word document."""
    response = client.get("/api/v1/reports/audit-101/docx")
    assert response.status_code == 200
    assert "openxmlformats" in response.headers["content-type"]
    assert len(response.content) > 1000


def test_auth_login_and_profile():
    """Verify local user profile and auth compatibility."""
    login_payload = {
        "email": "admin@legal-ai.io",
        "password": "AdminPass2026!"
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "user" in data

    profile_res = client.get("/api/v1/auth/me")
    assert profile_res.status_code == 200
    assert "tier" in profile_res.json()


def test_admin_endpoints():
    """Verify Admin metrics, user list, and model status."""
    login_payload = {
        "email": "admin@legal-ai.io",
        "password": "AdminPass2026!"
    }
    auth_res = client.post("/api/v1/auth/login", json=login_payload)
    assert auth_res.status_code == 200
    token = auth_res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    stats_res = client.get("/api/v1/admin/stats", headers=headers)
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert "totalUsers" in stats
    assert "totalAnalyses" in stats

    model_res = client.get("/api/v1/admin/model-status", headers=headers)
    assert model_res.status_code == 200
    m_data = model_res.json()
    assert "modelName" in m_data
    assert "readiness" in m_data


def test_create_and_poll_analysis_job():
    """Verify POST /api/v1/analyze/jobs initiates job and GET /api/v1/jobs/{job_id} tracks completion."""
    import time

    payload = {
        "sourceCode": SAMPLE_VALID_CONTRACT,
        "contractName": "SimpleEscrow.sol"
    }
    response = client.post("/api/v1/analyze/jobs", json=payload)
    assert response.status_code == 202
    job_data = response.json()
    assert "jobId" in job_data
    assert job_data["status"] in ("queued", "running")

    job_id = job_data["jobId"]

    # Poll for completion (up to 40 seconds for neural inference and SHAP/LIME on CPU)
    completed = False
    for _ in range(80):
        time.sleep(0.5)
        poll_res = client.get(f"/api/v1/jobs/{job_id}")
        assert poll_res.status_code == 200
        p_data = poll_res.json()
        if p_data["status"] == "completed":
            completed = True
            assert p_data["progress"] == 100
            assert p_data["result"] is not None
            assert "analysisId" in p_data["result"]
            assert "modelDisclosures" in p_data["result"]
            assert "xai" in p_data["result"]
            break
        elif p_data["status"] == "failed":
            pytest.fail(f"Job failed unexpectedly: {p_data.get('error')}")

    assert completed, "Analysis job did not complete within timeout"


def test_discard_temporary_analysis():
    """Verify POST /api/v1/analyze/{analysis_id}/discard purges ephemeral data."""
    payload = {
        "sourceCode": SAMPLE_VALID_CONTRACT,
        "contractName": "DiscardTest.sol"
    }
    res = client.post("/api/v1/analyze", json=payload)
    assert res.status_code == 200
    analysis_id = res.json()["analysisId"]

    # Discard
    discard_res = client.post(f"/api/v1/analyze/{analysis_id}/discard")
    assert discard_res.status_code == 200
    assert discard_res.json()["status"] == "discarded"

    # Confirm it is no longer in in-memory session cache
    get_res = client.get(f"/api/v1/analyze/{analysis_id}")
    assert get_res.status_code == 404


def test_accurate_line_numbers_and_saliency():
    """Verify line numbers point to actual lines and XAI token saliency is computed."""
    payload = {
        "sourceCode": SAMPLE_VALID_CONTRACT,
        "contractName": "SimpleEscrow.sol"
    }
    res = client.post("/api/v1/analyze", json=payload)
    assert res.status_code == 200
    data = res.json()

    # Check XAI attributions
    assert "xai" in data
    assert "tokenAttributions" in data["xai"]
    assert len(data["xai"]["tokenAttributions"]) > 0
    assert "value" in data["xai"]["tokenAttributions"][0]

    # Check findings line numbers
    for finding in data.get("findings", []):
        assert "lineNumbers" in finding
        assert len(finding["lineNumbers"]) > 0
        for ln in finding["lineNumbers"]:
            assert 1 <= ln <= data["metadata"]["linesOfCode"]
        assert "snippet" in finding
        assert finding["snippet"] != ""


def test_backend_vercel_entrypoints():
    """Verify backend and Vercel entrypoint modules expose the FastAPI app."""
    from backend.main import app as main_app
    from backend.api.index import app as vercel_app
    assert main_app is not None
    assert vercel_app is not None
    assert main_app.title == "Smart Contract Analyser API"
    assert vercel_app.title == "Smart Contract Analyser API"


def test_synchronous_file_upload_validation_and_analysis():
    """Verify POST /api/v1/analyze/upload performs synchronous analysis and handles errors."""
    # 1. Invalid extension
    bad_file = ("bad.txt", b"plain text", "text/plain")
    res_bad = client.post("/api/v1/analyze/upload", files={"file": bad_file})
    assert res_bad.status_code == 400
    assert res_bad.json()["detail"]["code"] == "INVALID_FILE_TYPE"

    # 2. Valid .sol file upload
    sol_file = ("SimpleEscrow.sol", SAMPLE_VALID_CONTRACT.encode("utf-8"), "application/octet-stream")
    res_valid = client.post("/api/v1/analyze/upload", files={"file": sol_file})
    assert res_valid.status_code == 200
    data = res_valid.json()
    assert "analysisId" in data
    assert data["contractName"] == "SimpleEscrow"
    assert "riskScore" in data


def test_cors_headers():
    """Verify CORS middleware headers are properly applied."""
    response = client.options(
        "/api/v1/analyze",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        }
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_no_login_local_analysis_submission_and_workflow():
    """Verify POST /api/v1/analyze, /upload, and /jobs succeed without login in local edition."""
    anon_client = TestClient(app)
    # 1. Direct Analysis without login
    r1 = anon_client.post("/api/v1/analyze", json={"sourceCode": SAMPLE_VALID_CONTRACT, "contractName": "NoLoginTest.sol"})
    assert r1.status_code == 200
    assert "analysisId" in r1.json()

    # 2. File Upload without login
    sol_file = ("NoLogin.sol", SAMPLE_VALID_CONTRACT.encode("utf-8"), "application/octet-stream")
    r2 = anon_client.post("/api/v1/analyze/upload", files={"file": sol_file})
    assert r2.status_code == 200
    assert "analysisId" in r2.json()

    # 3. Async Job Creation without login
    r3 = anon_client.post("/api/v1/analyze/jobs", json={"sourceCode": SAMPLE_VALID_CONTRACT, "contractName": "NoLoginJob.sol"})
    assert r3.status_code == 202
    job_id = r3.json()["jobId"]
    assert job_id.startswith("job-")

    # 4. Job Status Retrieval without login
    r4 = anon_client.get(f"/api/v1/jobs/{job_id}")
    assert r4.status_code == 200


def test_cross_site_origin_protection():
    """Verify state-changing requests from untrusted external web origins are blocked (403)."""
    anon_client = TestClient(app)

    # 1. Untrusted external origin attempting to trigger analysis is blocked
    res_evil = anon_client.post(
        "/api/v1/analyze",
        json={"sourceCode": SAMPLE_VALID_CONTRACT, "contractName": "Evil.sol"},
        headers={"Origin": "https://malicious-website.com"}
    )
    assert res_evil.status_code == 403
    assert res_evil.json()["code"] == "CROSS_SITE_REQUEST_BLOCKED"

    # 2. Untrusted origin attempting deletion is blocked
    res_del = anon_client.delete(
        "/api/v1/analyze/audit-fake-123",
        headers={"Origin": "http://evil-attacker.org"}
    )
    assert res_del.status_code == 403
    assert res_del.json()["code"] == "CROSS_SITE_REQUEST_BLOCKED"

    # 3. Trusted local origin is permitted
    res_local = anon_client.post(
        "/api/v1/analyze",
        json={"sourceCode": SAMPLE_VALID_CONTRACT, "contractName": "SafeLocal.sol"},
        headers={"Origin": "http://localhost:5173"}
    )
    assert res_local.status_code == 200
    assert "analysisId" in res_local.json()


def test_host_header_dns_rebinding_protection():
    """Verify requests with untrusted Host headers are rejected (403)."""
    anon_client = TestClient(app)
    res = anon_client.get("/health", headers={"Host": "attacker-dns-rebound.com"})
    assert res.status_code == 403
    assert res.json()["code"] == "INVALID_HOST"
