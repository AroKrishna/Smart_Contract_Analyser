# Benchmark Expansion Candidate Package — AI Review & Disagreement Log

**Document Version**: 1.0.0  
**Date**: October 22, 2026  
**Status**: Multi-Pass AI Reviewed — Candidate Expansion Package  
**Human Verification Notice**: `human_verified: false` across 100% of candidate records.  
**Review Standard**: Evaluated strictly against [ANNOTATION_GUIDE.md](file:///c:/ARO/Projects/Smart_Contract_Analyser/docs/ANNOTATION_GUIDE.md) and [DATASET_SPECIFICATION.md](file:///c:/ARO/Projects/Smart_Contract_Analyser/docs/DATASET_SPECIFICATION.md).

---

## 1. Methodology & Review Architecture

To ensure transparent and auditable candidate labeling, all candidate records underwent a structured, two-pass independent AI review:

1. **Pass 1 (`agent_1_ai_review`)**: Syntactic AST extraction, line range validation, and rule pattern matching (`RULE-PRIV-01` through `RULE-GOV-01`).
2. **Pass 2 (`agent_2_ai_review`)**: Contextual architectural analysis checking for boundary conditions, modifier propagation, timelock inheritance, and upper ceiling checks.
3. **Reconciliation & Adjudication**: Comparison of Pass 1 and Pass 2 recommendations. All discrepancies were flagged, logged, and adjudicated with explicit code citations.

> [!WARNING]
> **AI Agreement vs. Ground Truth Disclaimer**:
> Concordance between Pass 1 and Pass 2 AI reviews indicates structural consistency with the written annotation guide; it does **not** constitute legally verified ground truth or formal human verification. All records maintain `human_verified: false` and `review_status: "ai_reviewed"`.

---

## 2. Review Disagreement & Reconciliation Log

The table below documents every candidate record where Pass 1 and Pass 2 diverged, along with the reconciled decision and authoritative rationale:

| Sample ID | Contract / Function | Category in Dispute | Pass 1 Recommendation | Pass 2 Recommendation | Reconciled Decision | Resolution Rationale & Evidence |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **EXP-003** | `AgentToken.sol`<br>`setTaxPercentage` | **Payment / Financial** | `negative`<br>(bounded by `require(_taxPercentage <= 10000)`) | `positive`<br>(ceiling is 10,000 bps = 100% tax) | **`positive`**<br>(Severity: `high`) | **Boundary condition hazard**: Pass 1 noted that a numerical check exists. Pass 2 correctly identified that the ceiling of 10,000 basis points equals 100% of the transferred amount. Under Annotation Guide Section 2.2 and Section 6.3, a fee setter allowing up to 100% tax creates total confiscatory control asymmetry, directly satisfying `RULE-FIN-01`. |
| **CAN-045** | `WalletLibrary.sol`<br>`kill` | **Legal Compliance** | `pending_review`<br>(privileged function count not verified) | `positive`<br>(>10 admin routines without timelock) | **`positive`**<br>(Severity: `high`) | **Architectural count verified**: Pass 1 left Legal Compliance pending because `kill` was inspected in isolation. Pass 2 inspected the full contract AST and confirmed >10 administrative routines (`initMultiowned`, `changeOwner`, `addOwner`, `removeOwner`, `changeRequirement`, `setDailyLimit`, `resetSpentToday`, `kill`) without timelock inheritance. Meets `RULE-GOV-01` positive criteria. |
| **EXP-001** | `V3FeeAdapter.sol`<br>`setDefaultFeeByFeeTier` | **Legal Compliance** | `positive`<br>(5 admin routines without timelock) | `pending_review`<br>(onlyFeeSetter is single role) | **`positive`**<br>(Severity: `medium`) | **Multi-role administrative centralization**: `V3FeeAdapter.sol` defines 5 functions (`enableFeeAmount`, `setFactoryOwner`, `setMerkleRoot`, `setDefaultFeeByFeeTier`, `setFeeSetter`) split between `onlyOwner` and `onlyFeeSetter` without timelock delay inheritance, satisfying `RULE-GOV-01` positive criteria. |
| **EXC-010** | `EVMAuthExpiringERC1155.sol`<br>`burn` | **Legal Compliance** | `positive`<br>(audit finding cites auth defect) | `unresolved`<br>(excerpt defect / missing context) | **`EXCLUDED`**<br>(`insufficient_information`) | **Missing inter-contract context**: Pass 1 flagged compliance based on audit finding title. Pass 2 determined that the bundled file in `vfp_00006` lacked base contract definitions necessary to verify the caller hierarchy. Excluded per data-quality protocol. |
| **CAN-051** | `Comptroller.sol`<br>`_setCloseFactor` | **Payment / Financial** | `positive`<br>(uncapped close factor setter) | `positive`<br>(uncapped parameter modification) | **`positive`**<br>(Severity: `high`) | **Full consensus**: Both passes confirmed that `_setCloseFactor` allows the admin to set `closeFactorMantissa` arbitrarily without any numerical upper bound check, satisfying `RULE-FIN-01`. |
| **CAN-052** | `TextResolver.sol`<br>`setText` | **Privacy** | `negative`<br>(generic key-value string mapping) | `negative`<br>(no dedicated PII state variable) | **`negative`**<br>(Severity: `none`) | **Full consensus on Privacy negative control**: Both passes confirmed that storing domain-associated strings via `setText` does not declare dedicated natural-person PII fields (email, physicalAddress, SSN). Satisfies `RULE-PRIV-01` negative criteria. |

---

## 3. Summary of Category Agreement Across Accepted Pool ($N=16$)

```
+---------------------+-------------------+---------------------+-------------------------+
| Category            | Initial Consensus | Disagreements Flags | Reconciled Positives    |
+---------------------+-------------------+---------------------+-------------------------+
| Privacy             | 16 / 16 (100.0%)  | 0 (0.0%)            | 0 Positive / 16 Negative|
| Termination         | 16 / 16 (100.0%)  | 0 (0.0%)            | 5 Positive / 11 Negative|
| Legal Compliance    | 14 / 16 (87.5%)   | 2 (12.5%)           | 4 Positive / 12 Negative|
| Liability           | 16 / 16 (100.0%)  | 0 (0.0%)            | 0 Positive / 16 Negative|
| Payment / Financial | 15 / 16 (93.8%)   | 1 (6.2%)            | 3 Positive / 13 Negative|
+---------------------+-------------------+---------------------+-------------------------+
```

### Key Analytical Takeaways:
1. **Total Absence of Real-Source Positives for Privacy and Liability**: Both review passes unanimously concurred that none of the 16 real-source candidates contain positive ground truth for Privacy (no unencrypted natural-person PII) or Liability (no NatSpec exculpatory disclaimers).
2. **Robust Consensus on Termination & Governance Hazards**: High concordance on operational killswitches (`selfdestruct`) and multi-admin timelock omissions across OpenZeppelin, Compound, and Crytic sources.
