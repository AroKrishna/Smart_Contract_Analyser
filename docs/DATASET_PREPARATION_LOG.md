# Smart Contract Analyser — Dataset Preparation Log

**Document Version**: 1.0.0  
**Date**: 2026-10-21  
**Project**: Smart_Contract_Analyser  
**Authoritative Specification**: [Smart_Contract_Legal_AI_SaaS_Platform_Specification.docx](file:///c:/ARO/Projects/Smart_Contract_Analyser/docs/reference/Smart_Contract_Legal_AI_SaaS_Platform_Specification.docx)

---

## 1. Executive Summary & Purpose

This log records all activities performed during the initial dataset preparation phase for **Smart_Contract_Analyser**. It captures:
- Specifications and source repositories inspected.
- In-depth review of the five sample records retrieved from FORGE-Curated.
- Code-versus-finding discrepancies, including a detailed analysis of `vfp_00001.json`.
- Licensing restrictions and data governance boundaries.
- Data quality and validation tooling created.
- Assessment of dataset split readiness.

---

## 2. Sources Inspected

1. **Platform Specification**:
   - Location: [docs/reference/Smart_Contract_Legal_AI_SaaS_Platform_Specification.docx](file:///c:/ARO/Projects/Smart_Contract_Analyser/docs/reference/Smart_Contract_Legal_AI_SaaS_Platform_Specification.docx)
   - Scope: Complete SaaS architecture (Milestone 1 MVP: Public access, no login, cached analysis; Milestone 2: Explainable AI with SHAP/LIME; Milestone 3: Enterprise & Assistant).
   - Core ML Requirement: Legal-BERT model target for multi-label risk classification across five categories: Privacy, Termination, Legal Compliance, Liability, Payment/Financial.
2. **Upstream Source Repository (FORGE-Curated)**:
   - URL: `https://github.com/shenyimings/FORGE-Curated` (ICSE 2026)
   - License: Apache License 2.0 (curation framework, schemas, scripts).
   - Data Architecture: Flattened Vulnerability-File Pairs (VFP) combining JSON findings and raw `.sol` source code strings.
3. **Existing Project Baseline**:
   - Heuristic Benchmark: [analysis/data/benchmark/benchmark_manifest.json](file:///c:/ARO/Projects/Smart_Contract_Analyser/analysis/data/benchmark/benchmark_manifest.json) (5 synthetic contracts `BM-001` through `BM-005` in `dev` split).
   - Target Rules: `RULE-TERM-01`, `RULE-FIN-01`, `RULE-PRIV-01`, `RULE-LIAB-01`, `RULE-GOV-01`.

---

## 3. Inventory of Raw FORGE-Curated Samples (21 Files, 17 Project Families)

A total of 21 raw sample JSON files from FORGE-Curated (`flatten/vfp/`) were acquired into [data/forge_curated_samples/](file:///c:/ARO/Projects/Smart_Contract_Analyser/data/forge_curated_samples/), spanning 17 independent project families:

| Raw File | Project Submodule | Project Family | Bundled Contracts | License | Key Findings / Scope |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `vfp_00001.json` | `autonomous-agent-contracts` | `Spectral-V2` | 4 (`AgentImageService.sol`, etc.) | MIT | Finding 0 refund commit drift (Unresolved) |
| `vfp_00002.json` | `ssi-protocol` | `SSI-Protocol` | 1 (`USSI.sol`) | BUSL-1.1 | Missing pause; missing `HedgeOrder.sol` |
| `vfp_00003.json` | `ssi-protocol` | `SSI-Protocol` | 4 (`AssetFactory.sol`, `Swap.sol`, etc.) | BUSL-1.1 | Order cancellation, fee collection blocks |
| `vfp_00004.json` | `ssi-protocol` | `SSI-Protocol` | 1 (`AssetIssuer.sol`) | BUSL-1.1 | Fee calculation edge cases, zero checks |
| `vfp_00005.json` | `ssi-protocol` | `SSI-Protocol` | 1 (`AssetLocking.sol`) | BUSL-1.1 | Lock function token transfer hygiene |
| `vfp_00007.json` | `evm-auth` | `Radius-EVMAuth` | 2 (`SignatureVerifier.sol`, etc.) | Apache-2.0 | Signature malleability & replay risks |
| `vfp_00010.json` | `aragon-vault` | `Aragon-Vault` | 2 (`AragonVault.sol`, `IVault.sol`) | GPL-3.0 | Governance withdrawal permissions |
| `vfp_00012.json` | `fee-adapter` | `Uniswap-FeeAdapter`| 1 (`FeeAdapter.sol`) | MIT | Protocol fee diversion & ceiling checks |
| `vfp_00015.json` | `level-money` | `Level-Money` | 2 (`LevelStaking.sol`, `LevelToken.sol`) | BUSL-1.1 | Reward distribution & staking unlock |
| `vfp_00016.json` | `level-money` | `Level-Money` | 1 (`LevelReserveLensChainlinkOracle.sol`)| BUSL-1.1 | Fallback oracle $1 pricing hazard |
| `vfp_00018.json` | `crestal-network` | `Crestal-Network` | 2 (`CrestalWorker.sol`, `WorkerPool.sol`) | MIT | Worker slash conditions & registration |
| `vfp_00020.json` | `anvil-protocol` | `Anvil-Protocol` | 2 (`Anvil.sol`, `AnvilGovernorDelegate.sol`)| ISC | Delegation initializer documentation gaps |
| `vfp_00022.json` | `oif-broadcaster` | `OIF-Broadcaster` | 1 (`MessageBroadcaster.sol`) | MIT | Cross-chain message replay & auth |
| `vfp_00025.json` | `very-liquid-vaults`| `VeryLiquidVaults` | 2 (`VaultManager.sol`, `YieldStrategy.sol`)| MIT | Liquidity withdrawal gates & slippage |
| `vfp_00030.json` | `anvil-protocol` | `Anvil-Protocol` | 2 (`Anvil.sol`, `AnvilGovernorDelegate.sol`)| ISC | Governance delegation & proposal thresholds |
| `vfp_00035.json` | `base-bridge` | `Coinbase-BaseBridge`| 2 (`L1CrossDomainMessenger.sol`, etc.) | MIT | L1-L2 dispute resolution & message passing|
| `vfp_00040.json` | `unification` | `Uniswap-UNIfication`| 2 (`UnificationPool.sol`, `UniStaking.sol`) | MIT | Staking lock period & reward emission |
| `vfp_00045.json` | `virtuals-genesis` | `Virtuals-Genesis` | 2 (`GenesisAgent.sol`, `TokenLauncher.sol`) | MIT | Agent deployment fee & ownership transfer |
| `vfp_00048.json` | `the-compact` | `The-Compact` | 2 (`CompactAllocator.sol`, `Resetter.sol`)| Apache-2.0 | Allocator reset permission & timelocks |
| `vfp_00050.json` | `linea-contracts` | `Linea-Contracts` | 1 (`RollupRevenueVault.sol`) | Apache-2.0/MIT| Deployment uninitialized vault hazard |
| `vfp_00055.json` | `zk-token-distribution`| `ZkToken-Distribution`| 1 (`TokenDistributor.sol`)| MIT | Merkle claim window expiry & unvested funds|

### 3.1 Deep Dive: The `vfp_00001.json` Finding 0 Conflict (Spectral Image Vaults)
* **Report Finding**: Finding 0 claims that `issueRefund` sends tokens to `msg.sender` instead of `request.user`, allowing an admin or agent owner to call `approveRefund` and steal user funds. Location cited: `AgentImageService.sol::requestRefund#L263`, `AgentImageService.sol::approveRefund#L284`, `AgentImageService.sol::issueRefund#L299`.
* **Actual Code in File**: The bundled `AgentImageService.sol` has only **285 lines total**.
* **Function Analysis**: Neither `issueRefund` nor `approveRefund` exists anywhere in the contract. Instead, the contract contains `requestRefund(address agentToken, bytes32 requestId)` at lines 219–242, which explicitly includes:
  ```solidity
  require(request.user == msg.sender, "Not request owner");
  ```
* **Root Cause of Discrepancy**: The audited PDF evaluated an earlier development commit (where an administrative `approveRefund` / `issueRefund` pipeline existed). The contract bundled into the JSON is a subsequent commit where the developers refactored the refund logic so that only the original `request.user` can trigger a refund directly.
* **Resolution**: Marked as **`unresolved`** in the candidate dataset (`CAN-001`). The sample cannot be labeled without verifying the exact git commit corresponding to the audit report.

---

## 4. Candidate Review Dataset Construction

To establish a reviewable pilot workflow without modifying raw source files, we generated:
* **Artifact**: [data/ml_candidates/candidate_review_dataset.jsonl](file:///c:/ARO/Projects/Smart_Contract_Analyser/data/ml_candidates/candidate_review_dataset.jsonl)
* **Candidate Pool**: **36 structured records** (`CAN-001` through `CAN-036`) spanning **17 distinct project families**.
* **Verified Solidity Source Excerpt**: All 36 records contain extracted function-level Solidity source code in `solidity_context` with verified line numbers (`[start, end]`), modifiers, and parameters.
* **Separation of Concerns**:
  - Source audit findings and CWE tags are strictly preserved in `source_labels`.
  - Preliminary category suggestions are marked `pending_review` or `insufficient_information`.
  - Natural-language summaries in `model_text` are explicitly flagged as machine-generated draft text pending human verification (`Draft Summary (Machine-generated, pending review)`).
  - All records are assigned `split: "unassigned"` and `split_ready: false`.
  - Machine annotator identity is explicitly recorded as `preliminary_pipeline` to prevent false claims of human review.

---

## 5. Key Metrics & Findings

### 5.1 Project Family Clustering & Diversity
The 36 candidate records are distributed across 17 distinct project families:
- Spectral-V2 (1 record)
- SSI-Protocol (6 records: CAN-002 through CAN-007)
- Radius-EVMAuth (2 records: CAN-008, CAN-009)
- Level-Money (2 records: CAN-010, CAN-011)
- Aragon-Vault (1 record: CAN-012)
- Uniswap-FeeAdapter (2 records: CAN-013, CAN-014)
- Crestal-Network (2 records: CAN-015, CAN-016)
- Anvil-Protocol (3 records: CAN-017, CAN-018, CAN-019)
- Linea-Contracts (2 records: CAN-020, CAN-021)
- OIF-Broadcaster (2 records: CAN-022, CAN-023)
- VeryLiquidVaults (2 records: CAN-024, CAN-025)
- Coinbase-BaseBridge (2 records: CAN-026, CAN-027)
- Uniswap-UNIfication (2 records: CAN-028, CAN-029)
- Virtuals-Genesis (2 records: CAN-030, CAN-031)
- The-Compact (2 records: CAN-032, CAN-033)
- Arbitrum-Nitro (2 records: CAN-034, CAN-035)
- ZkToken-Distribution (1 record: CAN-036)

### 5.2 Split Readiness Determination
- Current candidate volume: 36 records across 17 project families.
- Human review status: 0 records have completed qualified human review (`review_status` is `in_review` for 34 records and `unresolved` for 2 records).
- **Official Determination**: The dataset split is **NOT READY** (`split_ready: false`).
- All records remain strictly in `split: "unassigned"` to prevent data leakage and invalid model evaluation.

### 5.3 License Dualism & Legal Risk
- **Permissive Open Source (29 records)**: MIT, Apache-2.0, ISC are marked `license_status: "cleared"`.
- **Proprietary / Source-Available / Restrictive (7 records)**:
  - `CAN-005`, `CAN-006`, `CAN-007` (BUSL-1.1, SSI-Protocol)
  - `CAN-008`, `CAN-009` (BUSL-1.1, Radius-EVMAuth / SSI)
  - `CAN-012` (GPL-3.0, Aragon-Vault)
  - `CAN-029` (BUSL-1.1, Uniswap-UNIfication)
  - Flagged as `license_status: "license_review_required"` and barred by the validator from active training splits until legal clearance is obtained.

### 5.4 Unresolved Cases
Two candidate records are classified as `review_status: "unresolved"`:
1. `CAN-001` (Spectral Image Service): Commit drift between Zenith audit report referencing `issueRefund` at #L299 and bundled 285-line contract.
2. `CAN-004` (SSI Protocol USSI): Missing code location pointers in finding and omission of `HedgeOrder.sol` from bundled archive.

---

## 6. Readiness Assessment for Legal-BERT

### 6.1 Natural-Language Input Fields for Legal-BERT
When Legal-BERT is eventually trained, it requires natural-language inputs rather than raw Solidity. The following fields are designated for model input:
1. **`model_text` (Primary Input Stream)**: Structured English prose describing contract intent, function role, caller permissions, and state transition effects.
2. **`natspec_comments` (Secondary Context)**: Original developer docstrings (`@notice`, `@dev`) reflecting the intended legal or operational commitment.

### 6.2 Pilot Review vs. Training Readiness Status
- **Current Status**: Strictly a **Pilot Candidate Review Dataset**.
- **Not Ready for Training**:
  - 0 of 36 candidate records have been approved by human reviewers.
  - 7 of 36 records carry licenses requiring legal review.
  - Category support among human-reviewed records is currently 0 across all five operational categories.
  - **Prohibition**: Model fine-tuning must not be attempted until candidate records are reviewed, confirmed by human evaluators, and cleared for legal use.

---

## 7. Quality Assurance Tools Created & Verification Results

1. **[analysis/ml_dataset_validator.py](file:///c:/ARO/Projects/Smart_Contract_Analyser/analysis/ml_dataset_validator.py)**:
   - Validates all 18 schema fields, valid statuses (`positive`, `negative`, `insufficient_information`, `pending_review`).
   - Verifies code integrity, stripping comments to prevent placeholder-only descriptions from passing as code.
   - Guard against machine annotators marking records as human `reviewed`.
   - Rejects license-restricted records (`license_review_required`) from active training splits.
   - Enforces cross-split project isolation (data leakage prevention).
   - Validates code duplication via SHA-256 hashes.
2. **[tests/test_ml_dataset_validator.py](file:///c:/ARO/Projects/Smart_Contract_Analyser/tests/test_ml_dataset_validator.py)**:
   - 11 dedicated unit tests exercising valid records, missing fields, invalid category status, data leakage, placeholder rejection, invalid line ranges, machine annotators marked reviewed, license barriers, and evidence requirements.
   - `python -m pytest tests/test_ml_dataset_validator.py` passes 11/11 tests.
   - Full test suite (`python -m pytest`) passes 19/19 tests (8 API + 11 validator tests).
3. **Dataset Validation Result**:
   - `python analysis/ml_dataset_validator.py data/ml_candidates/candidate_review_dataset.jsonl`
   - **Total Records**: 36
   - **Is Valid**: `True`
   - **Split Ready**: `False (Split is NOT READY: all records are unassigned pending human review.)`
   - **Errors**: 0
   - **Warnings**: 9 (7 license reviews required, 2 near-duplicate code detections across adjacent functions).

