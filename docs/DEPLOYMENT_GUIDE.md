# Smart Contract Analyser - Phase 1 Deployment Guide

> **Explainable AI (XAI) Legal-Risk Auditing Platform for Solidity Smart Contracts**  
> **Architecture Milestone:** Phase 1 (Anonymous Public Prototype, In-Memory Ephemeral Storage)

---

## 1. Architectural Boundary & Design Principles

The Phase 1 release operates strictly within the **anonymous, ephemeral research prototype boundary**:
- **No User Accounts:** Open to all visitors without registration, login, or authentication tokens.
- **No Permanent Database:** No Firebase, PostgreSQL, MongoDB, or disk-backed database is used for user data or contract submissions.
- **Ephemeral In-Memory Retention:**
  - Contracts and analysis reports reside exclusively in backend process RAM (`jobs_store` and `analyses_store`).
  - Strict **30-minute Time-To-Live (TTL)** auto-expiry per analysis.
  - Strict **100-entry Maximum FIFO eviction limit**.
  - **Explicit Client Discard:** Visitors can click "Discard Analysis" at any time to immediately purge the analysis from memory.
  - **Restart Policy:** In-memory analyses do **not** survive backend restarts (communicated via the `X-Persistence-Note: in-memory-only-does-not-survive-restart` response header).

---

## 2. Critical Hosting Requirements

### A. Single Backend Instance Requirement (Non-Negotiable for Phase 1)
Because the job queue and analysis results are held in memory:
1. **Do NOT deploy to multi-replica round-robin clusters without sticky sessions.** If request 1 (`POST /api/v1/analyze`) hits Instance A, but request 2 (`GET /api/v1/jobs/{job_id}`) hits Instance B, the client will receive `HTTP 404 Job not found`.
2. **Do NOT deploy to serverless platforms (e.g., AWS Lambda, Vercel Serverless Functions, Google Cloud Functions).** Serverless functions terminate or spin down between requests, erasing the in-memory background job before the client can poll the result.
3. **Run Uvicorn with a single worker process (`--workers 1`).** Running multiple Uvicorn workers behind a local process manager also splits in-memory dictionaries.
4. **Disable Scale-to-Zero during active sessions.** On platforms like Fly.io or Render Free Tier, ensure the instance does not spin down while users are waiting for the 8–15 second inference pipeline.

### B. Hardware & Resource Sizing
- **Active Model:** `legal_bert_v3.3.0` (frozen PyTorch transformer weights, ~440MB).
- **RAM Sizing:**
  - Base Python + FastAPI + PyTorch idle: ~600 MB.
  - Peak inference with PyTorch CPU forward pass + SHAP (32 background evaluations) + LIME (20 local perturbations): **~1.5 GB to 2.2 GB RAM**.
  - **Recommended Minimum Memory:** **2 GB RAM** (3 GB or 4 GB recommended for production stability).
- **CPU Sizing:** Minimum 1 vCPU; 2 vCPU recommended for ~8–12 second end-to-end response times on CPU.

---

## 3. Public Upload Safety Controls

Because the service accepts anonymous code uploads, the following defense-in-depth protections are enforced on the backend:

