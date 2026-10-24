"""
analysis/storage.py - Secure Pluggable File Storage Interface (Part 4)

Provides:
- Pluggable storage architecture: LocalFileSystemStorage (default, free/local)
  and S3StorageBackend (optional for AWS S3, Cloudflare R2, MinIO).
- Strict user sandboxing and path traversal prevention.
- Safe filename sanitization and file upload validation (type, size, encoding, binary detection).
- Secure file lifecycle operations (save, retrieve, delete, exists).
"""

import os
import re
import tempfile
import logging
from abc import ABC, abstractmethod
from typing import Tuple, Optional

logger = logging.getLogger("smart_contract_analyser.storage")

# Security constants
MAX_UPLOAD_SIZE = 1024 * 1024  # 1 MB
ALLOWED_EXTENSION = ".sol"


def sanitize_filename(filename: str) -> str:
    """
    Sanitizes a user-supplied filename to prevent path traversal and shell injection.
    Strips directory separators, restricts characters to alphanumeric, dot, underscore, and dash,
    and ensures a valid .sol extension.
    """
    if not filename:
        return "Contract.sol"

    # Strip any directory components
    base = os.path.basename(filename.strip().replace("\\", "/"))
    # Remove null bytes
    base = base.replace("\x00", "")

    # Split name and extension
    name, ext = os.path.splitext(base)
    # Sanitize name part
    clean_name = re.sub(r"[^a-zA-Z0-9_\-]", "_", name)
    clean_name = re.sub(r"_+", "_", clean_name).strip("._")

    if not clean_name:
        clean_name = "Contract"

    # Limit filename length to 80 chars
    clean_name = clean_name[:80]

    return f"{clean_name}.sol"


def validate_file_upload(
    filename: str,
    content_bytes: bytes,
    max_size: int = MAX_UPLOAD_SIZE
) -> Tuple[str, str]:
    """
    Validates uploaded Solidity file constraints:
    1. Extension must be .sol
    2. File size within limits
    3. No binary null bytes
    4. Valid UTF-8 encoding
    5. Non-empty text

    Returns:
        (safe_filename, decoded_source_text)
    Raises:
        ValueError with (code, message) tuple or descriptive message
    """
    if not filename or not filename.lower().endswith(ALLOWED_EXTENSION):
        raise ValueError("INVALID_FILE_TYPE: Unsupported file. Only Solidity smart contract files (.sol) are accepted.")

    if len(content_bytes) > max_size:
        raise ValueError(f"PAYLOAD_TOO_LARGE: Uploaded file ({len(content_bytes)} bytes) exceeds the maximum allowed limit of {max_size} bytes.")

    if b"\x00" in content_bytes:
        raise ValueError("INVALID_FILE_TYPE: File contains binary content or null bytes. Only UTF-8 text files are accepted.")

    try:
        source_text = content_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raise ValueError("INVALID_ENCODING: File content must be valid UTF-8 encoded text.")

    if not source_text.strip():
        raise ValueError("EMPTY_SOURCE: Uploaded Solidity file contains no source code.")

    safe_name = sanitize_filename(filename)
    return safe_name, source_text


class StorageBackend(ABC):
    """Abstract base class for storage backends."""

    @abstractmethod
    def save_file(self, user_id: str, file_id: str, filename: str, content: bytes) -> str:
        """Saves file bytes and returns canonical storage path/key."""
        pass

    @abstractmethod
    def get_file(self, storage_path: str, user_id: str) -> bytes:
        """Retrieves file bytes ensuring user isolation."""
        pass

    @abstractmethod
    def delete_file(self, storage_path: str, user_id: str) -> bool:
        """Deletes file ensuring user isolation. Returns True if removed or already absent."""
        pass

    @abstractmethod
    def file_exists(self, storage_path: str, user_id: str) -> bool:
        """Checks if file exists in storage."""
        pass


