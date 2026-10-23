#!/usr/bin/env python3
"""
scripts/setup_model.py - Safe Legal-BERT Model Weights Downloader & Checksum Verifier

Automates the acquisition and verification of the fine-tuned Legal-BERT v3.3.0
model checkpoint (~438 MB) for local execution of Smart Contract Analyser.

Conforms to project requirements:
- Downloads official verified release asset from GitHub releases.
- Validates SHA-256 checksum before placing binary into the active model directory.
- Keeps model binaries out of git tracking.
- Syncs checkpoint across canonical and backend model directories.
"""

import os
import sys
import shutil
import hashlib
import argparse
import urllib.request
import urllib.error
from typing import Optional

DEFAULT_ASSET_URL = "https://github.com/AroKrishna/Smart_Contract_Analyser/releases/download/v3.3.0/model.safetensors"
DEFAULT_EXPECTED_SHA256 = "4c5d1c1caf6f42e38173d6fc1b69a924cf2ad93e0188e0f5bb057ac0b73d972e"
DEFAULT_TARGET_REL_PATH = os.path.join("analysis", "models", "legal_bert_v3.3.0")
BACKEND_TARGET_REL_PATH = os.path.join("backend", "analysis", "models", "legal_bert_v3.3.0")
MIN_FILE_SIZE_BYTES = 350 * 1024 * 1024  # 350 MB


