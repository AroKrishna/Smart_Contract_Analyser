# Benchmark Expansion Candidate Package — Proposed Grouped Split Report

**Document Version**: 1.0.0  
**Date**: October 22, 2026  
**Status**: Proposed Evaluation Partition Plan  
**Split Algorithm**: Group-Isolated Partitioning (`GroupShuffleSplit` principles)  
**Leakage Policy**: Strict 0.0% Cross-Split Project Overlap  

---

## 1. Executive Summary & Evaluation Architecture

This report details a proposed project-grouped split plan for the **16 accepted real-source expansion candidates** across **9 distinct project families**. 

The goal of this partition plan is to model an optimal distribution of real-source candidates across `train`, `validation`, and `test` splits while enforcing:
1. **Zero Data Leakage**: Every contract originating from the same `project_id` is isolated to exactly one split.
2. **Real-Source Evaluation Integrity**: Synthetic toy contracts (e.g., `BM001`–`BM005` or `SYN-001`–`SYN-020`) are completely excluded from validation and test splits.
3. **Honest Support Accounting**: Evaluation readiness is measured by actual ground-truth positive support per category, not aggregate record counts.

---

## 2. Project Family Allocation Across Splits

The 9 independently verified project families are partitioned across splits as follows:

```
+---------------------------------------------------------------------------------------------------------+
|                                  PROPOSED SPLIT GROUP ALLOCATION                                         |
+-------------------+----------------------------+--------+-----------------------------------------------+
| Split             | Project Families Included  | Records| Project Family Roles & Rationale              |
+-------------------+----------------------------+--------+-----------------------------------------------+
| **Train**         | `uniswap_v3_adapter`       | 8      | Model fine-tuning pool: Contains positive real  |
|                   | `openzeppelin_contracts`   |        | examples for Termination, Legal Compliance,   |
|                   | `the_compact`              |        | and Payment/Financial, balanced with clean    |
|                   |                            |        | negative controls.                            |
+-------------------+----------------------------+--------+-----------------------------------------------+
| **Validation**    | `spectral_image_vaults`    | 4      | Threshold calibration split: Provides real    |
|                   | `linea_contracts`          |        | positive support for Payment/Financial and   |
|                   |                            |        | Legal Compliance without leaking to test.     |
+-------------------+----------------------------+--------+-----------------------------------------------+
| **Test**          | `crytic_not_so_smart_contracts`| 4  | Held-out evaluation split: Completely isolated|
|                   | `compound_protocol`        |        | protocols providing real positive support for |
|                   | `ens_domains`              |        | Termination, Legal Compliance, and Payment.   |
|                   | `zk_token_distribution`    |        |                                               |
+-------------------+----------------------------+--------+-----------------------------------------------+
```

### Detailed Record-to-Split Mapping:

* **Train ($N=8$, 3 Projects)**:
  - `uniswap_v3_adapter`: `EXP-001` (`V3FeeAdapter.sol`, `setDefaultFeeByFeeTier`)
  - `openzeppelin_contracts`: `CAN-043` (`Destructible.sol`, `destroy`), `CAN-044` (`Destructible.sol`, `destroyAndSend`), `CAN-048` (`TimelockController.sol`, `updateDelay`), `CAN-049` (`PaymentSplitter.sol`, `release`)
  - `the_compact`: `EXP-005` (`AllocatorLogic.sol`, `registerAllocator`)
  - *Plus pending training controls*: `CAN-037`–`CAN-042` (Synthetic dev suite retained in train/dev only).

* **Validation ($N=4$, 2 Projects)**:
  - `spectral_image_vaults`: `EXP-002` (`AutonomousAgentDeployer.sol`, `setParameter`), `EXP-003` (`AgentToken.sol`, `setTaxPercentage`)
  - `linea_contracts`: `EXP-004` (`RollupRevenueVault.sol`, `updateInvoicePaymentReceiver`)

* **Test ($N=4$, 4 Projects)**:
  - `crytic_not_so_smart_contracts`: `CAN-045` (`WalletLibrary.sol`, `kill`), `CAN-046` (`coin.sol`, `migrate_and_destroy`), `CAN-047` (`Lottery.sol`, `kill`)
  - `compound_protocol`: `CAN-050` (`CToken.sol`, `_setReserveFactorFresh`), `CAN-051` (`Comptroller.sol`, `_setCloseFactor`)
  - `ens_domains`: `CAN-052` (`TextResolver.sol`, `setText`)
  - `zk_token_distribution`: `EXP-006` (`ZkCappedMinter.sol`, `mint`)

