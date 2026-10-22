# Smart_Contract_Analyser — Current State & Gaps Audit

**Project**: Smart_Contract_Analyser  
**Document Status**: Official Architecture & Implementation Audit  
**Authoritative Specification**: `docs/reference/Smart_Contract_Legal_AI_SaaS_Platform_Specification.docx`  
**Audit Date**: October 21, 2026  
**Evaluation Runtime**: Python 3.14.3 (FastAPI 0.115+, Pytest 9.1.1) | Node.js / Vite 8.3.2 (React 19.2.8)

---

## Executive Summary

This document establishes the verified truth of the **Smart_Contract_Analyser** codebase (previously referenced in early working drafts as *X-LegalContract*). It directly compares the full target platform specification against the active source code, records empirical test results, classifies current capabilities, and delineates what is implemented, mocked, deferred, and remaining as implementation gaps.

In alignment with current project decisions:
- The initial online release is **public and requires no login**.
- Users can **submit Solidity source code** (.sol) and **inspect live analysis results**.
- Results are **temporarily held in in-memory and session cache** for this release.
- Accounts, authentication, notifications, admin panel, conversational AI legal assistant, and enterprise modules are **deferred to later phases**.
- **Legal-BERT remains a required core target** for the research and platform roadmap; the current deterministic rule engine serves as an operational baseline and heuristic pre-flight filter, not a permanent replacement for deep learning models.

---

## 1. What the Full Specification Requires

The product specification (`docs/reference/Smart_Contract_Legal_AI_SaaS_Platform_Specification.docx`) defines an enterprise-grade AI SaaS platform organized across 13 user flow phases and 3 progressive milestones:

### 1.1 Architectural Phases in Specification
1. **Phase 1: Public Website**: Landing page (Hero, features breakdown, workflow, pricing preview, about, contact) and Login / Register (Email/password, Google/GitHub OAuth, password recovery, email verification).
2. **Phase 2: User Dashboard**: Personalized welcome, aggregate metrics (total contracts analyzed, average risk score across contracts), recent contract analysis feed, primary "New Analysis" CTA, notifications banner.
3. **Phase 3: New Analysis Workspace**: Upload Solidity `.sol` file, direct paste of raw Solidity, future Legal Contract PDF upload, project metadata (name, description), and submission trigger.
4. **Phase 4: AI Processing Engine**: Asynchronous backend pipeline:
   - Solidity preprocessing & normalization.
   - Code & language tokenization (AST + sub-word).
   - **Legal-BERT deep learning model inference** for clause semantic classification.
   - **SHAP (SHapley Additive exPlanations)** game-theoretic marginal contribution calculations.
   - **LIME (Local Interpretable Model-agnostic Explanations)** local surrogate model interpretability.
   - Risk categorization across 5 domains (Privacy, Termination, Legal Compliance, Liability, Payment/Financial).
   - Database persistence of audit records.
   - Real-time interactive loading screen with progress percentage and stage status.
5. **Phase 5: Analysis Result Dashboard**:
   - Overall composite risk score (0–100) and severity badge (Low, Medium, High, Critical).
   - 5 Risk Categories Breakdown with severity, model confidence score, and detailed risk descriptions.
   - Interactive Contract Viewer with color-coded clause highlighting (Red = High Risk, Yellow = Medium Risk, Green = Safe / Standard).
   - Explainable AI (XAI) Panel with clause inspection, SHAP feature scores, LIME interpretability breakdown, and confidence metrics.
   - AI Recommendation Engine with side-by-side clause comparison (Current Risky Clause vs. Suggested Safer Legal Clause).
   - Compliance Score Matrix covering Consumer Law, Privacy Standards (GDPR/CCPA), AML Regulatory, and Contract Fairness.
