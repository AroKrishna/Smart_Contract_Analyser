"""
analysis/ml_dataset_validator.py - Validation and Data-Quality Tool for ML Dataset

Validates JSONL dataset records formatted for Legal-BERT multi-label training
against the Smart_Contract_Analyser specification.

Checks:
1. Required schema fields and valid label names.
2. Explicit statuses (positive, negative, insufficient_information).
3. Line range validity and code context integrity.
4. Model text presence for NLP / Legal-BERT consumption.
5. Exact code duplication and project/fork family clustering.
6. Data leakage prevention across splits (project isolation).
7. Split readiness assessment.
"""

from typing import Dict, Any, List, Tuple, Set
import hashlib
import json
import re

VALID_CATEGORIES = {
    "Privacy",
    "Termination",
    "Legal Compliance",
    "Liability",
    "Payment / Financial",
}

VALID_STATUSES = {
    "positive",
    "negative",
    "insufficient_information",
    "pending_review",
    "unresolved",
}

VALID_LICENSE_STATUSES = {
    "cleared",
    "license_review_required",
    "restricted_research_only",
}

VALID_SEVERITIES = {
    "critical",
    "high",
    "medium",
    "low",
    "info",
    "none",
}

VALID_REVIEW_STATUSES = {
    "draft",
    "in_review",
    "reviewed",
    "unresolved",
    "ai_reviewed",
    "ai_review_unresolved",
}

REQUIRED_ROOT_FIELDS = [
    "sample_id",
    "project_id",
    "contract_family",
    "source_repo_url",
    "commit_or_version",
    "compiler_version",
    "license",
    "collection_date",
    "contract_file",
    "function_name",
    "source_line_range",
    "solidity_context",
    "model_text",
    "categories",
    "source_labels",
    "provenance",
    "review_status",
    "unresolved_questions",
]

MIN_PROJECTS_FOR_SPLIT = 5


class DatasetValidationReport:
    def __init__(self):
        self.total_records = 0
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.split_counts: Dict[str, int] = {}
        self.project_counts: Dict[str, int] = {}
        self.project_splits: Dict[str, Set[str]] = {}
        self.seen_sample_ids: Set[str] = set()
        self.code_hashes: Dict[str, str] = {}  # hash -> sample_id
        self.split_ready: bool = False
        self.split_readiness_reason: str = ""

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0