class LocalStorageBackend(StorageBackend):
    """
    Local filesystem storage with strict user isolation and directory traversal prevention.
    Free, zero credentials required, works out of the box locally and in containers.
    """

    def __init__(self, base_dir: Optional[str] = None):
        if base_dir:
            self.base_dir = os.path.abspath(base_dir)
        elif os.environ.get("STORAGE_DIR"):
            self.base_dir = os.path.abspath(os.environ["STORAGE_DIR"])
        elif os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
            self.base_dir = os.path.join(tempfile.gettempdir(), "sca_storage")
        else:
            # Default to backend/data/storage
            backend_base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.base_dir = os.path.join(backend_base, "backend", "data", "storage")

        os.makedirs(self.base_dir, exist_ok=True)

    def _resolve_user_dir(self, user_id: Optional[str] = None) -> str:
        """Resolves and validates the user-scoped directory."""
        effective_user = (user_id or "local_user").strip()
        clean_user = re.sub(r"[^a-zA-Z0-9_\-]", "_", effective_user)
        if not clean_user:
            clean_user = "local_user"

        user_dir = os.path.abspath(os.path.join(self.base_dir, clean_user))
        # Directory traversal verification
        if os.path.commonpath([self.base_dir, user_dir]) != self.base_dir:
            raise PermissionError("Path traversal violation in user directory resolution.")

        os.makedirs(user_dir, exist_ok=True)
        return user_dir

    def _resolve_safe_file_path(self, storage_path: str, user_id: Optional[str] = None) -> str:
        """Resolves target file path and strictly enforces that it resides within the user directory."""
        effective_user = (user_id or "local_user").strip()
        clean_user = re.sub(r"[^a-zA-Z0-9_\-]", "_", effective_user)
        if not clean_user:
            clean_user = "local_user"
        user_dir = self._resolve_user_dir(clean_user)

        # Check for directory traversal sequences
        norm_path = storage_path.replace("\\", "/").strip("/")
        parts = [p for p in norm_path.split("/") if p]
        if ".." in parts:
            raise PermissionError("Path traversal violation: illegal path components.")

        if len(parts) > 1 and parts[0] != clean_user:
            raise PermissionError(f"Access violation: storage path '{storage_path}' does not belong to user '{clean_user}'.")

        filename = parts[-1]
        target_path = os.path.abspath(os.path.join(user_dir, filename))
        if os.path.commonpath([user_dir, target_path]) != user_dir:
            raise PermissionError("Path traversal violation: file path escapes user isolation sandbox.")

        return target_path

    def save_file(self, user_id: str, file_id: str, filename: str, content: bytes) -> str:
        user_dir = self._resolve_user_dir(user_id)
        safe_name = sanitize_filename(filename)
        clean_fid = re.sub(r"[^a-zA-Z0-9_\-]", "_", file_id.strip())
        stored_filename = f"{clean_fid}_{safe_name}"

        target_path = os.path.abspath(os.path.join(user_dir, stored_filename))
        if os.path.commonpath([user_dir, target_path]) != user_dir:
            raise PermissionError("Path traversal violation on file write.")

        # Atomic write
        tmp_path = f"{target_path}.tmp"
        with open(tmp_path, "wb") as f:
            f.write(content)
        os.replace(tmp_path, target_path)

        clean_user = os.path.basename(user_dir)
        return f"{clean_user}/{stored_filename}"

    def get_file(self, storage_path: str, user_id: str) -> bytes:
        target_path = self._resolve_safe_file_path(storage_path, user_id)
        if not os.path.exists(target_path):
            raise FileNotFoundError(f"Stored file '{storage_path}' not found.")

        with open(target_path, "rb") as f:
            return f.read()

    def delete_file(self, storage_path: str, user_id: str) -> bool:
        target_path = self._resolve_safe_file_path(storage_path, user_id)
        if os.path.exists(target_path):
            os.remove(target_path)
            logger.info("Deleted stored file: %s", target_path)
            return True
        return False

    def file_exists(self, storage_path: str, user_id: str) -> bool:
        try:
            target_path = self._resolve_safe_file_path(storage_path, user_id)
            return os.path.exists(target_path)
        except Exception:
            return False


