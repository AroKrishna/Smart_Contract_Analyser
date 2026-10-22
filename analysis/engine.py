"""
analysis/engine.py - Core Legal-BERT Analysis Engine for Smart Contract Legal-Risk Assessment

Authoritative implementation conforming strictly to:
- docs/reference/Smart_Contract_Legal_AI_SaaS_Platform_Specification.docx
- docs/DATASET_SPECIFICATION.md
- docs/LEGAL_BERT_EXPERIMENT_REPORT.md

Key Architecture:
1. Active Analysis Path uses ONLY the Legal-BERT multi-label transformer model.
2. Rule engine is completely isolated for legacy benchmark testing only; NEVER used as fallback or substitute.
3. If no trained model artifact exists, returns transparent model_unavailable status with empirical data readiness diagnostics.
4. Input representation extracted from submission-time observable context (dual-stream schema) with strict anti-leakage verification.
5. Genuine PyTorch word-embedding gradient saliency (Input x Gradient) provides interpretable token attributions.
6. Line numbers and snippets map accurately to the uploaded Solidity source code using structural parsing.
7. Disclosures explicitly report small-data evaluation limitations, zero-support test categories, and uncalibrated thresholds.
8. Database persistence is optional (ephemeral in-memory handling for Phase 1).
"""

import os
import re
import json
import uuid
import datetime
from typing import Dict, Any, List, Optional, Tuple

import numpy as np

from analysis.parser import SolidityParser

CATEGORIES = [
    "Privacy",
    "Termination",
    "Legal Compliance",
    "Liability",
    "Payment / Financial",
]

CATEGORY_SEVERITIES = {
    "Privacy": "Critical",
    "Termination": "Critical",
    "Legal Compliance": "High",
    "Liability": "High",
    "Payment / Financial": "High",
}

CATEGORY_DESCRIPTIONS = {
    "Privacy": "Evaluation of unencrypted personal data (PII) on-chain and statutory privacy compliance (GDPR/CCPA).",
    "Termination": "Evaluation of unilateral killswitches, irreversible contract destruction, or arbitrary state termination.",
    "Legal Compliance": "Evaluation of administrative centralization, missing timelock governance, and regulatory compliance safeguards.",
    "Liability": "Evaluation of asymmetric exculpatory disclaimers, unilateral indemnification, and liability exclusions.",
    "Payment / Financial": "Evaluation of unconstrained fee/tax modification, locked balances, or withdrawal confiscation.",
}

# Calibration and test support status documented in LEGAL_BERT_EXPERIMENT_REPORT.md
CATEGORY_SUPPORT_STATUS = {
    "Privacy": "inconclusive_zero_positive_support",
    "Termination": "sufficient_support",
    "Legal Compliance": "sufficient_support",
    "Liability": "inconclusive_zero_positive_support",
    "Payment / Financial": "inconclusive_zero_positive_support",
}


def resolve_default_model_dir() -> Tuple[str, str]:
    """
    Resolves the Phase 1 Legal-BERT model checkpoint directory.
    Strictly enforces legal_bert_v3.3.0 as the explicit Phase 1 model.
    Silent fallback to legacy models is strictly removed.
    A fallback to legal_bert_model is permitted ONLY if explicitly configured via
    the ALLOW_LEGACY_MODEL_FALLBACK environment variable or setting, and the exact
    checkpoint used is reported.
    """
    base = os.path.dirname(os.path.abspath(__file__))
    v3_path = os.path.join(base, "models", "legal_bert_v3.3.0")

    # Check if v3.3.0 checkpoint exists with model weights
    has_v3_weights = os.path.exists(v3_path) and (
        os.path.exists(os.path.join(v3_path, "model.safetensors")) or
        os.path.exists(os.path.join(v3_path, "pytorch_model.bin"))
    )
    if has_v3_weights:
        return v3_path, "legal_bert_v3.3.0"

    # Explicit legacy fallback check (never silent)
    allow_fallback = os.environ.get("ALLOW_LEGACY_MODEL_FALLBACK", "0").lower() in ("1", "true", "yes")
    legacy_path = os.path.join(base, "models", "legal_bert_model")
    has_legacy_weights = os.path.exists(legacy_path) and (
        os.path.exists(os.path.join(legacy_path, "model.safetensors")) or
        os.path.exists(os.path.join(legacy_path, "pytorch_model.bin"))
    )

    if allow_fallback and has_legacy_weights:
        return legacy_path, "legal_bert_model (explicit fallback)"

    # If v3.3.0 is missing and fallback is not explicitly configured, fail with v3_path
    return v3_path, "legal_bert_v3.3.0 (missing)"


DEFAULT_MODEL_DIR, DEFAULT_CHECKPOINT_NAME = resolve_default_model_dir()
MODEL_DIR = DEFAULT_MODEL_DIR


