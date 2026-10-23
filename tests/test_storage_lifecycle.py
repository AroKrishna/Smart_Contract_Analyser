"""
tests/test_storage_lifecycle.py - Automated Verification Suite for Part 4
Secure File Storage, User Sandboxing, Ownership Isolation, and Data Lifecycle.
"""

import io
import os
import sys
import uuid
import tempfile
import pytest
from fastapi.testclient import TestClient

# Ensure repo root and backend are in python path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_dir = os.path.join(root_dir, "backend")
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from backend.main import app, MAX_SOURCE_LENGTH, DATA_RETENTION_DAYS
import backend.analysis.db as db
from backend.analysis.storage import (
    sanitize_filename,
    validate_file_upload,
    LocalStorageBackend,
    get_storage
)

SAMPLE_VALID_SOL = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract StorageVault {
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


@pytest.fixture(autouse=True)
def setup_test_db():
    """Initializes clean database schema."""
    db.init_db()


def create_authenticated_client(email: str = "storage_tester@example.com", password: str = "SecurePass123!", role: str = "auditor"):
    """Creates a user account and returns an authenticated TestClient with active session cookies."""
    client = TestClient(app)
    # Check if user already exists
    user = db.get_user_by_email(email)
    if not user:
        clean_email = email.strip().lower()
        user_id = f"usr-{uuid.uuid4().hex[:8]}"
        p_hash = db.hash_password(password)
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO users (id, email, password_hash, full_name, organization, role, created_at)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
        """, (user_id, clean_email, p_hash, "Storage Tester", "Test Org", role))
        conn.commit()
        conn.close()

    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    token = res.json()["token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client, res.json()["user"]


# 1. Filename Sanitization & Path Traversal Validation
def test_filename_sanitization_and_path_traversal_prevention():
    # Dangerous path traversal attacks
    assert sanitize_filename("../../etc/passwd") == "passwd.sol"
    assert sanitize_filename("..\\..\\windows\\system32.cmd") == "system32.sol"
    assert sanitize_filename("../../../secret_contract.sol") == "secret_contract.sol"
    assert sanitize_filename("/root/private.key.sol") == "private_key.sol"
    # Null byte injection
    assert sanitize_filename("contract.sol\x00.exe") == "contract_sol.sol"
    # Special characters and spaces
    assert sanitize_filename("My Token [v2] (test)!.sol") == "My_Token_v2_test.sol"
    # Empty or blank input defaults safely
    assert sanitize_filename("") == "Contract.sol"
    assert sanitize_filename("   ") == "Contract.sol"
    assert sanitize_filename("....") == "Contract.sol"


# 2. File Upload Validation (Type, Size, Encoding, Null Bytes)
def test_upload_validation_file_types():
    # Non-.sol rejected
    with pytest.raises(ValueError) as exc_info:
        validate_file_upload("contract.txt", b"pragma solidity ^0.8.0;")
    assert "INVALID_FILE_TYPE" in str(exc_info.value)

    with pytest.raises(ValueError) as exc_info:
        validate_file_upload("contract.pdf", b"%PDF-1.4...")
    assert "INVALID_FILE_TYPE" in str(exc_info.value)

    with pytest.raises(ValueError) as exc_info:
        validate_file_upload("exploit.sol.exe", b"MZ...")
    assert "INVALID_FILE_TYPE" in str(exc_info.value)


def test_upload_validation_payload_too_large():
    oversized = b"a" * (MAX_SOURCE_LENGTH + 10)
    with pytest.raises(ValueError) as exc_info:
        validate_file_upload("big.sol", oversized, max_size=MAX_SOURCE_LENGTH)
    assert "PAYLOAD_TOO_LARGE" in str(exc_info.value)


def test_upload_validation_encoding_and_binary_null_bytes():
    # Null byte detection
    binary_content = b"pragma solidity ^0.8.0;\x00malicious_bytes"
    with pytest.raises(ValueError) as exc_info:
        validate_file_upload("corrupt.sol", binary_content)
    assert "INVALID_FILE_TYPE" in str(exc_info.value)

    # Invalid UTF-8 sequence
    bad_utf8 = b"pragma solidity ^0.8.0; \xff\xfe\xfa"
    with pytest.raises(ValueError) as exc_info:
        validate_file_upload("bad_encoding.sol", bad_utf8)
    assert "INVALID_ENCODING" in str(exc_info.value)

    # Empty source
    with pytest.raises(ValueError) as exc_info:
        validate_file_upload("empty.sol", b"   \n\t  ")
    assert "EMPTY_SOURCE" in str(exc_info.value)


# 3. LocalStorageBackend User Sandboxing & Traversal Defense
def test_local_storage_backend_user_sandboxing():
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = LocalStorageBackend(base_dir=tmpdir)
        user_a = "usr_alice"
        user_b = "usr_bob"
        file_id = "file_123"
        content = b"pragma solidity ^0.8.0; contract Vault {}"

        storage_path = storage.save_file(user_a, file_id, "Vault.sol", content)
        assert storage.file_exists(storage_path, user_a)

        # File is on disk under user directory
        full_path = os.path.join(tmpdir, storage_path.replace("/", os.sep))
        assert os.path.exists(full_path)
        assert storage.get_file(storage_path, user_a) == content

        # User B cannot access User A's file (PermissionError on cross-user check)
        with pytest.raises(PermissionError):
            storage.get_file(storage_path, user_b)

        # Path traversal attack in get_file
        with pytest.raises(PermissionError):
            storage.get_file(f"../{user_a}/Vault.sol", user_b)

        # Deletion respects isolation
        with pytest.raises(PermissionError):
            storage.delete_file(storage_path, user_b)
        assert storage.file_exists(storage_path, user_a)

        # User A can delete
        assert storage.delete_file(storage_path, user_a) is True
        assert not storage.file_exists(storage_path, user_a)


# 4. Upload Contract File Endpoint & Retrieval Flow
def test_authenticated_upload_and_file_retrieval():
    client_a, user_a = create_authenticated_client("alice_storage@example.com")

    # Upload valid contract file
    file_bytes = SAMPLE_VALID_SOL.encode("utf-8")
    files = {"file": ("VaultContract.sol", io.BytesIO(file_bytes), "text/plain")}
    data = {"contract_name": "VaultContract", "description": "Vault audit"}

    res = client_a.post("/api/v1/analyze/upload", files=files, data=data)
    assert res.status_code == 200, res.text
    result = res.json()
    assert result.get("status") == "completed"
    analysis_id = result.get("analysisId")
    file_id = result.get("fileId")
    assert analysis_id is not None
    assert file_id is not None

    # Retrieve source file via analysis endpoint
    file_res = client_a.get(f"/api/v1/analyze/{analysis_id}/file")
    assert file_res.status_code == 200
    assert file_res.content.decode("utf-8") == SAMPLE_VALID_SOL
    assert "VaultContract" in file_res.headers.get("content-disposition", "")

    # Retrieve source file via direct file endpoint
    direct_res = client_a.get(f"/api/v1/files/{file_id}")
    assert direct_res.status_code == 200
    assert direct_res.content.decode("utf-8") == SAMPLE_VALID_SOL

    # List files endpoint
    list_res = client_a.get("/api/v1/files")
    assert list_res.status_code == 200
    files_list = list_res.json().get("files", [])
    assert any(f["id"] == file_id for f in files_list)


# 5. Ownership Isolation Across Users
def test_cross_user_file_access_isolation():
    client_a, user_a = create_authenticated_client("alice_iso@example.com")
    client_b, user_b = create_authenticated_client("bob_iso@example.com")
    admin_client, admin_user = create_authenticated_client("admin_iso@legal-ai.io", role="admin")

    # Alice uploads a contract
    file_bytes = SAMPLE_VALID_SOL.encode("utf-8")
    files = {"file": ("AliceContract.sol", io.BytesIO(file_bytes), "text/plain")}
    res = client_a.post("/api/v1/analyze/upload", files=files)
    assert res.status_code == 200
    analysis_id = res.json()["analysisId"]
    file_id = res.json()["fileId"]

    # Bob attempts to download Alice's contract file via analysis endpoint -> 403 Forbidden
    res_b_analysis = client_b.get(f"/api/v1/analyze/{analysis_id}/file")
    assert res_b_analysis.status_code == 403
    assert res_b_analysis.json()["detail"]["code"] == "ACCESS_DENIED"

    # Bob attempts to download Alice's contract file via direct file endpoint -> 403 Forbidden
    res_b_direct = client_b.get(f"/api/v1/files/{file_id}")
    assert res_b_direct.status_code == 403
    assert res_b_direct.json()["detail"]["code"] == "ACCESS_DENIED"

    # Unauthenticated client -> 401 Unauthorized
    unauth_client = TestClient(app)
    assert unauth_client.get(f"/api/v1/analyze/{analysis_id}/file").status_code == 401
    assert unauth_client.get(f"/api/v1/files/{file_id}").status_code == 401

    # Admin CAN access Alice's contract file
    admin_res = admin_client.get(f"/api/v1/analyze/{analysis_id}/file")
    assert admin_res.status_code == 200
    assert admin_res.content.decode("utf-8") == SAMPLE_VALID_SOL


# 6. Complete Deletion Removes Physical File & Metadata
def test_complete_deletion_removes_physical_file_and_metadata():
    client, user = create_authenticated_client("deleter@example.com")

    # Upload contract
    file_bytes = SAMPLE_VALID_SOL.encode("utf-8")
    files = {"file": ("DeleteMe.sol", io.BytesIO(file_bytes), "text/plain")}
    res = client.post("/api/v1/analyze/upload", files=files)
    assert res.status_code == 200
    analysis_id = res.json()["analysisId"]
    file_id = res.json()["fileId"]

    # Verify file metadata exists in database
    file_meta = db.get_file_record(file_id)
    assert file_meta is not None
    storage = get_storage()
    assert storage.file_exists(file_meta["storagePath"], user["id"])

    # Delete the analysis
    del_res = client.delete(f"/api/v1/analyze/{analysis_id}")
    assert del_res.status_code == 200

    # Verification: physical file removed
    assert not storage.file_exists(file_meta["storagePath"], user["id"])

    # Verification: metadata row removed
    assert db.get_file_record(file_id) is None
    assert db.get_analysis_by_id(analysis_id) is None

    # Verification: endpoints return 404
    assert client.get(f"/api/v1/analyze/{analysis_id}").status_code == 404
    assert client.get(f"/api/v1/analyze/{analysis_id}/file").status_code == 404
    assert client.get(f"/api/v1/files/{file_id}").status_code == 404
    assert client.get(f"/api/v1/reports/{analysis_id}/pdf").status_code == 404


# 7. Cross-User Deletion Prevented
def test_cross_user_deletion_prevented():
    client_a, user_a = create_authenticated_client("alice_del@example.com")
    client_b, user_b = create_authenticated_client("bob_del@example.com")

    files = {"file": ("AliceSafe.sol", io.BytesIO(SAMPLE_VALID_SOL.encode("utf-8")), "text/plain")}
    res = client_a.post("/api/v1/analyze/upload", files=files)
    analysis_id = res.json()["analysisId"]
    file_id = res.json()["fileId"]

    # Bob attempts to delete Alice's analysis -> 403 Forbidden
    del_res = client_b.delete(f"/api/v1/analyze/{analysis_id}")
    assert del_res.status_code == 403

    # Alice's file and analysis remain intact
    assert client_a.get(f"/api/v1/analyze/{analysis_id}").status_code == 200
    assert client_a.get(f"/api/v1/files/{file_id}").status_code == 200


# 8. Data Retention & Cleanup Lifecycle
def test_data_retention_and_cleanup():
    admin_client, admin_user = create_authenticated_client("admin_retention@legal-ai.io", role="admin")
    client_user, _ = create_authenticated_client("user_retention@example.com")

    # Non-admin cannot invoke cleanup -> 403 Forbidden
    res_user = client_user.post("/api/v1/admin/cleanup")
    assert res_user.status_code == 403

    # Admin runs cleanup with 30 days retention
    res_admin = admin_client.post("/api/v1/admin/cleanup?retention_days=30")
    assert res_admin.status_code == 200
    data = res_admin.json()
    assert data["status"] == "success"
    assert "results" in data
    assert "deletedFiles" in data["results"]


# 9. Retention Cleanup Specifically Removes Expired Records and Preserves Unexpired Records
def test_retention_cleanup_removes_expired_preserves_unexpired():
    from backend.main import run_automatic_retention_cleanup
    client, user = create_authenticated_client("retention_diff@example.com")

    # Upload two contracts
    file_bytes = SAMPLE_VALID_SOL.encode("utf-8")
    files1 = {"file": ("ExpiredContract.sol", io.BytesIO(file_bytes), "text/plain")}
    res1 = client.post("/api/v1/analyze/upload", files=files1)
    assert res1.status_code == 200
    expired_analysis_id = res1.json()["analysisId"]
    expired_file_id = res1.json()["fileId"]

    files2 = {"file": ("ActiveContract.sol", io.BytesIO(file_bytes), "text/plain")}
    res2 = client.post("/api/v1/analyze/upload", files=files2)
    assert res2.status_code == 200
    active_analysis_id = res2.json()["analysisId"]
    active_file_id = res2.json()["fileId"]

    # Artificially set expired_analysis_id and expired_file_id expiry to the past
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE analyses SET created_at = datetime('now', '-35 days') WHERE id = ?
    """, (expired_analysis_id,))
    cursor.execute("""
        UPDATE stored_files SET expires_at = datetime('now', '-5 days') WHERE id = ?
    """, (expired_file_id,))

    # Keep active_analysis_id active
    cursor.execute("""
        UPDATE analyses SET created_at = datetime('now') WHERE id = ?
    """, (active_analysis_id,))
    cursor.execute("""
        UPDATE stored_files SET expires_at = datetime('now', '+30 days') WHERE id = ?
    """, (active_file_id,))
    conn.commit()
    conn.close()

    # Run cleanup
    cleanup_res = run_automatic_retention_cleanup(retention_days=30)
    assert cleanup_res["deletedAnalyses"] >= 1
    assert cleanup_res["deletedFiles"] >= 1

    # Verify expired contract is gone from DB and storage
    assert db.get_analysis_by_id(expired_analysis_id) is None
    assert db.get_file_record(expired_file_id) is None
    assert client.get(f"/api/v1/analyze/{expired_analysis_id}").status_code == 404

    # Verify active contract is intact and accessible
    assert db.get_analysis_by_id(active_analysis_id) is not None
    assert db.get_file_record(active_file_id) is not None
    assert client.get(f"/api/v1/analyze/{active_analysis_id}").status_code == 200
    assert client.get(f"/api/v1/files/{active_file_id}").status_code == 200


