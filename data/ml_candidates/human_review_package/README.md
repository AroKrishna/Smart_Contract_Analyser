# Smart Contract Analyser — Human Review Package

**Package Location**: `data/ml_candidates/human_review_package/`  
**Creation Date**: 2026-10-22  
**Target Dataset**: 58 Training-Eligible Records (38 Real-Source + 20 Synthetic)  
**Total Category Decisions**: 290 Label Evaluations (58 records × 5 categories)  
**Excluded Records**: 14 Records (Preserved in Sheet 4 for full traceability)  
**Status**: Prepared for Human Review (**Zero records are marked human-verified**)  

---

## 📌 Quick Start Guide (What to Open First)

1. Open **`human_review_workbook.xlsx`** in Microsoft Excel or your preferred spreadsheet viewer.
2. Read **Sheet 1: `START HERE`** for the core review principles and a quick worked example.
3. Review the contract inventory on **Sheet 2: `RECORD OVERVIEW`** (58 eligible records).
4. Perform your label review on **Sheet 3: `CATEGORY LABEL REVIEW`** (290 rows).
5. Consult **Sheet 5: `CATEGORY GUIDE`** whenever you need clarification on category definitions or review cautions.
6. Sheet 4 (**`EXCLUDED RECORDS`**) documents the 14 excluded contracts for your information — you do **not** need to review risk labels for excluded records.

---

## 🎯 What You Need to Review

| Item | Count | Description |
|:---|:---:|:---|
| **Total Contracts to Review** | **58** | 38 real-source audited contracts + 20 synthetic prototype templates. |
| **Category Decisions** | **290** | Exactly 5 risk category evaluations per eligible contract (58 × 5). |
| **Categories Evaluated** | **5** | `Privacy`, `Termination`, `Legal Compliance`, `Liability`, `Payment / Financial`. |
| **Excluded Contracts** | **14** | Barred from active training due to license restrictions (BUSL/AGPL) or source excerpt drift. |

---

## 📝 How to Record a Decision (Sheet 3)

In **Sheet 3: `CATEGORY LABEL REVIEW`**, each row corresponds to one contract and one category. Fill out columns **P through U**:

1. **Column P: `Reviewer Decision`** (Dropdown):
   * **`Confirm`**: You agree the AI-proposed status, evidence, and rationale are accurate.
   * **`Correct`**: The AI proposal is wrong. Choose your `Corrected Status` in Column Q and describe the reason in Column S.
   * **`Unresolved`**: The code context is missing, ambiguous, or cannot be decided with certainty.
   * **`Need help`**: You want another auditor or legal advisor to look at this contract.
2. **Column Q: `Corrected Status`** (Dropdown, only if `Correct`):
   * `positive`, `negative`, or `unresolved`.
3. **Column R: `Corrected Evidence / Lines`**:
   * Enter the exact Solidity code line range or snippet that supports your decision.
4. **Column S: `Reviewer Notes & Justification`**:
   * Plain-language explanation of why you made this decision.
5. **Column T: `Reviewer Name / Initials`**:
   * Enter your name or initials (e.g. `JD`). Required for every reviewed row.
6. **Column U: `Review Date`**:
   * Enter the date of review (e.g. `2026-10-23`). Required for every reviewed row.

---

## ⚖️ Important Review Cautions

* **Technical / Operational Indicators, Not Court Enforceability**: You are verifying whether the syntactic operational risk or documentation disclaimer defined in the Category Guide is factually present in the cited Solidity code. You are **not** certifying judicial enforceability across legal jurisdictions.
* **Privacy**: Check actual stored data and visibility. A variable name alone (e.g. `userAddress`) does not prove real personal data. Cryptographic hashes and addresses are not PII.
* **Termination**: Check what the function does, who can call it, and what protections apply. Do not treat every emergency pausing function as a termination risk automatically. A positive hazard requires irreversible bytecode destruction or balance sweeping via `selfdestruct`/`suicide`.
* **Legal Compliance**: If the conclusion depends on off-chain governance documents or missing context, mark it `Unresolved`. Standard single-admin functions do not trigger centralization hazards unless there are 3+ privileged routines without timelocks.
* **Liability**: If a legal disclaimer or liability term is not present in the available code or NatSpec docstrings, do not infer it. Standard repository LICENSE files (e.g. MIT notice) are excluded.
* **Payment / Financial**: Check amount bounds, caller permissions, and transfer behavior. Moving funds or charging standard fixed fees is not a hazard.
* **When in Doubt, Choose `Unresolved`**: Never guess. Missing or ambiguous evidence must always be marked `Unresolved`.

---

## 🔒 Provenance & Dataset Integrity Safeguards

* **Canonical Dataset Untouched**: `data/ml_candidates/final_dataset.jsonl` has **not** been modified or overwritten.
* **Zero Human Verification Claims**: 100% of records remain `human_verified: false` and `review_status: ai_reviewed`. AI agreement is never treated as human verification.
* **Review Copy Created**: `human_review_records.jsonl` contains the exact 72 canonical records with blank human-review fields added.
* **Promotion Script Prepared**: `import_human_review.py` is available to import your decisions once you finish the workbook. It refuses to promote unreviewed rows, requires reviewer initials and dates, and outputs to a separate file without altering canonical data.

---

## 📂 Package Contents

* **`human_review_workbook.xlsx`**: Primary 5-sheet review workbook for Microsoft Excel.
* **`human_review_records.jsonl`**: Machine-readable JSONL copy with blank human review fields.
* **`import_human_review.py`**: Automated import script to apply completed human decisions later.
* **`README.md`**: This instruction file.
