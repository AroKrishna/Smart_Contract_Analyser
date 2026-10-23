"""
analysis/chat.py - Context-Aware Interactive AI Legal Assistant (Phase 6)

Strictly scoped conversational interface evaluating questions solely within
the context of the analyzed smart contract.
Distinguishes source evidence & indicators extracted from code/AST from
model-predicted risks and assistant-generated explanations.
Supports external AI provider integration (OpenAI-compatible) when configured,
with zero-dependency, fault-tolerant local fallback providing limited offline
explanations when external keys are unavailable.
"""

import os
import json
import logging
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional

logger = logging.getLogger("smart_contract_analyser.chat")

LEGAL_ASSISTANT_DISCLAIMER = (
    "Legal AI Assistant insights are generated for operational risk triaging and informational "
    "purposes based on static syntactic extraction and neural Legal-BERT classification. "
    "They do not constitute formal legal opinions, attorney-client privileged advice, "
    "or guarantees of judicial enforceability."
)


def _filter_source_evidence(findings: List[Dict[str, Any]], category: str, keywords: List[str]) -> List[Dict[str, Any]]:
    """Filters source evidence and contract indicators strictly relevant to the query topic."""
    matched = []
    for f in findings:
        f_cat = f.get("category", "")
        f_desc = f.get("description", "").lower()
        f_snip = f.get("snippet", "").lower()
        if f_cat.lower() == category.lower():
            matched.append(f)
        elif any(k in f_desc or k in f_snip for k in keywords):
            if f not in matched:
                matched.append(f)
    return matched


def _try_external_provider(
    query: str,
    contract_name: str,
    source_code: str,
    source_evidence: List[Dict[str, Any]],
    risk_score: int,
    risk_level: str
) -> Optional[str]:
    """
    Attempts to query an external LLM provider if configured via environment variables.
    Fails safely without raising exceptions or leaking credentials.
    """
    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("LLM_API_KEY")
    if not api_key:
        return None

    api_base = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1").rstrip("/")
    model_name = os.environ.get("LLM_MODEL", "gpt-4o-mini")

    # Strict system prompt enforcing grounding in source evidence and forbidding fabricated citations
    system_prompt = (
        "You are an AI Legal Assistant specializing in smart contract legal analysis. "
        "You must answer user questions strictly grounded in the provided Solidity contract and extracted source evidence. "
        "Do NOT invent clauses, legal citations, judicial precedents, or vulnerabilities not present in the contract. "
        "Clearly distinguish between source evidence from the contract and your assistant-generated guidance."
    )

    evidence_summary = "\n".join([
        f"- [{f.get('category')}] (Severity: {f.get('severity')}): {f.get('description')} (Lines: {f.get('lineStart', 0)}-{f.get('lineEnd', 0)})"
        for f in source_evidence[:5]
    ]) or "No high-severity indicators recorded for this specific category."

    # Truncate source context if very large to prevent token blowup
    snippet_code = source_code[:3000] if len(source_code) > 3000 else source_code

    user_prompt = (
        f"Contract Name: {contract_name}\n"
        f"Overall Risk: {risk_score}/100 ({risk_level})\n"
        f"Source Evidence & Indicators:\n{evidence_summary}\n\n"
        f"Contract Source Snippet:\n```solidity\n{snippet_code}\n```\n\n"
        f"User Inquiry: {query}\n\n"
        "Please provide an assistant-generated explanation explaining the operational/legal risks and recommended mitigation."
    )

    try:
        req_data = json.dumps({
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": 600,
            "temperature": 0.2
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{api_base}/chat/completions",
            data=req_data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            },
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=4.0) as resp:
            if resp.status == 200:
                body = json.loads(resp.read().decode("utf-8"))
                choices = body.get("choices", [])
                if choices and "message" in choices[0]:
                    return choices[0]["message"].get("content", "").strip()
    except Exception as ex:
        # Graceful failure: log warning without logging secret key
        logger.warning("External AI provider call skipped or timed out (%s). Falling back to local offline explanation.", type(ex).__name__)
        return None

    return None


