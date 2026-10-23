# Smart Contract Analyser — Local Operation, Security & Release Checklist

**Platform Target**: Smart Contract Legal AI SaaS Platform  
**Cycle**: Parts 1 through 7 Final Release Readiness  
**Release Date**: October 2026  
**License**: MIT  

---

## 1. Quick Local Start (Zero Paid Services Required)

The platform is designed to operate 100% locally on standard developer hardware without requiring paid cloud infrastructure, external APIs, or cloud credentials.

### 1.1 Prerequisites
- **Python**: 3.10+ (Tested on Python 3.14.3)
- **Node.js**: 18+ (Tested on Node 20 / 22)
- **Git**: Installed
- **RAM**: Minimum 4 GB recommended (for CPU PyTorch inference + SHAP/LIME computation)

### 1.2 Step-by-Step Setup

#### Step 1: Clone Repository & Setup Environment File
```bash
git clone https://github.com/AroKrishna/Smart_Contract_Analyser.git
cd Smart_Contract_Analyser

# Copy environment configuration
# Windows (PowerShell):
Copy-Item .env.example .env
# Linux / macOS (Bash):
cp .env.example .env
```

#### Step 2: Acquire Legal-BERT Model Checkpoint
The fine-tuned model checkpoint must be placed at `analysis/models/legal_bert_v3.3.0/model.safetensors` (~438 MB).

```bash
# Windows (PowerShell):
New-Item -ItemType Directory -Force -Path "analysis\models\legal_bert_v3.3.0"
curl.exe -L -o "analysis\models\legal_bert_v3.3.0\model.safetensors" "https://github.com/AroKrishna/Smart_Contract_Analyser/releases/download/v3.3.0/model.safetensors"
(Get-FileHash -Algorithm SHA256 "analysis\models\legal_bert_v3.3.0\model.safetensors").Hash

# Linux / macOS (Bash):
mkdir -p analysis/models/legal_bert_v3.3.0
curl -L -o analysis/models/legal_bert_v3.3.0/model.safetensors "https://github.com/AroKrishna/Smart_Contract_Analyser/releases/download/v3.3.0/model.safetensors"
sha256sum analysis/models/legal_bert_v3.3.0/model.safetensors
```
*Expected Checksum*: `4c5d1c1caf6f42e38173d6fc1b69a924cf2ad93e0188e0f5bb057ac0b73d972e`

*(Alternatively, run `python analysis/train_legal_bert.py --check-readiness` to verify readiness).*

#### Step 3: Install Backend Dependencies & Start Server
```bash
# Windows (PowerShell):
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload

# Linux / macOS (Bash):
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

#### Step 4: Install Frontend Dependencies & Start UI
In a second terminal:
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:5173/](http://localhost:5173/) in your web browser.

---

## 2. Release & Security Checklist

| Check | Requirement | Verification Method | Status |
| :--- | :--- | :--- | :--- |
| **Model Gating** | Returns 503 if weights missing; never serves mock/rule results | `GET /ready` returns 200 when weights present; 503 if absent | ✅ PASS |
| **Authentication** | Password hashing with bcrypt / Argon2id; HttpOnly cookie sessions | `tests/test_auth.py` | ✅ PASS |
| **CSRF / CORS** | State-changing requests validate Origin; CORS rejects wildcards with credentials | CSRF middleware in `backend/main.py` | ✅ PASS |
| **Token Invalidation** | Logout immediately revokes access token; subsequent calls rejected | `tests/test_end_to_end_workflow.py` | ✅ PASS |
| **Tenant Isolation** | Users can only view/cancel/delete their own analyses, jobs, and files | `tests/test_ownership.py` | ✅ PASS |
| **Path Traversal** | File uploads sanitized; strict user directory sandbox prevents `../` attacks | `tests/test_storage_lifecycle.py` | ✅ PASS |
| **Truthful Cancellation** | Canceled in-flight inference discards output; result is never retrievable | `tests/test_jobs_assistant_reports.py` | ✅ PASS |
| **Honest Reboot** | Server reboot reconciles in-flight jobs to `interrupted` status with retry advice | `tests/test_ownership.py` | ✅ PASS |
| **AI Assistant Grounding** | Scoped strictly to contract findings; fallback clearly labeled, never faked | `tests/test_jobs_assistant_reports.py` | ✅ PASS |
| **Report Exports** | Authenticated PDF and DOCX reports include full XAI & compliance matrix | `tests/test_end_to_end_workflow.py` | ✅ PASS |
| **Secret Protection** | `.gitignore` excludes `.env`, `*.db`, weights, `*.pdf`, `*.docx`, and uploads | Verified via Git status and `.gitignore` audit | ✅ PASS |
| **Build Integrity** | Frontend production build succeeds without warnings or broken imports | `cd frontend && npm run build` | ✅ PASS |
| **Full Test Suite** | 100% backend test suite pass rate | `python -m pytest tests/` (84 tests) | ✅ PASS |

---

## 3. Scientific Honesty & Model Limitations

1. **Experimental Classification**:
   - The fine-tuned Legal-BERT multi-label model is trained and benchmarked on a canonical dataset of 58 eligible contracts (38 real, 20 synthetic in train only).
   - Because the held-out test split is 100% real-source contracts under strict project isolation, categories with low real-world prevalence (**Privacy**, **Liability**, and **Payment / Financial**) have zero ground-truth positive support in the test split.
   - For these categories, recall and F1 are mathematically non-evaluable; they are honestly reported as `inconclusive_zero_positive_support` rather than fabricating scores.
2. **Decision-Support Scope**:
   - The model output is explicitly marked as **Experimental Decision Support** in the UI and documentation.
   - It is designed to triage risk and assist auditors, not replace formal attorney review.
