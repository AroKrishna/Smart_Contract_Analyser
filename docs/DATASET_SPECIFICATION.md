# Smart Contract Analyser — Machine Learning Dataset Specification

**Document Version**: 2.1.0 (Dataset Readiness Standard)  
**Status**: Frozen Canonical Dataset (`v3.3.0`)  
**Dataset Path**: [data/ml_candidates/final_dataset.jsonl](file:///c:/ARO/Projects/Smart_Contract_Analyser/data/ml_candidates/final_dataset.jsonl) (SHA-256: `74464fd132e9268220549adc8e5cfb31d4ca69b9fae203b31ae2924c1500e456`)  
**Split Seed**: `42` (`GroupShuffleSplit`, 0.0% project overlap)  
**Target Model**: Legal-BERT (Multi-Label Operational Governance & Contractual Hazard Classification)  
**Project Authority**: [Smart_Contract_Legal_AI_SaaS_Platform_Specification.docx](file:///c:/ARO/Projects/Smart_Contract_Analyser/docs/reference/Smart_Contract_Legal_AI_SaaS_Platform_Specification.docx)

---

## 1. Objectives & Executive Scope

This specification establishes the format, schema, data-quality criteria, and input pipeline for the machine learning dataset used by **Smart_Contract_Analyser**.

### 1.1 Separation from Heuristic Baseline Benchmark
This ML dataset is strictly distinct from the existing heuristic regression suite ([benchmark_manifest.json](file:///c:/ARO/Projects/Smart_Contract_Analyser/analysis/data/benchmark/benchmark_manifest.json)). 
- The **baseline benchmark** evaluates deterministic regular expression and AST rules (`RULE-TERM-01` through `RULE-GOV-01`).
- The **ML dataset** prepares curated, multi-modal text-and-code representations for fine-tuning and evaluating **Legal-BERT**.

### 1.2 The Five Core Project Categories
All dataset records are labeled across five project-defined operational risk categories:
1. **Privacy**: Unencrypted personal identifiable information (PII) on-chain or lack of user privacy safeguards.
2. **Termination**: Unilateral killswitches, arbitrary contract destruction, or irreversible balance draining.
3. **Legal Compliance**: Excessive administrative centralization, lack of timelocks, regulatory compliance gaps (AML/sanctions), or architectural bypasses.
4. **Liability**: Asymmetric exculpatory disclaimers, unilateral indemnification, or total exclusion of responsibility.
5. **Payment / Financial**: Uncapped transaction fees, arbitrary tax manipulation, locked liquidity, or confiscation of user balances.

### 1.3 Non-Equivalence Principle: Operational Hazards vs. Legal Advice
Annotations in this dataset represent **project-defined operational risk indicators**. They do **not** constitute formal legal opinions, statutory determinations, or guarantees of judicial enforceability. A security vulnerability or code pattern does not inherently prove that a contract is illegal or void under any specific legal jurisdiction.

---

## 2. Model Input Strategy: Adapting Legal-BERT for Smart Contracts

### 2.1 Why Raw Solidity Fails with Legal-BERT
Legal-BERT is a transformer model pre-trained on legal corpora (court decisions, legislation, contracts, and legal briefs). It uses a specialized vocabulary optimized for legal terminology.

Feeding raw Solidity directly into Legal-BERT introduces severe failure modes:
1. **Vocabulary Mismatch & Token Fragmentation**: Tokens like `mapping(address => uint256)`, `assembly { extcodesize(addr) }`, and `safeTransferFrom` are fragmented into meaningless subwords (e.g., `['safe', '##Transfer', '##From']`), destroying semantic representations.
2. **Syntax Bloat**: Compiler pragmas, memory pointers, and low-level arithmetic checks consume the 512-token context window without providing contractual or governance meaning.
3. **Loss of High-Level Intent**: Legal-BERT excels at understanding rights, duties, limitations, and liabilities expressed in natural language. Raw EVM opcodes cannot convey the governance intent of a developer.

### 2.2 The `model_text` Field: Dual-Stream Representation
To utilize Legal-BERT effectively, every record includes a dedicated **`model_text`** field. This field transforms the smart contract clause into structured natural-language text while retaining essential code context.

#### Format of `model_text`:
```text
Contract: <ContractName> (<License>)
Function: <FunctionName> (<Visibility>)
Modifiers: <ModifiersApplied>
Documented Intent (NatSpec): <@notice and @dev text>
Operational Behavior: <Concise natural-language summary of state changes and fund transfers>
Key Code Logic: <Normalized Solidity statements with formatting simplified>
```

---

## 3. Sample Unit Definition

The dataset supports two granular sample units:

1. **Clause / Function-Level Unit (Primary)**:
   - A single callable function or state transition block, accompanied by its NatSpec documentation, modifiers, and referenced state variables.
   - Ideal for identifying targeted operational hazards such as fee manipulation (`setFee`), emergency termination (`kill`), or token lockups.
2. **Contract / Architecture-Level Unit (Secondary)**:
   - A contract-wide summary used when hazards stem from system-wide omissions rather than a single function (e.g., complete absence of timelock governance across 10 privileged functions, or absence of emergency pause mechanisms).

---

## 4. Machine-Readable Schema Specification

Records are stored in **JSON Lines (`.jsonl`)** format. Each line represents a valid JSON object matching the following schema:

```json
{
  "sample_id": "ML-00001",
  "project_id": "spectral_image_vaults",
  "contract_family": "Spectral-V2",
  "source_repo_url": "https://github.com/example/repo",
  "commit_or_version": "a24ebf0141e9350a42639d8593c1436241deae59",
  "compiler_version": "^0.8.20",
  "license": "MIT",
  "collection_date": "2026-10-21",
  "contract_file": "AgentImageService.sol",
  "function_name": "requestRefund",
  "source_line_range": [219, 242],
  "solidity_context": "function requestRefund(address agentToken, bytes32 requestId) external nonReentrant { ... }",
  "natspec_comments": "/// @notice Allows user to claim refund if image generation times out.",
  "model_text": "Contract: AgentImageService (MIT)\nFunction: requestRefund (external)\nDocumented Intent: Allows user to claim refund after timeout.\nOperational Behavior: Checks refund time limit, updates request state, and transfers agent tokens to msg.sender.",
  "categories": {
    "Privacy": {
      "status": "negative",
      "severity": "none",
      "evidence": null,
      "rationale": "No personal identifying information stored or requested."
    },
    "Termination": {
      "status": "negative",
      "severity": "none",
      "evidence": null,
      "rationale": "Does not selfdestruct or terminate contract execution."
    },
    "Legal Compliance": {
      "status": "negative",
      "severity": "none",
      "evidence": null,
      "rationale": "Standard service refund logic with no regulatory bypass."
    },
    "Liability": {
      "status": "negative",
      "severity": "none",
      "evidence": null,
      "rationale": "No exculpatory disclaimers or liability exclusions in NatSpec."
    },
    "Payment / Financial": {
      "status": "insufficient_information",
      "severity": "low",
      "evidence": "IERC20Upgradeable(agentToken).safeTransfer(msg.sender, request.amount);",
      "rationale": "Code refunds msg.sender while audit report suggests admin approval path might divert funds; commit version requires verification."
    }
  },
  "source_labels": {
    "source_dataset": "FORGE-Curated",
    "source_id": "vfp_00001",
    "original_cwe": ["CWE-284", "CWE-285", "CWE-863"],
    "original_severity": "High",
    "original_title": "Refunded agent tokens should be sent back to the requester"
  },
  "provenance": {
    "annotator_id": "reviewer_01",
    "review_status": "unresolved",
    "annotation_date": "2026-10-21"
  },
  "unresolved_questions": [
    "Does the audited commit differ from the contract version bundled in the sample?",
    "Is requestRefund callable by admins in any related contract file?"
  ],
  "split": "unassigned"
}
```

---

## 5. Schema Field Definitions

| Field Name | Type | Description |
| :--- | :--- | :--- |
| `sample_id` | `string` | Unique identifier (e.g., `ML-00001`). |
| `project_id` | `string` | Normalized project or protocol identifier used to prevent split leakage. |
| `contract_family` | `string` | Fork or codebase family (e.g., `Uniswap-V2`, `Compound-v2`). |
| `source_repo_url` | `string` | URL to the upstream public source repository. |
| `commit_or_version` | `string` | Exact Git commit hash or tagged release. |
| `compiler_version` | `string` | Pragma string (e.g., `^0.8.25`). |
| `license` | `string` | Verified SPDX license identifier (e.g., `MIT`, `BUSL-1.1`). |
| `license_status` | `string` | Review status of license permissions: `cleared`, `license_review_required`, or `restricted_research_only`. |
| `collection_date` | `string` | Date of data collection (YYYY-MM-DD). |
| `contract_file` | `string` | Filename containing the code (e.g., `Vault.sol`). |
| `function_name` | `string \| null` | Name of function, or `null` if whole-contract scope. |
| `source_line_range` | `[int, int] \| null` | Start and end line numbers in source file. |
| `solidity_context` | `string` | Verifiable Solidity source code snippet. |
| `natspec_comments` | `string \| null` | Associated developer docstrings and notices. |
| `model_text` | `string` | Formatted natural-language text prepared for Legal-BERT. |
| `categories` | `object` | Dictionary containing all five project categories. |
| `source_labels` | `object` | Source-level labels (CWE, audit findings) kept strictly separate. |
| `provenance` | `object` | Annotator identity, review timestamp, and review status. |
| `unresolved_questions` | `list[string]` | Open questions requiring expert or developer resolution. |
| `split` | `string` | Dataset partition (`train`, `validation`, `test`, or `unassigned`). |

---

## 6. Label Values & Review Protocol

### 6.1 Explicit Category Statuses
Every category object must explicitly set one of the defined statuses:
- **`positive`**: Clear evidence exists satisfying the category's operational hazard criteria. Requires supporting `evidence` and `rationale`.
- **`negative`**: Verifiable evidence that the hazard is absent, mitigated, or properly bounded. Requires `rationale`.
- **`unresolved`** / **`insufficient_information`**: Ambiguous architecture, unresolved commit mismatch, or missing related contracts. Must include open questions or reason.
- **`pending_review`**: Preliminary suggestion from heuristic, audit finding, or pipeline requiring verification before confirmation.

> **Rule**: An analyzer must **never** treat "no rule fired" or "clean static analysis" as proof of a `negative` status.

### 6.2 Risk of Circular Summaries in `model_text`
When generating natural-language behavior summaries for Legal-BERT input:
1. **The Circularity Trap**: If a heuristic rule or classifier detects `selfdestruct` and auto-generates the text *"This contract contains an arbitrary termination killswitch"*, feeding that text into Legal-BERT causes the model to merely memorize the summary generator rather than learning genuine contractual semantics.
2. **Mitigation**:
   - Clearly prefix draft text as `[Draft Summary (Machine-generated, pending human review)]`.
   - Ensure the summary describes the factual operations (inputs, state updates, external calls) rather than regurgitating the target hazard label.
   - Require independent verification of `model_text` before using records in training.

### 6.3 Review Status Lifecycle
Every record moves through an explicit review lifecycle:
1. `draft`: Extracted or generated record pending inspection.
2. `in_review`: Under active review by an annotator.
3. `ai_reviewed`: Carefully reviewed and reconciled by an evidence-based AI pass against source files. (Does not claim human review).
4. `ai_review_unresolved`: Escalated to unresolved queue during AI review due to code drift, file header extraction, or license barriers.
5. `reviewed`: Adjudicated and confirmed by a qualified human reviewer.
6. `unresolved`: Placed in a review queue due to code mismatch, missing files, or disputed classification.

---

## 7. Data Leakage Prevention & Split Allocation

To ensure valid model evaluation:
1. **Project Family Isolation**: All contracts and clauses belonging to the same `project_id` or `contract_family` **must reside in the exact same split**.
2. **Held-Out Integrity**: Contracts in the `test` split must never be inspected during feature engineering, prompt design, or hyperparameter tuning.
3. **Split Readiness Threshold**:
   - A dataset split must **never** be generated from a trivial number of projects.
   - Minimum threshold: At least **5 distinct, independently reviewed projects** with verified ground-truth labels across all five categories.
   - Any smaller corpus must remain labeled as `split: "unassigned"` or `split: "dev"`.