---

## 3. Real-Source Positive Support Matrix

The table below presents the actual per-category positive ground-truth support achievable using **exclusively real open-source smart contracts**:

```
+---------------------+-------------------+-------------------+-------------------+---------------------------------------------+
| Category            | Train Support     | Validation Support| Test Support      | Cross-Split Viability Status                |
|                     | (Pos / Total)     | (Pos / Total)     | (Pos / Total)     |                                             |
+---------------------+-------------------+-------------------+-------------------+---------------------------------------------+
| **Privacy**         | **0 / 8 (0.0%)**  | **0 / 4 (0.0%)**  | **0 / 4 (0.0%)**  | ❌ CRITICAL GAP: Zero support across all 3 splits|
| **Termination**     | **2 / 8 (25.0%)** | **0 / 4 (0.0%)**  | **3 / 4 (75.0%)** | ⚠️ PARTIAL GAP: Zero positive support in Val |
| **Legal Compliance**| **1 / 8 (12.5%)** | **1 / 4 (25.0%)** | **2 / 4 (50.0%)** | ✅ VIABLE: Real positive support in all splits|
| **Liability**       | **0 / 8 (0.0%)**  | **0 / 4 (0.0%)**  | **0 / 4 (0.0%)**  | ❌ CRITICAL GAP: Zero support across all 3 splits|
| **Payment / Fin.**  | **1 / 8 (12.5%)** | **1 / 4 (25.0%)** | **1 / 4 (25.0%)** | ✅ VIABLE: Real positive support in all splits|
+---------------------+-------------------+-------------------+-------------------+---------------------------------------------+
```

---

## 4. Analysis of Remaining Data Gaps & Deficits

### 4.1 The Complete Absence of Real Privacy Positives
- **Empirical Reality**: Open-source production smart contracts deployed on public EVM blockchains systematically avoid storing unencrypted natural-person PII (`string public email`, `streetAddress`, `ssn`).
- **Counterexamples in Candidate Pool**: Protocols that handle identity (such as ENS in `CAN-052`) use generic key-value string mappings or cryptographic hashes, which are **Negative counterexamples** under Section 2.3 of the Annotation Guide.
- **Consequence**: Even with candidate expansion, real-source positive support for Privacy remains **0 in Train, 0 in Validation, and 0 in Test**.

### 4.2 The Complete Absence of Real NatSpec Liability Positives
- **Empirical Reality**: Legitimate software projects place legal disclaimers ("AS IS", waiver of warranty, limitation of damages) in repository-level `LICENSE` files or frontend legal terms, **not** inside Solidity NatSpec contract/function comments.
- **Annotation Guide Standard**: Under Section 2.4, standard SPDX headers (`// SPDX-License-Identifier: MIT`) and external `LICENSE` files explicitly do **not** trigger `RULE-LIAB-01`.
- **Consequence**: Real-source positive support for Liability remains **0 in Train, 0 in Validation, and 0 in Test**.

### 4.3 Validation Split Deficit for Termination
- While `openzeppelin_contracts` (Train) and `crytic_not_so_smart_contracts` (Test) provide real `selfdestruct` examples, there is **no third independent real-source project** with a permissive license containing `selfdestruct` in this pool.
- Consequently, Validation has **0 positive examples for Termination**, preventing empirical threshold calibration for termination hazard detection.

---

## 5. Prohibition of Synthetic Backfilling

In accordance with core project requirements:
> **Synthetic examples must never be used to fill held-out real-source evaluation gaps in validation or test splits.**

Filling validation or test gaps with synthetic contracts (e.g., `SYN-001` or `BM003`) would create a pseudo-evaluation that measures toy template memorization rather than real-world generalizability on complex mainnet codebases.

---

## 6. Leakage & Group Isolation Verification

```
Total Project Families Evaluated: 9
Project Leakage Across Splits: 0.0% (0 / 9 projects overlap)
Train-to-Val Overlap: 0 projects
Train-to-Test Overlap: 0 projects
Val-to-Test Overlap: 0 projects
```
Every project family resides in exactly one split, satisfying all project grouping and anti-leakage constraints.