6. **Phase 6: Interactive AI Legal Assistant**: Context-aware conversational chatbot strictly scoped to the analyzed contract (plain-language explanation, clause rewriting, compliance checking).
7. **Phase 7: Exportable Audit Reports**: Professional executive reports in PDF and editable DOCX formats.
8. **Phase 8: Analysis History & Persistence**: Persistent database repository of past audits with card details (name, date, risk score tag, status) and re-open capability.
9. **Phase 9: Global Search & Filtering**: Multi-criteria exploration across historical audits (keywords, risk level, date range, company/organization, contract type).
10. **Phase 10: Notifications System**: Alerts for analysis completion, report generation, and new vulnerability patterns.
11. **Phase 11: User Profile Management**: User profile attributes (name, email, organization, password management, profile avatar).
12. **Phase 12: SaaS Platform Settings**: Theme switching (dark/light), notification preferences, localization, and developer API keys.
13. **Phase 13: Admin Control Panel**: User management, usage analytics, Legal-BERT model deployment and weight updating, resource monitoring, audit logs.
14. **Enterprise Modules (Roadmap)**: Multi-user team workspaces, Role-Based Access Control (RBAC), GitHub CI/CD automated PR auditing, external developer REST API, multi-chain support (Vyper, Move, Rust), and multi-jurisdictional compliance frameworks.

---

## 2. What Is Implemented Now (Verified from Source Files)

The following components are fully implemented and verified in the active codebase:

### 2.1 Backend Analysis Engine & API
- **FastAPI Service (`analysis/api.py`)**:
  - Implements operational REST endpoints:
    - `GET /health` and `GET /api/v1/health`: Returns service health, version (`0.1.0-baseline`), engine identifier (`rule_ast_hybrid_v1`), and legal disclaimer.
    - `POST /api/v1/analyze`: Accepts `{ sourceCode, contractName }` (or snake_case `{ source_code, contract_name }`). Executes parser and rule engine synchronously, stores result in LRU cache, and returns full audit schema.
    - `GET /api/v1/analyze/{analysis_id}`: Retrieves cached audit payload by ID.
  - **Payload Validation & HTTP Status Codes**:
    - `400 Bad Request`: When source code is empty/whitespace (`EMPTY_SOURCE`) or contains null bytes / unrecoverable syntax (`MALFORMED_SOURCE`).
    - `413 Request Entity Too Large`: When submitted source exceeds `MAX_SOURCE_LENGTH = 2 * 1024 * 1024` bytes (2MB) (`PAYLOAD_TOO_LARGE`).
    - `422 Unprocessable Entity`: When submitted text contains no recognized Solidity contracts, interfaces, libraries, or pragmas (`UNSUPPORTED_SOURCE`).
    - `200 OK`: Successful analysis response.
    - `404 Not Found`: When querying an unknown or evicted analysis ID (`ANALYSIS_NOT_FOUND`).
  - **In-Memory Cache & Eviction**:
    - Backed by Python `OrderedDict` (`analyses_store`) capped at `MAX_STORE_ENTRIES = 100`.
    - Implements FIFO/LRU eviction: `analyses_store.popitem(last=False)` once capacity exceeds 100 entries.
  - **Response Headers**:
    - Middleware injects `X-Analysis-Disclaimer: Heuristic operational indicators only; not authoritative legal advice.` and `X-Engine-Type: rule_ast_hybrid_v1`.
- **Pure-Python Regex & Text Token Parser (`analysis/parser.py`)**:
  - `SolidityParser` extracts contract names, kinds (`contract`, `interface`, `library`), inheritance lists, start/end line numbers via custom brace matching, preceding NatSpec docstrings, function signatures, modifiers, and state variable declarations.
  - Operates with zero native binary dependencies (runs without `solc` binary or Slither installed).
