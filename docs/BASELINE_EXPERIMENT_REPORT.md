# Smart Contract Analyser — Baseline Experiment & Benchmark Report

**Document Version**: 1.0.0  
**Status**: Completed  
**Milestone**: Dataset Preparation & Deterministic Baseline Experiment  
**Date**: October 21, 2026

---

## 1. Executive Summary

This report documents the preparation and evaluation of the **Deterministic Operational Baseline** for **Smart Contract Analyser** (referred to in earlier working drafts as *X-LegalContract*).

As established during the *Analysis Definition Step*, raw Solidity executable code cannot be treated as equivalent to natural language legal prose, and deep learning models like Legal-BERT should not be assumed to yield valid legal conclusions from code tokens alone. Before committing to neural fine-tuning or full FastAPI server construction, this phase implemented:
1. A **pure Python Solidity structural and NatSpec parser** (`analysis/parser.py`) that operates without external native binary dependencies (e.g., `solc` or `slither`).
2. A **deterministic rule engine** (`analysis/rules.py` and `analysis/engine.py`) detecting operational governance and contractual hazards, returning payloads conforming to the API specification defined in `ANALYSIS_SPECIFICATION.md`.
3. A **reproducible benchmark schema and manifest** (`analysis/benchmark_schema.py` and `analysis/data/benchmark/benchmark_manifest.json`) enforcing project-level grouping to prevent data leakage, complete with open-source MIT licensing and provenance tracking.
4. An **evaluation pipeline** (`analysis/evaluate.py`) that computes per-rule and per-category True Positives, False Positives, False Negatives, Precision, Recall, and F1 scores.

---

## 2. Assessment of Supportability: What Can and Cannot Be Extracted

A fundamental requirement of this phase is honesty regarding what Solidity syntax and NatSpec comments can reasonably support.

### 2.1 Critical Legal Disclaimers
* **AST patterns and NatSpec comments are NOT legal proof**: Detecting `selfdestruct` or a missing fee ceiling indicates an **operational capability** or **asymmetry of control**, not definitive proof that a contract violates a specific jurisdiction's statute or is legally unenforceable.
* **Security vs. Legal Risk Distinction**:
  - Technical security tools (Slither, Mythril) identify execution bugs (reentrancy, integer overflow, flash loan exploits).
  - This baseline strictly identifies **operational governance risks**: unilateral termination capabilities, unconstrained financial parameter modification, plaintext public personal data storage, and exculpatory liability waivers.

### 2.2 Category-by-Category Supportability Analysis

| Category | Input Source | What IS Supported | What CANNOT Be Supported | Operational Label |
|---|---|---|---|---|
| **`Termination`** | AST function statements | Presence of `selfdestruct` / `suicide` opcodes; privileged pause functions. | Cannot determine whether termination is mutual, approved by off-chain arbitration, or authorized by prior settlement agreements. | *Heuristic Operational Pattern: Unilateral Contract Termination Capability* |
| **`Payment / Financial`** | AST state assignments & conditions | Functions modifying fee/tax variables lacking ceiling `require()` checks. | Cannot determine if off-chain legal contracts bind the deployer not to raise fees, or if wrapper governance timelocks exist off-chain. | *Heuristic Operational Pattern: Unconstrained Financial Modification* |
| **`Privacy`** | AST state variable declarations | Non-constant `string` / `bytes` state variables named with sensitive PII terms (`email`, `ssn`, `physicalAddress`). | Cannot inspect whether off-chain payloads are encrypted with homomorphic encryption or zero-knowledge commitments unless typed as such. | *Heuristic Operational Pattern: High-Risk Plaintext PII Storage Indication* |
| **`Liability`** | NatSpec comments (`@notice`, `@dev`) | Broad exculpatory disclaimers (`as is`, `without warranty`, `no liability whatsoever`). | Cannot evaluate whether the user agreed via clickwrap/browsewrap, or whether local consumer law voids the clause. | *Heuristic Operational Pattern: Broad Liability Disclaimer in Documentation* |
| **`Legal Compliance`** | Contract inheritance & function modifiers | Contracts with multiple privileged administrative functions lacking inheritance of governance timelocks (`TimelockController`). | "Legal Compliance" as a broad legal category cannot be determined from code alone; it is strictly narrowed to advance notice and governance delay mechanisms. | *Heuristic Operational Pattern: Missing Governance Timelock Delay* |

---

## 3. Benchmark Methodology & Data Provenance

### 3.1 Sample Unit & Provenance Schema
A benchmark sample represents an entire Solidity source file with verified open-source licensing, explicit commit/version provenance, and contract-level grouping.

```json
{
  "sample_id": "BM-001",
  "project_name": "Synthetic-VulnerableEscrow-Project",
  "contract_file": "BM001_VulnerableEscrow.sol",
  "commit_or_version": "v1.0-benchmark",
  "license": "MIT",
  "source_url": "https://github.com/AroKrishna/Smart_Contract_Analyser/tree/main/analysis/data/contracts/BM001_VulnerableEscrow.sol",
  "collection_date": "2026-10-21",
  "split": "test",
  "labels": [ ... ]
}
```

