# Smart Contract Analyser — Machine Learning Dataset Finalization & Evaluation Report

**Document Version**: 3.1.0  
**Date**: 2026-10-22  
**Project**: Smart_Contract_Analyser  
**Authoritative Specification**: [docs/reference/Smart_Contract_Legal_AI_SaaS_Platform_Specification.docx](file:///c:/ARO/Projects/Smart_Contract_Analyser/docs/reference/Smart_Contract_Legal_AI_SaaS_Platform_Specification.docx)  
**Canonical Dataset**: [data/ml_candidates/final_dataset.jsonl](file:///c:/ARO/Projects/Smart_Contract_Analyser/data/ml_candidates/final_dataset.jsonl) (SHA-256: `0048f456c4ef0704962bd9b11ed2604d5f697a689f9bb2b8d1ffaa70f7725c28`)  
**Expansion Candidates Manifest**: [data/ml_candidates/expansion_candidates.jsonl](file:///c:/ARO/Projects/Smart_Contract_Analyser/data/ml_candidates/expansion_candidates.jsonl)  
**Dataset Standards**: [docs/DATASET_SPECIFICATION.md](file:///c:/ARO/Projects/Smart_Contract_Analyser/docs/DATASET_SPECIFICATION.md) & [docs/ANNOTATION_GUIDE.md](file:///c:/ARO/Projects/Smart_Contract_Analyser/docs/ANNOTATION_GUIDE.md)  
**Training Pipeline & Config**: [analysis/train_legal_bert.py](file:///c:/ARO/Projects/Smart_Contract_Analyser/analysis/train_legal_bert.py) & [analysis/training_config.json](file:///c:/ARO/Projects/Smart_Contract_Analyser/analysis/training_config.json)  

---

> [!IMPORTANT]
> ### Research Notice, Review Status & Non-Equivalence Notice
> All dataset classifications and review statuses represent **careful evidence-grounded AI reviews (`ai_reviewed` / `ai_review_unresolved`)**.
> - **Human Verification Claim**: **Zero (0.0%)**. Zero records are marked `human_verified: true` or imply human review.
> - **Legal Nature**: Operational risk labels capture syntactic capabilities, architectural control imbalances, and documentation disclosures defined in [ANNOTATION_GUIDE.md](file:///c:/ARO/Projects/Smart_Contract_Analyser/docs/ANNOTATION_GUIDE.md). This system is an experimental research and demonstration platform. Its outputs do **not** constitute formal legal advice, statutory interpretations, or judicial enforceability determinations.
> - **Synthetic Separation**: Synthetic records (`SYN-001`–`SYN-020`) are used **strictly for model training** (`synthetic_train`). Validation and test splits contain **100% real-source records only**.

---

## 1. Executive Summary & Audit Scope

This report records the complete dataset inspection, evaluation split restructuring, threshold calibration, and empirical model evaluation on [`data/ml_candidates/final_dataset.jsonl`](file:///c:/ARO/Projects/Smart_Contract_Analyser/data/ml_candidates/final_dataset.jsonl).

### Key Architectural Fixes Completed in this Release:
1. **Real-Source-Only Evaluation Splits**:
   - Synthetic records (`SYN-001` through `SYN-020`) were removed from validation and test splits and restricted **exclusively to training**.
   - Validation ($N=7$) and Test ($N=7$) splits consist of **100% real-source contracts**.
2. **Strict Project Isolation (Zero Cross-Split Leakage)**:
   - All contracts belonging to the same repository/project family reside in the exact same split.
   - Project overlap between Train, Validation, and Test is **0.0%**.
3. **Validation-Only Threshold Selection**:
   - Threshold calibration was attempted strictly on validation data. Because validation contained zero positive examples across all five categories (all 4 validation projects happen to be negative controls), threshold calibration was skipped to prevent artificial overfitting, and the default 0.50 threshold was retained and documented as uncalibrated.
   - The test split remained completely untouched during model and threshold selection.
4. **Honest Reporting of Small-Data Limitations**:
   - Categories with zero true positive examples in the test split (`Privacy`, `Liability`, and `Payment / Financial`) are explicitly designated as `inconclusive_zero_positive_support` rather than manufacturing a misleading metric.
   - Only categories with empirical test support (`Termination` with $N=3$ positives, and `Legal Compliance` with $N=4$ positives) are evaluated for precision, recall, and F1.
5. **Baseline Comparison**:
   - A TF-IDF + LogisticRegression baseline was trained and evaluated on the exact same splits, achieving an F1 of 0.8000 on `Termination` and 0.0000 on `Legal Compliance`.

---

## 2. Canonical Dataset Inventory & Record Breakdown

| Metric | Real-Source (`real_source`) | Synthetic Prototype (`synthetic`) | Combined Total | Details / Notes |
| :--- | :---: | :---: | :---: | :--- |
| **Total Records** | **52** | **20** | **72** | Complete sequence `CAN-001`–`CAN-052` and `SYN-001`–`SYN-020`. |
| **Training-Eligible** | **38** | **20** | **58** | `training_eligible: true`, `review_status: "ai_reviewed"`. |
| **Excluded / Unresolved** | **14** | **0** | **14** | `training_eligible: false`, `review_status: "ai_review_unresolved"`. |
| **Distinct Project / Template Families** | 17 eligible (22 total) | 10 eligible (10 total) | **27 eligible (32 total)** | 0 project overlap across train, validation, and test. |
| **Permissive Cleared Licenses** | 45 | 20 (MIT / Apache-2.0) | **65** | MIT, Apache-2.0, BSD-3-Clause, ISC. |
| **Restricted Licenses (Excluded)** | 7 | 0 | **7** | 6 BUSL-1.1 (`CAN-005`–`CAN-009`, `CAN-012`), 1 AGPL-3.0 (`CAN-029`). |
| **Source Defects (Excluded)** | 7 | 0 | **7** | Commit drift, upstream renames, or function extraction defects. |
| **Human-Verified Claims** | 0 (0.0%) | 0 (0.0%) | **0 (0.0%)** | 100% of records have `human_verified: false`. |
| **Provenance Completeness** | 100% (52/52) | 100% (20/20) | **100% (72/72)** | Complete repository URL, commit SHA, file path, license, line ranges. |
| **Dataset Validator Status** | VALID | VALID | **VALID** | `analysis/ml_dataset_validator.py` passes with 0 errors. |

---

## 3. Five-Category Label Distributions

### 3.1 Distribution Across Training-Eligible Records (58 records)

```
+---------------------+-------------------+------------------------+---------------------+-------------------+
| Category            | Real-Source Pos/Neg| Synthetic Pos/Neg      | Combined Pos/Neg    | Combined Pos Rate |
+---------------------+-------------------+------------------------+---------------------+-------------------+
| Privacy             |  1 Pos / 37 Neg   |  4 Pos / 16 Neg        |   5 Pos / 53 Neg    |       8.6%        |
| Termination         |  6 Pos / 32 Neg   |  0 Pos / 20 Neg        |   6 Pos / 52 Neg    |      10.3%        |
| Legal Compliance    |  9 Pos / 29 Neg   |  0 Pos / 20 Neg        |   9 Pos / 49 Neg    |      15.5%        |
| Liability           |  1 Pos / 37 Neg   |  4 Pos / 16 Neg        |   5 Pos / 53 Neg    |       8.6%        |
| Payment / Financial |  4 Pos / 34 Neg   |  2 Pos / 18 Neg        |   6 Pos / 52 Neg    |      10.3%        |
+---------------------+-------------------+------------------------+---------------------+-------------------+
```

### 3.2 Distribution Across All Canonical Records (72 records, including 14 excluded real records)

```
+---------------------+----------+----------+------------+----------------+----------+
| Category            | Positive | Negative | Unresolved | Excluded Count | Total    |
+---------------------+----------+----------+------------+----------------+----------+
| Privacy             |    5     |    67    |     0      |       0        |    72    |
| Termination         |    6     |    66    |     0      |       0        |    72    |
| Legal Compliance    |   14     |    50    |     8      |      14        |    72    |
| Liability           |    5     |    67    |     0      |       0        |    72    |
| Payment / Financial |    6     |    58    |     8      |      14        |    72    |
+---------------------+----------+----------+------------+----------------+----------+
```

---

## 4. Evaluation Split Strategy & Project Isolation

### 4.1 Split Allocation Logic
- **Fixed Seed**: `42` (`GroupShuffleSplit`).
- **Target Ratios**: `test_ratio = 0.20`, `eval_ratio = 0.20`.
- **Partitioning Order**:
  1. Real-source eligible records ($N=38$) are split into `real_test` ($N=7$) and `real_train_val` ($N=31$) grouped by `project_id`.
  2. `real_train_val` is split into `real_val` ($N=7$) and `real_train` ($N=24$) grouped by `project_id`.
  3. Synthetic records ($N=20$) are appended to `real_train` to form the training set ($N=44$).
  4. Validation ($N=7$) and Test ($N=7$) contain **zero synthetic records**.

### 4.2 Exact Split Breakdown

```
+-------------------+---------------+------------------+------------------+-------------------------------------------------------------+
| Split             | Total Records | Real-Source Recs | Synthetic Recs   | Project Groups                                              |
+-------------------+---------------+------------------+------------------+-------------------------------------------------------------+
| Train             |      44       |        24        |        20        | 19 groups (9 real projects + 10 synthetic template families)|
| Validation        |       7       |         7        |         0        | 4 real projects: coinbase_base_bridge, spectral_image_vaults|
|                   |               |                  |                  |                  the_compact, very_liquid_vaults            |
| Test (Untouched)  |       7       |         7        |         0        | 4 real projects: anvil_protocol, aragon_vault,              |
|                   |               |                  |                  |                  crytic_not_so_smart_contracts,             |
|                   |               |                  |                  |                  virtuals_genesis                           |
+-------------------+---------------+------------------+------------------+-------------------------------------------------------------+
```

### 4.3 Structural Limitation Analysis (Why Privacy and Liability Have Zero Test Positives)
Under strict group isolation (where all records from a project stay in one split):
- **`Privacy`**: Contains only **1 positive real record** across all 38 eligible real records, located in project `smart_contract_analyser_benchmark`. Because `smart_contract_analyser_benchmark` is assigned to Train, both Validation and Test mathematically have **0 real positive examples**.
- **`Liability`**: Contains only **1 positive real record** across all 38 eligible real records, located in project `smart_contract_analyser_benchmark`. Because `smart_contract_analyser_benchmark` is assigned to Train, both Validation and Test mathematically have **0 real positive examples**.
- **`Payment / Financial`**: Contains 4 positive real records across 3 projects (`smart_contract_analyser_benchmark` [2], `uniswap_v3_adapter` [1], `compound_protocol` [1]). All 3 projects were allocated to Train under seed 42, leaving 0 positive examples in Validation and Test.
- **`Termination`**: Contains 6 positive real records across 3 projects (`openzeppelin_contracts` [2, Train], `smart_contract_analyser_benchmark` [1, Train], and `crytic_not_so_smart_contracts` [3, Test]).
- **`Legal Compliance`**: Contains 9 positive real records across 6 projects. Train has 5 positives, Validation has 0, and Test has 4 positives (`aragon_vault` [1], `virtuals_genesis` [2], `crytic_not_so_smart_contracts` [1]).

> [!CAUTION]
> **Conclusion on Small-Data Split Balance**: It is mathematically impossible to construct group-safe Train, Validation, and Test splits that all contain positive examples for `Privacy` and `Liability` from the current real dataset. Moving synthetic records into validation/test to artificially create positive support would violate evaluation integrity. The limitation is therefore reported transparently.

---

## 5. Threshold Selection & Evaluation Results

### 5.1 Validation-Only Threshold Selection
- Calibration on Validation Split: Evaluated predicted probabilities on the 7 real-source validation records.
- Positive Validation Support: 0 positive examples across all five categories.
- Outcome: Threshold calibration was skipped to prevent artificial overfitting to an all-negative distribution. All five categories retained the default threshold of **0.50** (`default_uncalibrated`).

### 5.2 Legal-BERT Performance on Untouched Real-Source Test Split ($N=7$)

```
+---------------------+--------+---------+---------+----+----+----+----+--------+--------+--------+------------------------------------+
| Category            | Thresh | Real Pos| Real Neg| TP | FP | FN | TN | Prec   | Recall | F1     | Support Status                     |
+---------------------+--------+---------+---------+----+----+----+----+--------+--------+--------+------------------------------------+
| Privacy             |  0.50  |    0    |    7    |  0 |  0 |  0 |  7 | 0.0000 | 0.0000 | 0.0000 | inconclusive_zero_positive_support |
| Termination         |  0.50  |    3    |    4    |  0 |  0 |  3 |  4 | 0.0000 | 0.0000 | 0.0000 | sufficient_support (N=3)           |
| Legal Compliance    |  0.50  |    4    |    3    |  0 |  0 |  4 |  3 | 0.0000 | 0.0000 | 0.0000 | sufficient_support (N=4)           |
| Liability           |  0.50  |    0    |    7    |  0 |  0 |  0 |  7 | 0.0000 | 0.0000 | 0.0000 | inconclusive_zero_positive_support |
| Payment / Financial |  0.50  |    0    |    7    |  0 |  0 |  0 |  7 | 0.0000 | 0.0000 | 0.0000 | inconclusive_zero_positive_support |
+---------------------+--------+---------+---------+----+----+----+----+--------+--------+--------+------------------------------------+
```

- **Macro F1 (All Categories)**: `0.0000` (Unweighted mean across all 5 classes; zero-support classes contribute 0.0).
- **Macro F1 (Evaluable Categories: Termination & Legal Compliance)**: `0.0000`.
- **Micro F1**: `0.0000`.
- **Hamming Loss**: `0.2000` (7 incorrect decisions out of 35 binary decisions).

### 5.3 Diagnostic Findings on Legal-BERT Predictions
Analysis of raw sigmoid output probabilities on the test split:
- `Privacy`: $\sim 0.1765$ – $0.1937$
- `Liability`: $\sim 0.1628$ – $0.1797$
- `Payment / Financial`: $\sim 0.2175$ – $0.2374$
- `Termination`: $\sim 0.2512$ – $0.2729$
- `Legal Compliance`: $\sim 0.3144$ – $0.3284$

Because training targets are sparse (positive prevalence $\sim 8\text{--}15\%$), standard BCE loss aligns output probabilities with the base rates. At a fixed 0.50 threshold, the model predicts zero positives. Because test tuning is strictly prohibited, the threshold was not lowered against test data.

### 5.4 Comparison with Simple TF-IDF Baseline

A TF-IDF + LogisticRegression baseline with balanced class weights was trained on `train_records` ($N=44$) and evaluated on the untouched test split ($N=7$):

```
+---------------------+---------+---------+----+----+----+----+--------+--------+--------+------------------------------------+
| Category            | Real Pos| Real Neg| TP | FP | FN | TN | Prec   | Recall | F1     | Baseline Model Type / Status       |
+---------------------+---------+---------+----+----+----+----+--------+--------+--------+------------------------------------+
| Privacy             |    0    |    7    |  0 |  0 |  0 |  7 | 0.0000 | 0.0000 | 0.0000 | inconclusive_zero_positive_support |
| Termination         |    3    |    4    |  2 |  0 |  1 |  4 | 1.0000 | 0.6667 | 0.8000 | logistic_regression (balanced)     |
| Legal Compliance    |    4    |    3    |  0 |  0 |  4 |  3 | 0.0000 | 0.0000 | 0.0000 | logistic_regression (balanced)     |
| Liability           |    0    |    7    |  0 |  0 |  0 |  7 | 0.0000 | 0.0000 | 0.0000 | inconclusive_zero_positive_support |
| Payment / Financial |    0    |    7    |  0 |  0 |  0 |  7 | 0.0000 | 0.0000 | 0.0000 | inconclusive_zero_positive_support |
+---------------------+---------+---------+----+----+----+----+--------+--------+--------+------------------------------------+
```

- **Baseline Macro F1 (All Categories)**: `0.1600` ($0.8000 / 5$).
- **Baseline Macro F1 (Evaluable Categories: Termination & Legal Compliance)**: `0.4000` ($(0.8000 + 0.0000) / 2$).
- **Baseline Micro F1**: `0.4444`.
- **Baseline Hamming Loss**: `0.1429` (5 incorrect decisions out of 35).

---

## 6. Concrete, Prioritized Real-Source Data Collection Plan

To transition `Smart_Contract_Analyser` from an experimental prototype to an empirically evaluated system, additional real-source Solidity contracts must be collected for underrepresented categories:

### 6.1 Priority 1: Privacy Hazard Contracts (Target: +12 to +15 independent real projects)
- **Pattern**: Storage of off-chain personally identifiable information (PII), plain-text contact information, unhashed email/phone/SSN, or unencrypted biometric/KYC references on-chain.
- **Candidate Sources**:
  * Public Decentralized Identity (DID) registries and KYC attestation verifiers (e.g., Proof of Humanity, Gitcoin Passport schemas, Worldcoin identity verification interfaces).
  * On-chain social protocol profiles with contact fields (e.g., Lens Protocol profile metadata contracts, Farcaster registry contracts).
  * Web3 student/employee credential issuance registries.
- **License Requirement**: Permissive only (MIT, Apache-2.0, BSD-3-Clause).

### 6.2 Priority 2: Liability Hazard Contracts (Target: +12 to +15 independent real projects)
- **Pattern**: Asymmetric exculpatory disclaimers, unilateral indemnification, complete zero-warranty clauses, or "as-is / use at your own risk" waivers embedded in contract NatSpec or operational state transitions.
- **Candidate Sources**:
  * Experimental DeFi vaults and unaudited yield aggregators with explicit developer disclaimer NatSpec (`@notice THIS CODE IS EXPERIMENTAL AND PROVIDED AS-IS WITHOUT WARRANTY`).
  * Forked decentralized exchange routers with unilateral fee/loss disclaimers.
  * Algorithmic stablecoin experimental contracts with explicit "no loss compensation" terms.
- **License Requirement**: Permissive only (MIT, Apache-2.0, BSD-3-Clause).

### 6.3 Priority 3: Payment / Financial Hazard Contracts (Target: +8 to +10 independent real projects)
- **Pattern**: Unconstrained fee modification (no maximum fee ceiling), arbitrary owner-controlled transfer taxes, or balance confiscation routines.
- **Candidate Sources**:
  * Token contracts with configurable trading fees where `feeBasisPoints` has no upper bound check.
  * Staking pools with variable performance fee parameters adjustable by owner without timelock.
- **License Requirement**: Permissive only (MIT, Apache-2.0, BSD-3-Clause).

### 6.4 Verification Protocol for New Additions
1. Every newly collected contract must be assigned a unique `CAN-XXX` sample ID and recorded in `data/ml_candidates/expansion_candidates.jsonl`.
2. Provenance must record exact repository URL, commit SHA, contract file, compiler version, SPDX license identifier, line ranges, and objective code snippet.
3. **No Automated Ground-Truth Claims**: All initial labels must be tagged `human_verified: false` and `review_status: "ai_reviewed"`.
4. No proprietary or restricted licenses (BUSL-1.1, AGPL-3.0) may be marked `training_eligible: true`.

---

## 7. Artifact Summary & System Verification

### 7.1 Verified Files & Hashes
- **Canonical Dataset**: `data/ml_candidates/final_dataset.jsonl` (SHA-256: `0048f456c4ef0704962bd9b11ed2604d5f697a689f9bb2b8d1ffaa70f7725c28`)
- **Training Script**: `analysis/train_legal_bert.py`
- **Training Config**: `analysis/training_config.json`
- **Model Checkpoint**: `analysis/models/legal_bert_model/`
  * `training_metrics.json`: Complete record of seed 42, dataset SHA-256, split membership, confusion matrices, and support statuses.
  * `baseline_metrics.json`: TF-IDF baseline evaluation on the identical test split.
  * `training_log.txt`: Plain-text execution log.
- **Dataset Documentation**: `docs/DATASET_FINALIZATION_REPORT.md` (this report)

### 7.2 Validation Checks Run
1. `python analysis/ml_dataset_validator.py data/ml_candidates/final_dataset.jsonl` -> **PASSED** (72 records valid, 0 schema errors).
2. `python analysis/train_legal_bert.py --check-readiness` -> **PASSED** (verified 100% real-source evaluation splits, 0 project leakage).
3. `python analysis/train_legal_bert.py --eval-only` -> **PASSED** (evaluated model and baseline on real-only test split).
4. `python -m pytest` -> **PASSED** (32/32 tests passed in 25.82s).
5. `npm run build` in `frontend/` -> **PASSED** (Vite build completed in 2.03s, 0 errors).
