# Manual Testing Sample Contracts

This directory contains standalone Solidity (`.sol`) contracts designed for **manual end-to-end testing** of the **Smart Contract Analyser** web platform (Phase 1).

> [!WARNING]
> **Research & Testing Disclaimer**:
> These contracts are synthetic, illustrative test inputs designed to verify website file uploads, API processing, UI rendering, and token-attribution visualization.
> - They do **not** represent verified ground-truth training records.
> - They do **not** constitute legal advice, regulatory compliance guarantees, or judicial enforceability determinations.
> - Successful or unsuccessful hazard detection by the machine learning engine does not prove real-world legal immunity or safety.

---

## 📁 Sample Contracts Inventory

| File | Primary Pattern / Risk Category | Description |
| :--- | :--- | :--- |
| **[`00_CleanControl.sol`](00_CleanControl.sol)** | **Control Baseline (Benign)** | Balanced bilateral escrow with deposit, release, and arbiter dispute resolution. No killswitches, unbounded fees, PII, or broad exculpatory disclaimers. |
| **[`01_TerminationRisk.sol`](01_TerminationRisk.sol)** | **Termination** | Unilateral owner-controlled `emergencyKill()` function executing the `selfdestruct` opcode without participant notice or multi-sig delay. |
| **[`02_PrivacyRisk.sol`](02_PrivacyRisk.sol)** | **Privacy** | Public plaintext state variables (`userEmail`, `physicalAddress`) storing natural-person identifying data directly on an immutable public blockchain. |
| **[`03_UnboundedFeeRisk.sol`](03_UnboundedFeeRisk.sol)** | **Payment / Financial** | Administrative `setProtocolFee()` function modifying fee rates without enforcing an immutable upper ceiling check (`require(newFee <= MAX_CAP)`). |
| **[`04_LiabilityDisclaimer.sol`](04_LiabilityDisclaimer.sol)** | **Liability** | Token distributor with explicit NatSpec clauses disclaiming all warranties ("as is / without warranty"), excluding total liability, and waiving participant indemnification. |
| **[`05_CentralizedAdminRisk.sol`](05_CentralizedAdminRisk.sol)** | **Legal Compliance** | Highly centralized treasury with immediate pause toggling, unilateral blacklisting, allocation overrides, and zero timelock delay mechanisms. |
| **[`06_CombinedRisks.sol`](06_CombinedRisks.sol)** | **Composite (Multi-Risk)** | Multi-risk contract combining `selfdestruct`, plaintext PII (`userEmail`), unconstrained fee setters, and arbitrary operational halt controls. |

---

## 🚀 How to Test on the Web Application

1. **Start the Local Application** (if not already running):
   - **Backend**:
     ```bash
     uvicorn analysis.api:app --host 127.0.0.1 --port 8000 --reload
     ```
   - **Frontend**:
     ```bash
     cd frontend
     npm run dev
     ```
   - Open **`http://localhost:5173/`** in your browser.

2. **Navigate to the Upload Page**:
   - Click **"New Analysis"** in the sidebar or navbar (or visit `http://localhost:5173/new-analysis`).

3. **Upload a Sample Contract**:
   - Drag and drop one of the `.sol` files from this folder into the upload zone (or click to browse).
   - Alternatively, open the file in your editor, copy the Solidity code, and paste it into the code editor tab.

4. **Run the Analysis**:
   - Click **"Run Analysis"**.
   - Observe the multi-stage progress indicator:
     1. Syntax Parsing & AST Tokenization
     2. Legal-BERT Multi-Label Inference
     3. SHAP & LIME Interpretability Attribution
     4. Synthesizing Audit Report

5. **Inspect the Results**:
   - **Executive Risk Overview**: Overall risk level, uncalibrated sigmoid score, and 5-category breakdown.
   - **Code Viewer**: Highlighted lines pointing to real source code lines.
   - **Explainability (XAI)**: SHAP token attribution bar chart and LIME local surrogate weights.
   - **Remediation Recommendations**: Suggested before/after refactoring guidance.
   - **AI Legal Assistant**: Ask context-specific follow-up questions about the analyzed contract.
   - **Export**: Generate and download real PDF and DOCX audit reports.

---

## 🔒 Separation from the Machine Learning Dataset

To maintain scientific integrity and prevent data leakage:
- These files are **strictly excluded** from the canonical machine learning dataset (`data/ml_candidates/final_dataset.jsonl`).
- They are **not** training, validation, or test split samples.
- No model weights, decision thresholds, or production code have been modified to hardcode verdicts for these test files.
