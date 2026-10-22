# Smart Contract Analyser — Benchmark Annotation Guide

**Document Version**: 1.0.0  
**Status**: Active Standard  
**Target Engine**: Deterministic Baseline & Future Evaluators  
**Scope**: Operational Governance & Contractual Hazard Labeling  

---

## 1. Objectives & Grounding Principles

The Smart Contract Analyser benchmark establishes standardized ground truth for evaluating heuristic and static analysis rules across Solidity smart contracts.

### 1.1 Non-Equivalence Principle (Code vs. Legal Prose)
Solidity syntax, opcodes, and NatSpec documentation express **operational capabilities** and **informational disclosures**. They do **not** constitute legal contracts in isolation and cannot establish jurisdiction-specific legal validity, statutory compliance, or judicial enforceability. Annotators must label code based strictly on verifiable syntactic and structural evidence, never on speculative legal outcomes.

### 1.2 Separation of Security Vulnerabilities and Operational Hazards
Security audit tools (e.g., Slither, Mythril) focus on execution bugs (such as reentrancy, integer overflows, frontrunning, and flash loan exploits). This benchmark focuses strictly on **operational control asymmetries and governance hazards**:
- Unilateral termination and fund confiscation mechanisms.
- Arbitrary parameter adjustments (fees, taxes, rates) lacking ceiling constraints.
- Insecure storage of personal identifiable information (PII) on an immutable public ledger.
- Disproportionate exculpatory liability waivers embedded in contract documentation.
- Privilege concentration lacking mandatory governance delays (timelocks).

---

## 2. Rule-by-Rule Annotation Specifications

Each sample in the benchmark manifest must be labeled across all five defined heuristic rules. Annotators must apply the criteria below.

```
+--------------------------------------------------------------------------------------------------+
|                                  SUMMARY OF BENCHMARK RULES                                      |
+--------------+---------------------+-------------------------------------------------------------+
| Rule ID      | Category            | Operational Target                                          |
+--------------+---------------------+-------------------------------------------------------------+
| RULE-TERM-01 | Termination         | Unilateral termination opcodes (selfdestruct, suicide)      |
| RULE-FIN-01  | Payment / Financial | Unconstrained fee / tax modifications without ceiling checks|
| RULE-PRIV-01 | Privacy             | Plaintext PII storage declarations on-chain                 |
| RULE-LIAB-01 | Liability           | Blanket exculpatory disclaimers in NatSpec documentation    |
| RULE-GOV-01  | Legal Compliance    | High administrative privilege count without timelock delay  |
+--------------+---------------------+-------------------------------------------------------------+
```

---

### 2.1 RULE-TERM-01: Unilateral Contract Termination Capability
* **Category**: `Termination`
* **Target Hazard**: Arbitrary termination of bytecode execution and irreversible draining of ether balance to a target address.

#### Positive Criterion (`expected_trigger: true`)
A contract must be labeled positive if:
1. It contains an active `selfdestruct(...)` or legacy `suicide(...)` instruction within any callable function body (public, external, or internal called from public/external).
2. The termination function is callable post-deployment (regardless of whether access is restricted to an `onlyOwner` modifier).

#### Negative Criterion (`expected_trigger: false`)
A contract must be labeled negative if:
1. No `selfdestruct` or `suicide` instruction is present anywhere in the contract or inherited contracts.
2. Pausable mechanisms (`whenNotPaused`, `_pause()`) that temporarily halt state transitions without destroying the contract or draining bytecode are present—these do **not** satisfy `RULE-TERM-01`.

#### Supporting Evidence
* **AST/Source Line Match**: Exact line containing `selfdestruct(<address>)` or `suicide(<address>)`.
* **NatSpec Context**: Any `@notice` or `@dev` mentioning emergency termination or killswitches.

#### Boundary Cases & Disallowed Assumptions
* *Compiler Pragma Note*: Solidity >= 0.8.18 emits deprecation warnings for `selfdestruct`, and Cancun hard-fork (EIP-6780) limits its behavior to contracts created in the same transaction. Despite EVM changes, annotators must label the *syntactic capability* as positive because legacy EVM chains and explicit contract intentions still rely on the instruction.

---

### 2.2 RULE-FIN-01: Unconstrained Financial Parameter Modification
* **Category**: `Payment / Financial`
* **Target Hazard**: Deployers or administrators retaining unilateral ability to increase transactional fees, commissions, or protocol taxes to arbitrary levels (including 100%) without an enforceably bounded maximum ceiling.