- **Deterministic Heuristic Rule Engine (`analysis/rules.py` & `analysis/engine.py`)**:
  - Implements 5 operational pattern rules covering the 5 regulatory categories:
    1. `RULE-TERM-01` (`Termination`, Severity: `Critical`): Flags `selfdestruct` / `suicide` opcodes that permit unilateral contract destruction and fund draining.
    2. `RULE-FIN-01` (`Payment / Financial`, Severity: `High`): Flags unconstrained fee/tax variable modifications that lack ceiling validation (`require(newFee <= MAX)`), excluding constructor initialization.
    3. `RULE-PRIV-01` (`Privacy`, Severity: `Critical`): Flags non-constant public `string` / `bytes` state variables named with PII terms (`email`, `phone`, `ssn`, `physicaladdress`, etc.) conflicting with GDPR Right to Erasure.
    4. `RULE-LIAB-01` (`Liability`, Severity: `Medium`): Flags blanket exculpatory disclaimers (`as is`, `without warranty`, `no liability`) embedded in NatSpec documentation.
    5. `RULE-GOV-01` (`Legal Compliance`, Severity: `Medium`): Flags administrative privilege concentration (>= 3 privileged functions) without a timelock controller.
  - Computes composite risk score (weighted maximum category score dampener: `70% max + 30% avg`), risk level (`Low`, `Medium`, `High`, `Critical`), line-accurate snippets, remediation recommendations with before/after code, and compliance matrix indicators.

### 2.2 Verified Frontend Architecture (`frontend/`)
- **Technology Stack**:
  - `react: ^19.2.8` and `react-dom: ^19.2.8` (React 19).
  - `vite: ^8.3.0` (Vite 8) and `@vitejs/plugin-react: ^6.1.1`.
  - `tailwindcss: ^4.3.3` with `@tailwindcss/vite: ^4.3.3` (Tailwind CSS v4).
  - `react-router-dom: ^7.18.4` (React Router v7).
  - `lucide-react: ^1.52.0` and `recharts: ^3.10.1`.
- **Live Connected Screens**:
  - `NewAnalysis.jsx` (`/analysis/new`): Features live API health check polling (`api.checkHealth()`), Solidity file upload (.sol <= 2MB) or code pasting, client-side stage stepper, and live dispatch to `POST /api/v1/analyze`. Upon completion, seamlessly passes live audit payload to `AnalysisResult.jsx` via router navigation state and session cache.
  - `AnalysisResult.jsx` (`/analysis/:id`): Resolves audit data via 4-tier fallback: (1) router navigation state, (2) live backend/cache query via `api.getAnalysis(id)`, (3) local demo mock data, (4) not-found error state. Dynamically renders overall risk score gauge, 5 category cards, syntax-highlighted code viewer with line numbers and hazard badges, XAI tabs, side-by-side remediation recommendations, and statutory compliance matrix.
- **API Client (`frontend/src/services/api.js`)**:
  - Implements dual-target connection: attempts relative `/api/v1/...` (Vite dev proxy) with automatic fallback to `http://127.0.0.1:8000`.
  - Maintains in-memory `Map` and browser `sessionStorage` (`audit_${analysisId}`) caching to prevent redundant backend round-trips during navigation.

### 2.3 Benchmark & Evaluation Harness (`analysis/data/` & `analysis/evaluate.py`)
- Standardized manifest schema (`analysis/benchmark_schema.py`) enforcing split isolation and provenance tracking.
- Curated dev benchmark suite of 5 contracts (`analysis/data/contracts/BM001`–`BM005`):
  - `BM001_VulnerableEscrow.sol` (Positive hazard: `selfdestruct`, unconstrained fee).
  - `BM002_SafeTimelockedEscrow.sol` (Negative control: bounded fee, no killswitch).
  - `BM003_UserIdentityRegistry.sol` (Positive hazard: plaintext PII on-chain).
  - `BM004_HighRiskStaking.sol` (Positive hazard: unconstrained tax, blanket disclaimer).
  - `BM005_StandardGovernanceToken.sol` (Clean negative control: standard ERC-20).
- Evaluation script (`analysis/evaluate.py`) computing TP, FP, FN, TN, Support, Precision, Recall, and F1.

---

## 3. What Is Only Mocked, Simulated, or Planned

A rigorous audit of the source files confirms that several features referenced in UI elements or documentation are currently mocked or simulated:

