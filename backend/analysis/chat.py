"""
analysis/chat.py - Context-Aware Interactive AI Legal Assistant (Phase 6)

Strictly scoped conversational interface evaluating questions solely within
the context of the analyzed smart contract.
"""

from typing import Dict, Any, List


def answer_contract_query(query: str, audit_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Answers user queries strictly scoped to the analyzed contract.
    Extracts relevant context from the contract's code, risk breakdown,
    findings, and compliance matrix.
    """
    q_lower = query.lower().strip()
    contract_name = audit_data.get("contractName") or audit_data.get("name") or "the contract"
    source_code = audit_data.get("solidityCode", "")
    risk_score = audit_data.get("riskScore", 0)
    risk_level = audit.get("riskLevel") or audit_data.get("overallRiskLevel") or "Low" if "audit" in locals() else audit_data.get("overallRiskLevel", "Low")
    categories = audit_data.get("categories", [])
    findings = audit_data.get("findings", [])

    # 1. Termination query
    if any(k in q_lower for k in ["termination", "kill", "destroy", "selfdestruct", "suicide"]):
        has_kill = "selfdestruct" in source_code or "suicide" in source_code
        if has_kill:
            explanation = (
                f"In {contract_name}, an emergency killswitch was detected. "
                "The function invokes the EVM opcode `selfdestruct` (or `suicide`), allowing the contract owner "
                "to unilaterally sweep all deposited Ether and permanently delete bytecode from state storage. "
                "From a contractual fairness perspective, this creates an asymmetric termination right without "
                "prior counterparty notice or timelock safeguards."
            )
            suggestion = (
                "Recommendation: Replace the irreversible selfdestruct instruction with an OpenZeppelin "
                "`Pausable` circuit breaker or transfer funds through a multi-sig timelocked escrow queue."
            )
        else:
            explanation = (
                f"No unilateral termination killswitch (`selfdestruct`) was detected in {contract_name}. "
                "State and balance management adhere to continuous operational execution."
            )
            suggestion = "No termination refactoring required."

        return {
            "query": query,
            "category": "Termination",
            "scopedContract": contract_name,
            "answer": f"{explanation}\n\n{suggestion}",
            "relevantClauses": [f for f in findings if f.get("category") == "Termination"]
        }

    # 2. Privacy / GDPR query
    if any(k in q_lower for k in ["gdpr", "privacy", "pii", "personal", "email", "ccpa"]):
        has_pii = any(k in source_code.lower() for k in ["useremail", "physicaladdress", "ssn", "phone"])
        if has_pii:
            explanation = (
                f"In {contract_name}, plaintext personal data was identified in public storage variables. "
                "Under Article 17 of the General Data Protection Regulation (GDPR) — the statutory 'Right to be Forgotten' "
                "(right to erasure) — data controllers must ensure personal data can be deleted upon request. "
                "Because public blockchain state history is immutable, persisting plaintext personal identity info "
                "conflicts with statutory privacy mandates."
            )
            suggestion = (
                "Recommendation: Do not store plaintext PII on-chain. Store off-chain zero-knowledge commitments, "
                "salted cryptographic hashes (e.g. `keccak256(email, salt)`), or manage identities via decentralized DID resolvers."
            )
        else:
            explanation = (
                f"In {contract_name}, no plaintext natural-person personal identifying information (PII) was detected "
                "in public storage variables or emitted events. Data management relies on cryptographic hashes and addresses, "
                "which aligns with blockchain privacy best practices."
            )
            suggestion = "Maintain standard off-chain storage for any personal identifiers."

        return {
            "query": query,
            "category": "Privacy",
            "scopedContract": contract_name,
            "answer": f"{explanation}\n\n{suggestion}",
            "relevantClauses": [f for f in findings if f.get("category") == "Privacy"]
        }

    # 3. Fee / Payment / Financial query
    if any(k in q_lower for k in ["fee", "tax", "payment", "financial", "rate", "cost"]):
        has_fee = "fee" in source_code.lower() or "tax" in source_code.lower()
        explanation = (
            f"Regarding financial parameters in {contract_name}: "
            "Unconstrained administrative fee or tax setter functions present operational risks where a deployer "
            "can arbitrarily escalate transactional costs up to 100% post-deployment, extracting funds without user recourse. "
            "Under consumer protection law, non-disclosed or unbounded parameter changes may be challenged as unfair contract terms."
        )
        suggestion = "Recommendation: Implement an immutable upper ceiling check (e.g., `require(newFee <= MAX_FEE_CEILING, 'Fee cap exceeded');`)."

        return {
            "query": query,
            "category": "Payment / Financial",
            "scopedContract": contract_name,
            "answer": f"{explanation}\n\n{suggestion}",
            "relevantClauses": [f for f in findings if f.get("category") == "Payment / Financial"]
        }

    # 4. Liability / Disclaimer query
    if any(k in q_lower for k in ["liability", "warranty", "as is", "indemn", "disclaimer"]):
        explanation = (
            f"Regarding liability provisions in {contract_name}: "
            "Blanket exculpatory disclaimers (e.g., 'provided strictly as is without warranty of any kind; operator accepts no liability') "
            "attempt to exclude all statutory responsibility. Under statutory consumer protection acts across major jurisdictions "
            "(e.g., EU Unfair Contract Terms Directive, US UCC § 2-316), total liability waivers for gross negligence or core contractual "
            "commitments are frequently held unenforceable."
        )
        suggestion = "Recommendation: Define clear operational service boundaries and explicit mutual dispute resolution provisions rather than blanket waivers."

        return {
            "query": query,
            "category": "Liability",
            "scopedContract": contract_name,
            "answer": f"{explanation}\n\n{suggestion}",
            "relevantClauses": [f for f in findings if f.get("category") == "Liability"]
        }

    # 5. General / Overview query
    return {
        "query": query,
        "category": "General Analysis",
        "scopedContract": contract_name,
        "answer": (
            f"Scope Assessment for {contract_name}:\n"
            f"- Overall Risk Score: {risk_score}/100 ({risk_level} Risk)\n"
            f"- Evaluated across 5 core operational legal taxonomies: Privacy, Termination, Legal Compliance, Liability, and Payment / Financial.\n"
            f"- Identified {len(findings)} operational hazard signals.\n\n"
            "You can ask specific questions such as:\n"
            "• 'Explain the termination clause in plain terms'\n"
            "• 'Is this contract GDPR compliant?'\n"
            "• 'How can I fix the unbounded fee modification?'\n"
            "• 'What makes the exculpatory disclaimer problematic under consumer law?'"
        ),
        "relevantClauses": findings[:2]
    }
