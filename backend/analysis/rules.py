"""
analysis/rules.py - Deterministic Operational Pattern Rules for Smart Contract Legal-Risk Assessment

Each rule detects operational governance hazards from AST structure and NatSpec,
returning structured findings conforming strictly to ANALYSIS_SPECIFICATION.md.
"""

import re
from typing import List, Dict, Any

CAT_TERMINATION = 'Termination'
CAT_FINANCIAL = 'Payment / Financial'
CAT_PRIVACY = 'Privacy'
CAT_LIABILITY = 'Liability'
CAT_COMPLIANCE = 'Legal Compliance'

SEV_CRITICAL = 'Critical'
SEV_HIGH = 'High'
SEV_MEDIUM = 'Medium'
SEV_LOW = 'Low'

class BaseRule:
    rule_id: str
    category: str
    severity: str
    title: str

    def analyze(self, parsed_data: Dict[str, Any], source_code: str) -> List[Dict[str, Any]]:
        raise NotImplementedError


class UnilateralSelfDestructRule(BaseRule):
    rule_id = "RULE-TERM-01"
    category = CAT_TERMINATION
    severity = SEV_CRITICAL
    title = "Unilateral Contract Termination Capability (selfdestruct)"

    def analyze(self, parsed_data: Dict[str, Any], source_code: str) -> List[Dict[str, Any]]:
        findings = []
        for contract in parsed_data.get("contracts", []):
            for func in contract.get("functions", []):
                raw = func.get("raw_code", "")
                if re.search(r'\b(selfdestruct|suicide)\s*\(', raw):
                    lines = list(range(func["start_line"], func["end_line"] + 1))
                    findings.append({
                        "id": f"{self.rule_id}-{contract['name']}-{func['name']}",
                        "ruleId": self.rule_id,
                        "category": self.category,
                        "severity": self.severity,
                        "title": self.title,
                        "description": (
                            f"Function `{func['name']}` invokes `selfdestruct`. This gives privileged callers "
                            "the operational capability to unilaterally terminate contract execution and extract "
                            "residual balances, conflicting with reciprocal termination and counterparty protection principles."
                        ),
                        "lineNumbers": lines,
                        "snippet": func["raw_code"],
                        "evidenceSource": "ast_pattern",
                        "regulatoryCitation": "Unfair Contract Terms Directive (Directive 93/13/EEC, Annex 1.f)",
                        "recommendation": {
                            "findingId": f"{self.rule_id}-{contract['name']}-{func['name']}",
                            "title": "Deprecate `selfdestruct` in favor of Governance Timelock & Refund Vault",
                            "category": self.category,
                            "severity": self.severity,
                            "beforeCode": func["raw_code"],
                            "afterCode": (
                                f"function initiateDecommission() external onlyTimelock {{\n"
                                f"    require(totalLockedBalance == 0, 'Outstanding deposits remain');\n"
                                f"    isDecommissioned = true;\n"
                                f"    emit ContractDecommissioned(block.timestamp);\n"
                                f"}}"
                            ),
                            "rationale": "Ensures termination cannot unilaterally expropriate funds without counterparty notice and refund settlement."
                        }
                    })
        return findings