### 3.1 Explainable AI: Rule-Derived Illustrative Attributions vs. Real SHAP/LIME
- **Verification from `analysis/engine.py` (lines 171–197)**:
  - In `AnalysisEngine.analyze_source()`, `shapValues` and `limeExplanations` are computed directly from the rule engine's findings:
    ```python
    attribution_val = round(sev_weights.get(f["severity"], 10) / 100.0, 2)
    # Tokens are extracted by splitting the code snippet on whitespace
    ```
  - **Verdict**: There is **no actual SHAP algorithm** (e.g., TreeSHAP, KernelSHAP, or DeepSHAP computing game-theoretic Shapley values over feature permutations) and **no actual LIME algorithm** (e.g., generating perturbed code samples and training local linear surrogate models) running in the current codebase.
  - **Accurate Description**: These values are **rule-derived illustrative attributions** engineered to populate the UI charts with line-relevant data until true model explainability pipelines are trained and deployed.

### 3.2 Model Confidence: Fixed String vs. Empirical Probability
- **Verification from `analysis/engine.py` (line 283)**:
  - The API output returns:
    ```python
    "confidence": "94.0% (Heuristic Rule Baseline)"
    ```
  - **Verdict**: This is a **fixed, hardcoded static string**. It is not an empirical posterior probability, a softmax score, or a calibrated uncertainty metric from a machine learning classifier.

### 3.3 Parser: Lightweight Text/Regex Parsing vs. Real Compiler AST
- **Verification from `analysis/parser.py`**:
  - The parser uses Python regular expressions (`re.compile`) and character-by-character brace counting.
  - **Verdict**: It does not invoke the official Solidity compiler (`solc`), does not generate a compiler-verified Abstract Syntax Tree (such as `solc --ast-compact-json` or `py-solc-x`), and does not construct a full semantic graph with type checking or inter-procedural dataflow analysis.

### 3.4 Processing Mode: Synchronous Execution vs. Asynchronous Pipeline
- **Verification from `analysis/api.py` and `NewAnalysis.jsx`**:
  - `POST /api/v1/analyze` executes the entire parse and rule suite **synchronously** within the HTTP request thread and returns the final JSON immediately.
  - The 8-stage progress tracker displayed in `NewAnalysis.jsx` is driven by a client-side `setInterval` timer (stepping every 200ms) to provide a smooth UX transition while awaiting the synchronous HTTP response.
  - **Verdict**: There is no asynchronous worker queue (such as Celery, RQ, Redis, or Kafka), no background task supervisor, and no WebSocket streaming for stage status.

### 3.5 Frontend Screens Using Static Mock Data
While `NewAnalysis.jsx` and `AnalysisResult.jsx` are wired to the live backend engine, all other frontend views operate exclusively on static mock data from `frontend/src/data/mockData.js`:
- **`Dashboard.jsx` (`/dashboard`)**: Displays hardcoded KPI statistics (`mockDashboardStats`) and a static feed of 5 pre-canned contracts (`mockContracts`).
- **`History.jsx` (`/history`)**: Filters static `mockContracts` in local React state. Does not query the backend cache or an audit database.
- **`Reports.jsx` (`/reports`)**: Renders static report cards (`mockReports`). Clicking "Download PDF" or "Download DOCX" triggers a simulated `setTimeout` followed by a browser `alert()`; no actual PDF or DOCX file generation occurs.
- **`Profile.jsx` (`/profile`)**: Displays hardcoded auditor information ("Jane Doe") with mock `setTimeout` transitions for saves and password updates.
- **`Settings.jsx` (`/settings`)**: Classification threshold sliders and notification toggles are stored only in component React state and do not persist to backend configuration.
- **`Login.jsx` (`/login`) & `Register.jsx` (`/register`)**: Form submission performs a mock `setTimeout(..., 600)` delay before navigating to `/dashboard`; no real user authentication, session cookies, or JWT verification exists.

---

## 4. What Is Deferred to Later Releases

In accordance with the current release decisions:

1. **Authentication & User Management**:
   - Email/password authentication, OAuth providers (Google, GitHub), password recovery, and email verification.
   - User profiles, role assignments, and session tokens.
2. **Persistent Database Infrastructure**:
   - PostgreSQL / SQLite database persistence for contracts, users, audit history, and report files.
   - Permanent storage of historical analyses (currently held only in 100-slot LRU in-memory cache and client session storage).
