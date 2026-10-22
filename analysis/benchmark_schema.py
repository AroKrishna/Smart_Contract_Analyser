"""
analysis/benchmark_schema.py - Schema and Validation for Benchmark Dataset

Defines the ground-truth benchmark contract record, tracking provenance,
licensing, splits, and labeled operational risk findings.
"""

from typing import Dict, Any, List

def validate_benchmark_manifest(data: Dict[str, Any]) -> tuple[bool, List[str]]:
    """Validates the benchmark manifest against the expected specification."""
    errors = []
    
    if "benchmark_version" not in data:
        errors.append("Missing 'benchmark_version'")
    if "samples" not in data or not isinstance(data["samples"], list):
        errors.append("Missing or invalid 'samples' list")
        return False, errors

    required_fields = [
        "sample_id", "project_name", "contract_file", "source_url",
        "license", "collection_date", "split", "labels"
    ]

    seen_ids = set()
    project_splits: Dict[str, str] = {}

    for idx, sample in enumerate(data["samples"]):
        for f in required_fields:
            if f not in sample:
                errors.append(f"Sample #{idx} missing field '{f}'")

        sid = sample.get("sample_id")
        if sid in seen_ids:
            errors.append(f"Duplicate sample_id: '{sid}'")
        seen_ids.add(sid)

        split = sample.get("split")
        if split not in ("dev", "train", "validation", "test"):
            errors.append(f"Sample '{sid}' has invalid split '{split}'")

        # Check for project leakage across splits
        proj = sample.get("project_name")
        if proj:
            if proj in project_splits and project_splits[proj] != split:
                errors.append(
                    f"Data Leakage Detected: Project '{proj}' appears in multiple splits "
                    f"('{project_splits[proj]}' and '{split}'). All contracts from the same project must share one split."
                )
            project_splits[proj] = split

        # Validate labels
        labels = sample.get("labels", [])
        if not isinstance(labels, list):
            errors.append(f"Sample '{sid}' labels must be a list")
        else:
            for l_idx, lbl in enumerate(labels):
                if "rule_id" not in lbl or "expected_trigger" not in lbl:
                    errors.append(f"Sample '{sid}' label #{l_idx} missing 'rule_id' or 'expected_trigger'")

    return len(errors) == 0, errors