### 3.2 Leakage Prevention Strategy
All contracts derived from the same project family or template repository are assigned to the **exact same data split** (`train`, `validation`, or `test`). The validator in `analysis/benchmark_schema.py` explicitly raises a `Data Leakage Detected` error if any project name is assigned to multiple splits.

### 3.3 Initial Curated Benchmark Suite (5 Contracts)

To evaluate the baseline honestly without fabricating large-scale numbers, an initial suite of 5 curated, MIT-licensed benchmark contracts was created in `analysis/data/contracts/`:

1. **`BM001_VulnerableEscrow.sol`** (Positive Hazard):
   - Features unilateral `selfdestruct(owner)` in `emergencyKill()`.
   - Features unconstrained fee modification in `setFee()`.
2. **`BM002_SafeTimelockedEscrow.sol`** (Negative Control for Financial/Termination):
   - Demonstrates a bounded fee setter (`require(newFee <= MAX_FEE)`).
   - Lacks selfdestruct or killswitch opcodes.
3. **`BM003_UserIdentityRegistry.sol`** (Positive Hazard for Privacy):
   - Declares public `string public userEmail` and `string public physicalAddress` state variables.
4. **`BM004_HighRiskStaking.sol`** (Positive Hazard for Liability/Financial):
   - Contains unconstrained fee setter `setTax()`.
   - Contains blanket NatSpec liability disclaimer (*"provided strictly as is without warranty of any kind... no liability whatsoever"*).
5. **`BM005_StandardGovernanceToken.sol`** (Clean Negative Control):
   - Standard ERC-20 reference token with zero administrative backdoors, no killswitch, no fee setters, and no PII.

---

## 4. Deterministic Baseline Implementation Details

### 4.1 Parser (`analysis/parser.py`)
- Implemented as a standalone, zero-dependency Python class `SolidityParser`.
- Extracts pragmas, contract declarations, inheritance, state variables, function signatures, modifiers, and preceding NatSpec docstrings.
- Computes exact 1-indexed source line numbers for line-accurate frontend highlights.
- Handles multi-line comments and malformed input gracefully.

### 4.2 Rules (`analysis/rules.py`)
Five deterministic rules were implemented, matching the 5 frontend categories:
- `RULE-TERM-01`: Detects `selfdestruct` / `suicide` opcodes.
- `RULE-FIN-01`: Detects unconstrained fee variable updates (excluding constructors).
- `RULE-PRIV-01`: Detects plaintext PII string/bytes state variables.
- `RULE-LIAB-01`: Detects exculpatory disclaimers in NatSpec.
- `RULE-GOV-01`: Detects administrative privilege concentration without timelocks.

### 4.3 Engine (`analysis/engine.py`)
- Coordinates parsing and rule execution.
- Generates composite `riskScore` (0–100) and `riskLevel` (`Low`, `Medium`, `High`, `Critical`).
- Computes category breakdowns across `Privacy`, `Termination`, `Legal Compliance`, `Liability`, and `Payment / Financial`.
- Populates rule-grounded token attributions for `shapValues` and `limeExplanations`.
- Produces the exact JSON schema defined in `ANALYSIS_SPECIFICATION.md`.

---

## 5. Benchmark Evaluation Results & Methodology Audit

Running `python -m analysis.evaluate dev` against the initial development/regression suite produces the following verified results:

### 5.1 Per-Rule Performance

| Rule ID | Category | Target Hazard | TP | FP | FN | TN | Support | Precision | Recall | F1 | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **`RULE-TERM-01`** | Termination | Unilateral `selfdestruct` | 1 | 0 | 0 | 4 | 1 | 1.000 | 1.000 | 1.000 | EVALUATED |
| **`RULE-FIN-01`** | Payment / Financial | Unconstrained fee setter | 2 | 0 | 0 | 3 | 2 | 1.000 | 1.000 | 1.000 | EVALUATED |
| **`RULE-PRIV-01`** | Privacy | Plaintext PII state storage | 1 | 0 | 0 | 4 | 1 | 1.000 | 1.000 | 1.000 | EVALUATED |
| **`RULE-LIAB-01`** | Liability | NatSpec exculpatory disclaimer | 1 | 0 | 0 | 4 | 1 | 1.000 | 1.000 | 1.000 | EVALUATED |
| **`RULE-GOV-01`** | Legal Compliance | Missing governance timelock | 0 | 0 | 0 | 5 | 0 | *Undefined* (`null`) | *Undefined* (`null`) | *Undefined* (`null`) | ZERO_POSITIVE_SUPPORT |

### 5.2 Per-Category Performance

