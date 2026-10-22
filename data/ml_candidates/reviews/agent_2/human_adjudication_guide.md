# Human Adjudication Guide — Agent 2 Independent Review

**Purpose:** This document guides a human annotator in resolving the open questions and disputes identified by Agent 2's independent review of the candidate dataset.  
**Important:** Agent 2 is an AI reviewer. The human adjudicator's decision overrides all AI recommendations.

---

## How to Use This Guide

For each Priority Group below, a human reviewer should:
1. Open the raw source file at the path indicated
2. Inspect the actual Solidity function referenced
3. Apply the annotation rules from `docs/ANNOTATION_GUIDE.md` to make a final determination
4. Update `review_status` to `reviewed` and record `adjudication_notes` in each candidate record

---

## Priority Group A — Critical: Require Source Replacement Before Classification

These records cannot be reliably classified because the `solidity_context` does not contain the claimed function body. Classification must be deferred until the source context is corrected.

### A1 — CAN-001: Commit Drift (requestRefund vs. issueRefund/approveRefund)

**Action required:**
1. Locate the original audited commit of `AgentImageService.sol` referenced by the audit report in `vfp_00001.json` (project: `2025-10-spectral-imageagent`)
2. Confirm whether `issueRefund`/`approveRefund` exist in that commit
3. Decide: keep this record pointing to `requestRefund` in the bundled commit, OR replace it with a record pointing to the audited commit's function
4. If keeping bundled commit: reclassify Legal Compliance and Payment/Financial — the bundled `requestRefund` has `request.user == msg.sender` guard which mitigates the diversion risk found in the audit

**Questions to answer:**
- Does the bundled commit represent the current deployed version or the audited version?
- If the audited version had `issueRefund`/`approveRefund`, should a separate record be created for those functions?

---

### A2 — CAN-005: Truncated Context (USSI.sol)

**Action required:**
1. Open `data/forge_curated_samples/vfp_00002.json`
2. Locate the `USSI.sol` contract in `affected_files`
3. Extract a meaningful function-level excerpt (e.g., the pause function placeholder, or the contract-level declaration block)
4. Replace `solidity_context` with the complete excerpt
5. Confirm whether a callable `pause()` function exists or only `_pause()` internal is inherited

**Key question:** Does the deployed USSI.sol expose a public `pause()` admin function, or only inherit `_pause()` internal from `PausableUpgradeable`?

---

### A3 — CAN-010 & CAN-011: EVMAuth Function Body Absent (burnExpired, setExpiry)

**Action required:**
1. Open `data/forge_curated_samples/vfp_00006.json`
2. Locate `evmauth-core/src/base/EVMAuthExpiringERC1155.sol` in `affected_files`
3. Find the `_burnGroupBalances`, `_pruneGroups`, and `_update` functions
4. Replace `solidity_context` for CAN-010 with the `_burnGroupBalances`/`_pruneGroups` function bodies
5. For CAN-011, extract the `setExpiry` or equivalent function body (search for the expiry-setting logic)
6. Two records CANNOT share identical `solidity_context` for different functions — one must be corrected

**Key questions:**
- Does `_pruneGroups` call `_burn` to update ERC1155 balances after removing expired groups? (Finding says NO — verify this independently)
- Does `_burnGroupBalances` use `to` instead of `from` when calling the burn function? (Finding says YES — verify)

---

### A4 — CAN-012: Oracle Function Body Absent (getLatestPrice)

**Action required:**
1. Open `data/forge_curated_samples/vfp_00016.json`
2. Locate `LevelReserveLensChainlinkOracle.sol` in `affected_files`
3. Extract the `getLatestPrice` function body
4. Replace `solidity_context` with the actual function (remove ASCII art from context)
5. Verify: does `getLatestPrice` return `1e18` (or equivalent hardcoded value) when the Chainlink oracle is paused?

**Key question:** Is the $1 fallback hardcoded or derived from a configurable parameter?

---

### A5 — CAN-014: AvKATVault deposit (Inherited Function)

**Action required:**
1. Locate the ERC4626Upgradeable base contract
2. Verify that `deposit` is NOT overridden in AvKATVault.sol
3. If not overridden: decide whether to keep this record (the context should then reference the parent ERC4626 implementation) or remove it
4. If there is a local override: extract it and replace `solidity_context`

**Finding to verify:** Does the inherited `deposit` call `safeTransferFrom` on a known-safe contract unnecessarily, as claimed?

---

### A6 — CAN-018: GovernorDelegate _setVotingDelay (Inherited Function)

