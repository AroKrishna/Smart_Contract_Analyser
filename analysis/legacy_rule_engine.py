"""
analysis/legacy_rule_engine.py - Isolated Legacy Rule Engine for Benchmark Regression

================================================================================
IMPORTANT ARCHITECTURAL NOTICE:
This module contains the deterministic regex and AST rule engine used EXCLUSIVELY
for baseline regression testing against analysis/data/benchmark/benchmark_manifest.json.

It is STRICTLY ISOLATED from the SaaS platform's active analysis path.
Per project specifications, this rule engine:
- Is NOT the active analysis engine
- Is NOT used as a fallback or substitute for Legal-BERT
- Does NOT produce Legal-BERT predictions
================================================================================
"""

import uuid
import datetime
from typing import Dict, Any, List

from analysis.parser import SolidityParser
from analysis.rules import ACTIVE_RULES, CAT_TERMINATION, CAT_FINANCIAL, CAT_PRIVACY, CAT_LIABILITY, CAT_COMPLIANCE


class LegacyBenchmarkRuleEngine:
    """
    Deterministic rule engine strictly for regression benchmarking against
    benchmark_manifest.json. NOT used in the active SaaS application path.
    """
    VERSION = "0.1.0-legacy-benchmark"

    def __init__(self, rules=None):
        self.rules = rules or ACTIVE_RULES

    def analyze_source(self, source_code: str, contract_name: str = "BenchmarkContract") -> Dict[str, Any]:
        """Runs deterministic AST and NatSpec regex rules for benchmarking."""
        analysis_id = f"benchmark-{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6]}"
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

        parser = SolidityParser(source_code)
        parsed = parser.parse()

        if parsed["status"] in ("empty_input", "malformed_input") or (not parsed["contracts"] and not parsed["pragmas"]):
            return {
                "analysisId": analysis_id,
                "status": "failed",
                "engineType": "legacy_benchmark_rule_engine",
                "error": parsed.get("warnings", ["Invalid source"])
            }

        findings = []
        for rule in self.rules:
            try:
                rule_findings = rule.analyze(parsed, source_code)
                findings.extend(rule_findings)
            except Exception as e:
                parsed["warnings"].append(f"Rule {rule.rule_id} error: {str(e)}")

        risk_breakdown = {
            CAT_TERMINATION: 0,
            CAT_FINANCIAL: 0,
            CAT_PRIVACY: 0,
            CAT_LIABILITY: 0,
            CAT_COMPLIANCE: 0
        }

        sev_weights = {"Critical": 45, "High": 30, "Medium": 15, "Low": 5}
        for f in findings:
            cat = f["category"]
            sev = f["severity"]
            weight = sev_weights.get(sev, 10)
            if cat in risk_breakdown:
                risk_breakdown[cat] = min(100, risk_breakdown[cat] + weight)

        return {
            "analysisId": analysis_id,
            "contractName": contract_name,
            "status": "completed",
            "timestamp": timestamp,
            "findings": findings,
            "riskBreakdown": risk_breakdown,
            "engineType": "legacy_benchmark_rule_engine",
            "disclaimer": "LEGACY BENCHMARK ONLY. Not a Legal-BERT prediction."
        }