| Category | TP | FP | FN | TN | Support | Precision | Recall | F1 | Status |
|---|---|---|---|---|---|---|---|---|---|
| **`Termination`** | 1 | 0 | 0 | 4 | 1 | 1.000 | 1.000 | 1.000 | EVALUATED |
| **`Payment / Financial`** | 2 | 0 | 0 | 3 | 2 | 1.000 | 1.000 | 1.000 | EVALUATED |
| **`Privacy`** | 1 | 0 | 0 | 4 | 1 | 1.000 | 1.000 | 1.000 | EVALUATED |
| **`Liability`** | 1 | 0 | 0 | 4 | 1 | 1.000 | 1.000 | 1.000 | EVALUATED |
| **`Legal Compliance`** | 0 | 0 | 0 | 5 | 0 | *Undefined* (`null`) | *Undefined* (`null`) | *Undefined* (`null`) | ZERO_POSITIVE_SUPPORT |

### 5.3 Methodology Audit & Discrepancy Corrections
An audit of the previous baseline evaluation code and manifest identified two critical defects that have now been corrected:

1. **Fabricated 1.000 Score on Zero Support (`RULE-GOV-01`)**:
   - In earlier reports, `RULE-GOV-01` was claimed to achieve 1.000 Precision, 1.000 Recall, and 1.000 F1 despite having 0 positive ground-truth instances across the entire suite (`support = 0`).
   - The prior `calc_scores` function in `evaluate.py` defaulted 0/0 divisions to `1.0`.
   - *Impact & Correction*: Precision, Recall, and F1 on a zero-support positive class are mathematically undefined. `evaluate.py` was corrected to return `null` and set `metric_status = "ZERO_POSITIVE_SUPPORT_UNDEFINED"`. Perfect performance on `RULE-GOV-01` is not supported and cannot be claimed.

2. **Split Leakage & Dev Reclassification**:
   - `RULE-FIN-01` was refined specifically during development to ignore `constructor()` assignments to resolve a false positive observed on `BM002_SafeTimelockedEscrow.sol`.
   - Tuning rules directly against contracts labeled as `test` violates held-out evaluation principles.
   - *Impact & Correction*: `BM001` through `BM005` were formally reclassified from `test` to `dev` in `benchmark_manifest.json`. A genuine held-out test split does not yet exist and is scheduled for implementation in the [Benchmark Expansion Plan](file:///c:/ARO/Projects/Smart_Contract_Analyser/docs/BENCHMARK_EXPANSION_PLAN.md).

---

## 6. Limitations & Threats to Validity

1. **Benchmark Scale & Dev Classification**: 
   - While the initial 5-contract suite verifies parsing, schema compliance, and rule mechanics, **a 5-contract dev suite cannot establish broad reliability, operational generalizability, or legal validity across the Ethereum ecosystem**.
   - A larger corpus of 35 real-world mainnet and synthetic contracts is detailed in [BENCHMARK_EXPANSION_PLAN.md](file:///c:/ARO/Projects/Smart_Contract_Analyser/docs/BENCHMARK_EXPANSION_PLAN.md).
2. **Automated Visual Browser Testing Limitation**:
   - Automated end-to-end browser testing via Playwright could not run due to an environment dependency issue (the Playwright browser binary `1.57.0-win32_x64.zip` returned HTTP 404 from the upstream CDN).
   - While the React frontend was verified via Vite build, ESLint, and manual browser verification, automated browser visual regression tests remain unverified until alternative drivers (e.g., Selenium/Puppeteer) or driver mirrors are configured.
3. **Obfuscated and Proxy Patterns**:
   - The current baseline analyzes single-file Solidity source code. Contracts utilizing `delegatecall` upgradeable proxies (ERC-1967) or diamond multi-facet patterns (ERC-2535) can hide administrative killswitches in external implementation contracts.
4. **Regex vs. Full AST Graph**:
   - The lightweight regex/AST parser cannot trace inter-procedural dataflow (e.g., if a fee variable is passed through three internal helper functions before being validated).
5. **Non-Exhaustive NatSpec**:
   - Disclaimers formatted in non-standard English or outside NatSpec blocks will be missed.

---

## 7. Recommended Next Implementation Steps

Having established a working, honest, deterministic baseline that produces valid findings matching the UI schema:

1. **Step 1: Benchmark Dataset Expansion**:
   - Curate 20–30 real-world, open-source DeFi and token contracts from GitHub / Etherscan (e.g., Uniswap, Compound, OpenZeppelin clones) into `analysis/data/contracts/` and record their verified labels in `benchmark_manifest.json`.
2. **Step 2: FastAPI Wrapper**:
   - Wrap `AnalysisEngine.analyze_source()` in a minimal FastAPI service exposing `POST /api/v1/analyze`, returning the exact JSON payload already tested.
3. **Step 3: Frontend Integration**:
   - Replace the simulated timer in `frontend/src/pages/NewAnalysis.jsx` with an HTTP `fetch()` call to the FastAPI endpoint, rendering real baseline findings in `AnalysisResult.jsx`.
