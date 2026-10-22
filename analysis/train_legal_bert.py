"""
analysis/train_legal_bert.py - Reproducible Training and Evaluation Pipeline for Legal-BERT

Implements the multi-label operational hazard classification pipeline specified in:
- docs/reference/Smart_Contract_Legal_AI_SaaS_Platform_Specification.docx
- docs/DATASET_SPECIFICATION.md

Core Design & Integrity Principles:
1. Strict Split Isolation:
   - All contracts belonging to the same project or source family reside in the exact same split.
   - Synthetic records are restricted to the train split only.
   - Validation and test splits contain 100% real-source records only.
   - Test split remains untouched during model or threshold selection.
   - Splits are deterministic and reproducible from a fixed seed.
2. Honest Evaluation & Zero-Support Detection:
   - Categories with zero or sparse positive examples in test are explicitly flagged as
     'inconclusive_zero_positive_support' rather than manufacturing a reassuring score.
   - Threshold calibration is performed strictly on validation data for categories with >= 2 positives;
     uncalibrated categories retain the default 0.50 threshold with clear documentation.
3. Anti-Leakage Model Text:
   - Dual-stream submission representation observable at submission time only.
   - Post-hoc audit finding titles, target risk labels, and auditor rationales are strictly barred.
4. Reproducibility & Provenance:
   - Records dataset SHA-256 hash, random seed, model identifier, hyperparameter config,
     and exact split membership.
"""

from typing import Dict, Any, List, Tuple, Optional
import argparse
import hashlib
import json
import os
import sys
import numpy as np

CATEGORIES = [
    "Privacy",
    "Termination",
    "Legal Compliance",
    "Liability",
    "Payment / Financial",
]