class S3StorageBackend(StorageBackend):
    """
    Pluggable S3-compatible cloud storage backend (AWS S3, Cloudflare R2, MinIO, Wasabi).
    Activated only when STORAGE_BACKEND=s3 is configured.
    """

    def __init__(self):
        try:
            import boto3
            from botocore.config import Config
        except ImportError:
            raise ImportError(
                "boto3 is required for S3StorageBackend. Install it via 'pip install boto3' "
                "or use the default local filesystem storage."
            )

        self.bucket = os.environ.get("S3_BUCKET_NAME")
        if not self.bucket:
            raise ValueError("S3_BUCKET_NAME environment variable is required when STORAGE_BACKEND=s3.")

        endpoint_url = os.environ.get("S3_ENDPOINT_URL")
        region = os.environ.get("S3_REGION", "us-east-1")
        access_key = os.environ.get("S3_ACCESS_KEY_ID")
        secret_key = os.environ.get("S3_SECRET_ACCESS_KEY")

        config = Config(signature_version="s3v4", retries={"max_attempts": 3})
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=config,
        )

    def _build_key(self, user_id: str, filename: str) -> str:
        clean_user = re.sub(r"[^a-zA-Z0-9_\-]", "_", user_id.strip())
        return f"contracts/{clean_user}/{filename}"

    def save_file(self, user_id: str, file_id: str, filename: str, content: bytes) -> str:
        safe_name = sanitize_filename(filename)
        clean_fid = re.sub(r"[^a-zA-Z0-9_\-]", "_", file_id.strip())
        stored_filename = f"{clean_fid}_{safe_name}"
        key = self._build_key(user_id, stored_filename)

        self.s3_client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=content,
            ContentType="text/x-solidity",
        )
        return key

    def get_file(self, storage_path: str, user_id: str) -> bytes:
        clean_user = re.sub(r"[^a-zA-Z0-9_\-]", "_", user_id.strip())
        expected_prefix = f"contracts/{clean_user}/"
        if not storage_path.startswith(expected_prefix):
            raise PermissionError("Access denied: S3 object does not belong to user.")

        response = self.s3_client.get_object(Bucket=self.bucket, Key=storage_path)
        return response["Body"].read()

    def delete_file(self, storage_path: str, user_id: str) -> bool:
        clean_user = re.sub(r"[^a-zA-Z0-9_\-]", "_", user_id.strip())
        expected_prefix = f"contracts/{clean_user}/"
        if not storage_path.startswith(expected_prefix):
            raise PermissionError("Access denied: cannot delete S3 object of another user.")

        self.s3_client.delete_object(Bucket=self.bucket, Key=storage_path)
        return True

    def file_exists(self, storage_path: str, user_id: str) -> bool:
        clean_user = re.sub(r"[^a-zA-Z0-9_\-]", "_", user_id.strip())
        expected_prefix = f"contracts/{clean_user}/"
        if not storage_path.startswith(expected_prefix):
            return False

        try:
            self.s3_client.head_object(Bucket=self.bucket, Key=storage_path)
            return True
        except Exception:
            return False


_STORAGE_INSTANCE: Optional[StorageBackend] = None


def get_storage() -> StorageBackend:
    """Returns the singleton storage backend based on configuration."""
    global _STORAGE_INSTANCE
    if _STORAGE_INSTANCE is None:
        backend_type = os.environ.get("STORAGE_BACKEND", "local").lower()
        if backend_type == "s3":
            _STORAGE_INSTANCE = S3StorageBackend()
        else:
            _STORAGE_INSTANCE = LocalStorageBackend()
    return _STORAGE_INSTANCE


def reset_storage_instance():
    """Resets the storage singleton (primarily for testing with custom storage paths)."""
    global _STORAGE_INSTANCE
    _STORAGE_INSTANCE = None