| Protection | Implementation | Threshold / Behavior |
| :--- | :--- | :--- |
| **Server-Side File Size** | `_validate_source` in `analysis/api.py` | Maximum **1 MB** (1,048,576 bytes); rejects larger payloads with `HTTP 413`. |
| **Server-Side Type Validation** | `_validate_source` in `analysis/api.py` | Strict text decoding + mandatory Solidity syntax checks (`pragma solidity` or `contract/interface/library`). Rejects non-Solidity with `HTTP 422`. |
| **Sliding-Window Rate Limiting** | `_check_rate_limit` in `analysis/api.py` | **10 requests per minute per client IP**; returns `HTTP 429` with `Retry-After: 60`. |
| **Concurrency Semaphore** | `_analysis_semaphore` in `analysis/api.py` | Maximum **2 concurrent deep-learning jobs** to protect server CPU/RAM from starvation. |
| **Sanitized Safe Logging** | Python `logging` in `analysis/api.py` | Uploaded Solidity source code and full report bodies are **never** logged. Only sanitized metadata (Job ID, source length, execution duration) is recorded. |
| **Opaque Error Masking** | Global exception handler in `analysis/api.py` | Internal server errors return a generic message: `"An internal error occurred during contract analysis"`. Stack traces and server file paths are hidden from visitors. |
| **CORS Origin Restriction** | `CORSMiddleware` in `analysis/api.py` | Configurable via `ALLOWED_ORIGINS` environment variable. |
| **Model Readiness Gate** | `/ready` endpoint in `analysis/api.py` | Returns `HTTP 503` if `legal_bert_v3.3.0` checkpoint is missing or unreadable. Never generates mock reports on model failure. |

---

## 4. Honest Model Disclosures

The application explicitly discloses its research status and performance metrics to all visitors across the UI:
1. **Prominent Alert Banner:** Displays on every analysis:  
   *"Research Prototype Notice: Absence of legal-risk findings does NOT guarantee that a contract is safe, compliant, or legally binding. Smart Contract Analyser is an automated pre-deployment decision-support tool, not a substitute for qualified legal counsel."*
2. **Transparent Test Split Benchmark:** The analysis report presents the exact empirical performance on the held-out test split ($N=7$ real contracts):
   - **Macro F1 Score:** `0.0000` (at default 0.50 decision threshold)
   - **Specificity:** `100.0%`
   - **Empirical Context:** High precision on benign contracts, but small sample size and class imbalance mean low recall on rare hazard types.
3. **Score Labeling:** Risk scores are explicitly labeled as **"Uncalibrated Sigmoid Scores"** to prevent misleading visitors into treating raw model probabilities as calibrated risk likelihoods.

---

## 5. Deployment Options & Step-by-Step Instructions

### Option A: Render (Recommended for Simple PaaS Deployment)

1. **Create a New Web Service:**
   - Connect your GitHub repository: `https://github.com/AroKrishna/XAI-Contract_Analyser`
   - Environment: **Docker** (Render will automatically detect `Dockerfile`).
   - Instance Type: **Standard (2 GB RAM, 1 CPU)** or higher. (Do not use Free Tier due to 512MB RAM limit and sleep-mode disconnects).
2. **Set Environment Variables in Render Dashboard:**
   ```bash
   ALLOWED_ORIGINS=https://your-frontend-app.onrender.com
   MAX_CONCURRENT_ANALYSIS_JOBS=2
   RATE_LIMIT_PER_MINUTE=10
   ANALYSIS_TTL_MINUTES=30
   MAX_STORED_ANALYSES=100
   ```
3. **Deploy the Frontend:**
   - In Render, create a **Static Site** for the frontend.
   - Build Command: `cd frontend && npm install && npm run build`
   - Publish Directory: `frontend/dist`
   - Environment Variable: `VITE_API_BASE_URL=https://your-backend-service.onrender.com`

---

### Option B: Railway

1. **Deploy Backend Service:**
   - Create project from GitHub repository.
   - In Service Settings -> General -> **Dockerfile Path**: `Dockerfile`.
   - In Service Settings -> Resources: Allocate at least **2048 MB RAM**.
   - In Service Settings -> Variables:
     ```bash
     ALLOWED_ORIGINS=https://your-frontend.up.railway.app
     MAX_CONCURRENT_ANALYSIS_JOBS=2
     ```
2. **Deploy Frontend Service:**
   - Add a second service from the same repo.
   - Set **Dockerfile Path** to `Dockerfile.frontend`.
   - Set Build Variable: `VITE_API_BASE_URL=https://your-backend.up.railway.app`

---

### Option C: Fly.io (Single Dedicated Machine)