def locate_category_evidence(source_code: str, parsed: Dict[str, Any], cat_name: str) -> Dict[str, Any]:
    """
    Locates actual line numbers and real code snippets from the uploaded source code.
    Guarantees line numbers point to genuine, verified source lines rather than fabricated indices.
    """
    lines = source_code.splitlines()
    total_lines = len(lines)

    # Default fallback points to contract definition
    default_line = 1
    default_snippet = lines[0].strip() if lines else ""
    if parsed.get("contracts"):
        c = parsed["contracts"][-1]
        default_line = c.get("start_line", 1)
        if 1 <= default_line <= total_lines:
            default_snippet = lines[default_line - 1].strip()

    matched_lines: List[int] = []
    matched_snippet: str = ""
    evidence_desc: str = ""

    if cat_name == "Termination":
        # Search for selfdestruct, suicide, or emergency termination functions
        for idx, line in enumerate(lines, start=1):
            if re.search(r'\b(selfdestruct|suicide)\b', line, re.IGNORECASE):
                matched_lines.append(idx)
                if not matched_snippet:
                    matched_snippet = line.strip()
                evidence_desc = "Explicit contract termination / selfdestruct instruction"
                break

        if not matched_lines:
            for c in parsed.get("contracts", []):
                for f in c.get("functions", []):
                    fname = f.get("name", "").lower()
                    if any(k in fname for k in ["kill", "destroy", "close", "terminate", "pause"]):
                        st = f.get("start_line", default_line)
                        matched_lines = [st]
                        matched_snippet = lines[st - 1].strip() if 1 <= st <= total_lines else ""
                        evidence_desc = f"Termination or emergency routine in function '{f.get('name')}'"
                        break

    elif cat_name == "Payment / Financial":
        # Search for fee modifications, balance sweeping, or locked withdrawals
        for idx, line in enumerate(lines, start=1):
            if re.search(r'\b(feerate|setfee|settax|withdraw|confiscate)\b', line, re.IGNORECASE) and not line.strip().startswith("//"):
                matched_lines.append(idx)
                if not matched_snippet:
                    matched_snippet = line.strip()
                evidence_desc = "Privileged parameter modification or balance transfer logic"
                break
        if not matched_lines:
            for idx, line in enumerate(lines, start=1):
                if re.search(r'\b(fee|tax|balance)\b', line, re.IGNORECASE) and not line.strip().startswith("//"):
                    matched_lines.append(idx)
                    matched_snippet = line.strip()
                    evidence_desc = "Fee or balance reference in contract logic"
                    break

    elif cat_name == "Privacy":
        # Search for plaintext PII state variables or parameters
        for idx, line in enumerate(lines, start=1):
            if re.search(r'\b(email|phone|ssn|identity|passport|physicaladdress|firstname|lastname)\b', line, re.IGNORECASE) and not line.strip().startswith("//"):
                matched_lines.append(idx)
                if not matched_snippet:
                    matched_snippet = line.strip()
                evidence_desc = "On-chain state variable or parameter holding personal identification data"
                break

    elif cat_name == "Liability":
        # Search for disclaimers or exculpatory language in comments or slash logic
        for idx, line in enumerate(lines, start=1):
            if re.search(r'\b(as is|no liability|indemnify|hold harmless|slashing|penalty|forfeit)\b', line, re.IGNORECASE):
                matched_lines.append(idx)
                if not matched_snippet:
                    matched_snippet = line.strip()
                evidence_desc = "Contractual disclaimer, indemnification term, or collateral penalty term"
                break

    elif cat_name == "Legal Compliance":
        # Search for centralized owner/admin modifiers or lack of timelock
        for idx, line in enumerate(lines, start=1):
            if re.search(r'\b(onlyowner|onlyadmin|hasrole|timelock|multisig)\b', line, re.IGNORECASE) and not line.strip().startswith("//"):
                matched_lines.append(idx)
                if not matched_snippet:
                    matched_snippet = line.strip()
                evidence_desc = "Centralized administrative access control and governance structure"
                break

    if not matched_lines:
        matched_lines = [default_line]
        matched_snippet = default_snippet
        contract_name_decl = parsed["contracts"][-1]["name"] if parsed.get("contracts") else "Contract"
        evidence_desc = f"Evaluated across contract declaration scope in '{contract_name_decl}'"

    return {
        "lineNumbers": matched_lines,
        "snippet": matched_snippet,
        "evidenceDescription": evidence_desc
    }


def compute_embedding_gradient_saliency(
    model,
    tokenizer,
    model_text: str,
    target_category_idx: int
) -> List[Dict[str, Any]]:
    """
    Computes genuine token gradient saliency (Input x Gradient) using PyTorch autograd
    directly over Legal-BERT's word embeddings.
    """
    import torch

    inputs = tokenizer(
        model_text,
        max_length=512,
        truncation=True,
        padding="max_length",
        return_tensors="pt"
    )
    input_ids = inputs["input_ids"]
    attention_mask = inputs["attention_mask"]

    # Extract word embeddings and enable gradient tracking
    embeddings = model.bert.embeddings.word_embeddings(input_ids).detach().requires_grad_(True)
    outputs = model.bert(inputs_embeds=embeddings, attention_mask=attention_mask)
    pooled = outputs[1]
    logits = model.classifier(pooled)

    model.zero_grad()
    logits[0, target_category_idx].backward()

    grads = embeddings.grad[0]
    saliency = (grads * embeddings[0]).sum(dim=-1).detach().cpu().numpy()
    tokens = tokenizer.convert_ids_to_tokens(input_ids[0])

    attributions: List[Dict[str, Any]] = []
    seen_tokens = set()

    for tok, val in zip(tokens, saliency):
        if tok in ("[CLS]", "[SEP]", "[PAD]") or tok.startswith("["):
            continue
        clean_tok = tok.replace("##", "")
        if not clean_tok.strip() or len(clean_tok) < 2:
            continue
        if clean_tok.lower() in seen_tokens:
            continue
        seen_tokens.add(clean_tok.lower())

        attributions.append({
            "token": clean_tok,
            "feature": f"token: {clean_tok}",
            "value": round(float(val), 4),
            "contribution": round(float(val), 4),
            "category": CATEGORIES[target_category_idx],
            "impact": "positive" if val > 0 else "negative"
        })

    attributions.sort(key=lambda x: abs(x["value"]), reverse=True)
    return attributions[:12]


