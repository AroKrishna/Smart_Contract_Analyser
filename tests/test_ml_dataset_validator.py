"""
tests/test_ml_dataset_validator.py - Unit tests for ML dataset validator
"""

from analysis.ml_dataset_validator import (
    validate_ml_dataset,
    DatasetValidationReport,
)


def _build_valid_record(sample_id="ML-001", project_id="proj_alpha", split="unassigned"):
    return {
        "sample_id": sample_id,
        "project_id": project_id,
        "contract_family": "FamilyAlpha",
        "source_repo_url": "https://github.com/example/repo",
        "commit_or_version": "v1.0.0",
        "compiler_version": "^0.8.20",
        "license": "MIT",
        "collection_date": "2026-10-21",
        "contract_file": "TestContract.sol",
        "function_name": "setFee",
        "source_line_range": [10, 25],
        "solidity_context": "function setFee(uint256 newFee) external { fee = newFee; }",
        "natspec_comments": "/// @notice sets trading fee",
        "model_text": "Contract: TestContract (MIT)\nFunction: setFee\nOperational Behavior: Updates fee without ceiling check.",
        "categories": {
            "Privacy": {"status": "negative", "severity": "none", "evidence": None, "rationale": "No PII"},
            "Termination": {"status": "negative", "severity": "none", "evidence": None, "rationale": "No selfdestruct"},
            "Legal Compliance": {"status": "negative", "severity": "none", "evidence": None, "rationale": "Single admin function"},
            "Liability": {"status": "negative", "severity": "none", "evidence": None, "rationale": "No disclaimer"},
            "Payment / Financial": {"status": "positive", "severity": "high", "evidence": "fee = newFee;", "rationale": "Uncapped fee modification"},
        },
        "source_labels": {"original_cwe": ["CWE-284"]},
        "provenance": {"annotator_id": "test_annotator", "review_status": "reviewed", "annotation_date": "2026-10-21"},
        "unresolved_questions": [],
        "split": split,
    }


def test_validator_accepts_valid_record():
    records = [_build_valid_record()]
    report = validate_ml_dataset(records)
    assert report.is_valid, f"Expected valid, got errors: {report.errors}"
    assert report.total_records == 1
    # Split should be reported as NOT READY because there is only 1 record
    assert not report.split_ready
    assert "Split is NOT READY" in report.split_readiness_reason


def test_validator_catches_missing_model_text():
    bad_record = _build_valid_record()
    bad_record["model_text"] = ""
    report = validate_ml_dataset([bad_record])
    assert not report.is_valid
    assert any("missing non-empty 'model_text'" in e for e in report.errors)


def test_validator_catches_invalid_category_status():
    bad_record = _build_valid_record()
    bad_record["categories"]["Privacy"]["status"] = "maybe"
    report = validate_ml_dataset([bad_record])
    assert not report.is_valid
    assert any("status 'maybe' invalid" in e for e in report.errors)


def test_validator_detects_data_leakage_across_splits():
    # Same project in train and test
    rec1 = _build_valid_record("ML-001", "shared_project", split="train")
    rec2 = _build_valid_record("ML-002", "shared_project", split="test")
    report = validate_ml_dataset([rec1, rec2])
    assert not report.is_valid
    assert any("Data Leakage Detected" in e for e in report.errors)


def test_validator_accepts_pending_review_status():
    rec = _build_valid_record()
    rec["categories"]["Payment / Financial"]["status"] = "pending_review"
    report = validate_ml_dataset([rec])
    assert report.is_valid


def test_validator_excludes_unreviewed_from_active_splits():
    rec = _build_valid_record(split="train")
    rec["review_status"] = "unresolved"
    report = validate_ml_dataset([rec])
    assert not report.is_valid
    assert any("cannot be assigned to active split 'train'" in e for e in report.errors)


def test_validator_rejects_placeholder_only_solidity():
    bad_record = _build_valid_record()
    bad_record["solidity_context"] = "// This function allows users to withdraw their tokens safely."
    report = validate_ml_dataset([bad_record])
    assert not report.is_valid
    assert any("placeholder-only comment in 'solidity_context'" in e for e in report.errors)