1. Install Fly CLI: `flyctl`
2. Create `fly.toml` for the backend:
   ```toml
   app = "sca-backend"
   primary_region = "iad"

   [build]
     dockerfile = "Dockerfile"

   [http_service]
     internal_port = 8000
     force_https = true
     auto_stop_machines = false   # CRITICAL: Prevent sleeping during job polling
     auto_start_machines = true
     min_machines_running = 1

   [[vm]]
     cpu_kind = "shared"
     cpus = 2
     memory_mb = 2048
   ```
3. Deploy:
   ```bash
   fly launch --no-deploy
   fly secrets set ALLOWED_ORIGINS="https://sca-frontend.fly.dev"
   fly deploy
   ```

---

### Option D: Self-Hosted VPS with Docker Compose (DigitalOcean / Hetzner / AWS EC2)

1. **Provision a VM:**
   - Ubuntu 22.04 LTS (Minimum 2GB RAM, 1-2 vCPU; e.g., DigitalOcean Regular Droplet $12/mo).
2. **Install Docker & Compose:**
   ```bash
   sudo apt-get update
   sudo apt-get install -y docker.io docker-compose-v2
   ```
3. **Clone Repository & Configure:**
   ```bash
   git clone https://github.com/AroKrishna/XAI-Contract_Analyser.git
   cd XAI-Contract_Analyser
   cp .env.example .env
   # Edit .env to set your domain or IP in ALLOWED_ORIGINS
   ```
4. **Launch Containers:**
   ```bash
   docker compose up -d --build
   ```
5. **Configure SSL / HTTPS (Let's Encrypt / Certbot):**
   - Point your DNS A-Record to the VPS IP.
   - Install Nginx on the host as a TLS terminator or run Certbot:
     ```bash
     sudo apt-get install -y certbot python3-certbot-nginx
     sudo certbot --nginx -d yourdomain.com
     ```

---

## 6. Pre-Flight Verification Checklist

Before publishing the URL to users:

- [ ] **Verify Readiness Endpoint:**
  ```bash
  curl -i https://<backend-domain>/ready
  ```
  Expected output:
  ```json
  {"status":"ready","checkpointName":"legal_bert_v3.3.0","modelType":"Legal-BERT","explainabilityEngine":["SHAP","LIME"],"timestamp":"..."}
  ```
- [ ] **Verify Model Checkpoint Enforcement:**
  - Verify that diagnostics confirm `checkpointName: legal_bert_v3.3.0`.
- [ ] **Verify File Upload Flow:**
  1. Open the deployed website in a browser.
  2. Navigate to "New Analysis".
  3. Upload a sample `.sol` contract or paste contract source code.
  4. Verify the polling progress bar runs smoothly through Tokenization -> Legal-BERT -> SHAP/LIME.
  5. Verify the Analysis Report renders risk scores, category breakdowns, line references, SHAP token attribution bar chart, and LIME explanations.
- [ ] **Verify Discard & Expiry:**
  - Click "Discard Analysis" and verify the report is purged and redirects to the upload form.
- [ ] **Verify Rejection of Oversized / Invalid Files:**
  - Upload a `.txt` file or file > 1MB; verify a clear error message is shown without exposing Python stack traces.
- [ ] **Confirm Persistence Notice:**
  - Verify that the HTTP response headers include `X-Persistence-Note: in-memory-only-does-not-survive-restart`.

---

## 7. Current Deployment Status

- **Codebase Readiness:** Complete. All Phase 1 application code, model checkpoint enforcement, genuine SHAP/LIME explanations, safety controls, and Docker container definitions are implemented and tested.
- **Local Verification:** 35/35 backend pytest tests pass; frontend production build compiles cleanly without errors.
- **Live Online Hosting:** **Awaiting cloud account provisioning.** No active cloud hosting credentials (e.g., Render/Railway/Fly/AWS API keys) or billing decisions are stored in this repository. To deploy live online, select one of the hosting targets above (Option A, B, C, or D) and execute the corresponding steps.