def compute_genuine_shap(
    model,
    tokenizer,
    model_text: str,
    target_category_idx: int,
    max_evals: int = 64
) -> List[Dict[str, Any]]:
    """
    Computes genuine SHAP (SHapley Additive exPlanations) token-level attributions
    using shap.Explainer over the fine-tuned Legal-BERT multi-label model.
    """
    import shap
    import torch

    def predict_proba(texts):
        if isinstance(texts, np.ndarray):
            texts = [str(t) for t in texts]
        elif not isinstance(texts, list):
            texts = [str(texts)]
        else:
            texts = [str(t) for t in texts]
        inputs = tokenizer(texts, padding=True, truncation=True, max_length=128, return_tensors="pt")
        with torch.no_grad():
            logits = model(**inputs).logits
            probs = 1.0 / (1.0 + np.exp(-logits.cpu().numpy()))
        return probs

    try:
        explainer = shap.Explainer(predict_proba, tokenizer)
        shap_explanation = explainer([model_text], max_evals=max_evals)

        tokens = shap_explanation.data[0]
        values = shap_explanation.values[0, :, target_category_idx]

        token_impacts: List[Dict[str, Any]] = []
        seen_tokens = set()

        for tok, val in zip(tokens, values):
            clean_tok = str(tok).strip()
            if not clean_tok or clean_tok in ("[CLS]", "[SEP]", "[PAD]") or clean_tok.startswith("["):
                continue
            clean_tok = clean_tok.replace("##", "")
            if len(clean_tok) < 2 or clean_tok.lower() in seen_tokens:
                continue
            seen_tokens.add(clean_tok.lower())

            val_float = round(float(val), 4)
            token_impacts.append({
                "feature": clean_tok,
                "token": clean_tok,
                "value": val_float,
                "contribution": val_float,
                "category": CATEGORIES[target_category_idx],
                "impact": "positive" if val_float >= 0 else "negative"
            })

        token_impacts.sort(key=lambda x: abs(x["value"]), reverse=True)
        return token_impacts[:12]
    except Exception as exc:
        return [{
            "feature": "error",
            "token": "error",
            "value": 0.0,
            "contribution": 0.0,
            "category": CATEGORIES[target_category_idx],
            "impact": "neutral",
            "error": str(exc)
        }]


def compute_genuine_lime(
    model,
    tokenizer,
    model_text: str,
    target_category_idx: int,
    num_samples: int = 30
) -> List[Dict[str, Any]]:
    """
    Computes genuine LIME (Local Interpretable Model-agnostic Explanations)
    using LimeTextExplainer with local linear surrogate regression over text perturbations.
    """
    from lime.lime_text import LimeTextExplainer
    import torch

    def predict_proba(texts):
        if isinstance(texts, np.ndarray):
            texts = [str(t) for t in texts]
        elif not isinstance(texts, list):
            texts = [str(texts)]
        else:
            texts = [str(t) for t in texts]
        inputs = tokenizer(texts, padding=True, truncation=True, max_length=128, return_tensors="pt")
        with torch.no_grad():
            logits = model(**inputs).logits
            probs = 1.0 / (1.0 + np.exp(-logits.cpu().numpy()))
        return probs

    try:
        explainer = LimeTextExplainer(
            class_names=CATEGORIES,
            random_state=42
        )
        exp = explainer.explain_instance(
            text_instance=model_text,
            classifier_fn=predict_proba,
            labels=[target_category_idx],
            num_features=10,
            num_samples=num_samples
        )
        raw_list = exp.as_list(label=target_category_idx)

        lime_explanations: List[Dict[str, Any]] = []
        for tok, weight in raw_list:
            clean_tok = str(tok).strip()
            w_float = round(float(weight), 4)
            lime_explanations.append({
                "clause": f"Token '{clean_tok}' in {CATEGORIES[target_category_idx]}",
                "token": clean_tok,
                "score": w_float,
                "weight": w_float,
                "type": "risk" if w_float >= 0 else "safe",
                "explanation": (
                    f"LIME local surrogate linear weight: '{clean_tok}' has weight {w_float:+.4f} "
                    f"towards {CATEGORIES[target_category_idx]} prediction."
                )
            })

        return lime_explanations
    except Exception as exc:
        return [{
            "clause": "LIME computation notice",
            "token": "error",
            "score": 0.0,
            "weight": 0.0,
            "type": "neutral",
            "explanation": f"LIME explanation generation notice: {exc}"
        }]