class UnconstrainedFeeRule(BaseRule):
    rule_id = "RULE-FIN-01"
    category = CAT_FINANCIAL
    severity = SEV_HIGH
    title = "Unconstrained Fee Escalation Mechanism"

    def analyze(self, parsed_data: Dict[str, Any], source_code: str) -> List[Dict[str, Any]]:
        findings = []
        fee_var_re = re.compile(r'\b([A-Za-z0-9_]*(?:fee|tax|commission|toll|rate)[A-Za-z0-9_]*)\s*=', re.IGNORECASE)
        cap_check_re = re.compile(r'require\s*\([^;]*<\s*=?\s*[^;]*\)', re.IGNORECASE)

        for contract in parsed_data.get("contracts", []):
            for func in contract.get("functions", []):
                # Ignore constructor - initialization is not an ongoing administrative fee hike
                if func.get("name") == "constructor":
                    continue

                raw = func.get("raw_code", "")
                match = fee_var_re.search(raw)
                if match and func.get("mutability") not in ('view', 'pure'):
                    has_cap_check = bool(cap_check_re.search(raw))
                    if not has_cap_check:
                        lines = list(range(func["start_line"], func["end_line"] + 1))
                        findings.append({
                            "id": f"{self.rule_id}-{contract['name']}-{func['name']}",
                            "ruleId": self.rule_id,
                            "category": self.category,
                            "severity": self.severity,
                            "title": self.title,
                            "description": (
                                f"Function `{func['name']}` modifies fee variable `{match.group(1)}` without an explicit "
                                "maximum ceiling check. This grants administrators unchecked discretion to unilaterally increase fees, "
                                "posing consumer protection risk regarding unfair unilateral price modification."
                            ),
                            "lineNumbers": lines,
                            "snippet": func["raw_code"],
                            "evidenceSource": "ast_pattern",
                            "regulatoryCitation": "Consumer Rights Protection Regulations (Unfair Price Increases)",
                            "recommendation": {
                                "findingId": f"{self.rule_id}-{contract['name']}-{func['name']}",
                                "title": "Enforce Immutable Fee Cap Constant in Setter",
                                "category": self.category,
                                "severity": self.severity,
                                "beforeCode": func["raw_code"],
                                "afterCode": (
                                    f"uint256 public constant MAX_FEE_BPS = 500; // 5.00% max\n"
                                    f"function {func['name']}(uint256 newFee) external onlyOwner {{\n"
                                    f"    require(newFee <= MAX_FEE_BPS, 'Fee exceeds permissible ceiling');\n"
                                    f"    {match.group(1)} = newFee;\n"
                                    f"}}"
                                ),
                                "rationale": "Bound administrator price modification authority to statutory fair-trading limits."
                            }
                        })
        return findings


class PlaintextPIIStorageRule(BaseRule):
    rule_id = "RULE-PRIV-01"
    category = CAT_PRIVACY
    severity = SEV_CRITICAL
    title = "High-Risk Plaintext PII State Variable Storage"

    PII_TERMS = ('email', 'phone', 'ssn', 'realname', 'physicaladdress', 'passport', 'nationalid', 'homeaddress')

    def analyze(self, parsed_data: Dict[str, Any], source_code: str) -> List[Dict[str, Any]]:
        findings = []
        for contract in parsed_data.get("contracts", []):
            for var in contract.get("state_variables", []):
                v_name_lower = var["name"].lower()
                v_type = var["type"].lower()
                if any(term in v_name_lower for term in self.PII_TERMS):
                    if ('string' in v_type or 'bytes' in v_type) and not var.get("is_constant"):
                        findings.append({
                            "id": f"{self.rule_id}-{contract['name']}-{var['name']}",
                            "ruleId": self.rule_id,
                            "category": self.category,
                            "severity": self.severity,
                            "title": self.title,
                            "description": (
                                f"State variable `{var['name']}` of type `{var['type']}` stores identifiable personal data "
                                "on public immutable blockchain storage. Because blockchain state cannot be expunged, "
                                "this poses irremediable friction with GDPR Article 17 (Right to Erasure)."
                            ),
                            "lineNumbers": [var["line"]],
                            "snippet": var["raw"],
                            "evidenceSource": "ast_pattern",
                            "regulatoryCitation": "General Data Protection Regulation (GDPR Article 17 - Right to Erasure)",
                            "recommendation": {
                                "findingId": f"{self.rule_id}-{contract['name']}-{var['name']}",
                                "title": "Store Salted Cryptographic Hashes or ZK Commitments On-Chain",
                                "category": self.category,
                                "severity": self.severity,
                                "beforeCode": var["raw"],
                                "afterCode": f"bytes32 public {var['name']}Commitment; // keccak256(data + secret_salt)",
                                "rationale": "Prevents PII leakage on public ledgers while preserving identity verification."
                            }
                        })
        return findings