def validate_ml_sample(
    sample: Dict[str, Any],
    idx: int,
    report: DatasetValidationReport,
) -> None:
    """Validates a single ML dataset record."""
    sid = sample.get("sample_id", f"record_{idx}")

    # 1. Required root fields
    for field in REQUIRED_ROOT_FIELDS:
        if field == "review_status":
            if "review_status" not in sample and ("provenance" not in sample or "review_status" not in sample.get("provenance", {})):
                report.errors.append(f"Record #{idx} ('{sid}') missing required field 'review_status'")
        elif field not in sample:
            report.errors.append(f"Record #{idx} ('{sid}') missing required field '{field}'")

    # 2. Duplicate sample_id
    if sid in report.seen_sample_ids:
        report.errors.append(f"Duplicate sample_id detected: '{sid}'")
    report.seen_sample_ids.add(sid)

    # 3. Provenance, license status, and metadata
    proj_id = sample.get("project_id")
    if not proj_id or str(proj_id).strip() in ("", "n/a", "unknown"):
        report.warnings.append(f"Sample '{sid}' has missing or unverified 'project_id'")
    else:
        report.project_counts[proj_id] = report.project_counts.get(proj_id, 0) + 1

    lic = sample.get("license")
    if not lic or str(lic).strip() in ("", "unknown"):
        report.warnings.append(f"Sample '{sid}' has empty or unverified license")

    lic_status = sample.get("license_status")
    if lic_status is not None and lic_status not in VALID_LICENSE_STATUSES:
        report.errors.append(
            f"Sample '{sid}' invalid license_status '{lic_status}'. Must be one of {sorted(VALID_LICENSE_STATUSES)}"
        )
    elif lic_status == "license_review_required":
        report.warnings.append(f"Sample '{sid}' flagged as license_review_required; excluded from training until cleared.")

    # 4. Review status and human provenance verification
    rev_status = sample.get("review_status")
    if rev_status is None and isinstance(sample.get("provenance"), dict):
        rev_status = sample["provenance"].get("review_status")

    if rev_status not in VALID_REVIEW_STATUSES:
        report.errors.append(
            f"Sample '{sid}' invalid review_status '{rev_status}'. Must be one of {sorted(VALID_REVIEW_STATUSES)}"
        )

    annotator = ""
    if isinstance(sample.get("provenance"), dict):
        annotator = str(sample["provenance"].get("annotator_id", "")).lower()

    if rev_status == "reviewed":
        if any(kw in annotator for kw in ["pipeline", "script", "machine", "ai", "bot", "auto"]):
            report.errors.append(
                f"Sample '{sid}' is marked 'reviewed' by machine/pipeline annotator '{annotator}'. "
                f"Only verified human reviewers may mark records as 'reviewed'."
            )

    # 5. Separation of source labels from project target categories
    src_labels = sample.get("source_labels", {})
    if not isinstance(src_labels, dict):
        report.errors.append(f"Sample '{sid}' 'source_labels' must be a dictionary")

    # 6. Line range validity
    line_range = sample.get("source_line_range")
    if line_range is not None:
        if not (isinstance(line_range, (list, tuple)) and len(line_range) == 2):
            report.errors.append(f"Sample '{sid}' source_line_range must be [start, end] or null")
        else:
            start, end = line_range
            if not (isinstance(start, int) and isinstance(end, int)):
                report.errors.append(f"Sample '{sid}' line numbers must be integers")
            elif start > end:
                report.errors.append(f"Sample '{sid}' invalid line range: start ({start}) > end ({end})")

    # 7. Model text (for Legal-BERT)
    model_text = sample.get("model_text")
    if not model_text or not isinstance(model_text, str) or len(model_text.strip()) == 0:
        report.errors.append(f"Sample '{sid}' missing non-empty 'model_text' for Legal-BERT")

    # 8. Categories validation and evidence requirements
    has_pending_categories = False
    cats = sample.get("categories", {})
    if not isinstance(cats, dict):
        report.errors.append(f"Sample '{sid}' 'categories' must be a dictionary")
    else:
        for cat_name, cat_data in cats.items():
            if cat_name not in VALID_CATEGORIES:
                report.errors.append(f"Sample '{sid}' contains unrecognized category '{cat_name}'")
                continue
            if not isinstance(cat_data, dict):
                report.errors.append(f"Sample '{sid}' category '{cat_name}' value must be an object")
                continue

            status = cat_data.get("status")
            if status not in VALID_STATUSES:
                report.errors.append(
                    f"Sample '{sid}' category '{cat_name}' status '{status}' invalid. Must be one of {sorted(VALID_STATUSES)}"
                )
            if status in ("pending_review", "insufficient_information", "unresolved"):
                has_pending_categories = True

            severity = cat_data.get("severity")
            if severity not in VALID_SEVERITIES:
                report.errors.append(
                    f"Sample '{sid}' category '{cat_name}' severity '{severity}' invalid. Must be one of {sorted(VALID_SEVERITIES)}"
                )

            # Rationale is required for positive and negative decisions
            if status == "positive":
                if not cat_data.get("evidence") or not str(cat_data.get("evidence")).strip():
                    report.errors.append(f"Sample '{sid}' category '{cat_name}' marked 'positive' without code-grounded evidence")
                if not cat_data.get("rationale") or not str(cat_data.get("rationale")).strip():
                    report.errors.append(f"Sample '{sid}' category '{cat_name}' marked 'positive' without rationale")
            elif status == "negative":
                if not cat_data.get("rationale") or not str(cat_data.get("rationale")).strip():
                    report.errors.append(f"Sample '{sid}' category '{cat_name}' marked 'negative' without verification rationale")

    # 9. Solidity context integrity and placeholder check
    code = sample.get("solidity_context", "")
    if not code or not isinstance(code, str) or len(code.strip()) < 30:
        report.errors.append(f"Sample '{sid}' has missing or excessively short 'solidity_context'")
    else:
        stripped_code = re.sub(r"//.*", "", code)
        stripped_code = re.sub(r"/\*.*?\*/", "", stripped_code, flags=re.DOTALL).strip()
        if len(stripped_code) < 15 or not any(kw in stripped_code for kw in ["function", "contract", "interface", "library", "event", "modifier", "struct", "enum", "mapping"]):
            report.errors.append(f"Sample '{sid}' contains placeholder-only comment in 'solidity_context' without real Solidity code")
        else:
            normalized_code = "".join(stripped_code.split())
            code_hash = hashlib.sha256(normalized_code.encode("utf-8")).hexdigest()
            if code_hash in report.code_hashes:
                report.warnings.append(
                    f"Duplicate code detected between sample '{sid}' and '{report.code_hashes[code_hash]}'"
                )
            else:
                report.code_hashes[code_hash] = sid

    # 10. Training eligibility and split tracking, leakage, and exclusion checks
    is_training_eligible = sample.get("training_eligible")
    if is_training_eligible is not None:
        if not isinstance(is_training_eligible, bool):
            report.errors.append(f"Sample '{sid}' 'training_eligible' must be a boolean")
        elif is_training_eligible:
            # Training eligible requires strict verification
            if rev_status not in ("reviewed", "ai_reviewed") or has_pending_categories:
                report.errors.append(
                    f"Sample '{sid}' cannot be training_eligible=True when review_status is '{rev_status}' "
                    f"or contains pending/insufficient categories."
                )
            if lic_status == "license_review_required":
                report.errors.append(
                    f"Sample '{sid}' cannot be training_eligible=True when license_status is 'license_review_required'."
                )
            if sample.get("source_status") in ("requires_source_revision", "commit_drift_unresolved"):
                report.errors.append(
                    f"Sample '{sid}' cannot be training_eligible=True with source_status '{sample.get('source_status')}'."
                )
        else:
            # If not eligible, split cannot be train/val/test
            if sample.get("split") in ("train", "validation", "test"):
                report.errors.append(
                    f"Sample '{sid}' marked training_eligible=False cannot be assigned to active split '{sample.get('split')}'."
                )
            if not sample.get("training_ineligibility_reason"):
                report.warnings.append(
                    f"Sample '{sid}' is training_eligible=False but missing 'training_ineligibility_reason'."
                )

    # 11. Model text review status check
    mt_review = sample.get("model_text_review")
    if isinstance(mt_review, dict):
        if not mt_review.get("human_verified") and "draft" not in model_text.lower() and "pending" not in model_text.lower():
            report.warnings.append(
                f"Sample '{sid}' model_text is not human_verified but lacks draft/pending notice in text."
            )

    # 12. Split tracking, leakage, and unreviewed/license exclusion checks
    split = sample.get("split")
    if split is not None:
        if split not in ("train", "validation", "test", "unassigned"):
            report.errors.append(f"Sample '{sid}' invalid split '{split}'")
        else:
            # Enforce that unreviewed, pending, or license-restricted records CANNOT be placed in active splits
            if split in ("train", "validation", "test"):
                if rev_status not in ("reviewed", "ai_reviewed") or has_pending_categories:
                    report.errors.append(
                        f"Sample '{sid}' cannot be assigned to active split '{split}' because review_status is "
                        f"'{rev_status}' and has_pending_categories={has_pending_categories}. Must be 'unassigned' until fully reviewed."
                    )
                if lic_status == "license_review_required":
                    report.errors.append(
                        f"Sample '{sid}' with license_status 'license_review_required' cannot be assigned to active split '{split}'."
                    )
            report.split_counts[split] = report.split_counts.get(split, 0) + 1
            if proj_id:
                if proj_id not in report.project_splits:
                    report.project_splits[proj_id] = set()
                report.project_splits[proj_id].add(split)


