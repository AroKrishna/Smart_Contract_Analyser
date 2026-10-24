"""
tests/test_auth.py - Verification for Local Single-User Identity, Session, and Host/Origin Safeguards

Covers:
- Local single-user identity default (no login / no registration needed)
- Session restoration via /api/v1/auth/me returning default local auditor
- Graceful compatibility for legacy auth routes (/login, /register, /logout)
- Host header validation against DNS rebinding attacks (403 INVALID_HOST)
- Browser cross-site protection on state-changing requests (403 CROSS_SITE_REQUEST_BLOCKED)
- Allowed local origins (http://localhost:5173, etc.) permitted for state changes
- Password hashing with bcrypt ($2b$) and legacy hash migration in database layer
- Local admin diagnostics access (/admin/stats, /admin/users, /admin/model-status)
- Local password change and forgot-password safe notices
"""

import os
import hashlib
import pytest
from fastapi.testclient import TestClient
from backend.main import app, DEFAULT_LOCAL_USER
import backend.analysis.db as db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_auth_db():
    """Ensure clean database schema is initialized."""
    db.init_db()


def test_local_registration_endpoint():
    """Verify registration route responds with clean local-edition status without requiring accounts."""
    fresh_client = TestClient(app)
    res = fresh_client.post("/api/v1/auth/register", json={
        "email": "user@example.com",
        "password": "Password123!",
        "fullName": "Local Tester"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["mode"] == "local_single_user"
    assert data["user"]["id"] == "local_user"


def test_stored_password_is_bcrypt():
    """Verify passwords hashed with db.hash_password use modern bcrypt, never plaintext."""
    password = "BcryptSecret123!"
    stored_hash = db.hash_password(password)
    assert stored_hash.startswith("$2b$")
    assert password not in stored_hash
    is_valid, needs_rehash = db.verify_password(password, stored_hash)
    assert is_valid is True
    assert needs_rehash is False
    wrong_valid, _ = db.verify_password("WrongPassword!", stored_hash)
    assert wrong_valid is False


def test_legacy_password_migration_to_bcrypt():
    """Verify database verifies legacy SHA-256 hashes and flags them for rehash."""
    legacy_password = "LegacyPassword2025!"
    legacy_salt = "sca_saas_platform_salt_2026"
    legacy_hash = hashlib.sha256((legacy_password + legacy_salt).encode("utf-8")).hexdigest()

    assert len(legacy_hash) == 64
    assert not legacy_hash.startswith("$2b$")

    # verify_password recognizes legacy sha256 and flags needs_rehash=True
    is_valid, needs_rehash = db.verify_password(legacy_password, legacy_hash)
    assert is_valid is True
    assert needs_rehash is True
    wrong_valid, _ = db.verify_password("WrongPassword!", legacy_hash)
    assert wrong_valid is False


def test_local_login_behavior():
    """Verify login route returns active local user with local session token."""
    fresh_client = TestClient(app)
    res = fresh_client.post("/api/v1/auth/login", json={
        "email": "auditor@local.device",
        "password": "AnyPassword"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["mode"] == "local_single_user"
    assert data["user"]["id"] == "local_user"
    assert "token" in data


def test_session_restoration_and_local_profile():
    """Verify /api/v1/auth/me returns default local user profile without requiring credentials."""
    fresh_client = TestClient(app)
    res = fresh_client.get("/api/v1/auth/me")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["mode"] == "local_single_user"
    assert data["user"]["id"] == "local_user"
    assert data["user"]["role"] == "admin"
    assert "Legal-BERT Inference" in data["features"]


def test_logout_behavior():
    """Verify /api/v1/auth/logout resets session cleanly."""
    fresh_client = TestClient(app)
    res = fresh_client.post("/api/v1/auth/logout")
    assert res.status_code == 200
    assert res.json()["status"] == "success"


def test_local_host_and_origin_security():
    """
    Verify local security safeguards:
    1. Untrusted Host header (DNS rebinding defense) -> 403 INVALID_HOST.
    2. State-changing requests from untrusted external Origin -> 403 CROSS_SITE_REQUEST_BLOCKED.
    3. State-changing requests from permitted local Origin -> 200 OK.
    """
    fresh_client = TestClient(app)

    # 1. DNS rebinding attack with rogue Host header -> 403 Forbidden
    host_attack_res = fresh_client.get("/api/v1/auth/me", headers={"Host": "evil-attacker-site.com"})
    assert host_attack_res.status_code == 403
    assert host_attack_res.json()["code"] == "INVALID_HOST"

    # 2. State-changing request from unauthorized cross-origin -> 403 Forbidden
    origin_attack_res = fresh_client.put(
        "/api/v1/auth/me",
        json={"fullName": "Attacker"},
        headers={"Origin": "https://evil-attacker-site.com"}
    )
    assert origin_attack_res.status_code == 403
    assert origin_attack_res.json()["code"] == "CROSS_SITE_REQUEST_BLOCKED"

    # 3. State-changing request from trusted local origin -> 200 OK
    good_res = fresh_client.put(
        "/api/v1/auth/me",
        json={"fullName": "Auditor Name"},
        headers={"Origin": "http://localhost:5173"}
    )
    assert good_res.status_code == 200
    assert good_res.json()["status"] == "success"


def test_local_admin_diagnostics_access():
    """Verify local user has immediate access to platform diagnostics and statistics."""
    fresh_client = TestClient(app)

    # Admin stats
    res_stats = fresh_client.get("/api/v1/admin/stats")
    assert res_stats.status_code == 200
    assert "totalAnalyses" in res_stats.json() or "totalUsers" in res_stats.json()

    # Admin users list
    res_users = fresh_client.get("/api/v1/admin/users")
    assert res_users.status_code == 200
    assert "users" in res_users.json()
    assert any(u["id"] == "local_user" for u in res_users.json()["users"])

    # Admin model status
    res_model = fresh_client.get("/api/v1/admin/model-status")
    assert res_model.status_code == 200
    assert "modelName" in res_model.json()
    assert "isModelAvailable" in res_model.json()


def test_password_and_forgot_endpoints_safe_in_local_mode():
    """Verify change-password and forgot-password endpoints return safe informational notices."""
    fresh_client = TestClient(app)

    res_pw = fresh_client.post("/api/v1/auth/change-password", json={
        "currentPassword": "old",
        "newPassword": "newpassword123!"
    })
    assert res_pw.status_code == 200
    assert "does not require passwords" in res_pw.json()["message"]

    res_forgot = fresh_client.post("/api/v1/auth/forgot-password", json={
        "email": "user@example.com"
    })
    assert res_forgot.status_code == 200
    assert "does not use cloud passwords" in res_forgot.json()["message"]