**Action required:**
1. Locate `GovernorSettingsUpgradeable` from OpenZeppelin
2. Verify `_setVotingDelay` implementation
3. Confirm: does calling `_setVotingDelay(0)` bypass the governance timelock, or does it still require a governor proposal?
4. Update `solidity_context` with the relevant inherited function code

---

### A7 — CAN-021 & CAN-022: RollupRevenueVault (initialize, fallback)

**Action required:**
1. Open `data/forge_curated_samples/vfp_00050.json`
2. Locate `RollupRevenueVault.sol` in `affected_files`
3. Extract the `initialize` function body (10-parameter signature) for CAN-021
4. Extract the `fallback` function body for CAN-022
5. Replace `solidity_context` for both records (they currently share the same file header excerpt)
6. Verify finding 0: does the deployment script actually call a zero-parameter `initialize()` which routes to the fallback?
7. Determine patch status: was this fixed before mainnet activation?

**Key questions:**
- Has this vulnerability been patched in the deployed contract?
- If patched: should severity be downgraded or the record removed from the training set?

---

### A8 — CAN-033: Arbitrum Nitro (Wrong Function — bridge interface vs. perform)

**Action required:**
1. Open `data/forge_curated_samples/vfp_00191.json`
2. Locate `NitroContracts2Point1Point3UpgradeAction.sol` in `affected_files`
3. Find the `perform()` function (the actual upgrade action logic)
4. Replace `function_name` with `"perform"` and replace `solidity_context` with the `perform()` function body
5. Verify: does the upgrade action fail to check that the current version is not already above 2.2.3?

---

## Priority Group B — Mislabeled Categories (Require Human Correction)

These records have category statuses that are contradicted by the annotation guide. A human must confirm and then update the candidate record.

### B1 — CAN-013: Termination and Legal Compliance (AvKATVault.initialize)

**Agent 2 finding:** Termination is `pending_review` because of `_pause()` call. Per annotation guide §2.2, `_pause()` does NOT satisfy RULE-TERM-01 (requires selfdestruct or equivalent).

**Human action:** 
- [ ] Confirm Termination = `negative`
- [ ] Confirm Legal Compliance = `negative` (Informational finding about initialization ordering is not RULE-GOV-01)
- [ ] Update both fields

---

### B2 — CAN-016: Payment/Financial (V3FeeAdapter.collect)

**Agent 2 finding:** `pending_review medium` for an Informational type-cast finding. No funds at risk.

**Human action:**
- [ ] Confirm Payment/Financial = `negative`
- [ ] Update field

---

### B3 — CAN-017: Legal Compliance (AnvilGovernorDelegate.initialize)

**Agent 2 finding:** `pending_review` claimed but the contract explicitly initializes `GovernorTimelockControlUpgradeable` with a timelock — this is a NEGATIVE indicator for RULE-GOV-01.

**Human action:**
- [ ] Verify that `GovernorTimelockControlUpgradeable` is indeed initialized with a non-zero delay
- [ ] If yes: confirm Legal Compliance = `negative`
- [ ] Update field

---

### B4 — CAN-026: Legal Compliance (AaveStrategyVault.initialize)

**Agent 2 finding:** `pending_review` for an Informational gas optimization finding. `initialize()` is a one-time setup and should not be counted toward RULE-GOV-01.

**Human action:**
- [ ] Confirm Legal Compliance = `negative`
- [ ] Update field

---

### B5 — CAN-028: Termination (BridgeValidator.registerMessages)

**Agent 2 finding:** Termination `pending_review` because pause bypass found. Per annotation guide §2.2, pause bypass is NOT RULE-TERM-01.

**Human action:**
- [ ] Confirm Termination = `negative`
- [ ] Confirm Legal Compliance = `positive` (bypass of pause architectural control)
- [ ] Update both fields

---

### B6 — CAN-031: Termination (Genesis.onGenesisFailed)

**Agent 2 finding:** Termination `pending_review` because `isFailed = true`. Per annotation guide §2.2, state flag transitions do NOT satisfy RULE-TERM-01.

**Human action:**
- [ ] Confirm Termination = `negative`
- [ ] Confirm Payment/Financial = `positive` high (unbounded loop OOG traps all user deposits)
- [ ] Update fields

---

### B7 — CAN-034: Payment/Financial (ZkCappedMinter.mint)

**Agent 2 finding:** `pending_review` despite `_revertIfCapExceeded(_amount)` being a mitigating control. Cap is explicitly enforced — satisfies RULE-FIN-01 negative criteria.

**Human action:**
- [ ] Verify `_revertIfCapExceeded` enforces the `MAXIMUM_TOTAL_CLAIMABLE` cap
- [ ] Confirm Payment/Financial = `negative`
- [ ] Review finding association: why was this mint function associated with the ZkTokenV1 EIP-712 domain finding?

