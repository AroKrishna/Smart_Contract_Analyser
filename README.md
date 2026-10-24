# Smart Contract Analyser — Final Local Edition

> **Explainable AI (XAI) Framework for Automated Legal-Risk Assessment in Solidity Smart Contracts**  
> *Downloadable, fully offline & private single-user college application. No registration, no login, and no cloud accounts required.*

[![React](https://img.shields.io/badge/React-19-blue.svg)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-8-purple.svg)](https://vite.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-emerald.svg)](https://fastapi.tiangolo.com/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-red.svg)](https://pytorch.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📌 Project Overview

**Smart Contract Analyser** is a downloadable, locally run college research application designed to evaluate Solidity smart contracts for potential operational and legal risks prior to deployment.

While standard security audit tools focus on technical execution vulnerabilities (reentrancy, integer overflows, access control), a smart contract can execute without technical runtime errors while still containing clauses that violate legal standards, enforce punitive unilateral forfeitures, or impose unconstrained liabilities.

This application runs **entirely on your own computer**:
- The **FastAPI backend** runs on local loopback (`127.0.0.1:8000`).
- The **React frontend** runs locally via Vite (`http://127.0.0.1:5173`).
- **Legal-BERT neural inference** runs locally on your CPU/GPU.
- All uploaded `.sol` files, analysis history, SQLite database records, and generated PDF/DOCX reports remain strictly on your local disk.
- **Zero login requirement**: No registration, no passwords, no session cookies, and no cloud accounts or external database connections.

---

## 🔬 Core Analysis Pipeline

```text
Uploaded Solidity Contract (.sol)
        ↓
AST Tokenization & Clause Parsing
        ↓
Local Legal-BERT Multi-Category Classification
        ↓
SHAP + LIME Token-Level Interpretability
        ↓
Risk Breakdown Across 5 Operational Categories
        ↓
Context-Grounded AI Legal Assistant & Statutory Recommendations
        ↓
Local SQLite Persistence & PDF / DOCX Report Exports
```

### The 5 Operational Risk Categories:
1. **Privacy**: State-level exposure of personally identifiable information, non-compliance with data deletion mandates, public ledger confidentiality friction.
2. **Termination**: Unilateral emergency destruction (`selfdestruct`), unconstrained pause mechanisms without recourse, arbitrary contract kill-switches.
3. **Legal Compliance**: Unfair standard terms, consumer protection friction, regulatory disclosure non-compliance.
4. **Liability**: Unbalanced indemnity clauses, complete disclaimers for intentional misconduct, asymmetric risk allocation.
5. **Payment / Financial**: Unilateral fee modifications, locked balances, arbitrary confiscation routines.

---

## ⚖️ Non-Legal-Advice Disclaimer

> [!WARNING]
> **Academic Decision-Support Tool — Not Legal Advice**  
> Smart Contract Analyser is an automated, experimental decision-support application built for academic research and operational risk screening. It does **not** provide legal advice, does **not** substitute for qualified legal counsel, and does **not** guarantee statutory validity or compliance across legal jurisdictions. Always consult an attorney for contract reviews.

---

## 💻 System Prerequisites

Before running the project on your machine:

| Component | Minimum Version | Verified Version | Notes |
|:---|:---|:---|:---|
| **Python** | 3.10+ | 3.14.3 / 3.11 | Required for FastAPI backend and PyTorch |
| **Node.js** | 18.0+ | 20.x / 22.x | Required for React frontend |
| **npm** | 9.0+ | 10.x+ | Included with Node.js |
| **Git** | 2.30+ | Latest | Required to clone the repository |
| **Disk Space** | ~1.5 GB | - | Model weights (~418 MB) + virtual env + node_modules |

---

## 🚀 Setup & Installation Guide

Follow these steps in order to install and launch the application on your computer.

### Step 1: Clone the Official Repository

```bash
git clone https://github.com/AroKrishna/Smart_Contract_Analyser.git
cd Smart_Contract_Analyser
```

---

### Step 2: Set Up Python Backend & Dependencies

From the repository root:

**Windows (PowerShell):**
```powershell
# 1. Create a Python virtual environment
python -m venv .venv

# 2. Activate the virtual environment
.venv\Scripts\Activate.ps1

# 3. Upgrade pip and install backend dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt
```

**Linux / macOS (Bash):**
```bash
# 1. Create a Python virtual environment
python3 -m venv .venv

# 2. Activate the virtual environment
source .venv/bin/activate

# 3. Upgrade pip and install backend dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

### Step 3: Download & Verify Legal-BERT Model Weights

The neural analysis engine requires the fine-tuned Legal-BERT model weights (`model.safetensors`, ~418 MB). Model binaries are excluded from Git to keep the repository lightweight.

> [!NOTE]
> **Internet vs. Offline Execution**: Installing Python and npm packages and downloading the model weights require an active internet connection. Once dependencies and model weights are downloaded to your machine, the application operates **100% locally and completely offline** without requiring any internet access.

Run the built-in setup script to automatically download the verified release asset and check its SHA-256 hash:

```bash
python scripts/setup_model.py
```

To verify the local model file at any time without re-downloading:
```bash
python scripts/setup_model.py --check-only
```

#### Manual Download Alternative:
If your network restricts automated Python downloads, download the file manually:
- **Download URL**: `https://github.com/AroKrishna/Smart_Contract_Analyser/releases/download/v3.3.0/model.safetensors`
- **Destination Path**: `analysis/models/legal_bert_v3.3.0/model.safetensors`
- **Expected SHA-256**: `4c5d1c1caf6f42e38173d6fc1b69a924cf2ad93e0188e0f5bb057ac0b73d972e`

Verify the hash:
- **Windows (PowerShell)**: `(Get-FileHash -Algorithm SHA256 analysis\models\legal_bert_v3.3.0\model.safetensors).Hash`
- **Linux**: `sha256sum analysis/models/legal_bert_v3.3.0/model.safetensors`
- **macOS**: `shasum -a 256 analysis/models/legal_bert_v3.3.0/model.safetensors`

---

### Step 4: Install Frontend Dependencies

In a new terminal (or navigate to `frontend`):

```bash
cd frontend
npm install
cd ..
```

---

### Step 5: Start the Backend Service (Terminal 1)

In your activated Python environment from the repository root:

```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

The service will bind strictly to local loopback (`127.0.0.1`).

#### Verify Backend Status:
- **Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health) (returns `{"status":"healthy","engine":"legal_bert_ml_engine",...}`)
- **Model Readiness Probe**: [http://127.0.0.1:8000/ready](http://127.0.0.1:8000/ready) (returns `{"status":"ready","checkpointName":"legal_bert_v3.3.0",...}`)
- **Interactive OpenAPI Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

### Step 6: Start the Frontend Application (Terminal 2)

In a second terminal:

```bash
cd frontend
npm run dev
```

Open your browser at:
**[http://localhost:5173/](http://localhost:5173/)** (or [http://127.0.0.1:5173/](http://127.0.0.1:5173/))

---

## 🖥️ Using the Application (No Account Required)

1. **Direct Access**: When you open the application, you land directly on the **Auditor Workspace** dashboard. No login or registration screens appear.
2. **Submit a Contract**: Click **New Audit** or navigate to `/analysis/new`. Either upload a `.sol` file or paste Solidity source code directly into the editor. Sample contract templates (Escrow, Vault, Token) are provided as quick-load buttons.
3. **Run Analysis**: Click **Run Legal-BERT Analysis**. The live asynchronous stepper will track:
   - Syntax validation
   - AST clause extraction
   - Neural Legal-BERT multi-category classification
   - Real-time token saliency (SHAP & LIME computation)
   - Persistence into the local SQLite database
4. **Explore Explainability (XAI)**:
   - View composite and per-category risk scores (Low, Medium, High, Critical).
   - Review the syntax-highlighted contract source with flagged risk line badges.
   - Click clauses to inspect SHAP marginal contributions and LIME local surrogate weights.
   - Read specific statutory explanations and actionable code remediations.
5. **AI Legal Assistant**: Chat with the integrated assistant in the results pane. Answers are strictly grounded in the analyzed contract's findings.
6. **Download Reports**: Click **Export PDF** or **Export DOCX** to generate executive compliance audit reports.
7. **View Audit History**: Open `/history` to view all saved analyses. Filter by risk tier or search by contract name.
8. **Delete Analyses**: Click **Delete** on any audit card to permanently purge its database entry and associated uploaded source file from local disk.

---

## 📁 Local Data Storage, Privacy & Security

All application state is stored locally on your machine and never leaves your computer:

| Data Asset | Exact Local Location | Purpose |
|:---|:---|:---|
| **SQLite Database** | `backend/data/transient_smart_contract_analyser.db` | Stores audit records, risk scores, findings, and metadata. |
| **Uploaded Contracts** | `backend/data/storage/local_user/` | Physical storage directory for uploaded `.sol` files. |
| **Model Weights** | `analysis/models/legal_bert_v3.3.0/model.safetensors` | Neural weights for the fine-tuned classifier. |
| **Generated Reports** | Dynamically streamed | PDF and DOCX reports are generated in-memory on demand. |

### Browser Security Protection (No-Login Safeguards)
Because this application runs without passwords or cloud accounts on your local computer, the backend incorporates automatic **Host & Origin Protection**:
- **Loopback Binding**: The backend listens strictly on loopback (`127.0.0.1`), never exposing open ports on your local network.
- **DNS Rebinding Defense**: Requests with forged or untrusted `Host` headers are automatically rejected (HTTP 403).
- **Cross-Site Attack Prevention**: External websites running in your browser cannot issue state-changing requests (`POST`, `DELETE`, etc.) or drive-by submissions against your local application. State-changing calls must originate from your local frontend.

### How to Reset Local Data
- **In-App Reset**: Click **Delete** next to any audit in `/history` to remove it cleanly.
- **Complete Local Reset**: If you wish to wipe all past audits and uploads, stop the backend and delete the local database file:
  ```powershell
  # Windows
  Remove-Item backend\data\transient_smart_contract_analyser.db -ErrorAction SilentlyContinue
  Remove-Item backend\data\storage\local_user\* -Recurse -Force -ErrorAction SilentlyContinue
  ```
  ```bash
  # Linux / macOS
  rm -f backend/data/transient_smart_contract_analyser.db
  rm -rf backend/data/storage/local_user/*
  ```
  On next backend startup, a fresh SQLite database schema will be automatically created.

---

## 🔧 Troubleshooting

| Issue | Cause | Solution |
|:---|:---|:---|
| **Port 8000 already in use** | An old backend process is still running | Find and terminate the process using port 8000 (`Get-NetTCPConnection -LocalPort 8000` on Windows, or `lsof -i :8000` on Linux/Mac), or run on another port with `--port 8001` (and update frontend proxy in `frontend/vite.config.js`). |
| **`/ready` returns 503 "not_ready"** | Model weights missing or invalid hash | Run `python scripts/setup_model.py` to download and verify `model.safetensors`. |
| **Frontend shows "Backend Offline"** | Backend server is not running on port 8000 | Verify that Terminal 1 is running `uvicorn backend.main:app --host 127.0.0.1 --port 8000` and `http://127.0.0.1:8000/health` responds. |
| **Git Clone Permission Denied** | Target repository is private | Request that the owner add your GitHub username under **Repository Settings ➔ Collaborators**. |
| **Analysis job takes 15–30 seconds** | CPU computation of SHAP/LIME | This is normal behavior: calculating genuine Shapley values and LIME surrogate models on CPU takes 10–25 seconds depending on contract length. |

---

## 🧪 Automated Verification Suite

To verify the backend API contracts and end-to-end unauthenticated local workflows:
```bash
python -m pytest tests/test_api.py tests/test_end_to_end_workflow.py
```

To verify the frontend production build:
```bash
cd frontend
npm run build
```

---

## 🔬 Scientific Disclosure & Model Limitations

1. **Small-Scale Training Distribution & Evaluation Realism**:
   - The fine-tuned Legal-BERT multi-category classifier was trained on a small canonical dataset of 58 smart contracts (38 real-source, 20 synthetic training instances).
   - On strictly isolated held-out test contracts ($N=7$), natural prevalence of certain rare hazards (*Privacy*, *Liability*, and *Payment / Financial*) is zero. For these zero-support categories, metrics are transparently marked as inconclusive.
   - For categories with test support (*Termination* with $N=3$ positives, *Legal Compliance* with $N=4$ positives), predicted probabilities with the uncalibrated default 0.50 threshold fell below 0.50, yielding precision, recall, and F1 metrics of 0.00 (with specificity of 1.00).
   - **Academic Purpose**: This system is an experimental decision-support research prototype. Outputs are heuristic indicators and must **never** be represented as reliable, clinically validated, or production-grade legal advice.
2. **Deterministic Fallback Transparency**:
   - The platform never fabricates model verdicts. When the model weights are absent, the system transparently indicates `model_unavailable` with exact dataset readiness diagnostics rather than silently substituting mock predictions.
3. **Interpretability Scope**:
   - SHAP values and LIME weights are computed over normalized AST code tokens. They highlight clauses statistically correlated with operational hazards, but do not replace comprehensive human code review.

---

## 📄 License & Rights

- **Project-Owned Code**: Licensed under the **MIT License**. See [LICENSE](LICENSE) for full terms. Copyright (c) 2026 AroKrishna.
- **Third-Party Materials**: Pre-trained foundation weights (`nlpaueb/legal-bert-base-uncased`, Apache-2.0), smart contract code extracts, and third-party libraries retain their respective upstream licenses. See [ATTRIBUTION.md](ATTRIBUTION.md) for full notices.