3. **Conversational AI Legal Assistant (Phase 6)**:
   - Scoped LLM chatbot for querying contract terms, requesting clause rewrites, and GDPR compliance dialogues.
4. **Notifications System (Phase 10)**:
   - Automated workflow notifications, webhooks, and email dispatch upon audit completion.
5. **Platform Administration & Telemetry (Phase 13)**:
   - Admin control panel, platform usage metrics, worker telemetry, and dynamic model deployment interfaces.
6. **Enterprise Roadmap Features**:
   - Multi-user team workspaces, Role-Based Access Control (RBAC), GitHub CI/CD action triggers, multi-chain languages (Vyper, Move, Rust), and multi-jurisdictional legal mappings.

---

## 5. What Remains as an Implementation Gap

The following technical items represent active gaps between the current codebase and the full platform target:

| Priority | Gap Area | Current State | Required Target State |
|:---:|---|---|---|
| **P1** | **Legal-BERT Deep Learning Pipeline** | None. No model weights, no Hugging Face transformers, no PyTorch inference code. The backend is 100% deterministic rule-based. | Train or fine-tune Legal-BERT (e.g., `nlpaueb/legal-bert-base-uncased`) on paired contract clauses/NatSpec summaries to classify semantic legal risks alongside the rule engine. |
| **P2** | **Genuine Explainable AI (SHAP & LIME)** | Rule-derived illustrative attributions computed from rule severity weights and whitespace token splits. | Implement genuine model explainers: KernelSHAP / TreeSHAP for global feature attributions and LIME text/code surrogates with mathematically valid perturbation sampling. |
| **P3** | **Empirical Confidence Calibration** | Fixed hardcoded string (`"94.0% (Heuristic Rule Baseline)"`). | Calibrate empirical model confidence scores based on validation set probabilities (e.g., Platt scaling or temperature scaling). |
| **P4** | **Benchmark Scale & Held-Out Test Split** | 5 toy synthetic contracts (`BM001`–`BM005`) classified as a `dev` regression suite. Zero positive support for `RULE-GOV-01`. | Execute [Benchmark Expansion Plan](file:///c:/ARO/Projects/Smart_Contract_Analyser/docs/BENCHMARK_EXPANSION_PLAN.md): Curate 35 open-source mainnet contracts across 7 domains with verified labels and a strict held-out test split. |
| **P5** | **AST & Compilation Graph Depth** | Pure Python regex and brace matching (`SolidityParser`). Single-file only; misses inter-procedural calls and upgradeable proxy patterns. | Integrate a formal AST representation (e.g., `solc-ast` or Tree-sitter Solidity) and support multi-file compilation / proxy resolution (ERC-1967). |
| **P6** | **Genuine Document Export (PDF / DOCX)** | Simulated in `Reports.jsx` via `setTimeout` and browser `alert()`. | Implement automated server-side or client-side report generation (e.g., using `reportlab`, `python-docx`, or `@react-pdf/renderer`) outputting executive audit reports. |
| **P7** | **Asynchronous Job Execution & Scaling** | Synchronous execution in HTTP handler thread; in-memory cache capped at 100 items. | Introduce background task workers (Celery/Redis or FastAPI background tasks) with job IDs, status polling, and persistent storage. |
| **P8** | **Frontend Screens Persistence Integration** | `Dashboard`, `History`, and `Reports` rely exclusively on static `mockData.js`. | Wire `Dashboard` metrics and `History` tables to backend audit repository endpoints. |

---

## 6. Empirical Verification & Test Evidence

All claims in this document have been empirically verified by executing the project test suites directly on the host system:

### 6.1 Backend API Tests (`tests/test_api.py`)
- **Execution Command**: `python -m pytest tests/`
- **Environment**: Python 3.14.3, Pytest 9.1.1, Starlette / FastAPI TestClient
- **Result**: **8 passed**, 3 deprecation warnings in **2.92s**
- **Verified Test Cases**:
  1. `test_health_endpoints`: Verified both `/health` and `/api/v1/health` return status 200, engine metadata, and custom disclaimer headers.
  2. `test_analyze_valid_contract`: Verified `POST /api/v1/analyze` processes valid Solidity source, flags `RULE-TERM-01` and `RULE-FIN-01`, caches result, and supports retrieval via `GET /api/v1/analyze/{id}`.
  3. `test_analyze_snake_case_fields`: Verified snake_case JSON field compatibility.
  4. `test_analyze_empty_source`: Verified empty/whitespace strings return `400 Bad Request` with `EMPTY_SOURCE`.
  5. `test_analyze_unsupported_non_solidity_source`: Verified non-Solidity inputs return `422 Unprocessable Entity` with `UNSUPPORTED_SOURCE`.
  6. `test_analyze_payload_too_large`: Verified source code > 2MB returns `413 Request Entity Too Large` with `PAYLOAD_TOO_LARGE`.
  7. `test_analyze_null_byte_malformed`: Verified null byte inputs return `400 Bad Request` with `MALFORMED_SOURCE`.
  8. `test_get_nonexistent_analysis`: Verified non-existent audit ID returns `404 Not Found` with `ANALYSIS_NOT_FOUND`.

### 6.2 Benchmark Evaluation Suite (`analysis/evaluate.py`)
- **Execution Command**: `python -m analysis.evaluate dev`
- **Result**: Evaluated across 5 development contracts (`BM001`–`BM005`):
  - `RULE-TERM-01`: TP=1, FP=0, FN=0, TN=4, Support=1 | Precision=1.000, Recall=1.000, F1=1.000 (EVALUATED)
  - `RULE-FIN-01`: TP=2, FP=0, FN=0, TN=3, Support=2 | Precision=1.000, Recall=1.000, F1=1.000 (EVALUATED)
  - `RULE-PRIV-01`: TP=1, FP=0, FN=0, TN=4, Support=1 | Precision=1.000, Recall=1.000, F1=1.000 (EVALUATED)
  - `RULE-LIAB-01`: TP=1, FP=0, FN=0, TN=4, Support=1 | Precision=1.000, Recall=1.000, F1=1.000 (EVALUATED)
  - `RULE-GOV-01`: TP=0, FP=0, FN=0, TN=5, Support=0 | Precision=null, Recall=null, F1=null (`ZERO_POSITIVE_SUPPORT_UNDEFINED`)
- **Category Summary**:
  - `Termination`: Precision=1.000, Recall=1.000, F1=1.000
  - `Payment / Financial`: Precision=1.000, Recall=1.000, F1=1.000
  - `Privacy`: Precision=1.000, Recall=1.000, F1=1.000
  - `Liability`: Precision=1.000, Recall=1.000, F1=1.000
  - `Legal Compliance`: Precision=null, Recall=null, F1=null (Undefined due to zero positive ground truth in dev suite)

### 6.3 Frontend Production Build
- **Execution Command**: `npm run build` (within `frontend/`)
- **Environment**: Node.js, Vite 8.3.2, `@vitejs/plugin-react 6.1.1`
- **Result**: **Exit code 0**. 1941 modules transformed; production bundle compiled cleanly in **3.44s**:
  - `dist/index.html` (0.76 kB │ gzip: 0.43 kB)
  - `dist/assets/index-D1tMpm4V.css` (55.22 kB │ gzip: 9.27 kB)
  - `dist/assets/index-C7HJDUSg.js` (406.69 kB │ gzip: 114.78 kB)

---

## 7. Responsible Auditing & Legal Status Boundary

To maintain professional and academic integrity:
- **Heuristic Operational Indicators vs. Legal Conclusions**: The current platform flags **operational capabilities, governance asymmetries, and syntax patterns** (such as unconstrained setters, killswitches, or plaintext PII state variables). These findings are technical decision-support indicators. They do **not** constitute legal advice, judicial rulings, or binding determinations of statutory compliance or contractual enforceability.
- **No Guarantee of Statutory Compliance**: A contract that produces a 0 risk score under the current baseline rules is **not** certified as legally compliant, secure, or free from regulatory liability under the laws of any jurisdiction.
- **Disclaimer Banner**: All API responses and UI views carry explicit disclaimers instructing users that automated findings must be reviewed by qualified legal counsel.