# 10. Physical Storage Deletion Failure & Safe Retry Behavior
def test_physical_storage_deletion_failure_and_safe_retry(monkeypatch):
    client, user = create_authenticated_client("retry_tester@example.com")

    # Upload contract
    file_bytes = SAMPLE_VALID_SOL.encode("utf-8")
    files = {"file": ("RetryContract.sol", io.BytesIO(file_bytes), "text/plain")}
    res = client.post("/api/v1/analyze/upload", files=files)
    assert res.status_code == 200
    analysis_id = res.json()["analysisId"]
    file_id = res.json()["fileId"]

    file_meta = db.get_file_record(file_id)
    assert file_meta is not None
    storage = get_storage()
    assert storage.file_exists(file_meta["storagePath"], user["id"])

    # Simulate physical deletion failure on storage backend
    orig_delete_file = LocalStorageBackend.delete_file
    def mock_failing_delete(self_or_path, *args, **kwargs):
        return False

    monkeypatch.setattr(LocalStorageBackend, "delete_file", mock_failing_delete)
    monkeypatch.setattr(storage, "delete_file", lambda path, user_id: False)

    # Attempt delete -> must return HTTP 500 STORAGE_DELETION_FAILED
    del_res = client.delete(f"/api/v1/analyze/{analysis_id}")
    assert del_res.status_code == 500
    err_body = del_res.json()
    assert err_body["detail"]["code"] == "STORAGE_DELETION_FAILED"

    # Integrity verification: metadata and analysis MUST be retained for retry
    assert db.get_analysis_by_id(analysis_id) is not None
    assert db.get_file_record(file_id) is not None
    assert storage.file_exists(file_meta["storagePath"], user["id"])

    # Restore healthy storage behavior and retry delete
    monkeypatch.setattr(LocalStorageBackend, "delete_file", orig_delete_file)
    monkeypatch.setattr(storage, "delete_file", lambda path, user_id: orig_delete_file(storage, path, user_id))

    retry_res = client.delete(f"/api/v1/analyze/{analysis_id}")
    assert retry_res.status_code == 200

    # Verification: now completely removed
    assert not storage.file_exists(file_meta["storagePath"], user["id"])
    assert db.get_file_record(file_id) is None
    assert db.get_analysis_by_id(analysis_id) is None