def validate_ml_dataset(records: List[Dict[str, Any]]) -> DatasetValidationReport:
    """Validates an entire list/iterable of dataset records."""
    report = DatasetValidationReport()
    report.total_records = len(records)

    for idx, record in enumerate(records):
        validate_ml_sample(record, idx, report)

    # Cross-record check: Project family leakage across splits
    for proj_id, splits in report.project_splits.items():
        active_splits = splits - {"unassigned"}
        if len(active_splits) > 1:
            report.errors.append(
                f"Data Leakage Detected: Project '{proj_id}' spans multiple splits: {sorted(active_splits)}. "
                f"All contracts from the same project must reside in the same split."
            )

    # Split readiness evaluation
    distinct_projects = len(report.project_counts)
    if report.total_records < 20 or distinct_projects < MIN_PROJECTS_FOR_SPLIT:
        report.split_ready = False
        report.split_readiness_reason = (
            f"Split is NOT READY: dataset contains only {report.total_records} records across "
            f"{distinct_projects} distinct project(s). Minimum requirement is {MIN_PROJECTS_FOR_SPLIT} "
            f"independently reviewed projects to construct train/validation/test splits without leakage."
        )
    else:
        assigned = sum(report.split_counts.get(s, 0) for s in ("train", "validation", "test"))
        if assigned == 0:
            report.split_ready = False
            report.split_readiness_reason = "Split is NOT READY: all records are unassigned pending human review."
        else:
            report.split_ready = True
            report.split_readiness_reason = "Split criteria met."

    return report


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        target_path = sys.argv[1]
        records = []
        if target_path.endswith(".jsonl"):
            with open(target_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        records.append(json.loads(line))
        elif target_path.endswith(".json"):
            with open(target_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                records = loaded if isinstance(loaded, list) else [loaded]

        rep = validate_ml_dataset(records)
        print(f"Validation finished. Total records: {rep.total_records}")
        print(f"Is Valid: {rep.is_valid}")
        print(f"Split Ready: {rep.split_ready} ({rep.split_readiness_reason})")
        if rep.errors:
            print(f"Errors ({len(rep.errors)}):")
            for e in rep.errors[:10]:
                print(f"  - {e}")
        if rep.warnings:
            print(f"Warnings ({len(rep.warnings)}):")
            for w in rep.warnings[:10]:
                print(f"  - {w}")
