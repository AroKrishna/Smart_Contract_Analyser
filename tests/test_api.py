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

client = TestClient(app)

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
    """Verify GET /api/v1/analyses retrieves persistent history with filters."""
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
    """Verify user login and profile retrieval."""
    login_payload = {
        "email": "admin@legal-ai.io",
        "password": "AdminPass2026!"
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["user"]["email"] == "admin@legal-ai.io"

    profile_res = client.get("/api/v1/auth/me")
    assert profile_res.status_code == 200
    assert "tier" in profile_res.json()


def test_admin_endpoints():
    """Verify Admin metrics, user list, and model status."""
    stats_res = client.get("/api/v1/admin/stats")
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert "totalUsers" in stats
    assert "totalAnalyses" in stats

    model_res = client.get("/api/v1/admin/model-status")
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

