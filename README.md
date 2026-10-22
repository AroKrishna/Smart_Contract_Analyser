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
* **Node.js** (v18.0 or newer recommended)
* **npm** (v9.0 or newer)
* **Docker & Docker Compose** (optional, for containerized execution)

### 1. Clone the repository
```bash
git clone https://github.com/AroKrishna/XAI-Contract_Analyser.git
cd XAI-Contract_Analyser
```

### 2. Configure Environment Variables
Copy the template configuration:
```bash
cp .env.example .env
```
Key variables configured in `.env` (or in your hosting provider's dashboard):
- `ALLOWED_ORIGINS`: Comma-separated CORS origins (e.g. `http://localhost:5173,http://localhost:80`).
- `MAX_CONCURRENT_ANALYSIS_JOBS`: Concurrency throttle for CPU protection (default: `2`).
- `RATE_LIMIT_PER_MINUTE`: Sliding-window submission limit per client IP (default: `10`).
- `ANALYSIS_TTL_MINUTES`: Ephemeral in-memory analysis retention TTL (default: `30`).
- `MAX_STORED_ANALYSES`: Maximum in-memory FIFO analyses cache (default: `100`).
- `VITE_API_BASE_URL`: (Frontend only) Target API domain if the frontend is hosted separately from the backend (leave blank when using relative `/api` paths with the local proxy or Nginx).

### 3. Legal-BERT Model Checkpoint Setup
The active Phase 1 engine expects the fine-tuned Legal-BERT checkpoint at:
`analysis/models/legal_bert_v3.3.0/model.safetensors` (~438 MB).

> [!NOTE]
> Because ordinary GitHub repositories reject files exceeding 100 MiB and Git LFS is omitted to prevent bandwidth quotas and billing issues, the binary model weight file is excluded from git via `.gitignore`. The model architecture config, tokenizer definitions, and training metrics are tracked in the repository.

To obtain or train the model weights:
- **Option A (Train locally from canonical dataset)**:
  ```bash
  python -m analysis.train_legal_bert
  ```
  This trains the multi-label model on `data/ml_candidates/final_dataset.jsonl` and saves the weights to `analysis/models/legal_bert_v3.3.0/model.safetensors`.
- **Option B (Manual Checkpoint Placement)**:
  Place the pre-trained `model.safetensors` directly into `analysis/models/legal_bert_v3.3.0/`.
- If the checkpoint is missing, the backend will return a transparent `HTTP 503` readiness status at `/ready` explaining that the checkpoint is absent, rather than generating misleading mock predictions.

### 4. Start the FastAPI Backend Service
```bash
# Optional: create and activate a virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install backend dependencies
pip install -r requirements.txt

# Launch API server on port 8000 (single worker required for shared in-memory job store)
uvicorn analysis.api:app --host 127.0.0.1 --port 8000 --reload
```

### 5. Run Backend Tests
Run the test suite covering API contracts, model readiness gating, and dataset validation:
```bash
python -m pytest tests/
```

### 6. Install and Run the Frontend
In a separate terminal:
```bash
cd frontend
npm install
npm run dev
```
Open **`http://localhost:5173/`** in your browser. The Vite development server automatically proxies `/api` and `/ready` requests to `http://127.0.0.1:8000`.

### 7. Run via Docker Compose (Alternative)
To run both backend and frontend in containerized isolation:
```bash
docker compose up --build
```
Access the application at `http://localhost/`.

---

## 🌐 Deployment Architecture

### Frontend Deployment (Vercel / Netlify / Static CDN)
The frontend is a static React Single Page Application (SPA).
* **Vercel**: Set **Root Directory** to `frontend`. The configuration in [`frontend/vercel.json`](frontend/vercel.json) routes all client paths to `index.html`.
* Set the environment variable `VITE_API_BASE_URL` in the Vercel dashboard to your live backend URL (e.g. `https://api.yourdomain.com`).
* **Netlify**: Configured via `frontend/public/_redirects`.

> [!IMPORTANT]
> **Vercel hosts ONLY the frontend SPA.**  
> The Python FastAPI backend relies on in-memory asynchronous job queues and long-running deep learning inference (PyTorch, SHAP, LIME). It is **not** supported on Vercel Serverless Functions.

### Backend Deployment (Render / Railway / Fly.io / VPS)
The backend must run on a persistent, single-container compute instance with at least 2 GB RAM:
* **Render**: Web Service using Docker environment ([Dockerfile](Dockerfile)).
* **Railway**: Web Service using Dockerfile.
* **Fly.io**: Dedicated Machine deployment via `flyctl`.
* **Self-Hosted VPS**: Managed via [docker-compose.yml](docker-compose.yml) with Nginx reverse proxy and SSL.

For complete step-by-step production setup and hosting guides, refer to [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md).

---

## 📄 License
This project is licensed under the MIT License.

