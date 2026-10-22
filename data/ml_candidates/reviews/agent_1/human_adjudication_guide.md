# Smart Contract Analyser — Human Adjudication Guide (Agent 1 Review)

**Document Version**: 1.0.0  
**Target Review Package**: `data/ml_candidates/reviews/agent_1/`  
**Dataset Authority**: [ANNOTATION_GUIDE.md](file:///c:/ARO/Projects/Smart_Contract_Analyser/docs/ANNOTATION_GUIDE.md) & [DATASET_SPECIFICATION.md](file:///c:/ARO/Projects/Smart_Contract_Analyser/docs/DATASET_SPECIFICATION.md)  
**Date**: 2026-10-21  

> [!IMPORTANT]
> **Adjudicator Mandate**: Agent 1 has provided evidence-grounded **AI recommendations**, not human verification. A qualified human reviewer must review the specific code evidence and adjudicate the 8 core decisions and 36 candidate-level recommendations detailed below before any candidate record can be marked `reviewed` or assigned to a dataset split.

---

## 1. Core Adjudication Decisions for the Human Reviewer

### Decision 1: Resolving Source Commit Drift & Missing Dependencies
* **Affected Candidates**: `CAN-001` ([AgentImageService.sol](file:///c:/ARO/Projects/Smart_Contract_Analyser/data/forge_curated_samples/vfp_00001.json)), `CAN-005` ([USSI.sol](file:///c:/ARO/Projects/Smart_Contract_Analyser/data/forge_curated_samples/vfp_00002.json)), `CAN-033` ([NitroContracts2Point1Point3UpgradeAction.sol](file:///c:/ARO/Projects/Smart_Contract_Analyser/data/forge_curated_samples/vfp_00191.json)).
* **Evidence Conflict**:
  - `CAN-001`: The audit finding cites `issueRefund` at line 299 stealing funds. The bundled code ends at line 285 and only contains `requestRefund(L219-L242)` with `require(request.user == msg.sender)`.
  - `CAN-005`: Raw finding 1 references `HedgeOrder.sol`, which is completely absent from the raw FORGE file `vfp_00002.json`.
* **Decision Required**:
  1. For `CAN-001`: Retrieve the exact commit hash evaluated during the audit report, or re-scope the candidate strictly to the bundled `requestRefund` function and reject the audit finding premise.
  2. For `CAN-005`: Decide whether `USSI.sol` can be adjudicated as a standalone contract or must remain `unresolved` until `HedgeOrder.sol` is fetched.

---

### Decision 2: Approving Pipeline Re-Extraction for 7 Header Fallback Candidates
* **Affected Candidates**: `CAN-010`, `CAN-011`, `CAN-012`, `CAN-014`, `CAN-018`, `CAN-021`, `CAN-022`.
* **Defect**: The automated generator failed to locate the cited functions and extracted lines `[1, 20-34]` (1200-character file headers containing pragmas and imports) as `solidity_context`.
* **Action Required**:
  - Approve re-extracting with verified function line targets:
    - `CAN-010` / `CAN-011`: Target `_pruneGroups` (L177-L210) or `setTTL` (L251-L260) in [EVMAuthExpiringERC1155.sol](file:///c:/ARO/Projects/Smart_Contract_Analyser/data/forge_curated_samples/vfp_00006.json).
    - `CAN-012`: Target `latestRoundData` (L122-L148) in [LevelReserveLensChainlinkOracle.sol](file:///c:/ARO/Projects/Smart_Contract_Analyser/data/forge_curated_samples/vfp_00016.json).
    - `CAN-014`: Target `_deposit` (L187-L205) in [AvKATVault.sol](file:///c:/ARO/Projects/Smart_Contract_Analyser/data/forge_curated_samples/vfp_00021.json).
    - `CAN-018`: Target `votingDelay()` (L69-L72) in [AnvilGovernorDelegate.sol](file:///c:/ARO/Projects/Smart_Contract_Analyser/data/forge_curated_samples/vfp_00030.json).
    - `CAN-021`: Target `initialize` (L58-L74) in [RollupRevenueVault.sol](file:///c:/ARO/Projects/Smart_Contract_Analyser/data/forge_curated_samples/vfp_00050.json).
    - `CAN-022`: Target `fallback` (L266-L275) in [RollupRevenueVault.sol](file:///c:/ARO/Projects/Smart_Contract_Analyser/data/forge_curated_samples/vfp_00050.json).

---

### Decision 3: Confirming Positive Finding on Unconstrained Fee Setter (`CAN-015`)
* **Affected Candidate**: `CAN-015` ([V3FeeAdapter.sol::setDefaultFeeByFeeTier](file:///c:/ARO/Projects/Smart_Contract_Analyser/data/forge_curated_samples/vfp_00026.json#L98-L101)).
* **Code Evidence**:
  ```solidity
  function setDefaultFeeByFeeTier(uint24 feeTier, uint8 defaultFeeValue) external onlyFeeSetter {
    require(_feeTierExists(feeTier), InvalidFeeTier());
    defaultFees[feeTier] = defaultFeeValue;
  }
  ```
* **Decision Required**: Confirm that `defaultFees[feeTier] = defaultFeeValue` lacks an upper ceiling check, validating the label `Payment / Financial: positive` (severity: `high`) under `RULE-FIN-01`.

---

### Decision 4: Confirming Positive Determinations on Administrative Privilege Concentration (`RULE-GOV-01`)
* **Affected Candidates**: `CAN-005`, `CAN-006`, `CAN-007`, `CAN-008`, `CAN-009`, `CAN-013`, `CAN-014`, `CAN-015`, `CAN-016`, `CAN-023`, `CAN-030`, `CAN-031`.
* **Standard**: Contracts defining **>= 3 privileged functions** (restricted by `onlyOwner`, `onlyRole`, `auth`) without timelock inheritance are labeled positive for `Legal Compliance` under `RULE-GOV-01`.
* **Decision Required**: Confirm whether single-contract privilege concentration without timelock queues constitutes a positive operational hazard in the training ground truth for these 12 candidates.

---

### Decision 5: Adjudicating Complex Financial Edge Cases (12 Pending Review Records)
* **Affected Candidates**: `CAN-003`, `CAN-004`, `CAN-006`, `CAN-008`, `CAN-019`, `CAN-023`, `CAN-027`, `CAN-029`, `CAN-030`, `CAN-031`, `CAN-035`, `CAN-036`.
* **Specific Issues**:
  - `CAN-003` & `CAN-004`: Does interacting with fee-on-transfer tokens qualify as an operational financial hazard when token transfer applies a 100% max cap?
  - `CAN-019`: Does hardcoded request index 0 in `BlueprintCore.sol` overwriting user balances constitute `Payment / Financial: positive` (fund loss) or an unclassified software bug?
  - `CAN-023`: Does lack of slippage minimum output in DEX bridge swap constitute `Payment / Financial: positive`?
  - `CAN-031`: Does out-of-gas failure in refund iteration array warrant `Payment / Financial: positive`?
  - `CAN-036`: Does admin sweeping of unclaimed tokens after an airdrop window warrant a positive financial hazard label?

---

### Decision 6: Confirming Termination and Liability Negatives Across the Corpus
* **Negative Status Confirmation**:
  - `Termination`: Confirm that temporary circuit breakers and pause mechanisms (`whenNotPaused`, `_pause()`) do NOT trigger `RULE-TERM-01`. Confirm `negative` status across all 36 candidates (0 `selfdestruct` opcodes found).
  - `Liability`: Confirm that standard open-source license headers (`// SPDX-License-Identifier: MIT`) and technical architectural notes do NOT trigger `RULE-LIAB-01`. Confirm `negative` status across all 36 candidates.

---

### Decision 7: Replacing Boilerplate `model_text` with Structured Representations
* **Context**: All 36 candidate records contain generic boilerplate that parrots audit titles: *"Draft Summary (Machine-generated, pending review): Contract ... Scope evaluates function ... Context: observable operations include state updates and token balances. Related audit observation: '...'"*
* **Decision Required**: Authorize updating `model_text` to the dual-stream structured format (`Contract`, `Function`, `Modifiers`, `Documented Intent`, `Operational Behavior`, `Key Code Logic`) proposed in [review_recommendations.jsonl](file:///c:/ARO/Projects/Smart_Contract_Analyser/data/ml_candidates/reviews/agent_1/review_recommendations.jsonl) to prevent Legal-BERT from memorizing audit titles.

---

### Decision 8: Legal Clearance & Split Isolation for Restricted Licenses (7 Records)
* **Affected Records**:
  - `CAN-005`, `CAN-006`, `CAN-007`, `CAN-008`, `CAN-009`, `CAN-012` (`BUSL-1.1`, SSI-Protocol / Level-Money)
  - `CAN-029` (`AGPL-3.0-only`, Uniswap-UNIfication)
* **Decision Required**: Obtain formal legal clearance confirming that fine-tuning Legal-BERT on BUSL-1.1 and AGPL-3.0 smart contract excerpts qualifies as permissible non-infringing research use, OR exclude all 7 candidates from training splits permanently.

---

## 2. Complete Candidate-by-Candidate Adjudication Checklist

| Candidate ID | Contract File | Target Function | Agent 1 Recommended Status | Primary Adjudication Decision Required |
| :--- | :--- | :--- | :--- | :--- |
| **`CAN-001`** | `AgentImageService.sol` | `requestRefund` | **`unresolved`** | Resolve commit drift: audit report line 299 vs bundled 285-line file. |
| **`CAN-002`** | `AgentImageService.sol` | `withdrawFees` | `in_review` | Confirm fee withdrawal by agent owner is negative for all hazards. |
| **`CAN-003`** | `AgentImageService.sol` | `requestImage` | `in_review` | Adjudicate fee-on-transfer accounting mismatch (`pending_review` vs `negative`). |
| **`CAN-004`** | `AgentToken.sol` | `transfer` | `in_review` | Adjudicate transfer tax override with 100% ceiling (`pending_review` vs `negative`). |
| **`CAN-005`** | `USSI.sol` | Entire Contract | **`unresolved`** | Confirm `Legal Compliance: positive` (11 admin functions); locate `HedgeOrder.sol`. |
| **`CAN-006`** | `Swap.sol` | `cancelSwapRequest` | `in_review` | Confirm `Legal Compliance: positive` (9 roles); adjudicate swap cancellation bug. |
| **`CAN-007`** | `AssetToken.sol` | `burn` | `in_review` | Confirm `Legal Compliance: positive` (14 roles); confirm burn is `Payment: negative`. |
| **`CAN-008`** | `AssetIssuer.sol` | `addMintRequest` | `in_review` | Confirm `Legal Compliance: positive` (9 admins); adjudicate mint fee rounding order. |
| **`CAN-009`** | `AssetLocking.sol` | `lock` | `in_review` | Confirm `Legal Compliance: positive` (5 admins); confirm safeTransfer suggestion is `negative`. |
| **`CAN-010`** | `EVMAuthExpiringERC1155.sol` | `burnExpired` | **`requires_source_revision`** | Re-extract source: `burnExpired` does not exist; range `[1, 34]` is file header. |
| **`CAN-011`** | `EVMAuthExpiringERC1155.sol` | `setExpiry` | **`requires_source_revision`** | Re-extract source: `setExpiry` does not exist; range `[1, 34]` is file header. |
| **`CAN-012`** | `LevelReserveLensChainlinkOracle.sol`| `getLatestPrice`| **`requires_source_revision`** | Re-extract source: target `latestRoundData`; range `[1, 23]` is pragma/ASCII art. |
| **`CAN-013`** | `AvKATVault.sol` | `initialize` | `in_review` | Confirm `Legal Compliance: positive` (5 roles); confirm `Termination: negative` (pausing != destroy). |
| **`CAN-014`** | `AvKATVault.sol` | `deposit` | **`requires_source_revision`** | Re-extract source: range `[1, 20]` captures imports; actual `_deposit` is at line 187. |
| **`CAN-015`** | `V3FeeAdapter.sol` | `setDefaultFeeByFeeTier` | `in_review` | Confirm **`Payment / Financial: positive`** (unconstrained fee setter under RULE-FIN-01). |
| **`CAN-016`** | `V3FeeAdapter.sol` | `collect` | `in_review` | Confirm `Legal Compliance: positive` (contract-level); confirm collect is `Payment: negative`. |
| **`CAN-017`** | `AnvilGovernorDelegate.sol` | `initialize` | `in_review` | Confirm negative for all hazards; inherits `GovernorTimelockControlUpgradeable`. |
| **`CAN-018`** | `AnvilGovernorDelegate.sol` | `_setVotingDelay` | **`requires_source_revision`** | Re-extract source: `_setVotingDelay` is in parent library; range `[1, 24]` is file header. |
| **`CAN-019`** | `BlueprintCore.sol` | `createCommonProjectID...` | `in_review` | Adjudicate hardcoded request index 0 overwriting user balances (`pending_review: high`). |
| **`CAN-020`** | `BlueprintCore.sol` | `setWorkerPublicKey` | `in_review` | Adjudicate missing access control on public key setter (`pending_review: high`). |
| **`CAN-021`** | `RollupRevenueVault.sol` | `initialize` | **`requires_source_revision`** | Re-extract source: range `[1, 25]` captures constants; `initialize` is at line 58. |
| **`CAN-022`** | `RollupRevenueVault.sol` | `fallback` | **`requires_source_revision`** | Re-extract source: range `[1, 25]` captures constants; `fallback` is at line 266. |
| **`CAN-023`** | `RollupRevenueVault.sol` | `burnAndBridge` | `in_review` | Confirm `Legal Compliance: positive` (6 roles); adjudicate DEX slippage output check. |
| **`CAN-024`** | `Receiver.sol` | `updateBlockHashProverCopy` | `in_review` | Confirm negative for all hazards (prover revert bug is code defect, not governance). |
| **`CAN-025`** | `ChainMap.sol` | `setChainMap` | `in_review` | Confirm negative for all hazards (technical "as is" comment is not liability waiver). |
| **`CAN-026`** | `AaveStrategyVault.sol` | `initialize` | `in_review` | Confirm negative for all hazards (redundant external call is gas issue). |
| **`CAN-027`** | `BridgeValidator.sol` | `setThreshold` | `in_review` | Adjudicate signature threshold configuration hygiene across bridge. |
| **`CAN-028`** | `BridgeValidator.sol` | `registerMessages` | `in_review` | Confirm `Termination: negative`; adjudicate pause bypass under `Legal Compliance`. |
| **`CAN-029`** | `ResourceManager.sol` | `setThreshold` | `in_review` | Flag license review (`AGPL-3.0`); adjudicate mempool threshold overpayment. |
| **`CAN-030`** | `Genesis.sol` | `participate` | `in_review` | Confirm `Legal Compliance: positive` (3 admins); adjudicate participant deposit risk. |
| **`CAN-031`** | `Genesis.sol` | `onGenesisFailed` | `in_review` | Confirm `Termination: negative`; adjudicate out-of-gas refund failure (`Payment: high`). |
| **`CAN-032`** | `AllocatorLogic.sol` | `_registerAllocator` | `in_review` | Adjudicate EOA allocator registration bypass under `Legal Compliance`. |
| **`CAN-033`** | `NitroContracts2Point1Point3...` | `bridge` | `in_review` | Adjudicate rollup downgrade action; verify if interface stub excerpt is sufficient. |
| **`CAN-034`** | `ZkCappedMinter.sol` | `mint` | `in_review` | Confirm `Payment / Financial: negative` (minting strictly bounded by hard supply cap). |
| **`CAN-035`** | `ZkMerkleDistributor.sol` | `claim` | `in_review` | Adjudicate Merkle distributor overall claim cap enforcement. |
| **`CAN-036`** | `ZkMerkleDistributor.sol` | `sweepUnclaimed` | `in_review` | Adjudicate admin sweeping of unclaimed tokens after sunset window. |

---

## 3. Final Adjudication Protocol & Sign-Off Requirements

To transition records from `in_review` to `reviewed`:
1. **Human Annotator ID**: Replace `"preliminary_pipeline"` in `provenance.annotator_id` with verified human evaluator identifier (e.g., `"human_expert_01"`).
2. **Authoritative Timestamp**: Update `provenance.annotation_date` to the date of human adjudication.
3. **Category Consensus**: Confirm final binary or multi-label status across all five categories with verified source code evidence.
4. **License Clearing**: Verify that no record with `license_status: "license_review_required"` is assigned to `train`, `validation`, or `test` splits.
5. **Split Assignment**: Once at least **5 distinct projects** are fully adjudicated and cleared, generate project-isolated splits enforcing project family grouping without data leakage.