#### Positive Criterion (`expected_trigger: true`)
A contract must be labeled positive if:
1. It contains a non-constructor function that updates a state variable representing fees, taxes, or commission rates (e.g., `fee`, `tax`, `rate`, `commission`, `basisPoints`, `royaltyFee`).
2. The function assigns a user-supplied parameter to the fee state variable without a preceding or accompanying bounding validation statement (such as `require(newFee <= MAX_FEE, "Fee exceeds ceiling");` or `if (newFee > CAP) revert();`).

#### Negative Criterion (`expected_trigger: false`)
A contract must be labeled negative if:
1. Fee parameters are constants or immutables set exclusively during contract construction (`constructor`).
2. Every function mutating fee state variables contains an explicit upper-bound check against a constant, immutable, or hardcoded upper ceiling.
3. The contract has no adjustable financial parameters.

#### Supporting Evidence
* **AST/Source Line Match**: The specific assignment line (e.g., `liquidityTax = newTax;` or `tradingFee = _fee;`).
* **Condition Verification**: Verification that no `require` or `revert` check referencing an upper threshold guards the assignment block.

#### Boundary Cases & Disallowed Assumptions
* **Constructors**: Fee initializations inside `constructor(...)` MUST NOT be labeled as positive. Constructors run exactly once at deployment and do not represent ongoing unilateral modification risks on active users.
* **Two-Step Parameter Adjustments**: If fees can only be adjusted via a governance proposal voted on-chain, but the setter itself lacks a hardcoded numerical ceiling, it is labeled **Positive** at the contract heuristic level, with a NatSpec note explaining the governance dependency.

---

### 2.3 RULE-PRIV-01: High-Risk Plaintext PII Storage Indication
* **Category**: `Privacy`
* **Target Hazard**: Persisting unhashed, unencrypted natural-person identifiers directly on an immutable, globally readable public blockchain.

#### Positive Criterion (`expected_trigger: true`)
A contract must be labeled positive if:
1. It declares one or more non-constant, non-immutable state variables typed as `string` or `bytes`.
2. The variable identifier explicitly denotes personal identity information, including:
   - `email`, `userEmail`, `mailAddress`
   - `ssn`, `socialSecurity`, `nationalId`, `passport`
   - `physicalAddress`, `homeAddress`, `streetAddress`
   - `phoneNumber`, `telephone`, `mobileNumber`
   - `fullName`, `realName`, `dateOfBirth`, `dob`

#### Negative Criterion (`expected_trigger: false`)
A contract must be labeled negative if:
1. Identifiers are stored as cryptographic hashes (e.g., `bytes32 emailHash`, `bytes32 identityCommitment`).
2. Stored addresses represent Ethereum EVM accounts (`address userWallet`), not physical street addresses.
3. State variables are constant strings representing protocol metadata (e.g., `string public constant name = "Token"`).

#### Supporting Evidence
* **AST/Source Line Match**: The exact state variable declaration line (e.g., `string public userEmail;`).
* **NatSpec Context**: Verification that documentation describes the field as user personal data.

#### Boundary Cases & Disallowed Assumptions
* Annotators must not assume off-chain zero-knowledge proofs or homomorphic encryption unless the state variable types reflect cryptographic proof primitives (e.g., `uint256[2] a, uint256[2][2] b`). Raw `string` fields named after PII are positive examples.

---

### 2.4 RULE-LIAB-01: Broad Liability Disclaimer in Documentation
* **Category**: `Liability`
* **Target Hazard**: Deployers inserting unilateral blanket liability waivers, "as-is" disclaimers, and total liability exclusions into contract NatSpec documentation to deter claims or disclaim common-law duties of care.

#### Positive Criterion (`expected_trigger: true`)
A contract must be labeled positive if:
1. The contract-level or function-level NatSpec comments (`///` or `/** ... */`) contain explicit blanket exculpatory language, specifically matching phrases such as:
   - *"provided strictly as is"* or *"provided as is without warranty of any kind"*
   - *"no liability whatsoever"* or *"in no event shall the authors/owners be liable"*
   - *"use at your own risk"* combined with disclaimer of merchantability or fitness
   - *"hold harmless"* clauses disclaiming all direct, indirect, or consequential damages

#### Negative Criterion (`expected_trigger: false`)
A contract must be labeled negative if:
1. NatSpec comments describe purely technical functionality, architecture, or warnings without legal waiver phrases.
2. Standard SPDX license identifiers (e.g., `// SPDX-License-Identifier: MIT`) appear at the top of the file. Standard SPDX tags **do not** trigger `RULE-LIAB-01`.