def compute_sha256(file_path: str, chunk_size: int = 1024 * 1024) -> str:
    """Computes SHA-256 checksum of a file efficiently in 1MB chunks."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().lower()


def download_with_progress(url: str, destination_part: str) -> None:
    """Downloads a file from URL to destination with progress display."""
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "SmartContractAnalyser-ModelSetup/1.0"}
    )

    with urllib.request.urlopen(req) as resp, open(destination_part, "wb") as out_f:
        total_size = int(resp.headers.get("Content-Length", 0))
        downloaded = 0
        chunk_size = 512 * 1024  # 512 KB

        print(f"Downloading from: {url}")
        if total_size > 0:
            print(f"Total size: {total_size / (1024 * 1024):.1f} MB")

        while True:
            chunk = resp.read(chunk_size)
            if not chunk:
                break
            out_f.write(chunk)
            downloaded += len(chunk)
            if total_size > 0:
                pct = (downloaded / total_size) * 100
                sys.stdout.write(f"\rProgress: {pct:.1f}% ({downloaded / (1024 * 1024):.1f} / {total_size / (1024 * 1024):.1f} MB)")
                sys.stdout.flush()
            else:
                sys.stdout.write(f"\rDownloaded: {downloaded / (1024 * 1024):.1f} MB")
                sys.stdout.flush()
        print()


def setup_model(
    repo_root: str,
    target_dir: Optional[str] = None,
    url: str = DEFAULT_ASSET_URL,
    expected_sha256: str = DEFAULT_EXPECTED_SHA256,
    check_only: bool = False
) -> bool:
    """
    Executes model verification and safe download.
    Returns True if model is present and verified, False otherwise.
    """
    primary_dir = target_dir or os.path.join(repo_root, DEFAULT_TARGET_REL_PATH)
    secondary_dir = os.path.join(repo_root, BACKEND_TARGET_REL_PATH)
    primary_file = os.path.join(primary_dir, "model.safetensors")
    secondary_file = os.path.join(secondary_dir, "model.safetensors")

    expected_sha256 = expected_sha256.strip().lower()

    # Step 1: Check if primary or secondary already has valid weights
    for candidate_path, label in [(primary_file, "Primary"), (secondary_file, "Backend mirror")]:
        if os.path.isfile(candidate_path):
            file_size = os.path.getsize(candidate_path)
            print(f"Found existing checkpoint at {label} path ({candidate_path}, {file_size / (1024 * 1024):.1f} MB).")
            print("Verifying SHA-256 checksum...")
            actual_sha = compute_sha256(candidate_path)
            if actual_sha == expected_sha256:
                print(f"[SUCCESS] Checksum verified: {actual_sha}")
                # Ensure secondary is also populated
                other_file = secondary_file if candidate_path == primary_file else primary_file
                other_dir = os.path.dirname(other_file)
                if not os.path.isfile(other_file) and os.path.isdir(other_dir):
                    print(f"Syncing verified weights to {other_file}...")
                    try:
                        shutil.copy2(candidate_path, other_file)
                    except Exception as copy_err:
                        print(f"Warning: Could not copy to mirror ({copy_err}), primary remains valid.")
                return True
            else:
                print(f"[ERROR] Existing checkpoint checksum mismatch at {candidate_path}!")
                print(f"  Expected: {expected_sha256}")
                print(f"  Actual:   {actual_sha}")
                if check_only:
                    return False
                print("Removing corrupt checkpoint to prepare fresh download...")
                os.remove(candidate_path)

    if check_only:
        print(f"[ERROR] Model weights not found in {primary_dir}. Run setup without --check-only to download.")
        return False

    # Step 2: Download asset
    os.makedirs(primary_dir, exist_ok=True)
    temp_part = os.path.join(primary_dir, "model.safetensors.part")

    try:
        if os.path.exists(temp_part):
            os.remove(temp_part)

        download_with_progress(url, temp_part)

        # Verify minimum size
        downloaded_size = os.path.getsize(temp_part)
        if downloaded_size < MIN_FILE_SIZE_BYTES:
            print(f"[ERROR] Downloaded file size ({downloaded_size} bytes) is below minimum expected threshold.")
            if os.path.exists(temp_part):
                os.remove(temp_part)
            return False

        # Verify checksum
        print("Verifying downloaded file SHA-256 checksum...")
        downloaded_sha = compute_sha256(temp_part)
        if downloaded_sha != expected_sha256:
            print("[ERROR] Checksum verification failed!")
            print(f"  Expected: {expected_sha256}")
            print(f"  Actual:   {downloaded_sha}")
            print("The downloaded asset was corrupted or modified. Removing incomplete download.")
            if os.path.exists(temp_part):
                os.remove(temp_part)
            return False

        print(f"[SUCCESS] SHA-256 checksum verified: {downloaded_sha}")
        # Atomic rename
        if os.path.exists(primary_file):
            os.remove(primary_file)
        os.rename(temp_part, primary_file)
        print(f"Placed model weights at: {primary_file}")

        # Mirror to backend directory if backend dir exists
        if os.path.isdir(secondary_dir):
            try:
                shutil.copy2(primary_file, secondary_file)
                print(f"Mirrored model weights to: {secondary_file}")
            except Exception as e:
                print(f"Notice: Mirror copy to backend failed ({e}), primary path is active.")

        return True

    except urllib.error.URLError as url_err:
        print(f"[ERROR] Network error during model download: {url_err}")
        print("Please verify your internet connection or download the asset manually:")
        print(f"  URL:  {url}")
        print(f"  Dest: {primary_file}")
        if os.path.exists(temp_part):
            os.remove(temp_part)
        return False
    except Exception as exc:
        print(f"[ERROR] Unexpected error during model setup: {exc}")
        if os.path.exists(temp_part):
            os.remove(temp_part)
        return False


def main():
    parser = argparse.ArgumentParser(description="Legal-BERT v3.3.0 Model Checkpoint Setup & Verifier")
    parser.add_argument("--check-only", action="store_true", help="Only verify existing checkpoint without downloading")
    parser.add_argument("--url", default=DEFAULT_ASSET_URL, help="Custom download URL for model.safetensors")
    parser.add_argument("--sha256", default=DEFAULT_EXPECTED_SHA256, help="Expected SHA-256 checksum")
    parser.add_argument("--target-dir", default=None, help="Custom target directory for weights")

    args = parser.parse_args()

    # Determine repository root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(script_dir, ".."))

    success = setup_model(
        repo_root=repo_root,
        target_dir=args.target_dir,
        url=args.url,
        expected_sha256=args.sha256,
        check_only=args.check_only
    )

    if success:
        print("\nAll model verification checks PASSED. Smart Contract Analyser is ready for local execution.")
        sys.exit(0)
    else:
        print("\nModel setup FAILED. Please resolve the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