class AnalysisEngine:
    """
    Active SaaS Analysis Engine driven by Legal-BERT deep learning classifier.
    Preserves strict separation from deterministic rule engines.
    """
    VERSION = "1.0.0-legal-bert"
    ENGINE_TYPE = "legal_bert_ml_engine"

    _model = None
    _tokenizer = None

    def __init__(self, model_dir: Optional[str] = None):
        self.model_dir = model_dir or MODEL_DIR
        if self.model_dir == DEFAULT_MODEL_DIR:
            self.checkpoint_name = DEFAULT_CHECKPOINT_NAME
        else:
            self.checkpoint_name = os.path.basename(self.model_dir)

    @classmethod
    def get_model_and_tokenizer(cls, model_dir: str):
        """Loads and caches the fine-tuned Legal-BERT model and tokenizer."""
        if cls._model is None:
            from transformers import AutoTokenizer, AutoModelForSequenceClassification

            cls._tokenizer = AutoTokenizer.from_pretrained(model_dir)
            cls._model = AutoModelForSequenceClassification.from_pretrained(model_dir)
            cls._model.eval()
        return cls._model, cls._tokenizer

    def is_model_available(self) -> bool:
        """Verifies whether a real fine-tuned Legal-BERT model artifact exists."""
        if not os.path.exists(self.model_dir):
            return False
        has_config = os.path.exists(os.path.join(self.model_dir, "config.json"))
        has_weights = (
            os.path.exists(os.path.join(self.model_dir, "model.safetensors")) or
            os.path.exists(os.path.join(self.model_dir, "pytorch_model.bin"))
        )
        return has_config and has_weights

    def extract_submission_model_text(self, parsed: Dict[str, Any], source_code: str) -> str:
        """
        Extracts the dual-stream natural-language representation observable at submission time.
        Contains ONLY information observable from the submitted source code:
        - Contract Name & License
        - Primary Functions, Modifiers, and Visibility
        - NatSpec documentation comments
        - Observable State Mutations & Transfers
        - Normalized Key Logic
        
        Strictly excludes post-hoc audit titles, target labels, or auditor rationales.
        """
        contract_name = parsed["contracts"][-1]["name"] if parsed["contracts"] else "Contract"

        # License extraction
        spdx_match = re.search(r"SPDX-License-Identifier:\s*([^\r\n]+)", source_code, re.IGNORECASE)
        license_str = spdx_match.group(1).strip() if spdx_match else "Unspecified"

        functions = parsed.get("functions", [])
        primary_fn = functions[0]["name"] if functions else "contract_scope"
        visibility = functions[0].get("visibility", "public") if functions else "public"
        modifiers = ", ".join(functions[0].get("modifiers", [])) if functions and functions[0].get("modifiers") else "none"

        # NatSpec comments
        natspec_lines = []
        for line in source_code.splitlines():
            s = line.strip()
            if s.startswith("///") or s.startswith("* @notice") or s.startswith("* @dev"):
                natspec_lines.append(s.lstrip("/* @devnotice").strip())
        natspec = " ".join(natspec_lines[:3]) if natspec_lines else "Standard contract deployment without explicit NatSpec."

        # Observable behavior summary
        behavior_elements = []
        if "selfdestruct" in source_code or "suicide" in source_code:
            behavior_elements.append("Contains termination instruction capable of deleting bytecode and sweeping balance.")
        if "fee" in source_code.lower() or "tax" in source_code.lower():
            behavior_elements.append("Includes fee or tax parameter adjustment functions.")
        if any(var in source_code.lower() for var in ["email", "address", "phone", "ssn", "name"]):
            behavior_elements.append("Declares identity or contact state variables.")
        if not behavior_elements:
            behavior_elements.append("Standard state transition logic with no anomalous privileged operations.")

        behavior_str = " ".join(behavior_elements)
        normalized_code = " ".join([l.strip() for l in source_code.splitlines() if l.strip() and not l.strip().startswith("//")][:5])

        model_text = (
            f"[Submission Context — Observable Contract Representation]\n"
            f"Contract: {contract_name} ({license_str})\n"
            f"Function: {primary_fn} ({visibility})\n"
            f"Modifiers: {modifiers}\n"
            f"Documented Intent: {natspec}\n"
            f"Operational Behavior: {behavior_str}\n"
            f"Key Code Logic: {normalized_code[:300]}"
        )
        return model_text

    def get_dataset_readiness_summary(self) -> Dict[str, Any]:
        """Provides verified empirical data readiness metrics."""
        return {
            "totalCanonicalRecords": 52,
            "trainingEligibleRecords": 38,
            "minimumRequiredSamples": 50,
            "humanVerifiedClaims": 0,
            "provenance": "100% ai_reviewed, zero human verified claims",
            "categorySupport": {
                "Privacy": {"positive": 1, "negative": 37, "threshold": 5, "status": "blocked (needs >= 4 more)"},
                "Termination": {"positive": 6, "negative": 32, "threshold": 5, "status": "ready (>= 5)"},
                "Legal Compliance": {"positive": 9, "negative": 29, "threshold": 5, "status": "ready (>= 5)"},
                "Liability": {"positive": 1, "negative": 37, "threshold": 5, "status": "blocked (needs >= 4 more)"},
                "Payment / Financial": {"positive": 4, "negative": 34, "threshold": 5, "status": "blocked (needs >= 1 more)"}
            },
            "blockingReasons": [
                "Insufficient dataset volume: 38 eligible records available (minimum 50 required for 60/20/20 split).",
                "Severe class imbalance: Privacy (1 pos), Liability (1 pos), Payment / Financial (4 pos) prevent project-isolated validation.",
                "Zero human-verified ground-truth: records are AI-reviewed (ai_reviewed) and must not be misrepresented as human-verified."
            ],
            "ruleEngineSubstituteUsed": False,
            "modelStatus": "training_blocked_by_data_limitations"
        }

    def analyze_source(
        self,
        source_code: str,
        contract_name: str = "Contract.sol",
        description: str = "",
        persist: bool = False
    ) -> Dict[str, Any]:
        """
        Executes Legal-BERT multi-label operational hazard classification.
        
        Strict adherence to specification:
        - If trained model artifact exists, executes neural inference and genuine XAI attributions.
        - If no trained model artifact exists, returns model_unavailable status with full dataset readiness diagnostics.
        - NEVER falls back to or substitutes a deterministic rule engine.
        - Source code line references point directly to actual uploaded content and accurate line numbers.
        - Discloses model evaluation limitations honestly without claiming certified legal accuracy.
        - In Phase 1, temporary analysis results are not forced into permanent database storage unless persist=True.
        """
        analysis_id = f"audit-{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6]}"
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # 1. Structural Pre-parse Check
        parser = SolidityParser(source_code)
        parsed = parser.parse()

        if parsed["status"] == "empty_input":
            return {
                "analysisId": analysis_id,
                "contractName": contract_name,
                "status": "failed",
                "timestamp": timestamp,
                "error": {"code": "EMPTY_SOURCE", "message": "Solidity source code was empty."}
            }

        if parsed["status"] == "malformed_input":
            return {
                "analysisId": analysis_id,
                "contractName": contract_name,
                "status": "failed",
                "timestamp": timestamp,
                "error": {"code": "MALFORMED_SOURCE", "message": f"Syntax error: {', '.join(parsed['warnings'])}"}
            }

        if not parsed["contracts"] and not parsed["pragmas"]:
            return {
                "analysisId": analysis_id,
                "contractName": contract_name,
                "status": "failed",
                "timestamp": timestamp,
                "error": {"code": "UNSUPPORTED_SOURCE", "message": "No recognized Solidity declarations found."}
            }

        if parsed["contracts"]:
            contract_name = parsed["contracts"][-1]["name"]
        solidity_version = parsed["pragmas"][0]["version"] if parsed["pragmas"] else "^0.8.20"

        # 2. Extract Submission-Time Representation
        model_input_text = self.extract_submission_model_text(parsed, source_code)

        # 3. Model Artifact Availability Check
        if not self.is_model_available():
            readiness_info = self.get_dataset_readiness_summary()
            return {
                "analysisId": analysis_id,
                "id": analysis_id,
                "contractName": contract_name,
                "name": contract_name,
                "contractType": "Solidity Smart Contract",
                "solidityVersion": solidity_version,
                "status": "model_unavailable",
                "timestamp": timestamp,
                "modelStatus": "training_blocked_by_data_limitations",
                "message": (
                    "Legal-BERT model artifact is not available. Fine-tuning is responsibly blocked "
                    "due to verified dataset volume and category support limitations (38 eligible records, "
                    "1 Privacy positive, 1 Liability positive, 4 Payment/Financial positives). "
                    "In strict accordance with the platform specification, rule-based analyzers and mock "
                    "predictions are prohibited from acting as model substitutes."
                ),
                "modelInputText": model_input_text,
                "readiness": readiness_info,
                "metadata": {
                    "engineType": self.ENGINE_TYPE,
                    "analysisModelVersion": self.VERSION,
                    "ruleEngineSubstituteUsed": False,
                    "mockPredictionsUsed": False,
                    "disclaimer": "Operational hazard assessment requires a trained Legal-BERT model artifact."
                }
            }

        # 4. Neural Inference (When Model Artifact Exists)
        import torch
        model, tokenizer = self.get_model_and_tokenizer(self.model_dir)

        inputs = tokenizer(
            model_input_text,
            max_length=512,
            truncation=True,
            padding="max_length",
            return_tensors="pt"
        )

        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits.squeeze(0).cpu().numpy()
            probabilities = 1.0 / (1.0 + np.exp(-logits))

        # Build Category Scores, Verified Findings, and Honest Disclosures
        categories_list = []
        findings = []
        recommendations = []
        risk_breakdown = {}

        # Track top category index for XAI gradient saliency
        top_category_idx = int(np.argmax(probabilities))

        for idx, cat_name in enumerate(CATEGORIES):
            prob = float(probabilities[idx])
            cat_score = int(round(prob * 100))
            risk_breakdown[cat_name] = cat_score

            is_positive = prob >= 0.5
            sev = CATEGORY_SEVERITIES[cat_name] if is_positive else "Low"

            # Find real line numbers and code snippets from the uploaded source
            evidence = locate_category_evidence(source_code, parsed, cat_name)
            matched_lines = evidence["lineNumbers"]
            matched_snippet = evidence["snippet"]

            if is_positive:
                summary_text = (
                    f"Legal-BERT predicted elevated operational hazard in {cat_name} "
                    f"(model probability: {cat_score}%, threshold: 0.50 uncalibrated)."
                )
                findings.append({
                    "findingId": f"ml-{cat_name.lower().replace(' ', '-')}-{uuid.uuid4().hex[:4]}",
                    "category": cat_name,
                    "title": f"Legal-BERT Prediction: Elevated Hazard in {cat_name}",
                    "severity": sev,
                    "description": CATEGORY_DESCRIPTIONS[cat_name],
                    "confidence": f"{cat_score}% (uncalibrated model score)",
                    "probability": round(prob, 4),
                    "threshold": 0.50,
                    "supportStatus": CATEGORY_SUPPORT_STATUS[cat_name],
                    "snippet": matched_snippet or model_input_text[:120],
                    "lineNumbers": matched_lines,
                    "evidenceDescription": evidence["evidenceDescription"],
                    "suggestion": f"Review and constrain privileged {cat_name.lower()} controls according to documented standards."
                })
                recommendations.append({
                    "id": f"rec-{idx+1}",
                    "category": cat_name,
                    "riskLevel": sev,
                    "title": f"Review {cat_name} Architecture",
                    "clause": f"{cat_name} clause at line(s) {', '.join(str(l) for l in matched_lines)} in {contract_name}",
                    "suggestion": f"Refactor contract to eliminate unilateral {cat_name.lower()} controls or introduce timelock/multisig governance.",
                    "beforeCode": matched_snippet if matched_snippet else "// Unconstrained pattern",
                    "afterCode": "// Recommended bounded governance implementation"
                })
            else:
                summary_text = (
                    f"Legal-BERT evaluated {cat_name} with low predicted hazard "
                    f"(model probability: {cat_score}%, threshold: 0.50 uncalibrated)."
                )
                # If specific structural evidence was located in the source code, include as observational finding
                if evidence["evidenceDescription"] and not evidence["evidenceDescription"].startswith("Evaluated across contract declaration scope"):
                    findings.append({
                        "findingId": f"ml-obs-{cat_name.lower().replace(' ', '-')}-{uuid.uuid4().hex[:4]}",
                        "category": cat_name,
                        "title": f"Legal-BERT Observation: {cat_name} Evaluated Low Hazard",
                        "severity": "Low",
                        "description": f"{CATEGORY_DESCRIPTIONS[cat_name]} Model evaluated this construct below the 0.50 decision threshold.",
                        "confidence": f"{cat_score}% (uncalibrated model score)",
                        "probability": round(prob, 4),
                        "threshold": 0.50,
                        "supportStatus": CATEGORY_SUPPORT_STATUS[cat_name],
                        "snippet": matched_snippet,
                        "lineNumbers": matched_lines,
                        "evidenceDescription": evidence["evidenceDescription"],
                        "suggestion": f"Ensure {cat_name.lower()} logic remains bounded and documented in contract NatSpec."
                    })

            categories_list.append({
                "name": cat_name,
                "riskLevel": sev,
                "severity": sev,
                "score": cat_score,
                "probability": round(prob, 4),
                "threshold": 0.50,
                "isCalibrated": False,
                "supportStatus": CATEGORY_SUPPORT_STATUS[cat_name],
                "detectedClauses": len(matched_lines) if is_positive else 0,
                "summary": summary_text
            })

        # 5. Compute Genuine SHAP, LIME, and PyTorch Embedding Gradient Saliency
        # Top predicted hazard category for explainability focus
        shap_values = compute_genuine_shap(
            model=model,
            tokenizer=tokenizer,
            model_text=model_input_text,
            target_category_idx=top_category_idx,
            max_evals=32
        )

        lime_explanations = compute_genuine_lime(
            model=model,
            tokenizer=tokenizer,
            model_text=model_input_text,
            target_category_idx=top_category_idx,
            num_samples=20
        )

        token_attributions = compute_embedding_gradient_saliency(
            model=model,
            tokenizer=tokenizer,
            model_text=model_input_text,
            target_category_idx=top_category_idx
        )

        # Overall risk calculation
        max_cat_score = max(risk_breakdown.values()) if risk_breakdown else 0
        avg_cat_score = sum(risk_breakdown.values()) / max(len(risk_breakdown), 1)
        composite_score = int(min(100, round((max_cat_score * 0.7) + (avg_cat_score * 0.3))))

        if composite_score >= 80:
            risk_level = "Critical"
        elif composite_score >= 60:
            risk_level = "High"
        elif composite_score >= 35:
            risk_level = "Medium"
        else:
            risk_level = "Low"

        # Compliance Matrix
        compliance_matrix = [
            {
                "area": "Consumer Law Protections",
                "assessment": "Potential Operational Hazard" if (risk_breakdown.get("Termination", 0) > 50 or risk_breakdown.get("Payment / Financial", 0) > 50) else "Compliant Scope",
                "status": "Warning" if (risk_breakdown.get("Termination", 0) > 50 or risk_breakdown.get("Payment / Financial", 0) > 50) else "Pass",
                "note": "Legal-BERT evaluation of unilateral termination and fee manipulation clauses under consumer protection standards."
            },
            {
                "area": "Privacy Standards (GDPR / CCPA)",
                "assessment": "Potential Operational Hazard" if risk_breakdown.get("Privacy", 0) > 50 else "Compliant Scope",
                "status": "Warning" if risk_breakdown.get("Privacy", 0) > 50 else "Pass",
                "note": "Legal-BERT evaluation of personal identity attributes stored on public distributed ledger."
            },
            {
                "area": "Contract Fairness & Governance",
                "assessment": "Potential Operational Hazard" if (risk_breakdown.get("Liability", 0) > 50 or risk_breakdown.get("Legal Compliance", 0) > 50) else "Compliant Scope",
                "status": "Warning" if (risk_breakdown.get("Liability", 0) > 50 or risk_breakdown.get("Legal Compliance", 0) > 50) else "Pass",
                "note": "Legal-BERT evaluation of exculpatory disclaimers and administrative control centralization."
            }
        ]

        # Test Benchmark Evaluation from docs/LEGAL_BERT_EXPERIMENT_REPORT.md
        test_evaluation_report = {
            "testSplitSize": 7,
            "testSplitComposition": "100% real-source contracts (anvil_protocol, aragon_vault, crytic_not_so_smart_contracts, virtuals_genesis)",
            "trainingSplitSize": 44,
            "validationSplitSize": 7,
            "macroF1AllCategories": 0.0000,
            "macroF1EvaluableCategories": 0.0000,
            "specificity": "100.0% (28/28 negatives correctly classified)",
            "hammingLoss": 0.2000,
            "baselineComparison": {
                "model": "TF-IDF + Logistic Regression",
                "macroF1AllCategories": 0.1600,
                "macroF1EvaluableCategories": 0.4000
            },
            "categoryBreakdown": [
                {
                    "category": "Privacy",
                    "testPositives": 0,
                    "testNegatives": 7,
                    "truePositives": 0,
                    "falsePositives": 0,
                    "falseNegatives": 0,
                    "trueNegatives": 7,
                    "precision": 0.0,
                    "recall": 0.0,
                    "f1": 0.0,
                    "supportStatus": "inconclusive_zero_positive_support",
                    "auditorNote": "Zero positive test support. Held-out empirical recall cannot be evaluated."
                },
                {
                    "category": "Termination",
                    "testPositives": 3,
                    "testNegatives": 4,
                    "truePositives": 0,
                    "falsePositives": 0,
                    "falseNegatives": 3,
                    "trueNegatives": 4,
                    "precision": 0.0,
                    "recall": 0.0,
                    "f1": 0.0,
                    "supportStatus": "sufficient_support (missed at 0.50)",
                    "auditorNote": "Sufficient positive support (N=3), but all test positives were missed at uncalibrated threshold 0.50."
                },
                {
                    "category": "Legal Compliance",
                    "testPositives": 4,
                    "testNegatives": 3,
                    "truePositives": 0,
                    "falsePositives": 0,
                    "falseNegatives": 4,
                    "trueNegatives": 3,
                    "precision": 0.0,
                    "recall": 0.0,
                    "f1": 0.0,
                    "supportStatus": "sufficient_support (missed at 0.50)",
                    "auditorNote": "Sufficient positive support (N=4), but all test positives were missed at uncalibrated threshold 0.50."
                },
                {
                    "category": "Liability",
                    "testPositives": 0,
                    "testNegatives": 7,
                    "truePositives": 0,
                    "falsePositives": 0,
                    "falseNegatives": 0,
                    "trueNegatives": 7,
                    "precision": 0.0,
                    "recall": 0.0,
                    "f1": 0.0,
                    "supportStatus": "inconclusive_zero_positive_support",
                    "auditorNote": "Zero positive test support. Held-out empirical recall cannot be evaluated."
                },
                {
                    "category": "Payment / Financial",
                    "testPositives": 0,
                    "testNegatives": 7,
                    "truePositives": 0,
                    "falsePositives": 0,
                    "falseNegatives": 0,
                    "trueNegatives": 7,
                    "precision": 0.0,
                    "recall": 0.0,
                    "f1": 0.0,
                    "supportStatus": "inconclusive_zero_positive_support",
                    "auditorNote": "Zero positive test support. Held-out empirical recall cannot be evaluated."
                }
            ],
            "calibrationStatus": "All categories use default 0.50 uncalibrated decision thresholds. Validation set had 0 positive examples, preventing empirical threshold tuning without degenerate overfitting.",
            "safetyWarning": (
                "CRITICAL: Low confidence or the absence of detected findings is NOT proof that the contract is safe, compliant, or free of legal risks. "
                "The model missed all test positives at threshold 0.50 and had zero test support for 3 categories. "
                "Outputs are experimental decision-support signals only and must never be treated as legal certification."
            )
        }

        safety_warning = (
            "CRITICAL SAFETY DISCLOSURE: Low predicted scores or an absence of detected findings do NOT constitute "
            "proof that a contract is safe, legally compliant, or without operational hazards. The prototype Legal-BERT "
            "model was evaluated on a small held-out test split (N=7) with zero positive support for Privacy, Liability, "
            "and Payment/Financial, and missed test positives for Termination and Legal Compliance at the default 0.50 "
            "uncalibrated threshold. Always perform independent professional legal review."
        )

        # Transparent Model Disclosures
        model_disclosures = {
            "modelName": f"nlpaueb/legal-bert-base-uncased ({self.checkpoint_name})",
            "checkpointName": self.checkpoint_name,
            "checkpointPath": f"analysis/models/{self.checkpoint_name}",
            "datasetVersion": "v3.3.0",
            "datasetSha256": "74464fd132e9268220549adc8e5cfb31d4ca69b9fae203b31ae2924c1500e456",
            "isCalibrated": False,
            "thresholds": {c: 0.50 for c in CATEGORIES},
            "evaluationLimitations": (
                "As documented in docs/LEGAL_BERT_EXPERIMENT_REPORT.md, this prototype Legal-BERT model "
                "was trained on a small canonical dataset (N=44). In the held-out real-source test split (N=7), "
                "categories Privacy, Liability, and Payment / Financial had zero positive ground-truth examples, "
                "rendering test recall and F1 mathematically non-evaluable (inconclusive_zero_positive_support). "
                "Categories Termination and Legal Compliance had ground-truth positives that were missed at the "
                "0.50 uncalibrated decision threshold (Macro F1 = 0.0000, Specificity = 100.0%). "
                "Raw sigmoid scores are uncalibrated and do NOT represent true statistical probabilities."
            ),
            "safetyWarning": safety_warning,
            "testEvaluationReport": test_evaluation_report,
            "xaiMethodology": "Genuine SHAP (Partition/Permutation) + LIME (Local Linear Surrogate) + PyTorch Embedding Gradient Saliency",
            "xaiLimitations": (
                "SHAP values and LIME weights are genuine mathematical explainability calculations over input tokens. "
                "They reflect feature attribution to model internal parameters, not statutory legal proof."
            )
        }

        result = {
            "analysisId": analysis_id,
            "id": analysis_id,
            "contractName": contract_name,
            "name": contract_name,
            "contractType": "Solidity Smart Contract",
            "auditDate": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            "solidityVersion": solidity_version,
            "status": "completed",
            "timestamp": timestamp,
            "riskScore": composite_score,
            "overallRiskScore": composite_score,
            "overallScore": composite_score,
            "riskLevel": risk_level,
            "overallRiskLevel": risk_level,
            "confidence": f"{round(float(np.mean(list(probabilities))) * 100, 1)}% (Uncalibrated Neural Sigmoid Mean)",
            "isCalibrated": False,
            "safetyWarning": safety_warning,
            "testEvaluationReport": test_evaluation_report,
            "summary": f"Legal-BERT neural analysis evaluated {len(CATEGORIES)} risk categories using checkpoint {self.checkpoint_name}, identifying {len(findings)} operational hazard signals.",
            "solidityCode": source_code,
            "riskBreakdown": risk_breakdown,
            "categories": categories_list,
            "findings": findings,
            "shapValues": shap_values,
            "shapExplanations": shap_values,
            "limeExplanations": lime_explanations,
            "recommendations": recommendations,
            "complianceMatrix": compliance_matrix,
            "modelDisclosures": model_disclosures,
            "xai": {
                "targetCategory": CATEGORIES[top_category_idx],
                "tokenAttributions": token_attributions,
                "shap": {
                    "method": "SHAP (SHapley Additive exPlanations via shap.Explainer)",
                    "tokenAttributions": shap_values,
                    "description": "Game-theoretic Shapley values computing marginal feature contributions across input perturbations."
                },
                "lime": {
                    "method": "LIME (Local Interpretable Model-agnostic Explanations via LimeTextExplainer)",
                    "tokenWeights": lime_explanations,
                    "description": "Local linear surrogate model trained on perturbed contract representation instances."
                },
                "gradientSaliency": {
                    "method": "PyTorch Word Embedding Gradient Saliency (Input x Gradient)",
                    "tokenAttributions": token_attributions,
                    "description": "Direct neural sensitivity from backpropagated loss gradients onto input token embeddings."
                }
            },
            "metadata": {
                "linesOfCode": parsed["total_lines"],
                "parserWarnings": parsed["warnings"],
                "analysisModelVersion": self.VERSION,
                "engineType": self.ENGINE_TYPE,
                "checkpointName": self.checkpoint_name,
                "checkpointPath": f"analysis/models/{self.checkpoint_name}",
                "datasetVersion": "v3.3.0",
                "datasetSha256": "74464fd132e9268220549adc8e5cfb31d4ca69b9fae203b31ae2924c1500e456",
                "ruleEngineSubstituteUsed": False,
                "mockPredictionsUsed": False,
                "trainedModelArtifactUsed": True,
                "isCalibrated": False,
                "disclaimer": "Automated Legal-BERT machine learning inference. Operational risk indicators; not formal legal advice."
            }
        }

        # Optional persistence (strictly disabled by default in Phase 1 no-login mode)
        if persist:
            from analysis.db import insert_analysis
            insert_analysis(result)

        return result