---

## Priority Group C — Evidence Verification (Medium Priority)

These records have AI-supported category classifications that still require human code verification before promotion to `positive`.

### C1 — CAN-002: Legal Compliance + Payment/Financial (withdrawFees)

**Verify:** Count all privileged functions in `AutonomousAgentDeployer.sol` (bundle in `vfp_00001.json`). Agent 2 identified 8+ but a human must confirm there is no TimelockController inheritance.

### C2 — CAN-008: Payment/Financial (addMintRequest)

**Verify:** Find the `issueFee` setter in `AssetIssuer.sol`. Confirm there is no ceiling check when `issueFee` is set.

### C3 — CAN-019: Legal Compliance + Payment/Financial (createCommonProjectIDAndDeploymentRequest)

**Verify:** Is there any refund mechanism in `BlueprintCore.sol` for a user whose deployment request is overwritten by the hardcoded index 0?

### C4 — CAN-023: Payment/Financial (burnAndBridge)

**Verify:** Does the current `V3DexSwap` adapter enforce `amountOutMinimum` internally, or does `RollupRevenueVault` need to enforce it independently?

### C5 — CAN-028: Legal Compliance (registerMessages)

**Verify:** Is there a `whenNotPaused` modifier anywhere in the `BridgeValidator.sol` contract? If not on `registerMessages`, confirm the bypass applies.

### C6 — CAN-031: Payment/Financial (onGenesisFailed)

**Verify:** Is `reserveAmount` transferred to `virtualsFactoryAddress` during launch, reducing the contract's balance below the total owed to participants?

### C7 — CAN-029: Payment/Financial (setThreshold)

**Action:** No further verification needed — code is unambiguous (`threshold = _threshold` with no ceiling). Promote to `positive`.

---

## Priority Group D — License Review Required

These records must receive legal clearance before inclusion in any ML training dataset:

| Record | License | Status |
|---|---|---|
| CAN-006 | BUSL-1.1 | `license_review_required` |
| CAN-007 | BUSL-1.1 | `license_review_required` |
| CAN-008 | BUSL-1.1 | `license_review_required` |
| CAN-009 | BUSL-1.1 | `license_review_required` |
| CAN-012 | BSL-1.1 | `license_review_required` |
| CAN-029 | AGPL-3.0-only | `license_review_required` |

**Note:** AGPL-3.0 (CAN-029) requires that any derivative work also be open-sourced under AGPL. Verify with legal counsel whether model training on AGPL-licensed code constitutes a derivative work.

---

## Priority Group E — Open Questions from Candidate Records

The following `unresolved_questions` from the candidate records require human or domain expert input:

| Record | Question |
|---|---|
| CAN-001 | Does the bundled commit represent the currently deployed contract? |
| CAN-002 | Can the AutonomousAgentDeployer owner withdraw tokens from any agent token without agent creator consent? |
| CAN-005 | Does USSI.sol expose a public callable pause() function? |
| CAN-006 | What is MAX_MARKER_CONFIRM_DELAY? Does it create an unacceptably long fund-lock window? |
| CAN-008 | Is there a ceiling on issueFee values in AssetIssuer? |
| CAN-012 | Is the $1 oracle fallback hardcoded or configurable? |
| CAN-021 | Has the deployment script vulnerability been patched before mainnet activation? |
| CAN-024 | Does updateBlockHashProverCopy have access control (not visible in excerpt)? |
| CAN-027 | Can setThreshold set the threshold to 0? Does VerificationLib.setThreshold have a minimum floor? |
| CAN-031 | Has the OOG loop been patched (e.g., replaced with a pull-payment model)? |
| CAN-034 | Why was ZkCappedMinter.mint associated with the ZkTokenV1 EIP-712 domain finding? |

---

## Final Adjudication Checklist

For each record, the human adjudicator should confirm:

- [ ] `solidity_context` contains the actual function body (not a file header or interface)
- [ ] `function_name` matches the function in `solidity_context`
- [ ] `source_finding_id` matches the finding content in the raw VFP file
- [ ] Each category classification is justified by code evidence per `docs/ANNOTATION_GUIDE.md`
- [ ] `model_text` accurately describes the specific function behavior (not generic boilerplate)
- [ ] `natspec_comments` contains actual NatSpec (`@notice`/`@dev`/`@param` blocks), or is `null`
- [ ] `license_status` is cleared before the record is assigned to a training split
- [ ] `review_status` is updated from `in_review` to `reviewed`
- [ ] `annotator_id` is updated to the human reviewer's ID

---

*This guide was prepared by Agent 2 (AI independent reviewer) on 2026-10-21. It does not constitute a final human review.*