# 11. Automatic Startup / Periodic Cleanup Fault Tolerance
def test_cleanup_fault_tolerance(monkeypatch):
    from backend.main import run_automatic_retention_cleanup

    # Even if database or storage raises an unexpected error, cleanup must never crash
    def mock_exploding_cleanup(retention_days):
        raise RuntimeError("Simulated transient storage or disk I/O lock")

    monkeypatch.setattr(db, "cleanup_expired_records", mock_exploding_cleanup)

    # Calling run_automatic_retention_cleanup should catch and return error payload gracefully
    res = run_automatic_retention_cleanup()
    assert res.get("status") == "error"
    assert "Simulated transient storage" in res.get("error", "")


# 12. Deletion During Active Analysis Discards Results
def test_deletion_during_active_analysis_discards_results():
    from backend.main import jobs_store, cancelled_jobs
    client, user = create_authenticated_client("active_job_user@example.com")

    # Create an active in-memory job
    job_id = f"job-active-{uuid.uuid4().hex[:8]}"
    jobs_store[job_id] = {
        "jobId": job_id,
        "userId": user["id"],
        "status": "running",
        "stage": "inferring",
        "progress": 50,
        "contractName": "ActiveInFlightContract"
    }

    # Delete the analysis while in flight
    del_res = client.delete(f"/api/v1/analyze/{job_id}")
    assert del_res.status_code == 200

    # Job is removed from memory jobs_store and marked in cancelled_jobs
    assert job_id not in jobs_store
    assert job_id in cancelled_jobs

    # Direct retrieval returns 404
    assert client.get(f"/api/v1/analyze/{job_id}").status_code == 404


# 13. Database Migration Compatibility
def test_database_migration_compatibility():
    # Calling init_db multiple times must be idempotent and preserve columns
    db.init_db()
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(analyses)")
    cols = [r["name"] for r in cursor.fetchall()]
    assert "user_id" in cols
    assert "file_id" in cols

    cursor.execute("PRAGMA table_info(stored_files)")
    file_cols = [r["name"] for r in cursor.fetchall()]
    assert "id" in file_cols
    assert "user_id" in file_cols
    assert "storage_path" in file_cols
    assert "sha256_hash" in file_cols
    conn.close()