class BlanketLiabilityDisclaimerRule(BaseRule):
    rule_id = "RULE-LIAB-01"
    category = CAT_LIABILITY
    severity = SEV_MEDIUM
    title = "Broad Liability Disclaimer in Contract Documentation"

    DISCLAIMER_PATTERNS = [
        r'\b(?:as\s+is|without\s+warranty|no\s+liability|at\s+your\s+own\s+risk)\b',
        r'\b(?:hold\s+harmless|sole\s+responsibility|no\s+guarantee)\b'
    ]

    def analyze(self, parsed_data: Dict[str, Any], source_code: str) -> List[Dict[str, Any]]:
        findings = []
        for contract in parsed_data.get("contracts", []):
            natspec = contract.get("natspec", {})
            raw_comment = natspec.get("raw", "")
            for pattern in self.DISCLAIMER_PATTERNS:
                if re.search(pattern, raw_comment, re.IGNORECASE):
                    findings.append({
                        "id": f"{self.rule_id}-{contract['name']}",
                        "ruleId": self.rule_id,
                        "category": self.category,
                        "severity": self.severity,
                        "title": self.title,
                        "description": (
                            f"Contract `{contract['name']}` docstrings contain blanket liability disclaimers. "
                            "In many consumer protection jurisdictions, total disclaimers of liability for operator "
                            "negligence or breach of fundamental obligations are legally invalid and unenforceable."
                        ),
                        "lineNumbers": [contract["start_line"]],
                        "snippet": raw_comment[:200] + ("..." if len(raw_comment) > 200 else ""),
                        "evidenceSource": "heuristic",
                        "regulatoryCitation": "Statutory Standards on Unenforceability of Blanket Liability Exclusions",
                        "recommendation": {
                            "findingId": f"{self.rule_id}-{contract['name']}",
                            "title": "Clarify Scope of Disclaimer and Warranties",
                            "category": self.category,
                            "severity": self.severity,
                            "beforeCode": raw_comment[:150],
                            "afterCode": "/// @notice Operator adheres to published SLA terms with capped liquidated liability.",
                            "rationale": "Replaces unenforceable total waivers with bounded, legally enforceable liability terms."
                        }
                    })
                    break
        return findings


class MissingTimelockRule(BaseRule):
    rule_id = "RULE-GOV-01"
    category = CAT_COMPLIANCE
    severity = SEV_MEDIUM
    title = "Missing Governance Timelock Delay on Privileged Functions"

    def analyze(self, parsed_data: Dict[str, Any], source_code: str) -> List[Dict[str, Any]]:
        findings = []
        for contract in parsed_data.get("contracts", []):
            inheritance = [i.lower() for i in contract.get("inheritance", [])]
            has_timelock = any('timelock' in inh for inh in inheritance)
            if has_timelock:
                continue

            privileged_funcs = [
                f for f in contract.get("functions", [])
                if any(m.lower() in ('onlyowner', 'onlyadmin', 'onlyrole') for m in f.get("modifiers", []))
            ]

            if len(privileged_funcs) >= 3 and not has_timelock:
                findings.append({
                    "id": f"{self.rule_id}-{contract['name']}",
                    "ruleId": self.rule_id,
                    "category": self.category,
                    "severity": self.severity,
                    "title": self.title,
                    "description": (
                        f"Contract `{contract['name']}` possesses {len(privileged_funcs)} privileged administrative functions "
                        "executing immediately without a timelock delay. Participants receive zero advance notice of critical parameter updates."
                    ),
                    "lineNumbers": [contract["start_line"]],
                    "snippet": f"contract {contract['name']} is " + ", ".join(contract.get("inheritance", ["Ownable"])),
                    "evidenceSource": "ast_pattern",
                    "regulatoryCitation": "Consumer Advance Notice & Modification Transparency Standards",
                    "recommendation": {
                        "findingId": f"{self.rule_id}-{contract['name']}",
                        "title": "Route Privileged Operations Through TimelockController",
                        "category": self.category,
                        "severity": self.severity,
                        "beforeCode": f"contract {contract['name']} is Ownable",
                        "afterCode": f"contract {contract['name']} is AccessControl, TimelockController",
                        "rationale": "Guarantees a minimum 48-hour delay for parameter updates, providing participant exit rights."
                    }
                })
        return findings


ACTIVE_RULES = [
    UnilateralSelfDestructRule(),
    UnconstrainedFeeRule(),
    PlaintextPIIStorageRule(),
    BlanketLiabilityDisclaimerRule(),
    MissingTimelockRule(),
]
