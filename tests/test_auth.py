"""
tests/test_auth.py - Comprehensive Unit and Integration Tests for Part 2 Authentication & Access Control

Covers:
- Password hashing with bcrypt (min 12 rounds) and transparent legacy SHA-256 migration
- User registration input validation and account enumeration prevention
- Dual session handling: HttpOnly cookies and Bearer token authorization
- Session restoration via /api/v1/auth/me
- Logout behavior and session invalidation
- Server-side role enforcement (RBAC): Admin vs Auditor endpoints
- Profile updates and password changes
"""

import os
import hashlib
import sqlite3
import pytest
from fastapi.testclient import TestClient
from analysis.api import app
import analysis.db as db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_auth_db():
    """Ensure database is initialized and dev accounts exist for tests."""
    os.environ["SEED_DEV_ACCOUNTS"] = "true"
    db.init_db()


def test_registration_validation_and_no_enumeration():
    """Verify input validation and that registration does not leak existing email addresses."""
    fresh_client = TestClient(app)

    # 1. Invalid email format
    res = fresh_client.post("/api/v1/auth/register", json={
        "email": "not-an-email",
        "password": "ValidPassword123!",
        "fullName": "Test User"
    })
    assert res.status_code == 400
    assert "email" in str(res.json()["detail"]).lower()

    # 2. Short password (< 8 chars)
    res = fresh_client.post("/api/v1/auth/register", json={
        "email": "shortpass@example.com",
        "password": "short",
        "fullName": "Test User"
    })
    assert res.status_code == 400
    assert "8 characters" in str(res.json()["detail"]).lower()

    # 3. Successful registration
    unique_email = "auditor_new_test@example.com"
    # Clean up test user if previously registered
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE email = ?", (unique_email,))
    conn.commit()
    conn.close()

    res = fresh_client.post("/api/v1/auth/register", json={
        "email": unique_email,
        "password": "SecurePassword2026!",
        "fullName": "New Auditor",
        "organization": "Test Security Inc"
    })
    assert res.status_code == 200 or res.status_code == 201
    data = res.json()
    assert data["status"] == "success"
    assert data["user"]["email"] == unique_email
    assert data["user"]["role"] == "auditor"
    assert "token" in data
    # Confirm HttpOnly cookie set
    assert "access_token" in res.cookies

    # 4. Duplicate registration attempts must return neutral message without account enumeration
    res_dup = fresh_client.post("/api/v1/auth/register", json={
        "email": unique_email,
        "password": "DifferentPassword123!",
        "fullName": "Duplicate Person"
    })
    assert res_dup.status_code == 400
    detail_str = str(res_dup.json()["detail"])
    # Check that it doesn't say "Email already exists" or "User already registered"
    assert "could not be completed" in detail_str.lower()


def test_stored_password_is_bcrypt():
    """Verify newly registered passwords are saved with modern bcrypt hashes, never plaintext."""
    fresh_client = TestClient(app)
    email = "bcrypt_verify@example.com"
    password = "BcryptSecret123!"

    # Clean up test user if exists
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE email = ?", (email,))
    conn.commit()
    conn.close()

    res = fresh_client.post("/api/v1/auth/register", json={
        "email": email,
        "password": password,
        "fullName": "Bcrypt Tester"
    })
    assert res.status_code == 200 or res.status_code == 201

    # Query SQLite database directly
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()
    assert row is not None
    stored_hash = row["password_hash"]
    # Must start with bcrypt prefix ($2b$) and NOT match plaintext or simple sha256
    assert stored_hash.startswith("$2b$")
    assert password not in stored_hash