def answer_contract_query(query: str, audit_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Answers user queries strictly scoped to the analyzed contract.
    Extracts relevant context from the contract's code, risk breakdown,
    findings, and compliance matrix.
    Distinguishes source evidence from model-predicted risks and assistant-generated explanations.
    """
    q_lower = query.lower().strip()
    contract_name = audit_data.get("contractName") or audit_data.get("name") or "the contract"
    source_code = audit_data.get("solidityCode", "")
    risk_score = audit_data.get("riskScore") or audit_data.get("overallRiskScore") or 0
    risk_level = audit_data.get("riskLevel") or audit_data.get("overallRiskLevel") or "Low"
    findings = audit_data.get("findings", [])
    categories = audit_data.get("categories", [])

    model_predicted_risks = [c for c in categories if c.get("riskLevel") in ("High", "Critical", "Medium")]
    if not model_predicted_risks and categories:
        model_predicted_risks = categories

    # Check for external AI provider first if configured
    external_response = None

    # 1. Termination / Killswitch query
    if any(k in q_lower for k in ["termination", "kill", "destroy", "selfdestruct", "suicide"]):
        cat_name = "Termination"
        evidence = _filter_source_evidence(findings, cat_name, ["selfdestruct", "suicide", "destroy", "kill"])
        has_kill = "selfdestruct" in source_code or "suicide" in source_code or len(evidence) > 0

        external_response = _try_external_provider(query, contract_name, source_code, evidence, risk_score, risk_level)

        if external_response:
            assistant_explanation = external_response
            remediation = "Apply suggested mitigations in accordance with your governance requirements."
        elif has_kill:
            assistant_explanation = (
                f"In {contract_name}, an emergency killswitch was identified in the source code. "
                "The function invokes the EVM opcode `selfdestruct` (or `suicide`), allowing the contract owner "
                "to unilaterally sweep deposited Ether and permanently delete bytecode from state storage. "
                "From a contractual fairness perspective, this creates an asymmetric termination right without "
                "prior counterparty notice or timelock safeguards."
            )
            remediation = (
                "Replace the irreversible selfdestruct instruction with an OpenZeppelin "
                "`Pausable` circuit breaker or transfer funds through a multi-sig timelocked escrow queue."
            )
        else:
            assistant_explanation = (
                f"No unilateral termination killswitch (`selfdestruct`) was detected in {contract_name}. "
                "State and balance management adhere to continuous operational execution."
            )
            remediation = "No termination refactoring required."

        full_answer = f"{assistant_explanation}\n\n**Remediation Recommendation:**\n{remediation}" if not external_response else assistant_explanation

        return {
            "query": query,
            "category": cat_name,
            "scopedContract": contract_name,
            "sourceEvidence": evidence,
            "verifiedFindings": evidence,  # backwards-compatible alias
            "modelPredictedRisks": model_predicted_risks,
            "assistantGeneratedExplanation": assistant_explanation,
            "modelExplanations": assistant_explanation,  # backwards-compatible alias
            "remediation": remediation,
            "answer": full_answer,
            "engineType": "external_llm" if external_response else "offline_deterministic_explanation",
            "engineLabel": "Generative AI Explanation (External LLM)" if external_response else "Limited Offline Explanation (Deterministic Analysis)",
            "isGenerativeAi": bool(external_response),
            "relevantClauses": evidence,
            "disclaimer": LEGAL_ASSISTANT_DISCLAIMER,
            "sourceCodeAvailable": bool(source_code)
        }

    # 2. Privacy / GDPR query
    if any(k in q_lower for k in ["gdpr", "privacy", "pii", "personal", "email", "ccpa"]):
        cat_name = "Privacy"
        evidence = _filter_source_evidence(findings, cat_name, ["email", "address", "phone", "pii", "ssn"])
        has_pii = any(k in source_code.lower() for k in ["useremail", "physicaladdress", "ssn", "phone"]) or len(evidence) > 0

        external_response = _try_external_provider(query, contract_name, source_code, evidence, risk_score, risk_level)

        if external_response:
            assistant_explanation = external_response
            remediation = "Consult statutory privacy guidelines before persisting natural-person records."
        elif has_pii:
            assistant_explanation = (
                f"In {contract_name}, plaintext personal data was identified in public storage variables. "
                "Under Article 17 of the General Data Protection Regulation (GDPR) — the statutory 'Right to be Forgotten' "
                "(right to erasure) — data controllers must ensure personal data can be deleted upon request. "
                "Because public blockchain state history is immutable, persisting plaintext personal identity info "
                "conflicts with statutory privacy mandates."
            )
            remediation = (
                "Do not store plaintext PII on-chain. Store off-chain zero-knowledge commitments, "
                "salted cryptographic hashes (e.g. `keccak256(email, salt)`), or manage identities via decentralized DID resolvers."
            )
        else:
            assistant_explanation = (
                f"In {contract_name}, no plaintext natural-person personal identifying information (PII) was detected "
                "in public storage variables or emitted events. Data management relies on cryptographic hashes and addresses, "
                "which aligns with blockchain privacy best practices."
            )
            remediation = "Maintain standard off-chain storage for any personal identifiers."

        full_answer = f"{assistant_explanation}\n\n**Remediation Recommendation:**\n{remediation}" if not external_response else assistant_explanation

        return {
            "query": query,
            "category": cat_name,
            "scopedContract": contract_name,
            "sourceEvidence": evidence,
            "verifiedFindings": evidence,
            "modelPredictedRisks": model_predicted_risks,
            "assistantGeneratedExplanation": assistant_explanation,
            "modelExplanations": assistant_explanation,
            "remediation": remediation,
            "answer": full_answer,
            "engineType": "external_llm" if external_response else "offline_deterministic_explanation",
            "engineLabel": "Generative AI Explanation (External LLM)" if external_response else "Limited Offline Explanation (Deterministic Analysis)",
            "isGenerativeAi": bool(external_response),
            "relevantClauses": evidence,
            "disclaimer": LEGAL_ASSISTANT_DISCLAIMER,
            "sourceCodeAvailable": bool(source_code)
        }

    # 3. Fee / Payment / Financial query
    if any(k in q_lower for k in ["fee", "tax", "payment", "financial", "rate", "cost"]):
        cat_name = "Payment / Financial"
        evidence = _filter_source_evidence(findings, cat_name, ["fee", "tax", "payment", "withdraw", "balance"])

        external_response = _try_external_provider(query, contract_name, source_code, evidence, risk_score, risk_level)

        if external_response:
            assistant_explanation = external_response
            remediation = "Ensure all fees have verifiable caps and transparent distribution events."
        else:
            assistant_explanation = (
                f"Regarding financial parameters in {contract_name}: "
                "Unconstrained administrative fee or tax setter functions present operational risks where a deployer "
                "can arbitrarily escalate transactional costs post-deployment, extracting funds without user recourse. "
                "Under consumer protection law, non-disclosed or unbounded parameter changes may be challenged as unfair contract terms."
            )
            remediation = "Implement an immutable upper ceiling check (e.g., `require(newFee <= MAX_FEE_CEILING, 'Fee cap exceeded');`)."

        full_answer = f"{assistant_explanation}\n\n**Remediation Recommendation:**\n{remediation}" if not external_response else assistant_explanation

        return {
            "query": query,
            "category": cat_name,
            "scopedContract": contract_name,
            "sourceEvidence": evidence,
            "verifiedFindings": evidence,
            "modelPredictedRisks": model_predicted_risks,
            "assistantGeneratedExplanation": assistant_explanation,
            "modelExplanations": assistant_explanation,
            "remediation": remediation,
            "answer": full_answer,
            "engineType": "external_llm" if external_response else "offline_deterministic_explanation",
            "engineLabel": "Generative AI Explanation (External LLM)" if external_response else "Limited Offline Explanation (Deterministic Analysis)",
            "isGenerativeAi": bool(external_response),
            "relevantClauses": evidence,
            "disclaimer": LEGAL_ASSISTANT_DISCLAIMER,
            "sourceCodeAvailable": bool(source_code)
        }

    # 4. Liability / Disclaimer query
    if any(k in q_lower for k in ["liability", "warranty", "as is", "indemn", "disclaimer"]):
        cat_name = "Liability"
        evidence = _filter_source_evidence(findings, cat_name, ["liability", "warranty", "as is", "disclaimer", "indemn"])

        external_response = _try_external_provider(query, contract_name, source_code, evidence, risk_score, risk_level)

        if external_response:
            assistant_explanation = external_response
            remediation = "Review liability limitations with regional legal counsel."
        else:
            assistant_explanation = (
                f"Regarding liability provisions in {contract_name}: "
                "Blanket exculpatory disclaimers (e.g., 'provided strictly as is without warranty of any kind; operator accepts no liability') "
                "attempt to exclude all statutory responsibility. Under statutory consumer protection acts across major jurisdictions "
                "(e.g., EU Unfair Contract Terms Directive, US UCC § 2-316), total liability waivers for gross negligence or core contractual "
                "commitments are frequently held unenforceable."
            )
            remediation = "Define clear operational service boundaries and explicit mutual dispute resolution provisions rather than blanket waivers."

        full_answer = f"{assistant_explanation}\n\n**Remediation Recommendation:**\n{remediation}" if not external_response else assistant_explanation

        return {
            "query": query,
            "category": cat_name,
            "scopedContract": contract_name,
            "sourceEvidence": evidence,
            "verifiedFindings": evidence,
            "modelPredictedRisks": model_predicted_risks,
            "assistantGeneratedExplanation": assistant_explanation,
            "modelExplanations": assistant_explanation,
            "remediation": remediation,
            "answer": full_answer,
            "engineType": "external_llm" if external_response else "offline_deterministic_explanation",
            "engineLabel": "Generative AI Explanation (External LLM)" if external_response else "Limited Offline Explanation (Deterministic Analysis)",
            "isGenerativeAi": bool(external_response),
            "relevantClauses": evidence,
            "disclaimer": LEGAL_ASSISTANT_DISCLAIMER,
            "sourceCodeAvailable": bool(source_code)
        }

    # 5. General / Overview query
    cat_name = "General Analysis"
    evidence = findings[:3]

    external_response = _try_external_provider(query, contract_name, source_code, evidence, risk_score, risk_level)

    if external_response:
        assistant_explanation = external_response
    else:
        assistant_explanation = (
            f"Scope Assessment for {contract_name}:\n"
            f"- Overall Risk Score: {risk_score}/100 ({risk_level} Risk)\n"
            f"- Evaluated across 5 core operational legal taxonomies: Privacy, Termination, Legal Compliance, Liability, and Payment / Financial.\n"
            f"- Identified {len(findings)} operational hazard signals.\n\n"
            "You can ask specific questions such as:\n"
            "• 'Explain the termination clause in plain terms'\n"
            "• 'Is this contract GDPR compliant?'\n"
            "• 'How can I fix the unbounded fee modification?'\n"
            "• 'What makes the exculpatory disclaimer problematic under consumer law?'"
        )

    return {
        "query": query,
        "category": cat_name,
        "scopedContract": contract_name,
        "sourceEvidence": evidence,
        "verifiedFindings": evidence,
        "modelPredictedRisks": model_predicted_risks,
        "assistantGeneratedExplanation": assistant_explanation,
        "modelExplanations": assistant_explanation,
        "remediation": "Review the full audit categories and findings in the main dashboard for line-by-line mitigations.",
        "answer": assistant_explanation,
        "engineType": "external_llm" if external_response else "offline_deterministic_explanation",
        "engineLabel": "Generative AI Explanation (External LLM)" if external_response else "Limited Offline Explanation (Deterministic Analysis)",
        "isGenerativeAi": bool(external_response),
        "relevantClauses": evidence,
        "disclaimer": LEGAL_ASSISTANT_DISCLAIMER,
        "sourceCodeAvailable": bool(source_code)
    }
