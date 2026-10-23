# Smart Contract Analyser

> **Explainable AI (XAI) Framework for Automated Legal-Risk Assessment in Solidity Smart Contracts**

[![React](https://img.shields.io/badge/React-19-blue.svg)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-8-purple.svg)](https://vite.dev/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-v4-38bdf8.svg)](https://tailwindcss.com/)
[![License](https://img.shields.io/badge/License-MIT-emerald.svg)](LICENSE)

---

## 📌 Project Overview

**Smart Contract Analyser** is a web-based Explainable AI SaaS platform designed to analyze Solidity smart contracts for potential pre-deployment legal and compliance risks.

While traditional smart contract auditing predominantly focuses on execution-level security (reentrancy, integer overflows, access control), a smart contract can execute without technical runtime errors while still containing terms that impose illegal penalties, violate consumer protection guidelines, or create severe legal liability.

This system provides automated pre-deployment decision support, pairing **Legal-BERT-based semantic classification** with **SHAP and LIME interpretability** to highlight risky clauses, explain model verdicts, and suggest safer contractual alternatives.

---

## 🔬 Core AI & Research Pipeline

```text
Solidity Smart Contract
        ↓
Preprocessing & Normalization
        ↓
AST Tokenization
        ↓
Legal-BERT-based Analysis
        ↓
Legal Risk Classification
        ↓
SHAP + LIME Interpretability Engine
        ↓
Risk Score & 5 Risk Categories
        ↓
Remediation Recommendations
        ↓
Structured Decision-Support Audit Report
```

### The 5 Primary Legal Risk Categories:
1. **Privacy**: Unintended exposure of personal data, storage of identifiable records on public ledger states, and GDPR/CCPA friction.
2. **Termination**: Unilateral emergency self-destruction (`selfdestruct`), indefinite freeze mechanisms, and cancellation without participant recourse.
3. **Legal Compliance**: Non-compliance with consumer protection regulations, fee disclosure mandates, and statutory standards.
4. **Liability**: Punitive indemnity clauses, complete exclusion of liability for intentional misconduct, and unbalanced risk allocation.
5. **Payment / Financial**: Locked withdrawals, arbitrary fee alterations, and unilateral fund confiscation clauses.

### Explainable AI (XAI) Layer:
* **SHAP (Shapley Additive Explanations)**: Measures the game-theoretic marginal contribution of each code token to demonstrate which constructs pushed the contract into a higher or lower risk category.
* **LIME (Local Interpretable Model-agnostic Explanations)**: Constructs local surrogate models around individual clause boundaries to provide human-interpretable explanations.

---

## ⚖️ Responsible Auditing Disclaimer

**Smart Contract Analyser is an automated, pre-deployment decision-support auditing tool.** 
* It is **not** intended to replace qualified legal counsel.
* It does **not** guarantee statutory legal compliance across jurisdictions.
* It does **not** certify that a smart contract is legally binding or valid.
Developers and organizations must always consult professional legal advisors for official contract validation.

---

## 📂 Project Architecture

```text
Smart_Contract_Analyser/
├── docs/
│   ├── CURRENT_STATE_AND_GAPS.md   # Verified audit of implementation vs target spec
│   ├── ANALYSIS_SPECIFICATION.md   # Unified analysis schema & API contract
│   ├── BASELINE_EXPERIMENT_REPORT.md # Deterministic baseline experiment & dev metrics
│   ├── BENCHMARK_EXPANSION_PLAN.md # 35-contract benchmark expansion roadmap
│   ├── ANNOTATION_GUIDE.md         # Labeling standards for operational hazards
│   ├── PROJECT_CONTEXT.md          # Master context and taxonomy
│   ├── FRONTEND_ROUTES.md          # 10 application routes mapping
│   └── reference/                  # Authoritative DOCX platform specification
│
├── analysis/
│   ├── api.py                      # FastAPI REST service & LRU in-memory cache
│   ├── engine.py                   # Composite risk calculator & finding synthesizer
│   ├── parser.py                   # Pure Python Solidity regex & NatSpec parser
│   ├── rules.py                    # 5 deterministic operational pattern rules
│   ├── evaluate.py                 # Benchmark evaluation & confusion matrix harness
│   ├── benchmark_schema.py         # Provenance schema & split isolation validator
│   └── data/                       # Dev contracts (BM001-BM005) & benchmark manifest
│
├── tests/
│   └── test_api.py                 # FastAPI endpoint & payload validation tests
│
├── frontend/
│   ├── public/                     # Static assets & routing rewrites
│   ├── src/
│   │   ├── components/             # Reusable UI, layout, dashboard, & analysis components
│   │   ├── pages/                  # Landing, Login, Register, Dashboard, NewAnalysis, AnalysisResult, History, Reports, Profile, Settings
│   │   ├── layouts/                # PublicLayout, DashboardLayout
│   │   ├── data/                   # mockData.js (Fallback demo datasets)
│   │   ├── services/api.js         # API client with dual-target fallback & session cache
│   │   ├── utils/constants.js      # Risk categories, levels, and pipeline stages
│   │   ├── App.jsx                 # React Router v7 configuration
│   │   └── index.css               # Tailwind CSS v4 styling & Inter font
│   └── package.json
│
├── .gitignore                      # Prevents committing node_modules, cache, and builds
└── README.md
```

---

## 🚦 Current Release vs. Research Target

- **Current Public Release**:
  - Open public access without mandatory login.
  - Interactive Solidity source code upload (.sol) or paste.
  - Deterministic operational baseline analyzing 5 primary legal-risk categories.
  - Temporary in-memory LRU cache (100 entries) and browser session caching.
  - Rule-derived illustrative token attributions populating XAI charts.
- **Research & Platform Target (In Progress)**:
  - Deep learning integration with **Legal-BERT** for semantic clause classification.
  - Genuine game-theoretic **SHAP** and local surrogate **LIME** model interpretability.
  - Empirical model confidence calibration.
  - Multi-contract compilation with full AST graphs and proxy resolution.
  - Persistent database, user accounts, and scoped AI legal assistant.

See [docs/CURRENT_STATE_AND_GAPS.md](docs/CURRENT_STATE_AND_GAPS.md) for the complete verified gap audit.

---

## 🚀 Getting Started Locally

### Prerequisites
* **Python** (v3.10+ recommended, verified on 3.14.3)
* **Node.js** (v18.0 or newer recommended, verified on v20+)
* **npm** (v9.0 or newer)
* **Docker & Docker Compose** (optional, for containerized execution)

---

### 1. Clone the repository
```bash
git clone https://github.com/AroKrishna/Smart_Contract_Analyser_Private.git
cd Smart_Contract_Analyser_Private
```

---

### 2. Configure Environment Variables
Copy the template configuration into `.env` in the project root:

**Windows (PowerShell):**
```powershell
Copy-Item .env.example .env
```

**Linux / macOS (Bash):**
```bash
cp .env.example .env
```

Key variables configured in `.env` (with safe default placeholders):
- `ALLOWED_ORIGINS`: Comma-separated CORS origins (defaults to `http://localhost:5173,http://127.0.0.1:5173`).
- `MAX_CONCURRENT_ANALYSIS_JOBS`: Concurrency throttle for CPU protection (default: `1`).
- `RATE_LIMIT_PER_MINUTE`: Sliding-window submission limit per client IP (default: `20`).
- `ANALYSIS_TTL_MINUTES`: In-memory analysis retention TTL in minutes (default: `30`).
- `MAX_STORED_ANALYSES`: Maximum in-memory FIFO analyses cache (default: `100`).
- `STORAGE_DIR`: Local filesystem storage directory for uploaded `.sol` files (defaults to `backend/data/storage`).
- `DATA_RETENTION_DAYS`: Retention lifecycle period for analyses and uploaded contracts (default: `30` days).
- `JWT_SECRET`: Secret key used for signing session tokens (pre-configured for development; change for production).
- `SEED_DEV_ACCOUNTS`: Automatically seeds local test accounts when set to `true` (default: `true` in local development).
- `MODEL_WEIGHTS_URL`: Optional direct HTTPS URL to download weights automatically if absent.
- `EXPECTED_MODEL_SHA256`: Expected SHA-256 hash for verifying model weights (`4c5d1c1caf6f42e38173d6fc1b69a924cf2ad93e0188e0f5bb057ac0b73d972e`).

---

### 3. Legal-BERT Model Checkpoint Setup
The active analysis engine expects the fine-tuned Legal-BERT checkpoint at:
`analysis/models/legal_bert_v3.3.0/model.safetensors` (~438 MB).
*(The backend also automatically recognizes `backend/analysis/models/legal_bert_v3.3.0/model.safetensors`).*

> [!NOTE]
> Because ordinary Git repositories reject files exceeding 100 MiB and Git LFS is omitted to prevent bandwidth quotas, binary model weight files are excluded from Git via `.gitignore`. Model architecture configs (`config.json`), tokenizer definitions, and training metrics are tracked in the repository.

#### Option A: Automated Cross-Platform Setup Script (Recommended)
Use the included model setup script to download and verify the checksum in one command:
```bash
python scripts/setup_model.py
```
To check an existing local checkpoint without re-downloading:
```bash
python scripts/setup_model.py --check-only
```

#### Option B: Manual Download from Official Release Asset
You can download the verified release asset directly:

- **Release Asset URL**:
  `https://github.com/AroKrishna/Smart_Contract_Analyser/releases/download/v3.3.0/model.safetensors`
- **Expected SHA-256 Checksum**:
  `4c5d1c1caf6f42e38173d6fc1b69a924cf2ad93e0188e0f5bb057ac0b73d972e`

**Windows (PowerShell):**
```powershell
# Create destination directory if needed
New-Item -ItemType Directory -Force -Path "analysis\models\legal_bert_v3.3.0"

# Download model checkpoint weights (~438 MB)
curl.exe -L -o "analysis\models\legal_bert_v3.3.0\model.safetensors" "https://github.com/AroKrishna/Smart_Contract_Analyser/releases/download/v3.3.0/model.safetensors"

# Verify SHA-256 checksum
(Get-FileHash -Algorithm SHA256 "analysis\models\legal_bert_v3.3.0\model.safetensors").Hash
# Must output: 4C5D1C1CAF6F42E38173D6FC1B69A924CF2AD93E0188E0F5BB057AC0B73D972E
```

**Linux / macOS (Bash):**
```bash
# Create destination directory if needed
mkdir -p analysis/models/legal_bert_v3.3.0

# Download model checkpoint weights (~438 MB)
curl -L -o analysis/models/legal_bert_v3.3.0/model.safetensors "https://github.com/AroKrishna/Smart_Contract_Analyser/releases/download/v3.3.0/model.safetensors"

# Verify SHA-256 checksum
# Linux:
sha256sum analysis/models/legal_bert_v3.3.0/model.safetensors
# macOS:
shasum -a 256 analysis/models/legal_bert_v3.3.0/model.safetensors
# Expected output: 4c5d1c1caf6f42e38173d6fc1b69a924cf2ad93e0188e0f5bb057ac0b73d972e
```

#### Option C: Automated Runtime Acquisition via Environment Variables
Configure your `.env` with:
```bash
MODEL_WEIGHTS_URL=https://github.com/AroKrishna/Smart_Contract_Analyser/releases/download/v3.3.0/model.safetensors
EXPECTED_MODEL_SHA256=4c5d1c1caf6f42e38173d6fc1b69a924cf2ad93e0188e0f5bb057ac0b73d972e
```
On boot or first request, the backend engine safely downloads the weights into cache, verifies the SHA-256 checksum, and performs an atomic file swap.

#### Strict Model Integrity Gating
If model weights are missing or have an invalid checksum, the system **never generates mock, simulated, or rule-substituted predictions**:
- `GET /ready` returns `HTTP 503 Service Unavailable` with `"status": "not_ready"`.
- `POST /api/v1/analyze` returns transparent `"status": "model_unavailable"` with exact dataset readiness diagnostics.
Once the valid checkpoint is present:
```bash
curl http://127.0.0.1:8000/ready
# Returns HTTP 200: {"status":"ready","checkpointName":"legal_bert_v3.3.0", ...}
```

---

### 4. Start the FastAPI Backend (Terminal 1)

**Windows (PowerShell):**
```powershell
# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install backend dependencies
pip install -r requirements.txt

# Launch API server on port 8000
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

**Linux / macOS (Bash):**
```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install backend dependencies
pip install -r requirements.txt

# Launch API server on port 8000
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

To stop the backend service: press `Ctrl + C` in the backend terminal.

#### Verified Local Backend Endpoints:
- **Backend Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- **Model Readiness Probe**: [http://127.0.0.1:8000/ready](http://127.0.0.1:8000/ready)
- **Interactive Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc API Documentation**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

### 5. Start the React Frontend (Terminal 2)

In a second terminal:

**Windows / Linux / macOS:**
```bash
cd frontend
npm install
npm run dev
```

To stop the frontend service: press `Ctrl + C` in the frontend terminal.

#### Verified Local Frontend URL:
- **Frontend Web Application**: [http://localhost:5173/](http://localhost:5173/)

The Vite development server automatically proxies `/api`, `/health`, and `/ready` requests to the local backend at `http://127.0.0.1:8000`.

---

### 6. Local First-Use Walkthrough

1. **Access Application**: Navigate to [http://localhost:5173/](http://localhost:5173/) in your web browser.
2. **Account Registration / Login**:
   - Register a new local account at `/register` (name, email, password, organization), or:
   - Log in using seeded development credentials:
     - **Auditor**: `auditor@enterprise.com` / `AuditorPass2026!`
     - **Admin**: `admin@legal-ai.io` / `AdminPass2026!`
3. **Submit a Contract for Analysis**:
   - Navigate to `/analysis/new`.
   - Paste raw Solidity code or upload a `.sol` contract file (sample contracts are provided in `sample_contracts/` and the UI sample buttons).
   - Click **Run Legal-BERT Analysis**.
4. **Inspect Real-Time Analysis Progress**:
   - The interactive stepper tracks the asynchronous pipeline stages: Syntax Validation ➔ AST Clause Extraction ➔ Neural Legal-BERT Inference ➔ XAI Token Attribution (SHAP/LIME) ➔ Compliance Synthesis & Persistence.
5. **Review Analysis Results**:
   - View the overall composite risk score and category breakdown (Privacy, Termination, Legal Compliance, Liability, Payment / Financial).
   - Inspect the interactive code viewer with syntax highlighting and hazard line badges.
   - Click clauses to review the **Explainable AI (XAI)** token attributions (SHAP marginal contribution and LIME interpretability breakdown).
   - Review side-by-side remediation recommendations (risky clause vs safer alternative).
6. **Query the AI Legal Assistant**:
   - In the results panel, chat with the context-scoped AI assistant. The assistant answers questions strictly grounded in the analyzed contract's findings and statutory matrix.
7. **Export Audit Reports**:
   - Download professional **PDF** and editable **DOCX** audit reports directly from `/reports` or the results dashboard.
8. **Manage History & Data Deletion**:
   - View historical audits at `/history`.
   - Perform cascading deletion of any audit: removes the database record, physical uploaded file, and background jobs permanently from local storage.

---

### 7. Local Storage & Data Lifecycle Locations

All application state, user accounts, uploaded files, and model weights remain strictly on your local computer:

| Asset | Local Location | Description |
|:---|:---|:---|
| **Database** | `backend/data/transient_smart_contract_analyser.db` | SQLite database storing accounts, analysis metadata, jobs, and file references. |
| **Uploaded Files** | `backend/data/storage/<user_id>/` | User-sandboxed local directory holding uploaded `.sol` contract source files. |
| **Model Checkpoint** | `analysis/models/legal_bert_v3.3.0/` | Fine-tuned Legal-BERT multi-label model weights (`model.safetensors`, `config.json`, tokenizer). |
| **Generated Reports** | Streamed dynamically | PDF and DOCX reports are generated on-the-fly via ReportLab and python-docx. |

---

### 8. Verification & Running the Tests

To run the complete automated test suite (85 tests covering API contracts, authentication, ownership isolation, job lifecycles, and storage sandboxing):
```bash
python -m pytest tests/
```

To run the frontend production build verification:
```bash
cd frontend
npm run build
```

---

### 9. Scientific Disclosure & Model Limitations

In accordance with academic and engineering integrity standards:

1. **Dataset Scope & Low-Prevalence Support**:
   - The fine-tuned Legal-BERT multi-label classifier is trained on a frozen canonical dataset of 58 eligible contracts (38 real-source, 20 synthetic in train).
   - On the strictly isolated, held-out test split (7 real-source contracts across independent projects `anvil_protocol`, `aragon_vault`, `crytic_not_so_smart_contracts`, and `virtuals_genesis`), real-world prevalence of certain hazards (**Privacy**, **Liability**, and **Payment / Financial**) is zero.
   - For these zero-support categories, recall and F1 cannot be mathematically evaluated; they are transparently reported as inconclusive rather than substituting fabricated scores.
2. **Model Classification Scores**:
   - On CPU inference with the small sample size, predicted logits fall below the uncalibrated 0.50 threshold on test data. See [docs/LEGAL_BERT_EXPERIMENT_REPORT.md](docs/LEGAL_BERT_EXPERIMENT_REPORT.md) for full empirical loss curves and evaluation tables.
3. **Decision-Support Boundary**:
   - The platform provides operational pre-deployment risk triaging for developers and auditors.
   - Output does not constitute judicial rulings, binding legal opinions, or guarantees of statutory compliance under any jurisdiction. All automated findings should be reviewed by qualified legal counsel.

---

## 📄 License
This project is licensed under the MIT License.