#### Supporting Evidence
* **NatSpec Docstring Match**: The exact comment lines containing the exculpatory disclaimer.

#### Boundary Cases & Disallowed Assumptions
* Standard open-source license text in a standalone `LICENSE` repository file does not trigger this rule; the disclaimer must be intentionally embedded in the contract's NatSpec docstrings.

---

### 2.5 RULE-GOV-01: Administrative Privilege Concentration Without Timelock Delay
* **Category**: `Legal Compliance`
* **Target Hazard**: Contracts concentrating critical administrative capabilities in a single privileged role without introducing mandatory notice periods, timelocks, or governance delays.

#### Positive Criterion (`expected_trigger: true`)
A contract must be labeled positive if:
1. The contract defines **3 or more privileged administrative functions** (functions restricted by modifiers such as `onlyOwner`, `onlyAdmin`, `onlyRole`, `authorized`, `requiresAuth`).
2. The contract **lacks inheritance** from a recognized governance delay or timelock mechanism (e.g., OpenZeppelin `TimelockController`, `ITimelock`, `DelayModule`).

#### Negative Criterion (`expected_trigger: false`)
A contract must be labeled negative if:
1. The contract has fewer than 3 privileged functions (e.g., simple single-admin or two-admin setups).
2. The contract inherits directly from a timelock or governance controller mechanism that enforces execution delay queues.
3. All functions are completely permissionless, community-governed via decentralized voting tokens, or immutable.

#### Supporting Evidence
* **AST/Source Line Match**: Contract definition line showing absence of timelock inheritance, accompanied by list of the >= 3 privileged function signatures.

#### Boundary Cases & Disallowed Assumptions
* Multi-signature wallets (e.g., Gnosis Safe) used as the `owner` address off-chain cannot be verified from single-contract source code. Unless the delay is encoded in the contract's bytecode or inheritance hierarchy, the source-level heuristic must be evaluated as-is.

---

## 3. Ambiguous and Unsupported Case Protocol

When a contract exhibits ambiguous architecture, annotators must adhere to the following tagging protocol rather than forcing a speculative binary label:

| Architecture Pattern | Annotation Tag | Benchmark Action | Rationale |
|---|---|---|---|
| **ERC-1967 / Transparent Proxy** | `AMBIGUOUS_PROXY_STUB` | Exclude from single-contract baseline; evaluate only on implementation contract | A proxy stub merely delegates calls (`delegatecall`); its operational hazards reside in the implementation contract. |
| **Diamond Pattern (ERC-2535)** | `AMBIGUOUS_MULTI_FACET` | Exclude until multi-file analyzer is enabled | Facets split storage and logic across separate contracts; single-file parsers cannot resolve combined governance. |
| **Off-Chain Hybrid Agreements** | `UNSUPPORTED_OFFCHAIN_LEGAL` | Mark rule label as `NOT_SUPPORTED` | Terms governed by Ricardian signatures, external PDFs, or off-chain arbitration cannot be extracted from Solidity code. |
| **Complex Inter-Procedural Fees** | `AMBIGUOUS_DATAFLOW_FEE` | Requires full AST dataflow verification | If a fee setter invokes multiple internal libraries (`Math.mulDiv`) before capping, regex rules cannot reliably resolve ceiling checks. |

---

## 4. Split Grouping & Data Leakage Prevention Rules

To guarantee that evaluation metrics accurately reflect generalization rather than memorization, benchmark dataset splits must adhere strictly to these rules:

1. **Project Family Isolation**:
   - Every contract originating from the same project, repository, fork, or contract family (e.g., Uniswap v2 core + periphery, Compound cToken + Comptroller, Aave Pool + Configurator) **must reside in the exact same split**.
   - Mixing contracts from the same project family across `dev`, `train`, `validation`, and `test` splits constitutes **Data Leakage** and is prohibited.

2. **Split Designations**:
   - **`dev`**: Curated unit and regression cases used during rule development, debugging, and initial sanity checks (e.g., BM-001 through BM-005).
   - **`train`**: Designated for future statistical or neural model training (minimum 60% of expanded corpus).
   - **`validation`**: Designated for tuning rule thresholds, confidence weighting, and hyperparameter calibration (minimum 20% of expanded corpus).
   - **`test`**: Genuinely held-out test contracts that are never inspected during rule development or tuned against (minimum 20% of expanded corpus).