def test_validator_rejects_invalid_line_range():
    bad_record = _build_valid_record()
    bad_record["source_line_range"] = [50, 20]  # start > end
    report = validate_ml_dataset([bad_record])
    assert not report.is_valid
    assert any("invalid line range: start (50) > end (20)" in e for e in report.errors)


def test_validator_rejects_machine_annotator_marked_reviewed():
    bad_record = _build_valid_record()
    bad_record["provenance"]["annotator_id"] = "preliminary_pipeline_v1"
    bad_record["provenance"]["review_status"] = "reviewed"
    bad_record["review_status"] = "reviewed"
    report = validate_ml_dataset([bad_record])
    assert not report.is_valid
    assert any("marked 'reviewed' by machine/pipeline annotator" in e for e in report.errors)


def test_validator_rejects_license_restricted_in_active_split():
    bad_record = _build_valid_record(split="train")
    bad_record["license_status"] = "license_review_required"
    report = validate_ml_dataset([bad_record])
    assert not report.is_valid
    assert any("license_status 'license_review_required' cannot be assigned to active split" in e for e in report.errors)


def test_validator_rejects_positive_label_without_evidence_or_rationale():
    bad_record = _build_valid_record()
    bad_record["categories"]["Payment / Financial"]["evidence"] = ""
    report = validate_ml_dataset([bad_record])
    assert not report.is_valid
    assert any("marked 'positive' without code-grounded evidence" in e for e in report.errors)

    bad_record2 = _build_valid_record()
    bad_record2["categories"]["Payment / Financial"]["rationale"] = ""
    report2 = validate_ml_dataset([bad_record2])
    assert not report2.is_valid
    assert any("marked 'positive' without rationale" in e for e in report2.errors)


def test_validator_rejects_ineligible_in_active_split():
    bad_record = _build_valid_record(split="train")
    bad_record["training_eligible"] = False
    bad_record["training_ineligibility_reason"] = "Awaiting human review"
    report = validate_ml_dataset([bad_record])
    assert not report.is_valid
    assert any("marked training_eligible=False cannot be assigned to active split" in e for e in report.errors)


def test_validator_rejects_training_eligible_with_pending_categories():
    bad_record = _build_valid_record(split="unassigned")
    bad_record["training_eligible"] = True
    bad_record["categories"]["Privacy"]["status"] = "pending_review"
    report = validate_ml_dataset([bad_record])
    assert not report.is_valid
    assert any("cannot be training_eligible=True when review_status" in e for e in report.errors)


def test_validator_rejects_training_eligible_with_license_review_required():
    bad_record = _build_valid_record(split="unassigned")
    bad_record["training_eligible"] = True
    bad_record["license_status"] = "license_review_required"
    report = validate_ml_dataset([bad_record])
    assert not report.is_valid
    assert any("cannot be training_eligible=True when license_status is 'license_review_required'" in e for e in report.errors)


def test_validator_warns_on_unverified_model_text_without_draft_notice():
    rec = _build_valid_record()
    rec["model_text"] = "Contract: Simple (MIT)\nFunction: doSomething"
    rec["model_text_review"] = {"human_verified": False, "status": "pending_human_review"}
    report = validate_ml_dataset([rec])
    assert any("model_text is not human_verified but lacks draft/pending notice" in w for w in report.warnings)


def test_validator_accepts_ai_reviewed_status():
    rec = _build_valid_record()
    rec["review_status"] = "ai_reviewed"
    rec["provenance"]["review_status"] = "ai_reviewed"
    rec["provenance"]["annotator_id"] = "ai_evidence_review_pass"
    report = validate_ml_dataset([rec])
    assert report.is_valid


def test_validator_accepts_ai_review_unresolved_status():
    rec = _build_valid_record()
    rec["review_status"] = "ai_review_unresolved"
    rec["provenance"]["review_status"] = "ai_review_unresolved"
    rec["provenance"]["annotator_id"] = "ai_evidence_review_pass"
    report = validate_ml_dataset([rec])
    assert report.is_valid


def test_validator_allows_ai_reviewed_training_eligible():
    rec = _build_valid_record()
    rec["review_status"] = "ai_reviewed"
    rec["provenance"]["review_status"] = "ai_reviewed"
    rec["provenance"]["annotator_id"] = "ai_evidence_review_pass"
    rec["training_eligible"] = True
    report = validate_ml_dataset([rec])
    assert report.is_valid