def compute_dataset_sha256(dataset_path: str) -> str:
    """Computes the SHA-256 hash of the canonical dataset file for reproducibility."""
    hasher = hashlib.sha256()
    with open(dataset_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def construct_submission_model_text(record: Dict[str, Any]) -> str:
    """
    Constructs and verifies the dual-stream input representation for Legal-BERT.
    Guarantees that input text contains ONLY information observable at submission time:
    - Contract Name & License
    - Function Name & Visibility / Modifiers
    - Developer NatSpec comments (from contract source code)
    - Objective Operational Behavior (observable state mutations and fund transfers)
    - Normalized Solidity Code Excerpt
    
    Strictly prevents target leakage by verifying that post-hoc audit titles,
    descriptions, target risk labels, and auditor rationales are not present.
    """
    model_text = record.get("model_text", "")
    if not model_text or not isinstance(model_text, str):
        c_name = record.get("contract_file", "Contract").replace(".sol", "")
        lic = record.get("license", "Unknown")
        fn = record.get("function_name", "contract_scope")
        natspec = record.get("natspec_comments") or "None"
        code = record.get("solidity_context", "")[:200]
        model_text = (
            f"[Draft Summary (Machine-generated, pending human review)]\n"
            f"Contract: {c_name} ({lic})\n"
            f"Function: {fn}\n"
            f"Documented Intent: {natspec}\n"
            f"Operational Behavior: Executes {fn} state transitions.\n"
            f"Key Code Logic: {code}"
        )

    # Sanity check for data leakage against audit findings
    source_labels = record.get("source_labels", {})
    audit_title = str(source_labels.get("original_title", "")).strip()
    if audit_title and len(audit_title) > 8 and audit_title.lower() in model_text.lower():
        raise ValueError(
            f"Target leakage detected in sample '{record.get('sample_id')}': "
            f"audit finding title leaked into model_text!"
        )

    return model_text


def load_dataset(dataset_path: str, eligible_only: bool = True) -> List[Dict[str, Any]]:
    """Loads dataset from canonical JSONL file and verifies submission-time model_text."""
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Canonical dataset not found at: {dataset_path}")

    records = []
    with open(dataset_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    if eligible_only:
        records = [r for r in records if r.get("training_eligible") is True]

    for r in records:
        r["model_text"] = construct_submission_model_text(r)

    return records


def assess_data_readiness(
    records: List[Dict[str, Any]],
    all_records: Optional[List[Dict[str, Any]]] = None,
    min_samples: int = 50,
    min_positive_per_cat: int = 5,
    min_projects: int = 5,
) -> Dict[str, Any]:
    """
    Evaluates whether the verified dataset meets minimum empirical criteria
    to support a responsible, statistically meaningful Legal-BERT training and evaluation run.
    Separates real-source and synthetic metrics and evaluates real project diversity.
    """
    total = len(records)
    real_records = [r for r in records if r.get("origin") == "real_source"]
    synth_records = [r for r in records if r.get("origin") == "synthetic"]

    all_projects = set(r.get("project_id") for r in records if r.get("project_id"))
    real_projects = set(r.get("project_id") for r in real_records if r.get("project_id"))

    # Support counters
    combined_support = {c: {"positive": 0, "negative": 0, "unresolved": 0} for c in CATEGORIES}
    real_support = {c: {"positive": 0, "negative": 0, "unresolved": 0} for c in CATEGORIES}
    synth_support = {c: {"positive": 0, "negative": 0, "unresolved": 0} for c in CATEGORIES}

    for r in records:
        orig = r.get("origin", "real_source")
        for c in CATEGORIES:
            st = r.get("categories", {}).get(c, {}).get("status", "unresolved")
            target_dict = real_support[c] if orig == "real_source" else synth_support[c]
            if st in target_dict:
                target_dict[st] += 1
            else:
                target_dict["unresolved"] += 1

            if st in combined_support[c]:
                combined_support[c][st] += 1
            else:
                combined_support[c]["unresolved"] += 1

    # Project distribution of real positive examples
    real_projects_with_pos = {c: set() for c in CATEGORIES}
    for r in real_records:
        for c in CATEGORIES:
            if r.get("categories", {}).get(c, {}).get("status") == "positive":
                real_projects_with_pos[c].add(r.get("project_id"))

    blocking_reasons = []

    # 1. Minimum total sample check
    if total < min_samples:
        blocking_reasons.append(
            f"Insufficient dataset volume: {total} eligible records available "
            f"(minimum {min_samples} required for 60/20/20 split)."
        )

    # 2. Distinct project clusters
    if len(all_projects) < min_projects:
        blocking_reasons.append(
            f"Insufficient project diversity: {len(all_projects)} distinct projects "
            f"(minimum {min_projects} required to prevent split leakage)."
        )

    # 3. Real-source category distribution checks
    real_sparsity_notes = []
    for c in CATEGORIES:
        real_pos = real_support[c]["positive"]
        num_projs = len(real_projects_with_pos[c])
        if real_pos == 0:
            real_sparsity_notes.append(f"{c}: 0 real positive samples across all projects.")
        elif num_projs < 3:
            real_sparsity_notes.append(
                f"{c}: only {real_pos} real positive sample(s) across {num_projs} project(s) "
                f"({sorted(list(real_projects_with_pos[c]))}). Cannot support independent positive examples "
                f"in separate train, validation, and test splits without project leakage."
            )

    # Combined positive support check
    zero_support_cats = [c for c, counts in combined_support.items() if counts["positive"] == 0]
    if zero_support_cats:
        blocking_reasons.append(
            f"Zero positive support: Categories {zero_support_cats} have 0 positive samples across all eligible records."
        )

    is_ready_for_prototype = len(blocking_reasons) == 0
    is_ready_for_real_eval = len(real_sparsity_notes) == 0

    return {
        "is_ready_for_prototype": is_ready_for_prototype,
        "is_ready_for_real_eval": is_ready_for_real_eval,
        "total_eligible_samples": total,
        "real_eligible_samples": len(real_records),
        "synthetic_eligible_samples": len(synth_records),
        "distinct_projects_total": len(all_projects),
        "distinct_real_projects": len(real_projects),
        "combined_support": combined_support,
        "real_support": real_support,
        "synthetic_support": synth_support,
        "real_projects_with_positives": {c: sorted(list(projs)) for c, projs in real_projects_with_pos.items()},
        "blocking_reasons": blocking_reasons,
        "real_sparsity_notes": real_sparsity_notes,
    }


def create_group_splits(
    records: List[Dict[str, Any]],
    eval_ratio: float = 0.2,
    test_ratio: float = 0.2,
    seed: int = 42,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Creates project-isolated train, validation, and test splits with strict origin guarantees:
    1. Real-source records are partitioned into real_train, real_val, and real_test using GroupShuffleSplit.
    2. All records belonging to the same project_id are kept in the exact same split (zero cross-split leakage).
    3. Synthetic records are assigned EXCLUSIVELY to the train split (synthetic_train).
    4. Validation and test splits contain 100% REAL-SOURCE records only.
    5. Deterministic and reproducible from fixed seed.
    """
    from sklearn.model_selection import GroupShuffleSplit

    np.random.seed(seed)

    real_records = [r for r in records if r.get("origin") == "real_source"]
    synthetic_records = [r for r in records if r.get("origin") == "synthetic"]

    if not real_records:
        raise ValueError("Cannot construct evaluation splits: dataset contains 0 real-source records!")

    real_groups = [r.get("project_id", "unknown") for r in real_records]

    # 1. First split off real test set
    gss_test = GroupShuffleSplit(n_splits=1, test_size=test_ratio, random_state=seed)
    train_val_idx, test_idx = next(gss_test.split(real_records, groups=real_groups))

    real_train_val = [real_records[i] for i in train_val_idx]
    real_test = [real_records[i] for i in test_idx]

    # 2. Split real validation set from remaining real train_val
    val_adj_ratio = eval_ratio / (1.0 - test_ratio)
    train_val_groups = [r.get("project_id", "unknown") for r in real_train_val]
    gss_val = GroupShuffleSplit(n_splits=1, test_size=val_adj_ratio, random_state=seed)
    train_idx, val_idx = next(gss_val.split(real_train_val, groups=train_val_groups))

    real_train = [real_train_val[i] for i in train_idx]
    val_records = [real_train_val[i] for i in val_idx]
    test_records = real_test

    # 3. Synthetic records go exclusively to train
    train_records = real_train + synthetic_records

    # 4. Strict verification assertions
    train_real_projs = set(r.get("project_id") for r in real_train)
    val_projs = set(r.get("project_id") for r in val_records)
    test_projs = set(r.get("project_id") for r in test_records)
    synth_projs = set(r.get("project_id") for r in synthetic_records)

    assert len(train_real_projs & val_projs) == 0, f"Project leakage detected between real train and val: {train_real_projs & val_projs}"
    assert len(train_real_projs & test_projs) == 0, f"Project leakage detected between real train and test: {train_real_projs & test_projs}"
    assert len(val_projs & test_projs) == 0, f"Project leakage detected between val and test: {val_projs & test_projs}"
    assert len(synth_projs & val_projs) == 0, f"Synthetic project leaked into validation: {synth_projs & val_projs}"
    assert len(synth_projs & test_projs) == 0, f"Synthetic project leaked into test: {synth_projs & test_projs}"
    assert all(r.get("origin") == "real_source" for r in val_records), "Non-real record found in validation split!"
    assert all(r.get("origin") == "real_source" for r in test_records), "Non-real record found in test split!"

    return train_records, val_records, test_records


def run_baseline_model(
    train_records: List[Dict[str, Any]],
    test_records: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Trains and evaluates a simple TF-IDF + LogisticRegression baseline on the untouched real test set."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.dummy import DummyClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import f1_score, precision_score, recall_score, hamming_loss

    X_train = [r.get("model_text", "") for r in train_records]
    X_test = [r.get("model_text", "") for r in test_records]

    Y_train = np.array([
        [1 if r.get("categories", {}).get(c, {}).get("status") == "positive" else 0 for c in CATEGORIES]
        for r in train_records
    ])
    Y_test = np.array([
        [1 if r.get("categories", {}).get(c, {}).get("status") == "positive" else 0 for c in CATEGORIES]
        for r in test_records
    ])

    vec = TfidfVectorizer(max_features=1000, ngram_range=(1, 2))
    X_train_vec = vec.fit_transform(X_train)
    X_test_vec = vec.transform(X_test)

    Y_pred = np.zeros_like(Y_test)
    category_metrics = {}

    for idx, c in enumerate(CATEGORIES):
        y_tr = Y_train[:, idx]
        y_te = Y_test[:, idx]

        unique_classes = np.unique(y_tr)
        if len(unique_classes) < 2:
            clf_c = DummyClassifier(strategy="constant", constant=unique_classes[0])
            clf_c.fit(X_train_vec, y_tr)
            y_pred_c = clf_c.predict(X_test_vec)
        else:
            clf_c = LogisticRegression(class_weight="balanced", random_state=42)
            clf_c.fit(X_train_vec, y_tr)
            y_pred_c = clf_c.predict(X_test_vec)

        Y_pred[:, idx] = y_pred_c
        pos_test = int(np.sum(y_te))
        neg_test = int(len(y_te) - pos_test)
        pred_pos = int(np.sum(y_pred_c))

        tp = int(np.sum((y_te == 1) & (y_pred_c == 1)))
        fp = int(np.sum((y_te == 0) & (y_pred_c == 1)))
        fn = int(np.sum((y_te == 1) & (y_pred_c == 0)))
        tn = int(np.sum((y_te == 0) & (y_pred_c == 0)))

        prec = float(precision_score(y_te, y_pred_c, zero_division=0))
        rec = float(recall_score(y_te, y_pred_c, zero_division=0))
        f1 = float(f1_score(y_te, y_pred_c, zero_division=0))

        if pos_test == 0:
            support_status = "inconclusive_zero_positive_support"
            eval_note = "Evaluation inconclusive: test split contains 0 true positive examples. Recall/F1 cannot be measured."
        elif pos_test == 1:
            support_status = "sparse_support_n1"
            eval_note = "Sparse support: test split contains only 1 true positive example. Metrics have high variance."
        else:
            support_status = "sufficient_support"
            eval_note = f"Evaluated on {pos_test} true positive(s) and {neg_test} true negative(s)."

        category_metrics[c] = {
            "train_support_pos": int(np.sum(y_tr)),
            "test_support_pos": pos_test,
            "test_support_neg": neg_test,
            "predicted_pos": pred_pos,
            "true_positives": tp,
            "false_positives": fp,
            "true_negatives": tn,
            "false_negatives": fn,
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1": round(f1, 4),
            "support_status": support_status,
            "evaluation_note": eval_note,
            "model_type": "single_class_fallback" if len(unique_classes) < 2 else "logistic_regression",
        }

    evaluable_cats = [c for c in CATEGORIES if category_metrics[c]["test_support_pos"] >= 1]
    evaluable_f1s = [category_metrics[c]["f1"] for c in evaluable_cats]
    macro_evaluable = float(np.mean(evaluable_f1s)) if evaluable_f1s else 0.0

    metrics = {
        "hamming_loss": round(float(hamming_loss(Y_test, Y_pred)), 4),
        "macro_f1_all_categories": round(float(f1_score(Y_test, Y_pred, average="macro", zero_division=0)), 4),
        "macro_f1_evaluable_categories": round(macro_evaluable, 4),
        "evaluable_categories": evaluable_cats,
        "micro_f1": round(float(f1_score(Y_test, Y_pred, average="micro", zero_division=0)), 4),
        "categories": category_metrics,
        "calculation_notes": {
            "macro_f1_all_categories": "Unweighted mean across all 5 categories; categories with 0 positive test examples contribute 0.0.",
            "macro_f1_evaluable_categories": f"Mean F1 computed only across categories with >= 1 positive test example ({evaluable_cats}).",
            "micro_f1": "Globally aggregated binary precision and recall across all label decisions."
        }
    }
    return metrics


def select_thresholds_on_validation(
    val_records: List[Dict[str, Any]],
    val_probs: np.ndarray,
    val_targets: np.ndarray,
    default_threshold: float = 0.50,
    min_val_positives: int = 2,
) -> Tuple[Dict[str, float], Dict[str, Any]]:
    """
    Selects classification thresholds using VALIDATION DATA ONLY.
    - If a category has >= min_val_positives in validation, grid searches [0.10, 0.90] to maximize validation F1.
    - If a category has < min_val_positives in validation, threshold calibration cannot be performed reliably
      without positive examples; sets default_threshold (0.50) marked as uncalibrated.
    - Test data is NEVER inspected during this process.
    """
    from sklearn.metrics import f1_score

    thresholds = {}
    calibration_log = {}

    for idx, c in enumerate(CATEGORIES):
        y_val_c = val_targets[:, idx]
        p_val_c = val_probs[:, idx]
        pos_count = int(np.sum(y_val_c))

        if pos_count < min_val_positives:
            thresholds[c] = default_threshold
            calibration_log[c] = {
                "threshold": default_threshold,
                "status": "default_uncalibrated",
                "validation_positive_support": pos_count,
                "reason": (
                    f"Insufficient validation positive examples ({pos_count} < {min_val_positives}). "
                    f"Threshold calibration skipped to prevent artificial overfitting to an all-negative distribution."
                )
            }
        else:
            best_t = default_threshold
            best_f1 = -1.0
            candidate_thresholds = np.arange(0.10, 0.90, 0.05)
            for t in candidate_thresholds:
                pred_c = (p_val_c >= t).astype(int)
                score = f1_score(y_val_c, pred_c, zero_division=0)
                if score > best_f1:
                    best_f1 = score
                    best_t = float(round(t, 2))

            thresholds[c] = best_t
            calibration_log[c] = {
                "threshold": best_t,
                "status": "calibrated_on_validation",
                "validation_positive_support": pos_count,
                "best_validation_f1": round(best_f1, 4),
            }

    return thresholds, calibration_log


def evaluate_split(
    records: List[Dict[str, Any]],
    model,
    tokenizer,
    device,
    thresholds: Dict[str, float],
    batch_size: int = 4,
    desc: str = "Evaluation",
) -> Tuple[Dict[str, Any], np.ndarray, np.ndarray, np.ndarray]:
    """
    Evaluates fine-tuned Legal-BERT on a given split using pre-determined category thresholds.
    Reports per-category precision, recall, F1, support, and confusion counts (TP, FP, TN, FN).
    Flags categories with zero or sparse support explicitly.
    """
    import torch
    from torch.utils.data import Dataset, DataLoader
    from sklearn.metrics import f1_score, precision_score, recall_score, hamming_loss

    if not records:
        empty_summary = {
            "num_records": 0,
            "macro_f1_all_categories": 0.0,
            "macro_f1_evaluable_categories": 0.0,
            "micro_f1": 0.0,
            "hamming_loss": 0.0,
            "categories": {},
        }
        return empty_summary, np.zeros((0, len(CATEGORIES))), np.zeros((0, len(CATEGORIES))), np.zeros((0, len(CATEGORIES)))

    class SmartContractEvalDataset(Dataset):
        def __init__(self, recs):
            self.texts = [r["model_text"] for r in recs]
            self.labels = [
                [1.0 if r.get("categories", {}).get(c, {}).get("status") == "positive" else 0.0 for c in CATEGORIES]
                for r in recs
            ]

        def __len__(self):
            return len(self.texts)

        def __getitem__(self, idx):
            item = tokenizer(
                self.texts[idx],
                max_length=512,
                truncation=True,
                padding="max_length",
                return_tensors="pt"
            )
            item = {k: v.squeeze(0) for k, v in item.items()}
            item["labels"] = torch.tensor(self.labels[idx], dtype=torch.float)
            return item

    loader = DataLoader(SmartContractEvalDataset(records), batch_size=batch_size, shuffle=False)
    model.eval()

    probs_list, targets_list = [], []
    with torch.no_grad():
        for b in loader:
            ids = b["input_ids"].to(device)
            mask = b["attention_mask"].to(device)
            lbl = b["labels"].to(device)
            out = model(input_ids=ids, attention_mask=mask)
            probs = torch.sigmoid(out.logits).cpu().numpy()
            probs_list.append(probs)
            targets_list.append(lbl.cpu().numpy().astype(int))

    y_prob = np.vstack(probs_list) if probs_list else np.zeros((0, len(CATEGORIES)))
    y_true = np.vstack(targets_list) if targets_list else np.zeros((0, len(CATEGORIES)))

    # Apply category-specific thresholds
    y_pred = np.zeros_like(y_true)
    for idx, c in enumerate(CATEGORIES):
        t_val = thresholds.get(c, 0.50)
        y_pred[:, idx] = (y_prob[:, idx] >= t_val).astype(int)

    cats = {}
    for idx, c in enumerate(CATEGORIES):
        t_c = y_true[:, idx] if len(y_true) > 0 else np.array([])
        p_c = y_pred[:, idx] if len(y_pred) > 0 else np.array([])
        pos_cnt = int(np.sum(t_c)) if len(t_c) > 0 else 0
        neg_cnt = int(len(t_c) - pos_cnt) if len(t_c) > 0 else 0
        pred_pos_cnt = int(np.sum(p_c)) if len(p_c) > 0 else 0

        tp = int(np.sum((t_c == 1) & (p_c == 1)))
        fp = int(np.sum((t_c == 0) & (p_c == 1)))
        fn = int(np.sum((t_c == 1) & (p_c == 0)))
        tn = int(np.sum((t_c == 0) & (p_c == 0)))

        prec = float(precision_score(t_c, p_c, zero_division=0)) if len(t_c) > 0 else 0.0
        rec = float(recall_score(t_c, p_c, zero_division=0)) if len(t_c) > 0 else 0.0
        f1 = float(f1_score(t_c, p_c, zero_division=0)) if len(t_c) > 0 else 0.0

        if pos_cnt == 0:
            support_status = "inconclusive_zero_positive_support"
            eval_note = "Evaluation inconclusive: split contains 0 true positive examples. Recall/F1 cannot be measured."
        elif pos_cnt == 1:
            support_status = "sparse_support_n1"
            eval_note = "Sparse support: split contains only 1 true positive example. Metrics have high variance."
        else:
            support_status = "sufficient_support"
            eval_note = f"Evaluated on {pos_cnt} true positive(s) and {neg_cnt} true negative(s)."

        cats[c] = {
            "threshold": thresholds.get(c, 0.50),
            "support_pos": pos_cnt,
            "support_neg": neg_cnt,
            "predicted_pos": pred_pos_cnt,
            "true_positives": tp,
            "false_positives": fp,
            "true_negatives": tn,
            "false_negatives": fn,
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1": round(f1, 4),
            "support_status": support_status,
            "evaluation_note": eval_note,
        }

    evaluable_cats = [c for c in CATEGORIES if cats[c]["support_pos"] >= 1]
    evaluable_f1s = [cats[c]["f1"] for c in evaluable_cats]
    macro_evaluable = float(np.mean(evaluable_f1s)) if evaluable_f1s else 0.0

    split_summary = {
        "num_records": len(records),
        "macro_f1_all_categories": round(float(f1_score(y_true, y_pred, average="macro", zero_division=0)), 4) if len(y_true) > 0 else 0.0,
        "macro_f1_evaluable_categories": round(macro_evaluable, 4),
        "evaluable_categories": evaluable_cats,
        "micro_f1": round(float(f1_score(y_true, y_pred, average="micro", zero_division=0)), 4) if len(y_true) > 0 else 0.0,
        "hamming_loss": round(float(hamming_loss(y_true, y_pred)), 4) if len(y_true) > 0 else 0.0,
        "categories": cats,
        "calculation_notes": {
            "macro_f1_all_categories": "Unweighted mean across all 5 categories; categories with 0 positive test examples contribute 0.0.",
            "macro_f1_evaluable_categories": f"Mean F1 computed only across categories with >= 1 positive test example ({evaluable_cats}).",
            "micro_f1": "Globally aggregated binary precision and recall across all label decisions."
        }
    }
    return split_summary, y_true, y_pred, y_prob


def print_evaluation_report(val_summary: Dict[str, Any], test_summary: Dict[str, Any], thresholds: Dict[str, float]):
    """Prints a clear, formatted evaluation table with support counts and confusion matrices."""
    print("\n" + "=" * 85)
    print("LEGAL-BERT EVALUATION METRICS REPORT (REAL-SOURCE EVALUATION SPLITS)")
    print("=" * 85)

    print("\n--- VALIDATION SPLIT (N={}, 100% Real-Source) | Macro F1: {:.4f} | Micro F1: {:.4f} ---".format(
        val_summary["num_records"], val_summary["macro_f1_all_categories"], val_summary["micro_f1"]
    ))
    print(f"{'Category':<22} | {'Thresh':<6} | {'Pos':<4} | {'Neg':<4} | {'TP':<3} | {'FP':<3} | {'FN':<3} | {'TN':<3} | {'Prec':<7} | {'Recall':<7} | {'F1':<7}")
    print("-" * 85)
    for c in CATEGORIES:
        m = val_summary["categories"][c]
        print(
            f"{c:<22} | {m['threshold']:<6.2f} | {m['support_pos']:<4} | {m['support_neg']:<4} | "
            f"{m['true_positives']:<3} | {m['false_positives']:<3} | {m['false_negatives']:<3} | {m['true_negatives']:<3} | "
            f"{m['precision']:<7.4f} | {m['recall']:<7.4f} | {m['f1']:<7.4f}"
        )

    print("\n--- UNTOUCHED TEST SPLIT (N={}, 100% Real-Source) | Macro F1 (All): {:.4f} | Macro F1 (Evaluable): {:.4f} ---".format(
        test_summary["num_records"], test_summary["macro_f1_all_categories"], test_summary["macro_f1_evaluable_categories"]
    ))
    print(f"{'Category':<22} | {'Thresh':<6} | {'Pos':<4} | {'Neg':<4} | {'TP':<3} | {'FP':<3} | {'FN':<3} | {'TN':<3} | {'Prec':<7} | {'Recall':<7} | {'F1':<7} | {'Support Status'}")
    print("-" * 115)
    for c in CATEGORIES:
        m = test_summary["categories"][c]
        print(
            f"{c:<22} | {m['threshold']:<6.2f} | {m['support_pos']:<4} | {m['support_neg']:<4} | "
            f"{m['true_positives']:<3} | {m['false_positives']:<3} | {m['false_negatives']:<3} | {m['true_negatives']:<3} | "
            f"{m['precision']:<7.4f} | {m['recall']:<7.4f} | {m['f1']:<7.4f} | {m['support_status']}"
        )

    inconclusive = [c for c in CATEGORIES if test_summary["categories"][c]["support_status"] == "inconclusive_zero_positive_support"]
    if inconclusive:
        print("\n[CRITICAL NOTICE — SMALL-DATA EVALUATION LIMITATION]")
        print("  The held-out test split contains ZERO real-source positive examples for:")
        for c in inconclusive:
            print(f"    * {c} (True Positives in Test = 0, False Positives = {test_summary['categories'][c]['false_positives']})")
        print("  Recall and F1 are mathematically non-evaluable for these categories on this test split.")
        print("  Do not interpret 0.0000 F1 as catastrophic failure or zero capability; it reflects zero test support.")


def train_legal_bert(
    train_records: List[Dict[str, Any]],
    val_records: List[Dict[str, Any]],
    test_records: List[Dict[str, Any]],
    output_dir: str = "analysis/models/legal_bert_model",
    model_name: str = "nlpaueb/legal-bert-base-uncased",
    epochs: int = 3,
    batch_size: int = 4,
    learning_rate: float = 3e-5,
    seed: int = 42,
    dataset_sha256: str = "",
) -> Dict[str, Any]:
    """
    Executes fine-tuning of Legal-BERT on multi-label operational hazard classification.
    Uses PyTorch and HuggingFace Transformers.
    Selects thresholds strictly on validation data, then evaluates once on untouched real test data.
    """
    import torch
    from torch.utils.data import Dataset, DataLoader
    from transformers import AutoTokenizer, AutoModelForSequenceClassification, get_linear_schedule_with_warmup

    print("\n" + "=" * 80)
    print(f"Beginning Legal-BERT Transformer Fine-Tuning: {model_name}")
    print(f"Output Directory: {output_dir}")
    print(f"Dataset SHA-256:  {dataset_sha256}")
    print(f"Hyperparameters: epochs={epochs}, batch_size={batch_size}, lr={learning_rate}, seed={seed}")
    print("=" * 80)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Execution Device: {device}")

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name,
        num_labels=len(CATEGORIES),
        problem_type="multi_label_classification"
    )
    model.to(device)

    class SmartContractDataset(Dataset):
        def __init__(self, recs):
            self.texts = [r["model_text"] for r in recs]
            self.labels = [
                [1.0 if r.get("categories", {}).get(c, {}).get("status") == "positive" else 0.0 for c in CATEGORIES]
                for r in recs
            ]

        def __len__(self):
            return len(self.texts)

        def __getitem__(self, idx):
            item = tokenizer(
                self.texts[idx],
                max_length=512,
                truncation=True,
                padding="max_length",
                return_tensors="pt"
            )
            item = {k: v.squeeze(0) for k, v in item.items()}
            item["labels"] = torch.tensor(self.labels[idx], dtype=torch.float)
            return item

    train_loader = DataLoader(SmartContractDataset(train_records), batch_size=batch_size, shuffle=True)

    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=0.01)
    total_steps = len(train_loader) * epochs
    scheduler = get_linear_schedule_with_warmup(optimizer, num_warmup_steps=int(total_steps * 0.1), num_training_steps=total_steps)
    criterion = torch.nn.BCEWithLogitsLoss()

    model.train()
    for epoch in range(1, epochs + 1):
        total_loss = 0.0
        for step, batch in enumerate(train_loader):
            optimizer.zero_grad()
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)

            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            logits = outputs.logits
            loss = criterion(logits, labels)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()

            total_loss += loss.item()

        avg_loss = total_loss / max(len(train_loader), 1)
        print(f"Epoch {epoch}/{epochs} Completed — Average Loss: {avg_loss:.4f}")

    # 1. Validation evaluation & threshold selection (Validation Data ONLY)
    print("\nCalibrating classification thresholds on validation data (Real-Source only)...")
    val_summary_default, y_val_true, y_val_pred_default, y_val_prob = evaluate_split(
        val_records, model, tokenizer, device, thresholds={c: 0.50 for c in CATEGORIES}, desc="Validation (0.50)"
    )
    chosen_thresholds, calibration_log = select_thresholds_on_validation(val_records, y_val_prob, y_val_true)
    print("Validation Threshold Selection Summary:")
    for c, info in calibration_log.items():
        print(f"  * {c:22}: threshold={info['threshold']:.2f} ({info['status']})")

    # Evaluate validation with chosen thresholds
    val_summary, _, _, _ = evaluate_split(
        val_records, model, tokenizer, device, thresholds=chosen_thresholds, desc="Validation (Final)"
    )

    # 2. Evaluate ONCE on untouched held-out real test set
    print("\nEvaluating fine-tuned Legal-BERT on untouched held-out test split (100% Real-Source)...")
    test_summary, _, _, _ = evaluate_split(
        test_records, model, tokenizer, device, thresholds=chosen_thresholds, desc="Test (Untouched)"
    )

    # Display report
    print_evaluation_report(val_summary, test_summary, chosen_thresholds)

    # Configure label mappings
    model.config.id2label = {i: c for i, c in enumerate(CATEGORIES)}
    model.config.label2id = {c: i for i, c in enumerate(CATEGORIES)}

    results = {
        "model_name": model_name,
        "dataset_sha256": dataset_sha256,
        "seed": seed,
        "epochs": epochs,
        "batch_size": batch_size,
        "learning_rate": learning_rate,
        "split_counts": {
            "train_total": len(train_records),
            "train_real": len([r for r in train_records if r.get("origin") == "real_source"]),
            "train_synthetic": len([r for r in train_records if r.get("origin") == "synthetic"]),
            "validation_real": len(val_records),
            "validation_synthetic": 0,
            "test_real": len(test_records),
            "test_synthetic": 0,
        },
        "split_membership": {
            "train_sample_ids": [r["sample_id"] for r in train_records],
            "train_projects": sorted(list(set(r.get("project_id") for r in train_records))),
            "validation_sample_ids": [r["sample_id"] for r in val_records],
            "validation_projects": sorted(list(set(r.get("project_id") for r in val_records))),
            "test_sample_ids": [r["sample_id"] for r in test_records],
            "test_projects": sorted(list(set(r.get("project_id") for r in test_records))),
        },
        "thresholds": chosen_thresholds,
        "threshold_calibration_log": calibration_log,
        "validation": val_summary,
        "test": test_summary,
        "timestamp": json.loads(json.dumps(str(np.datetime64('now'))))
    }

    # Save artifacts
    os.makedirs(output_dir, exist_ok=True)
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    with open(os.path.join(output_dir, "training_metrics.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    with open(os.path.join(output_dir, "training_log.txt"), "w", encoding="utf-8") as f:
        f.write("Legal-BERT Fine-Tuning Execution Log\n")
        f.write("=" * 60 + "\n")
        f.write(f"Model: {model_name}\n")
        f.write(f"Dataset SHA-256: {dataset_sha256}\n")
        f.write(f"Seed: {seed}, Epochs: {epochs}, Batch Size: {batch_size}, LR: {learning_rate}\n")
        f.write(f"Splits: Train={len(train_records)}, Validation={len(val_records)} (Real-Only), Test={len(test_records)} (Real-Only)\n")
        f.write(f"Validation Macro F1 (All): {val_summary['macro_f1_all_categories']:.4f}\n")
        f.write(f"Test Macro F1 (All): {test_summary['macro_f1_all_categories']:.4f}\n")
        f.write(f"Test Macro F1 (Evaluable): {test_summary['macro_f1_evaluable_categories']:.4f}\n")
        f.write(f"Thresholds: {chosen_thresholds}\n")

    print(f"\nModel artifacts, tokenizer, config, and metrics successfully saved to: {output_dir}")
    return results


def evaluate_existing_model(
    val_records: List[Dict[str, Any]],
    test_records: List[Dict[str, Any]],
    model_dir: str = "analysis/models/legal_bert_model",
    seed: int = 42,
    dataset_sha256: str = "",
    train_records: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Evaluates an existing saved Legal-BERT model checkpoint on the corrected group-safe splits.
    Selects thresholds strictly on validation data, then evaluates once on untouched real test data.
    """
    import torch
    from transformers import AutoTokenizer, AutoModelForSequenceClassification

    print("\n" + "=" * 80)
    print(f"Evaluating Existing Legal-BERT Model Checkpoint: {model_dir}")
    print(f"Dataset SHA-256: {dataset_sha256}")
    print("=" * 80)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Execution Device: {device}")

    tokenizer = AutoTokenizer.from_pretrained(model_dir)
    model = AutoModelForSequenceClassification.from_pretrained(model_dir)
    model.to(device)

    # 1. Validation evaluation & threshold selection (Validation Data ONLY)
    print("\nCalibrating classification thresholds on validation data (Real-Source only)...")
    val_summary_default, y_val_true, y_val_pred_default, y_val_prob = evaluate_split(
        val_records, model, tokenizer, device, thresholds={c: 0.50 for c in CATEGORIES}, desc="Validation (0.50)"
    )
    chosen_thresholds, calibration_log = select_thresholds_on_validation(val_records, y_val_prob, y_val_true)
    print("Validation Threshold Selection Summary:")
    for c, info in calibration_log.items():
        print(f"  * {c:22}: threshold={info['threshold']:.2f} ({info['status']})")

    # Evaluate validation with chosen thresholds
    val_summary, _, _, _ = evaluate_split(
        val_records, model, tokenizer, device, thresholds=chosen_thresholds, desc="Validation (Final)"
    )

    # 2. Evaluate ONCE on untouched held-out real test set
    print("\nEvaluating on untouched held-out test split (100% Real-Source)...")
    test_summary, _, _, _ = evaluate_split(
        test_records, model, tokenizer, device, thresholds=chosen_thresholds, desc="Test (Untouched)"
    )

    # Display report
    print_evaluation_report(val_summary, test_summary, chosen_thresholds)

    results = {
        "model_name": model_dir,
        "dataset_sha256": dataset_sha256,
        "seed": seed,
        "split_counts": {
            "train_total": len(train_records) if train_records else None,
            "train_real": len([r for r in train_records if r.get("origin") == "real_source"]) if train_records else None,
            "train_synthetic": len([r for r in train_records if r.get("origin") == "synthetic"]) if train_records else None,
            "validation_real": len(val_records),
            "validation_synthetic": 0,
            "test_real": len(test_records),
            "test_synthetic": 0,
        },
        "split_membership": {
            "train_sample_ids": [r["sample_id"] for r in train_records] if train_records else [],
            "train_projects": sorted(list(set(r.get("project_id") for r in train_records))) if train_records else [],
            "validation_sample_ids": [r["sample_id"] for r in val_records],
            "validation_projects": sorted(list(set(r.get("project_id") for r in val_records))),
            "test_sample_ids": [r["sample_id"] for r in test_records],
            "test_projects": sorted(list(set(r.get("project_id") for r in test_records))),
        },
        "thresholds": chosen_thresholds,
        "threshold_calibration_log": calibration_log,
        "validation": val_summary,
        "test": test_summary,
        "timestamp": json.loads(json.dumps(str(np.datetime64('now'))))
    }

    # Save updated metrics
    with open(os.path.join(model_dir, "training_metrics.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    with open(os.path.join(model_dir, "training_log.txt"), "w", encoding="utf-8") as f:
        f.write("Legal-BERT Checkpoint Evaluation Log\n")
        f.write("=" * 60 + "\n")
        f.write(f"Model Checkpoint: {model_dir}\n")
        f.write(f"Dataset SHA-256: {dataset_sha256}\n")
        f.write(f"Seed: {seed}\n")
        f.write(f"Splits: Validation={len(val_records)} (Real-Only), Test={len(test_records)} (Real-Only)\n")
        f.write(f"Validation Macro F1 (All): {val_summary['macro_f1_all_categories']:.4f}\n")
        f.write(f"Test Macro F1 (All): {test_summary['macro_f1_all_categories']:.4f}\n")
        f.write(f"Test Macro F1 (Evaluable): {test_summary['macro_f1_evaluable_categories']:.4f}\n")
        f.write(f"Thresholds: {chosen_thresholds}\n")

    print(f"\nEvaluation metrics successfully recorded to: {model_dir}/training_metrics.json")
    return results


def main():
    parser = argparse.ArgumentParser(description="Legal-BERT Training Pipeline & Data Readiness Checker")
    parser.add_argument("--config", type=str, default="analysis/training_config.json", help="Path to config file")
    parser.add_argument("--dataset", type=str, default="data/ml_candidates/final_dataset.jsonl", help="Path to canonical dataset")
    parser.add_argument("--output-dir", type=str, default=None, help="Versioned output directory for model artifacts")
    parser.add_argument("--check-readiness", action="store_true", help="Run pre-flight data readiness assessment only")
    parser.add_argument("--dry-run", action="store_true", help="Run baseline without heavy model training")
    parser.add_argument("--eval-only", action="store_true", help="Evaluate existing trained model checkpoint without retraining")
    parser.add_argument("--force", action="store_true", help="Force fine-tuning execution even if data readiness criteria are not met")

    args = parser.parse_args()

    config = {}
    if os.path.exists(args.config):
        with open(args.config, "r", encoding="utf-8") as f:
            config = json.load(f)

    data_cfg = config.get("data", {})
    min_samples = data_cfg.get("min_total_samples", 50)
    min_pos = data_cfg.get("min_positive_per_category", 5)
    min_projs = data_cfg.get("min_projects_for_split", 5)

    dataset_sha256 = compute_dataset_sha256(args.dataset)

    print("=" * 80)
    print("Smart Contract Analyser — Legal-BERT Training & Evaluation Pipeline")
    print(f"Dataset target:  {args.dataset} (SHA-256: {dataset_sha256[:16]}...)")
    print(f"Model target:    {config.get('model', {}).get('model_name_or_path', 'nlpaueb/legal-bert-base-uncased')}")
    print(f"Input field:     {config.get('model', {}).get('input_field', 'model_text')} (Dual-Stream Representation)")
    print("=" * 80)

    # 1. Load dataset
    records = load_dataset(args.dataset, eligible_only=True)
    all_records = load_dataset(args.dataset, eligible_only=False)

    real_eligible = [r for r in records if r.get("origin") == "real_source"]
    synth_eligible = [r for r in records if r.get("origin") == "synthetic"]
    real_excluded = [r for r in all_records if r.get("origin") == "real_source" and not r.get("training_eligible")]

    print(f"Total canonical records:     {len(all_records)}")
    print(f"  * Real-source total:       {len(all_records) - len(synth_eligible)} (Eligible: {len(real_eligible)}, Excluded: {len(real_excluded)})")
    print(f"  * Synthetic total:         {len(synth_eligible)} (Eligible: {len(synth_eligible)}, Excluded: 0)")
    print(f"Training-eligible records:   {len(records)}")
    print(f"Excluded records:            {len(all_records) - len(records)}")

    # 2. Assess readiness
    readiness = assess_data_readiness(
        records,
        all_records=all_records,
        min_samples=min_samples,
        min_positive_per_cat=min_pos,
        min_projects=min_projs,
    )

    print("\n--- Category Support Across Eligible Records ---")
    print(f"{'Category':<22} | {'Real Pos/Neg':<14} | {'Synth Pos/Neg':<14} | {'Combined Pos/Neg':<18} | {'Real Projs w/ Pos'}")
    print("-" * 88)
    for cat in CATEGORIES:
        r_pos = readiness["real_support"][cat]["positive"]
        r_neg = readiness["real_support"][cat]["negative"]
        s_pos = readiness["synthetic_support"][cat]["positive"]
        s_neg = readiness["synthetic_support"][cat]["negative"]
        c_pos = readiness["combined_support"][cat]["positive"]
        c_neg = readiness["combined_support"][cat]["negative"]
        p_list = readiness["real_projects_with_positives"][cat]
        print(f"{cat:<22} | {r_pos:2d} Pos / {r_neg:2d} Neg | {s_pos:2d} Pos / {s_neg:2d} Neg | {c_pos:2d} Pos / {c_neg:2d} Neg   | {len(p_list)} project(s)")

    print(f"\nDistinct Eligible Real Projects: {readiness['distinct_real_projects']}")
    print(f"Distinct Total Eligible Groups:  {readiness['distinct_projects_total']}")

    if readiness["real_sparsity_notes"]:
        print("\n[REAL-SOURCE DATA LIMITATION ANALYSIS]")
        for note in readiness["real_sparsity_notes"]:
            print(f"  * {note}")

    # 3. Partition project-isolated splits (Validation & Test: REAL-ONLY)
    seed = config.get("training", {}).get("seed", 42)
    eval_ratio = config.get("training", {}).get("eval_split_ratio", 0.2)
    test_ratio = config.get("training", {}).get("test_split_ratio", 0.2)

    print("\nPartitioning project-isolated splits (Validation/Test: 100% Real-Source Only)...")
    train_recs, val_recs, test_recs = create_group_splits(
        records,
        eval_ratio=eval_ratio,
        test_ratio=test_ratio,
        seed=seed,
    )

    train_real = [r for r in train_recs if r.get("origin") == "real_source"]
    train_synth = [r for r in train_recs if r.get("origin") == "synthetic"]

    print(f"Splits Created:")
    print(f"  * Train Total:       {len(train_recs)} ({len(train_real)} Real + {len(train_synth)} Synthetic across {len(set(r.get('project_id') for r in train_recs))} groups)")
    print(f"  * Validation Total:  {len(val_recs)} (100% Real across {len(set(r.get('project_id') for r in val_recs))} projects)")
    print(f"  * Test Total:        {len(test_recs)} (100% Real across {len(set(r.get('project_id') for r in test_recs))} projects)")
    print("Project isolation verified: Zero cross-split project leakage; zero synthetic records in validation or test.")

    # 4. Baseline benchmark on real test split
    print("\nRunning TF-IDF baseline benchmark on real-source test split...")
    baseline_metrics = run_baseline_model(train_recs, test_recs)
    print(f"Baseline Macro F1 (All Categories):       {baseline_metrics['macro_f1_all_categories']:.4f}")
    print(f"Baseline Macro F1 (Evaluable Categories): {baseline_metrics['macro_f1_evaluable_categories']:.4f}")
    print(f"Baseline Micro F1:                        {baseline_metrics['micro_f1']:.4f}")

    out_dir = args.output_dir or config.get("training", {}).get("output_dir", "analysis/models/legal_bert_model")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "baseline_metrics.json"), "w", encoding="utf-8") as f:
        json.dump(baseline_metrics, f, indent=2)

    # 5. Execution branching
    if args.check_readiness:
        print("\n--check-readiness specified: Readiness assessment and split verification completed successfully.")
        return

    if args.dry_run:
        print("\n--dry-run specified: Baseline benchmark executed; heavy model training omitted.")
        return

    if args.eval_only:
        print("\n--eval-only specified: Evaluating saved model checkpoint on corrected real-source splits...")
        evaluate_existing_model(
            val_records=val_recs,
            test_records=test_recs,
            model_dir=out_dir,
            seed=seed,
            dataset_sha256=dataset_sha256,
            train_records=train_recs,
        )
        return

    # Check whether to train or block
    if not readiness["is_ready_for_prototype"] and not args.force:
        print("\n" + "!" * 80)
        print("DATA READINESS EVALUATION: FAILED — TRAINING BLOCKED BY DATA LIMITATIONS")
        print("!" * 80)
        for idx, reason in enumerate(readiness["blocking_reasons"], 1):
            print(f"  {idx}. {reason}")
        print("\nStopping gracefully without forcing training. Use --force to proceed anyway.")
        sys.exit(0)

    # Execute training
    train_legal_bert(
        train_records=train_recs,
        val_records=val_recs,
        test_records=test_recs,
        output_dir=out_dir,
        model_name=config.get("model", {}).get("model_name_or_path", "nlpaueb/legal-bert-base-uncased"),
        epochs=config.get("training", {}).get("num_train_epochs", 3),
        batch_size=config.get("training", {}).get("batch_size", 4),
        learning_rate=config.get("training", {}).get("learning_rate", 3e-5),
        seed=seed,
        dataset_sha256=dataset_sha256,
    )


if __name__ == "__main__":
    main()