def test_legacy_password_migration_to_bcrypt():
    """
    Verify transparent migration of legacy single-round SHA-256 password hashes to bcrypt.
    1. Seed a user with legacy static-salt SHA-256 hash.
    2. User logs in with valid password -> verify login succeeds.
    3. User's stored hash is automatically upgraded in-place to bcrypt.
    4. Subsequent logins verify against the upgraded bcrypt hash.
    """
    legacy_email = "legacy_auditor@protocol.org"
    legacy_password = "LegacyPassword2025!"
    legacy_salt = "sca_saas_platform_salt_2026"
    legacy_hash = hashlib.sha256((legacy_password + legacy_salt).encode("utf-8")).hexdigest()

    # Verify legacy format is a 64-char hex string
    assert len(legacy_hash) == 64
    assert not legacy_hash.startswith("$2b$")

    # Insert legacy user directly into DB
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE email = ?", (legacy_email,))
    cursor.execute(
        """
        INSERT INTO users (id, email, password_hash, full_name, organization, role, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        ("usr-legacy-01", legacy_email, legacy_hash, "Legacy Auditor", "Old DAO", "auditor", "2025-01-01T00:00:00Z")
    )
    conn.commit()
    conn.close()

    fresh_client = TestClient(app)

    # Log in with the legacy credentials
    res = fresh_client.post("/api/v1/auth/login", json={
        "email": legacy_email,
        "password": legacy_password
    })
    assert res.status_code == 200
    assert res.json()["status"] == "success"

    # Verify that the stored hash in the database was upgraded to bcrypt
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash FROM users WHERE email = ?", (legacy_email,))
    updated_hash = cursor.fetchone()["password_hash"]
    conn.close()
    assert updated_hash.startswith("$2b$"), "Legacy SHA-256 hash was not migrated to bcrypt"
    assert updated_hash != legacy_hash

    # Log in a second time using the newly migrated bcrypt hash
    res_second = fresh_client.post("/api/v1/auth/login", json={
        "email": legacy_email,
        "password": legacy_password
    })
    assert res_second.status_code == 200
    assert res_second.json()["status"] == "success"


def test_invalid_login_credentials():
    """Verify login failure handling for wrong passwords and unknown accounts (no enumeration)."""
    fresh_client = TestClient(app)

    # 1. Non-existent account
    res_unknown = fresh_client.post("/api/v1/auth/login", json={
        "email": "nobody_exists_here@unknown.com",
        "password": "SomePassword123!"
    })
    assert res_unknown.status_code == 401
    assert "INVALID_CREDENTIALS" in str(res_unknown.json()["detail"])

    # 2. Existing account with wrong password
    res_wrong = fresh_client.post("/api/v1/auth/login", json={
        "email": "admin@legal-ai.io",
        "password": "WrongPasswordHere!"
    })
    assert res_wrong.status_code == 401
    assert "INVALID_CREDENTIALS" in str(res_wrong.json()["detail"])


def test_session_restoration_bearer_and_cookie():
    """Verify session can be restored via both Bearer token header and HttpOnly cookie."""
    fresh_client = TestClient(app)

    # Login as auditor
    res = fresh_client.post("/api/v1/auth/login", json={
        "email": "auditor@enterprise.com",
        "password": "AuditorPass2026!"
    })
    assert res.status_code == 200
    token = res.json()["token"]

    # 1. Restore via Cookie (fresh client with cookie only)
    cookie_client = TestClient(app, cookies={"access_token": token})
    res_cookie = cookie_client.get("/api/v1/auth/me")
    assert res_cookie.status_code == 200
    data_cookie = res_cookie.json()
    user_info = data_cookie.get("user", data_cookie)
    assert user_info["email"] == "auditor@enterprise.com"
    assert user_info["role"] == "auditor"

    # 2. Restore via Bearer header (fresh client without cookies)
    header_client = TestClient(app)
    res_bearer = header_client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res_bearer.status_code == 200
    data_bearer = res_bearer.json()
    user_info_b = data_bearer.get("user", data_bearer)
    assert user_info_b["email"] == "auditor@enterprise.com"

    # 3. Unauthenticated request without token/cookie
    anon_client = TestClient(app)
    res_anon = anon_client.get("/api/v1/auth/me")
    assert res_anon.status_code == 401

    # 4. Malformed/invalid token
    res_invalid = anon_client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid.jwt.token"})
    assert res_invalid.status_code == 401


def test_logout_clears_cookie_and_invalidates_token():
    """Verify POST /api/v1/auth/logout clears cookie and revokes the token from further access."""
    fresh_client = TestClient(app)
    login_res = fresh_client.post("/api/v1/auth/login", json={
        "email": "auditor@enterprise.com",
        "password": "AuditorPass2026!"
    })
    assert login_res.status_code == 200
    token = login_res.json()["token"]

    # Perform logout
    logout_res = fresh_client.post("/api/v1/auth/logout")
    assert logout_res.status_code == 200
    assert logout_res.json()["status"] == "success"

    # Verify cookie was cleared (set-cookie has max-age=0 or path=/)
    set_cookie_header = logout_res.headers.get("set-cookie", "")
    assert "access_token" in set_cookie_header

    # Verify server-side token revocation: attempting to reuse the revoked token fails
    blocked_res = fresh_client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert blocked_res.status_code == 401
    assert "TOKEN_REVOKED" in str(blocked_res.json()["detail"])


def test_csrf_cookie_state_changing_protection():
    """Verify cookie-authenticated state-changing requests are protected from rogue cross-origin callers."""
    fresh_client = TestClient(app)
    login_res = fresh_client.post("/api/v1/auth/login", json={
        "email": "auditor@enterprise.com",
        "password": "AuditorPass2026!"
    })
    assert login_res.status_code == 200
    token = login_res.json()["token"]

    cookie_client = TestClient(app, cookies={"access_token": token})

    # 1. State-changing request from unauthorized cross-origin -> 403 Forbidden
    evil_res = cookie_client.put(
        "/api/v1/auth/me",
        json={"fullName": "Hacked Name"},
        headers={"Origin": "https://evil-attacker-site.com"}
    )
    assert evil_res.status_code == 403
    assert "CSRF_FORBIDDEN" in str(evil_res.json()["detail"])

    # 2. State-changing request from allowed origin -> 200 OK
    good_res = cookie_client.put(
        "/api/v1/auth/me",
        json={"fullName": "Auditor Allowed"},
        headers={"Origin": "http://localhost:5173"}
    )
    assert good_res.status_code == 200


def test_role_based_access_control():
    """
    Verify server-side RBAC enforcement:
    - Anonymous: 401 Unauthorized on admin endpoints
    - Auditor: 403 Forbidden on admin endpoints
    - Admin: 200 OK on admin endpoints
    """
    anon_client = TestClient(app)

    # 1. Anonymous requests to admin endpoints -> 401
    for endpoint in ["/api/v1/admin/stats", "/api/v1/admin/users", "/api/v1/admin/model-status"]:
        res = anon_client.get(endpoint)
        assert res.status_code == 401, f"Expected 401 on {endpoint} for anonymous user"

    # 2. Auditor requests to admin endpoints -> 403 Forbidden
    auditor_client = TestClient(app)
    auditor_login = auditor_client.post("/api/v1/auth/login", json={
        "email": "auditor@enterprise.com",
        "password": "AuditorPass2026!"
    })
    assert auditor_login.status_code == 200
    auditor_token = auditor_login.json()["token"]

    for endpoint in ["/api/v1/admin/stats", "/api/v1/admin/users", "/api/v1/admin/model-status"]:
        res = auditor_client.get(endpoint, headers={"Authorization": f"Bearer {auditor_token}"})
        assert res.status_code == 403, f"Expected 403 on {endpoint} for auditor user"
        assert "Administrator privileges required" in str(res.json()["detail"]) or "ACCESS_DENIED" in str(res.json()["detail"])

    # 3. Admin requests to admin endpoints -> 200 OK
    admin_client = TestClient(app)
    admin_login = admin_client.post("/api/v1/auth/login", json={
        "email": "admin@legal-ai.io",
        "password": "AdminPass2026!"
    })
    assert admin_login.status_code == 200
    admin_token = admin_login.json()["token"]

    res_stats = admin_client.get("/api/v1/admin/stats", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_stats.status_code == 200
    assert "totalUsers" in res_stats.json()

    res_users = admin_client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_users.status_code == 200
    assert "users" in res_users.json()

    res_model = admin_client.get("/api/v1/admin/model-status", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_model.status_code == 200
    assert "modelName" in res_model.json()


def test_password_change_flow():
    """Verify password change endpoint requires current password and enforces minimum length."""
    fresh_client = TestClient(app)
    user_email = "pw_change_user@example.com"
    old_pw = "OriginalPassword2026!"
    new_pw = "BrandNewSecret2026!"

    # Clean up test user if exists
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE email = ?", (user_email,))
    conn.commit()
    conn.close()

    reg_res = fresh_client.post("/api/v1/auth/register", json={
        "email": user_email,
        "password": old_pw,
        "fullName": "Password Changer"
    })
    assert reg_res.status_code == 200 or reg_res.status_code == 201
    token = reg_res.json()["token"]

    # 1. Wrong current password -> 400
    res_bad_current = fresh_client.post(
        "/api/v1/auth/change-password",
        json={"currentPassword": "WrongCurrentPassword!", "newPassword": new_pw},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_bad_current.status_code == 400
    assert "Current password is incorrect" in str(res_bad_current.json()["detail"])

    # 2. Short new password -> 400
    res_short = fresh_client.post(
        "/api/v1/auth/change-password",
        json={"currentPassword": old_pw, "newPassword": "short"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_short.status_code == 400
    assert "8 characters" in str(res_short.json()["detail"])

    # 3. Successful change -> 200
    res_success = fresh_client.post(
        "/api/v1/auth/change-password",
        json={"currentPassword": old_pw, "newPassword": new_pw},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_success.status_code == 200

    # 4. Old password no longer works
    res_login_old = fresh_client.post("/api/v1/auth/login", json={
        "email": user_email,
        "password": old_pw
    })
    assert res_login_old.status_code == 401

    # 5. New password works
    res_login_new = fresh_client.post("/api/v1/auth/login", json={
        "email": user_email,
        "password": new_pw
    })
    assert res_login_new.status_code == 200
