# Smart Contract Analyser — Canonical Dataset Readiness & Freeze Report

**Document Status**: Official Dataset Readiness & Freeze Audit  
**Dataset Version**: `v3.3.0`  
**Dataset Path**: [`data/ml_candidates/final_dataset.jsonl`](file:///c:/ARO/Projects/Smart_Contract_Analyser/data/ml_candidates/final_dataset.jsonl)  
**Dataset SHA-256**: `74464fd132e9268220549adc8e5cfb31d4ca69b9fae203b31ae2924c1500e456`  
**Current Version Snapshot Path**: [`data/ml_candidates/final_dataset_v3.3.0_snapshot.jsonl`](file:///c:/ARO/Projects/Smart_Contract_Analyser/data/ml_candidates/final_dataset_v3.3.0_snapshot.jsonl) (SHA-256: `74464fd132e9268220549adc8e5cfb31d4ca69b9fae203b31ae2924c1500e456`)  
**Prior Frozen Snapshot Path**: [`data/ml_candidates/final_dataset_v3.2.0_snapshot.jsonl`](file:///c:/ARO/Projects/Smart_Contract_Analyser/data/ml_candidates/final_dataset_v3.2.0_snapshot.jsonl) (SHA-256: `b8e8060b1b0534514702a66738d4519f862e19a976ca89930ab7c39e1b53b94b`)  
**Pre-Freeze Snapshot Path**: [`data/ml_candidates/final_dataset_v3_snapshot.jsonl`](file:///c:/ARO/Projects/Smart_Contract_Analyser/data/ml_candidates/final_dataset_v3_snapshot.jsonl) (SHA-256: `0048f456c4ef0704962bd9b11ed2604d5f697a689f9bb2b8d1ffaa70f7725c28`)  
**Freeze Date**: October 22, 2026  
**Split Seed**: `42` (`GroupShuffleSplit`, 0.0% project overlap)  
**Validator Status**: **`Is Valid: True`** | **`Split Ready: True`** (0 schema errors, 0 split leakage)  

---

> [!IMPORTANT]
> ### Non-Human-Verified Provenance & Research Scope
> 1. **AI Review Disclosure**: All dataset classifications, status codes, and model summaries represent **bounded multi-pass AI reviews (`ai_reviewed` / `ai_review_unresolved`)**. Zero records are marked `human_verified: true` (0 / 72).
> 2. **Operational Risk Definition**: Annotations reflect syntactic capabilities, architectural control concentration, and documentation disclosures defined in [ANNOTATION_GUIDE.md](file:///c:/ARO/Projects/Smart_Contract_Analyser/docs/ANNOTATION_GUIDE.md). They do **not** constitute formal legal advice, statutory interpretations, or judicial enforceability determinations.
> 3. **Synthetic Separation**: Synthetic records (`SYN-001`–`SYN-020`) reside **strictly in the `train` split**. Validation and test splits contain **100% real-source records only**.

---

## 1. Freeze Reconciliation & Resolution of Audit Questions

### 1.1 Resolution of Privacy Count Discrepancy
- **Investigated Sample**: `CAN-020` (project `crestal_network`, contract `BlueprintCore.sol`, function `deployBlueprint`).
- **Review History**: In Round 2, Agent 2 raised a flag for `pending_review` stating `publicKey bytes stored on-chain. If this is a cryptographic public key (secp256k1), it is not PII per RULE-PRIV-01...`. In Round 3 adjudication, `CAN-020` was ruled **negative** because secp256k1 public keys and cryptographic addresses do not constitute natural-person PII under `RULE-PRIV-01`.
- **Exact Field Values in Records**: In both `v3.2.0-frozen` and `v3.3.0`, `CAN-020` has `categories.Privacy.status == "negative"`. It is **not** positive.
- **Why Train Reports 5 Positives in Privacy**:
  Recalculation directly from `data/ml_candidates/final_dataset.jsonl` shows that the 5 positives in `train` consist of:
  - **1 Real-Source Benchmark Record**: `CAN-040` (`BM003_UserIdentityRegistry.sol` in `smart_contract_analyser_benchmark`), which explicitly declares state variables `string public userEmail; string public physicalAddress;`.
  - **4 Synthetic Prototype Records**:
    - `SYN-001` (`KYCRegistry.sol`): `string public userEmail; string public physicalAddress;`
    - `SYN-003` (`UserProfileDirectory.sol`): `string public phoneNumber; string public realName;`
    - `SYN-005` (`StudentCredentialRegistry.sol`): `string public nationalId; string public dateOfBirth;`
    - `SYN-007` (`OnChainAddressBook.sol`): `string public mailAddress; string public streetAddress;`
  - `CAN-020` is **NOT** counted in the 5 positives. The prior freeze report presented aggregate numbers without separating real vs. synthetic origin, creating the mistaken impression that `CAN-020` was still counted as positive.

### 1.2 Unresolved Label Isolation
- In `analysis/ml_dataset_validator.py`, any record with a category status of `pending_review`, `insufficient_information`, or `unresolved` triggers `has_pending_categories = True`.
- The validator enforces that no record with `has_pending_categories = True` may have `training_eligible == True` or `split` in `("train", "validation", "test")`.
- In `final_dataset.jsonl`, exactly **16 unresolved labels** exist across 8 defect records (8 in Legal Compliance, 8 in Payment / Financial). **All 16 unresolved labels belong exclusively to the 14 excluded records (`split: "unassigned"`, `training_eligible: false`).**
- Zero unresolved labels exist in `train`, `validation`, or `test`. No unresolved label is converted to negative during training.

### 1.3 Project-Level Group Isolation & Leakage Verification
- Partitioning via `GroupShuffleSplit(test_size=0.20, random_state=42)` was evaluated:
  - Train Projects: 19 (9 real + 10 synthetic)
  - Validation Projects: 4 (all real)
  - Test Projects: 4 (all real)
  - Unassigned Projects: 9 (all real)
- Cross-split project overlap:
  - `train ∩ validation = ∅` (0.0% overlap)
  - `train ∩ test = ∅` (0.0% overlap)
  - `validation ∩ test = ∅` (0.0% overlap)
- Zero data leakage exists across splits.

---

## 2. Dataset Inventory & Breakdown by Origin

| Metric | Real-Source (`real_source`) | Synthetic Prototype (`synthetic`) | Combined Total |
| :--- | :---: | :---: | :---: |
| **Total Records** | **52** (`CAN-001`–`CAN-052`) | **20** (`SYN-001`–`SYN-020`) | **72** |
| **Training-Eligible** | **38** | **20** | **58** |
| **Excluded / Unassigned** | **14** | **0** | **14** |
| **Distinct Project Groups** | 17 eligible (26 total) | 10 eligible (10 total) | **27 eligible (36 total)** |
| **Human-Verified Records** | 0 (0.0%) | 0 (0.0%) | **0 (0.0%)** |
| **Provenance Completeness** | 100% (52/52) | 100% (20/20) | **100% (72/72)** |

### Comprehensive Breakdown by Origin Across Categories
```
+---------------------+-------------------------------+-------------------------------+
| Category            | Real-Source (N=52: 38 Elig)   | Synthetic (N=20: 20 Elig)     |
+---------------------+-------------------------------+-------------------------------+
| Privacy             |  1 Pos / 51 Neg /  0 Unr      |  4 Pos / 16 Neg /  0 Unr      |
| Termination         |  6 Pos / 46 Neg /  0 Unr      |  0 Pos / 20 Neg /  0 Unr      |
| Legal Compliance    | 14 Pos / 30 Neg /  8 Unr *    |  0 Pos / 20 Neg /  0 Unr      |
| Liability           |  1 Pos / 51 Neg /  0 Unr      |  4 Pos / 16 Neg /  0 Unr      |
| Payment / Financial |  4 Pos / 40 Neg /  8 Unr *    |  2 Pos / 18 Neg /  0 Unr      |
+---------------------+-------------------------------+-------------------------------+
```
*\* Note: The 8 unresolved labels in Legal Compliance and Payment / Financial reside exclusively on the 14 excluded real-source records.*

---

## 3. Split Distribution & Category Support

```
+---------------+---------------+--------------------+---------------+-------------------+
| Split         | Real Records  | Synthetic Records  | Total Records | Distinct Projects |
+---------------+---------------+--------------------+---------------+-------------------+
| train         |      24       |         20         |      44       |        19         |
| validation    |       7       |          0         |       7       |         4         |
| test          |       7       |          0         |       7       |         4         |
| unassigned    |      14       |          0         |      14       |         9         |
+---------------+---------------+--------------------+---------------+-------------------+
| TOTAL         |      52       |         20         |      72       |        36         |
+---------------+---------------+--------------------+---------------+-------------------+
```

### Per-Category Positive and Negative Support by Split
```
+---------------------+------------------------+-------------------+-------------------+-------------------+
| Category            | Train (N=44)           | Validation (N=7)  | Test (N=7)        | Unassigned (N=14) |
|                     | [24 Real / 20 Synth]   | [7 Real / 0 Synth]| [7 Real / 0 Synth]| [14 Real / 0 Synth|
+---------------------+------------------------+-------------------+-------------------+-------------------+
| Privacy             | 5 Pos (1 Real, 4 Synth)|  0 Pos / 7 Neg    |  0 Pos / 7 Neg    |  0 Pos / 14 Neg   |
| Termination         | 3 Pos (3 Real, 0 Synth)|  0 Pos / 7 Neg    |  3 Pos / 4 Neg    |  0 Pos / 14 Neg   |
| Legal Compliance    | 5 Pos (5 Real, 0 Synth)|  0 Pos / 7 Neg    |  4 Pos / 3 Neg    |  5 Pos / 1 Neg *  |
| Liability           | 5 Pos (1 Real, 4 Synth)|  0 Pos / 7 Neg    |  0 Pos / 7 Neg    |  0 Pos / 14 Neg   |
| Payment / Financial | 6 Pos (4 Real, 2 Synth)|  0 Pos / 7 Neg    |  0 Pos / 7 Neg    |  0 Pos / 6 Neg *  |
+---------------------+------------------------+-------------------+-------------------+-------------------+
```

---

## 4. Honest Disclosure of Evaluation Adequacy & Limitations

A critical distinction must be drawn between **structural validity** (the dataset parses cleanly, respects schemas, and isolates project groups) and **statistical adequacy** (the splits contain enough ground-truth positive examples to evaluate model generalizability):

### 4.1 Evaluable Categories on Held-Out Test Split
- **`Termination`** (3 Pos / 4 Neg): Sufficient real-source positive support to compute empirical Precision, Recall, and F1 on held-out test contracts (`CAN-045`, `CAN-046`, `CAN-047`).
- **`Legal Compliance`** (4 Pos / 3 Neg): Sufficient real-source positive support to compute empirical Precision, Recall, and F1 on held-out test contracts (`CAN-013`, `CAN-030`, `CAN-031`, `CAN-045`).

### 4.2 Inconclusive Categories on Held-Out Test Split
- **`Privacy`** (0 Pos / 7 Neg): **Inconclusive**. Zero real-source positive examples exist in the test split. True Recall and F1 cannot be empirically measured without false-negative opportunities.
- **`Liability`** (0 Pos / 7 Neg): **Inconclusive**. Zero real-source positive examples exist in the test split.
- **`Payment / Financial`** (0 Pos / 7 Neg): **Inconclusive**. Zero real-source positive examples exist in the test split.
> *Standard of Integrity*: The model cannot be claimed accurate or production-ready for Privacy, Liability, or Payment / Financial under this split.

### 4.3 Validation Split Limitation
- The validation split ($N=7$) consists exclusively of negative examples across all five categories.
- As a consequence, empirical threshold calibration on the validation split is statistically invalid (calibrating on pure negatives would collapse probability thresholds). All categories retain the default threshold of **0.50** (`default_uncalibrated`).

---

## 5. Audit Log of Excluded Records ($N=14$)

All 14 excluded records are assigned to `split: "unassigned"` and `training_eligible: false`:

1. **`CAN-005`** (`USSI.sol`): Excluded due to `BUSL-1.1` license restriction.
2. **`CAN-006`** (`Swap.sol`): Excluded due to `BUSL-1.1` license restriction.
3. **`CAN-007`** (`AssetToken.sol`): Excluded due to `BUSL-1.1` license restriction.
4. **`CAN-008`** (`AssetIssuer.sol`): Excluded due to `BUSL-1.1` license restriction.
5. **`CAN-009`** (`AssetLocking.sol`): Excluded due to `BUSL-1.1` license restriction.
6. **`CAN-012`** (`LevelStake.sol`): Excluded due to `BUSL-1.1` license restriction and unverified source pragma.
7. **`CAN-029`** (`ResourceManager.sol`): Excluded due to `AGPL-3.0-only` copyleft license restriction.
8. **`CAN-001`** (`AgentImageService.sol`): Excluded due to source excerpt defect; audit report cites `issueRefund` at L299, but contract has only 285 lines (`commit_drift_unresolved`).
9. **`CAN-010`** (`LevelStake.sol`): Excluded due to missing cited routine `burnExpired`; excerpt defaulted to header comments.
10. **`CAN-011`** (`LevelStake.sol`): Excluded due to function name mismatch (`setTTL` at L251 vs cited `setExpiry`).
11. **`CAN-014`** (`EulerVault.sol`): Excluded because cited routine `deposit` is an inherited OpenZeppelin ERC4626 implementation.
12. **`CAN-018`** (`GovernorBravo.sol`): Excluded because cited routine `_setVotingDelay` is inherited from OpenZeppelin GovernorSettings.
13. **`CAN-021`** (`RollupRevenueVault.sol`): Excluded because cited function `initialize` does not match exact initializer routine signatures.
14. **`CAN-033`** (`NitroContractsUpgrade.sol`): Excluded because excerpt is an interface stub, not the implementation logic at line 50.

---

## 6. Freeze Terms & Future Modification Policy

1. **Frozen Status**: Dataset version `v3.3.0` (SHA-256: `74464fd132e9268220549adc8e5cfb31d4ca69b9fae203b31ae2924c1500e456`) is officially **frozen for active project development and model experimentation**.
2. **No Silent Modifications**: No record, label, or split in this dataset may be edited silently.
3. **Reopening Criteria**: The dataset may only be reopened if a **concrete, material defect** is formally discovered (e.g., license status change, provenance error, or code mismatch). Any reopening requires an incremented version identifier (e.g., `v3.4.0`), a new SHA-256 hash, and an updated audit log.
4. **Snapshot Preservation**:
   - `data/ml_candidates/final_dataset_v3_snapshot.jsonl` (pre-freeze snapshot)
   - `data/ml_candidates/final_dataset_v3.2.0_snapshot.jsonl` (v3.2.0-frozen snapshot)
   - `data/ml_candidates/final_dataset_v3.3.0_snapshot.jsonl` (v3.3.0-readiness snapshot)