3. **Automated Enforcement**:
   - The validation function in [benchmark_schema.py](file:///c:/ARO/Projects/Smart_Contract_Analyser/analysis/benchmark_schema.py) scans all entries and raises a validation error if any `project_name` maps to more than one split.

4. **Zero-Support Metric Handling**:
   - If an evaluation split contains **0 positive ground-truth instances** for any rule (`support = 0`), precision, recall, and F1 must be reported as `null` / `undefined`. 
   - Evaluation scripts must **never** default 0/0 divisions to 1.0 or claim 100% precision/recall on untested rules.

---

## 5. Machine Learning Annotation Protocol (Legal-BERT Multi-Label)

This section guides human annotators preparing training and evaluation data for **Legal-BERT** multi-label classification across the five project categories.

> [!IMPORTANT]
> **Legal Nature Disclaimer**: Annotations in this dataset are **project-defined operational-risk labels**, not legal opinions, formal legal advice, or statutory determinations. In the absence of jurisdictional legal counsel, labels capture structural asymmetries, control imbalances, and documentation risks, rather than enforceable legal judgments.

### 5.1 How Code Evidence Supports an Operational Indicator
An operational indicator is a verifiable capability or omission in code, state storage, or documentation.
- **Direct Code Evidence**: A specific function, modifier, opcode, or state variable declaration that executes an action (e.g., `selfdestruct(recipient)`, `taxRate = newRate`).
- **Absence Evidence**: An omission where a protective boundary is missing (e.g., modifying fees without an upper ceiling check, or having multiple admin capabilities without a timelock).
- **Documentation Evidence**: NatSpec docstrings, comments, or external disclosures that create contractual expectations or disclaim liabilities.

### 5.2 Category Definitions, Examples, and Counterexamples

#### 1. Privacy
* **Definition**: Storage, handling, or exposure of natural-person identifiable information (PII) on an immutable public ledger, or lack of privacy-preserving techniques for sensitive user data.
* **Positive Example**: State variables or event parameters storing cleartext emails, government IDs, physical street addresses, or telephone numbers (`string public userEmail;`, `event KYCRecorded(address user, string nationalId)`).
* **Counterexample (Negative)**: Cryptographic commitments, zero-knowledge roots, or hashes (`bytes32 public identityCommitment;`, `bytes32 emailHash`). Standard EVM addresses (`address wallet`) do not constitute PII violations under this operational standard.

#### 2. Termination
* **Definition**: Capabilities allowing deployers, administrators, or third parties to unilaterally terminate contract execution, destroy bytecode, or permanently freeze user interactions without bilateral consensus.
* **Positive Example**: Unilateral `selfdestruct` or `suicide` opcodes, irreversible emergency shutdown routines that bypass standard dispute or claim periods.
* **Counterexample (Negative)**: Temporary circuit breakers or pausable mechanisms (`PausableUpgradeable`, `whenNotPaused`) that halt transfers during emergencies while preserving user balances and contract state for subsequent resumption.

#### 3. Legal Compliance
* **Definition**: Governance concentration, bypasses of expected financial/regulatory hygiene (such as AML/KYC expectations in regulated assets), or architectural backdoors enabling unrestricted parameter changes without notice periods or multi-stakeholder approval.
* **Positive Example**: Centralized multi-role contracts where a single private key controls treasury, fee setters, minting, and proxy upgrades without timelock delays (`TimelockController`), allowing instant retroactive changes.
* **Counterexample (Negative)**: Decentralized governance systems with mandatory timelock delay queues (e.g., minimum 48-hour delay), multi-signature requirements with quorum thresholds, or immutable contracts with zero administrative backdoors.

#### 4. Liability
* **Definition**: Unilateral legal risk allocation, blanket exculpatory disclaimers in NatSpec, total exclusion of damages, or clauses shifting operational and software fault entirely onto end users.
* **Positive Example**: NatSpec comments containing explicit liability waivers: *"Software provided strictly as is. In no event shall developers be liable for direct, indirect, or lost funds"*, or clauses demanding users indemnify developers against all third-party actions.
* **Counterexample (Negative)**: Standard technical documentation, architecture diagrams, informational cautions (*"Caution: audit in progress"*), or standard SPDX open-source license declarations (`// SPDX-License-Identifier: MIT`).

#### 5. Payment / Financial
* **Definition**: Control asymmetries regarding fund custody, arbitrary fee/tax escalation without hard ceilings, balance confiscation, or mechanisms that alter settlement amounts unexpectedly.
* **Positive Example**: Admin functions modifying transfer taxes, commissions, or protocol fees without an enforceably bounded numerical maximum (`function setTax(uint256 newTax) external onlyOwner { tax = newTax; }`).
* **Counterexample (Negative)**: Fixed transaction fees, fee setters strictly bounded by constant maximums (`require(newFee <= MAX_FEE, "Exceeds cap")`), or immutable zero-fee protocols.

---

## 6. Review Workflow, Overlaps, and Severity Guidelines

### 6.1 Security Bugs vs. Legal/Operational Risk Labels
| Attribute | Security Vulnerability (e.g., CWE, Slither) | Operational Risk Label (Smart Contract Analyser) |
| :--- | :--- | :--- |
| **Focus** | Software defects, implementation bugs, arithmetic exploits, reentrancy. | Control asymmetry, governance imbalance, unilateral power, unfair terms. |
| **Intent** | Unintended coding flaw or execution edge-case. | Often intentional architectural feature granted to administrators or developers. |
| **Remediation** | Patch bug, fix math, add reentrancy guard. | Introduce governance timelocks, hard ceilings, bilateral rights, transparent disclaimers. |

*Crucial rule*: A security finding (such as `CWE-863: Incorrect Authorization`) does **not** automatically translate into an operational category (e.g., `Legal Compliance` or `Payment / Financial`). Annotators must evaluate the contractual consequence on user rights and funds.

### 6.2 Managing Overlapping Categories
Some functions exhibit characteristics across multiple categories. For example:
- A `setFee(uint256 newFee)` function without a ceiling in a single-admin contract triggers **`Payment / Financial`** (due to the unbounded fee) and contributes evidence to **`Legal Compliance`** (due to administrative centralization).
- Annotators should assign multi-label positive statuses where justified, providing category-specific rationales.

### 6.3 Severity Assignment
- **`critical`**: Imminent, irreversible fund loss or total unilateral contract destruction executable by a single party without warning.
- **`high`**: Significant control imbalance (e.g., uncapped tax up to 100%, plaintext PII on-chain) that directly harms users or violates core privacy standards.
- **`medium`**: Moderate operational hazard (e.g., parameter adjustments without timelock, ambiguous refund workflows) with bounded blast radius.
- **`low`**: Minor operational discrepancy or parameter edge case with low likelihood of user harm.
- **`info`**: Code hygiene, documentation gaps, or best-practice recommendations (e.g., using `safeTransferFrom` over `transfer`).
- **`none`**: Hazard absent or fully mitigated.

### 6.4 Escalation to Review Queue (`unresolved`)
An annotator must mark a record as **`unresolved`** and escalate it when:
1. **Code/Report Discrepancy**: The audit report describes a function or vulnerability not found in the bundled contract source code (e.g., version mismatch).
2. **Missing Inter-Contract Context**: The operational behavior depends on an external contract (e.g., Oracle, Factory, Proxy) that is missing from the record.
3. **Novel Architectural Pattern**: Complex governance architectures (e.g., optimistic rollups, dual-token voting) where standard timelock heuristics do not directly apply.

### 6.5 Status Values & Negative Verification Rule
Every category must explicitly hold one of four statuses:
- **`positive`**: Concrete syntactic or structural evidence satisfies the operational hazard criteria. Requires evidence and rationale.
- **`negative`**: Verifiable proof that the hazard is bounded, mitigated, or impossible (e.g., fee setter strictly bounded by constant ceiling).
- **`insufficient_information`**: Architectural context is missing, or related external contracts are needed.
- **`pending_review`**: Preliminary suggestion from automated parsing or audit finding awaiting human verification.

> [!WARNING]
> **The Negative Verification Principle**: Never treat "no security finding," "no rule fired," or missing evidence as proof that a contract is safe (`negative`). Absence of a finding only means the tool did not detect an issue; it does not prove the contract has fair or safe terms.

### 6.6 Avoiding Circular Labeling in `model_text`
When creating natural-language representations for Legal-BERT:
- Do not generate descriptive summaries using templates that parrot the rule's conclusion (e.g., generating *"This function has an unconstrained fee hazard"* and then labeling it as a fee hazard). This creates a circular feedback loop where the model learns the template syntax rather than underlying code and contractual meaning.
- All natural-language summaries must describe objective facts (who can call, what state changes, what funds move), must be labeled as `Draft Summary (Machine-generated, pending review)`, and must undergo human review before being used in training splits.
