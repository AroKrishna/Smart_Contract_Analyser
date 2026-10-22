"""
analysis/evaluate.py - Honest Evaluation Pipeline for Deterministic Baseline

Validates the benchmark manifest, runs the AnalysisEngine against benchmark contracts,
and calculates per-rule and per-category TP, FP, FN, TN, Support, Precision, Recall, and F1.
Properly handles zero-support cases without fabricating 1.0 scores.
"""

import os
import json
from collections import defaultdict
from typing import Dict, Any, Optional

from analysis.engine import AnalysisEngine
from analysis.benchmark_schema import validate_benchmark_manifest

def run_evaluation(manifest_path: str, contracts_dir: str, target_split: Optional[str] = None) -> Dict[str, Any]:
    if not os.path.exists(manifest_path):
        return {
            "status": "blocked",
            "reason": f"Manifest file not found at {manifest_path}"
        }

    with open(manifest_path, "r", encoding="utf-8-sig") as f:
        manifest = json.load(f)

    is_valid, validation_errors = validate_benchmark_manifest(manifest)
    if not is_valid:
        return {
            "status": "blocked",
            "reason": f"Benchmark manifest validation failed: {validation_errors}"
        }

    raw_samples = manifest.get("samples", [])
    if not raw_samples:
        return {
            "status": "blocked",
            "reason": "Benchmark manifest contains zero samples. Labeled data is missing."
        }

    # Filter by split if specified
    if target_split:
        samples = [s for s in raw_samples if s.get("split") == target_split]
        if not samples:
            return {
                "status": "blocked",
                "reason": f"Zero samples found for target split '{target_split}'."
            }
    else:
        samples = raw_samples

    engine = AnalysisEngine()

    rule_metrics = defaultdict(lambda: {"TP": 0, "FP": 0, "FN": 0, "TN": 0})
    category_metrics = defaultdict(lambda: {"TP": 0, "FP": 0, "FN": 0, "TN": 0})
    sample_results = []
    split_counts = defaultdict(int)

    for sample in samples:
        split_counts[sample.get("split", "unknown")] += 1
        c_file = os.path.join(contracts_dir, sample["contract_file"])
        if not os.path.exists(c_file):
            print(f"[WARN] Contract file missing: {c_file}")
            continue

        with open(c_file, "r", encoding="utf-8-sig") as f:
            source = f.read()

        result = engine.analyze_source(source, contract_name=sample["sample_id"])
        detected_rule_ids = {f.get("ruleId") for f in result["findings"] if f.get("ruleId")}

        sample_eval = {
            "sample_id": sample["sample_id"],
            "contract": sample["contract_file"],
            "split": sample["split"],
            "risk_score": result["riskScore"],
            "risk_level": result["riskLevel"],
            "rule_checks": []
        }

        for label in sample.get("labels", []):
            rid = label["rule_id"]
            cat = label["category"]
            expected = label["expected_trigger"]
            actual = rid in detected_rule_ids

            if expected and actual:
                rule_metrics[rid]["TP"] += 1
                category_metrics[cat]["TP"] += 1
            elif not expected and actual:
                rule_metrics[rid]["FP"] += 1
                category_metrics[cat]["FP"] += 1
            elif expected and not actual:
                rule_metrics[rid]["FN"] += 1
                category_metrics[cat]["FN"] += 1
            else:
                rule_metrics[rid]["TN"] += 1
                category_metrics[cat]["TN"] += 1

            sample_eval["rule_checks"].append({
                "rule_id": rid,
                "category": cat,
                "expected": expected,
                "actual": actual,
                "match": expected == actual
            })

        sample_results.append(sample_eval)

    def calc_scores(counts):
        tp, fp, fn, tn = counts["TP"], counts["FP"], counts["FN"], counts["TN"]
        support = tp + fn  # Total ground-truth positive instances
        total_evals = tp + fp + fn + tn

        # Precision is undefined if no positive predictions occurred (tp + fp == 0)
        prec = round(tp / (tp + fp), 3) if (tp + fp) > 0 else None

        # Recall is undefined if no actual positive instances exist in ground truth (support == 0)
        rec = round(tp / (tp + fn), 3) if support > 0 else None

        # F1 is undefined if precision or recall is undefined, or prec + rec == 0
        if prec is not None and rec is not None and (prec + rec) > 0:
            f1 = round(2 * prec * rec / (prec + rec), 3)
        else:
            f1 = None

        return {
            "TP": tp,
            "FP": fp,
            "FN": fn,
            "TN": tn,
            "support": support,
            "total_evaluations": total_evals,
            "precision": prec,
            "recall": rec,
            "f1": f1,
            "metric_status": "EVALUATED" if support > 0 else "ZERO_POSITIVE_SUPPORT_UNDEFINED"
        }

    formatted_rule_metrics = {r: calc_scores(c) for r, c in sorted(rule_metrics.items())}
    formatted_cat_metrics = {cat: calc_scores(c) for cat, c in sorted(category_metrics.items())}

    return {
        "status": "completed",
        "benchmark_version": manifest["benchmark_version"],
        "evaluated_split": target_split or "all_splits",
        "split_counts": dict(split_counts),
        "total_samples": len(sample_results),
        "rule_metrics": formatted_rule_metrics,
        "category_metrics": formatted_cat_metrics,
        "sample_results": sample_results
    }

if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else None
    manifest_p = os.path.join(os.path.dirname(__file__), "data", "benchmark", "benchmark_manifest.json")
    contracts_d = os.path.join(os.path.dirname(__file__), "data", "contracts")
    res = run_evaluation(manifest_p, contracts_d, target_split=target)
    print(json.dumps(res, indent=2))
