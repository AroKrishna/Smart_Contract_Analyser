# Smart Contract Analyser — Benchmark Expansion Candidate Report

**Document Version**: 1.0.0  
**Date**: October 22, 2026  
**Status**: Data-Preparation Milestone — Candidate Expansion Package  
**Target Milestone**: Benchmark Dataset Expansion Candidate Review (Pre-Release Phase)  
**Human Verification Status**: `human_verified: false` (AI-reviewed candidate package; not ground truth)  
**Frozen Baseline Protection**: `data/ml_candidates/final_dataset.jsonl` (SHA-256: `74464fd132e9268220549adc8e5cfb31d4ca69b9fae203b31ae2924c1500e456` strictly verified and unchanged).

---

## 1. Executive Summary & Objective

Following the baseline Legal-BERT experiment on frozen dataset `v3.3.0`—in which the model yielded 0.0000 F1 across all five operational categories due to an uncalibrated default threshold (0.50) and zero positive ground-truth support in the validation split—this milestone prepares a rigorously sourced **benchmark expansion candidate package**.

### 1.1 Scope Boundaries & Core Guarantees
* **New Candidate Milestone**: This package collects, verifies, annotates, and models real-source open-source smart contracts to evaluate the feasibility of preparing a future versioned dataset (`v4.0.0`).
* **Protection of Frozen Assets**: Neither `data/ml_candidates/final_dataset.jsonl`, its snapshot `final_dataset_v3.3.0_snapshot.jsonl`, `analysis/training_config.json`, nor the `legal_bert_v3.3.0` model artifacts were altered, renamed, or overwritten.
* **Separation of Candidates**: All new records, provenance manifests, review logs, and split plans are isolated in `data/ml_candidates/expansion_candidate_package/`.
* **Zero Fabrication / Non-Ground-Truth Disclosure**: Labels represent two-pass AI review recommendations against [ANNOTATION_GUIDE.md](file:///c:/ARO/Projects/Smart_Contract_Analyser/docs/ANNOTATION_GUIDE.md). All records carry `human_verified: false`.
* **Separation of Synthetic Data**: Synthetic toy contracts (`BM001`–`BM005`) are classified as dev controls and prohibited from validation/test evaluation splits.

---

## 2. Expansion Package Deliverables & Repository Locations

All expansion artifacts have been created in designated candidate directories:

1. **Candidate JSONL Dataset**:
   [`data/ml_candidates/expansion_candidate_package/expansion_candidates.jsonl`](file:///c:/ARO/Projects/Smart_Contract_Analyser/data/ml_candidates/expansion_candidate_package/expansion_candidates.jsonl)
   * 16 accepted real-source records strictly conforming to [DATASET_SPECIFICATION.md](file:///c:/ARO/Projects/Smart_Contract_Analyser/docs/DATASET_SPECIFICATION.md) schema.
2. **Candidate Source & Provenance Manifest**:
   [`data/ml_candidates/expansion_candidate_package/candidate_source_manifest.json`](file:///c:/ARO/Projects/Smart_Contract_Analyser/data/ml_candidates/expansion_candidate_package/candidate_source_manifest.json)
   * Full provenance tracking 32 total evaluated candidates (16 accepted, 10 excluded, 6 synthetic separated) with verified commit hashes, line ranges, and SPDX licenses.
3. **AI Review & Disagreement Log**:
   [`data/ml_candidates/expansion_candidate_package/review_disagreement_log.md`](file:///c:/ARO/Projects/Smart_Contract_Analyser/data/ml_candidates/expansion_candidate_package/review_disagreement_log.md)
   * Detailed record of Pass 1 vs. Pass 2 AI reviews, flagged discrepancies, and adjudicated rationales.
4. **Proposed Grouped Split Report**:
   [`data/ml_candidates/expansion_candidate_package/proposed_grouped_split_report.md`](file:///c:/ARO/Projects/Smart_Contract_Analyser/data/ml_candidates/expansion_candidate_package/proposed_grouped_split_report.md)
   * Group-isolated partition plan across 9 independent project families with zero cross-split leakage and per-category support accounting.

---

## 3. Candidate Summary by Category and Label Status

Across the 16 accepted real-source candidates, the reconciled category label distribution is:

```
+---------------------+----------+----------+--------------------------+---------------------+
| Category            | Positive | Negative | Insufficient / Unresolved| Total Records (N=16)|
+---------------------+----------+----------+--------------------------+---------------------+
| Privacy             | 0 (0.0%) | 16(100.0%)| 0 (0.0%)                 | 16                  |
| Termination         | 5 (31.2%)| 11(68.8%)| 0 (0.0%)                 | 16                  |
| Legal Compliance    | 4 (25.0%)| 12(75.0%)| 0 (0.0%)                 | 16                  |
| Liability           | 0 (0.0%) | 16(100.0%)| 0 (0.0%)                 | 16                  |
| Payment / Financial | 3 (18.8%)| 13(81.2%)| 0 (0.0%)                 | 16                  |
+---------------------+----------+----------+--------------------------+---------------------+
```

---

## 4. Source Provenance, Licensing & Exclusion Audit

### 4.1 Accepted Real-Source Candidates ($N=16$, 9 Project Families)
All 16 accepted records have verified upstream repository URLs, exact commit hashes/tags, confirmed file paths, matching source code excerpts, and permissive licenses:

| Sample ID | Project Family | Contract File | Function / Excerpt | Lines | License | Verified Category Hazard |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **CAN-043** | `openzeppelin_contracts` | `Destructible.sol` | `destroy` | 19–21 | MIT | Termination (selfdestruct to owner) |
| **CAN-044** | `openzeppelin_contracts` | `Destructible.sol` | `destroyAndSend` | 23–25 | MIT | Termination (selfdestruct to recipient) |
| **CAN-045** | `crytic_not_so_smart_contracts`| `WalletLibrary.sol`| `kill` | 223–225 | Apache-2.0 | Termination & Legal Compliance |
| **CAN-046** | `crytic_not_so_smart_contracts`| `coin.sol` | `migrate_and_destroy` | 179–182 | Apache-2.0 | Termination (suicide to owner) |
| **CAN-047** | `crytic_not_so_smart_contracts`| `Lottery.sol` | `kill` | 74–78 | Apache-2.0 | Termination (selfdestruct to owner) |
| **CAN-048** | `openzeppelin_contracts` | `TimelockController.sol` | `updateDelay` | 351–356 | MIT | Clean Control (enforced timelock) |
| **CAN-049** | `openzeppelin_contracts` | `PaymentSplitter.sol` | `release` | 145–161 | MIT | Clean Control (deterministic release) |
| **CAN-050** | `compound_protocol` | `CToken.sol` | `_setReserveFactorFresh` | 936–958 | BSD-3-Clause | Clean Control (bounded reserve cap) |
| **CAN-051** | `compound_protocol` | `Comptroller.sol` | `_setCloseFactor` | 849–858 | BSD-3-Clause | Payment / Financial & Legal Compliance |
| **CAN-052** | `ens_domains` | `TextResolver.sol` | `setText` | 18–25 | MIT | Clean Control (generic key-value string) |
| **EXP-001** | `uniswap_v3_adapter` | `V3FeeAdapter.sol` | `setDefaultFeeByFeeTier` | 98–101 | MIT | Payment / Financial & Legal Compliance |
| **EXP-002** | `spectral_image_vaults` | `AutonomousAgentDeployer.sol` | `setParameter` | 470–475 | MIT | Legal Compliance (>=5 admin routines) |
| **EXP-003** | `spectral_image_vaults` | `AgentToken.sol` | `setTaxPercentage` | 120–125 | MIT | Payment / Financial (100% tax ceiling) |
| **EXP-004** | `linea_contracts` | `RollupRevenueVault.sol` | `updateInvoicePaymentReceiver` | 207–215 | Apache-2.0 | Clean Control (role-governed receiver) |
| **EXP-005** | `the_compact` | `AllocatorLogic.sol` | `registerAllocator` | 80–92 | MIT | Clean Control (non-zero address check) |
| **EXP-006** | `zk_token_distribution` | `ZkCappedMinter.sol` | `mint` | 45–55 | MIT | Clean Control (bounded mint cap) |

### 4.2 Excluded Candidates ($N=10$)
Candidates were strictly excluded in accordance with project licensing and data integrity standards:
* **`EXC-001` (`suicidal.sol`, Slither tests)**: Licensed under `AGPL-3.0` (copyleft constraint requiring commercial license review).
* **`EXC-002` (`Selfdestruct.sol`, DeFiVulnLabs)**: Unclear / unlicensed repository (no SPDX header).
* **`EXC-003`–`EXC-006` (Zenith SSI Protocol: `USSI.sol`, `AssetFactory.sol`, `AssetIssuer.sol`, `AssetLocking.sol`)**: Licensed under `BUSL-1.1` (Business Source License 1.1; proprietary/restricted).
* **`EXC-007` (`LevelReserveLensChainlinkOracle.sol`, Level Money)**: Licensed under `BUSL-1.1`.
* **`EXC-008`–`EXC-009` (`ResourceManager.sol`, `UNIVesting.sol`, Uniswap Unification)**: Licensed under `AGPL-3.0-only`.
* **`EXC-010` (`EVMAuthExpiringERC1155.sol`, Radius EVMAuth)**: Excluded due to audit finding mismatch and missing external authorization contracts (`insufficient_information`).

### 4.3 Separated Synthetic Benchmark Controls ($N=6$)
* `CAN-037`–`CAN-042` (`BM001_VulnerableEscrow.sol` through `BM005_StandardGovernanceToken.sol`): Maintained as isolated dev/regression controls; prohibited from validation and test splits.

---

## 5. AI Review Methodology & Disagreement Log Summary

All records underwent two independent review passes (`agent_1` and `agent_2`). In accordance with project instructions:
* **`human_verified: false`**: Maintained across all records. AI agreement is never claimed to establish ground truth.
* **Disagreements Resolved Transparently**:
  - `EXP-003` (`setTaxPercentage`): Resolved to `positive` because setting a tax ceiling of 10,000 basis points equals a confiscatory 100% tax under Section 2.2 and Section 6.3 of the Annotation Guide.
  - `CAN-045` (`WalletLibrary.sol`): Resolved to `positive` for Legal Compliance after AST inspection verified >10 privileged administrative functions without timelock inheritance.
  - `EXP-001` (`V3FeeAdapter.sol`): Resolved to `positive` for Legal Compliance based on multi-role privilege concentration without timelock inheritance.

---

## 6. Proposed Project-Grouped Split Plan & Support Matrix

To prevent data leakage, contracts from the same `project_id` must reside in the exact same split. The proposed grouped partition allocates the 9 project families as follows:
* **Train ($N=8$, 3 Projects)**: `uniswap_v3_adapter`, `openzeppelin_contracts`, `the_compact`.
* **Validation ($N=4$, 2 Projects)**: `spectral_image_vaults`, `linea_contracts`.
* **Test ($N=4$, 4 Projects)**: `crytic_not_so_smart_contracts`, `compound_protocol`, `ens_domains`, `zk_token_distribution`.

### Per-Category Real-Source Positive Support Across Splits:

```
+---------------------+---------------+-------------------+---------------+-----------------------------------------+
| Category            | Train Support | Validation Support| Test Support  | Cross-Split Viability Outcome           |
+---------------------+---------------+-------------------+---------------+-----------------------------------------+
| Privacy             | 0 / 8 (0.0%)  | 0 / 4 (0.0%)      | 0 / 4 (0.0%)  | ❌ CRITICAL GAP: Zero support in all 3 splits |
| Termination         | 2 / 8 (25.0%) | 0 / 4 (0.0%)      | 3 / 4 (75.0%) | ⚠️ PARTIAL GAP: Zero support in Validation   |
| Legal Compliance    | 1 / 8 (12.5%) | 1 / 4 (25.0%)     | 2 / 4 (50.0%) | ✅ VIABLE: Real positive in Train, Val, Test|
| Liability           | 0 / 8 (0.0%)  | 0 / 4 (0.0%)      | 0 / 4 (0.0%)  | ❌ CRITICAL GAP: Zero support in all 3 splits |
| Payment / Financial | 1 / 8 (12.5%) | 1 / 4 (25.0%)     | 1 / 4 (25.0%) | ✅ VIABLE: Real positive in Train, Val, Test|
+---------------------+---------------+-------------------+---------------+-----------------------------------------+
```

---

## 7. Data Quality & Dataset Validator Results

The existing validation tool [`analysis/ml_dataset_validator.py`](file:///c:/ARO/Projects/Smart_Contract_Analyser/analysis/ml_dataset_validator.py) was executed directly against `data/ml_candidates/expansion_candidate_package/expansion_candidates.jsonl`:

```
Target File: data/ml_candidates/expansion_candidate_package/expansion_candidates.jsonl
Total Records: 16
Is Valid: True (0 Schema or Integrity Errors)
Warnings: 0
Split Readiness Assessment: Split is NOT READY (candidate pool is in unassigned status pending human review; 16 records across 9 projects).
```

Full automated regression test suite (`python -m pytest tests/`):
```
Results: 32 passed, 0 failed in 23.44s.
```

---

## 8. Root-Cause Analysis: The Structural Scarcity of Privacy and Liability in Real Contracts

The critical finding of this benchmark expansion milestone is the **systematic absence of real-source positive examples for Privacy and Liability**:

1. **Why Real Smart Contracts Lack Privacy Positives**:
   - Public blockchain immutability and data privacy laws (GDPR) make storing plaintext natural-person PII (`string public email`, `streetAddress`, `ssn`) a severe anti-pattern. 
   - Real-world identity and registry protocols (such as ENS, EAS, Worldcoin, and Proof of Humanity) store cryptographic commitments, Merkle roots, or IPFS hashes (`bytes32`). Under Section 2.3 of [ANNOTATION_GUIDE.md](file:///c:/ARO/Projects/Smart_Contract_Analyser/docs/ANNOTATION_GUIDE.md), cryptographic hashes are **explicitly defined as Negative counterexamples**.
2. **Why Real Smart Contracts Lack NatSpec Liability Positives**:
   - Open-source smart contract developers place liability waivers ("AS IS", waiver of warranty) in standalone repository `LICENSE` files or frontend Terms of Service, **never** in NatSpec docstrings inside Solidity contract files.
   - Under Section 2.4 of [ANNOTATION_GUIDE.md](file:///c:/ARO/Projects/Smart_Contract_Analyser/docs/ANNOTATION_GUIDE.md), standard SPDX tags (`// SPDX-License-Identifier: MIT`) and external `LICENSE` files explicitly do **not** trigger `RULE-LIAB-01`.
3. **Prohibition Against Synthetic Backfilling**:
   - In accordance with project instructions, synthetic examples cannot be used to fill held-out evaluation gaps in validation or test splits. Using synthetic data in validation or test would measure toy pattern memorization rather than real-world generalizability.

---

## 9. Final Recommendation on Dataset Versioning

> [!CAUTION]
> **Definitive Recommendation: INSUFFICIENT to Prepare a New Dataset Version (`v4.0.0`)**
> 
> The candidate expansion package is **INSUFFICIENT** to justify preparing, freezing, or releasing a new dataset version at this time.
> 
> **Core Rationale**:
> 1. **Persistent Zero-Support Failure**: If a new dataset version were generated from these real candidates, **Privacy** and **Liability** would still have **zero positive examples in both Validation and Test**.
> 2. **Threshold Calibration Remains Impossible**: Validation would still have zero positive examples for Privacy, Liability, and Termination, causing threshold calibration to fail exactly as it did in the `v3.3.0` experiment.
> 3. **Mathematical Inconclusiveness**: Evaluating a Legal-BERT model on this expansion would continue to report `0.0000 F1` / `inconclusive_zero_positive_support` on test for Privacy and Liability.
> 
> **Required Next Steps Prior to Dataset v4.0.0**:
> 1. Conduct a dedicated data acquisition pass targeting niche decentralized identity projects (e.g., legacy ERC-725/ERC-735 identity claims or off-chain attestation schemas) to identify real, licensed Solidity contracts declaring natural-person PII.
> 2. Alternatively, seek formal project specification amendments authorizing a defined, hybrid benchmark protocol that explicitly permits calibrated synthetic examples for categories where mainnet codebases exhibit structural absence.
> 3. Until such support is verified across all three splits for all five categories, the project should remain frozen at `v3.3.0` with expansion candidates preserved strictly in the candidate stage.
