"""
tests/test_legacy_benchmark_rules.py - Tests for Isolated Legacy Benchmark Rule Engine

Verifies that the legacy deterministic rule engine remains available strictly for
regression benchmarking against benchmark_manifest.json without polluting the active
Legal-BERT analysis path.
"""

import json
import os
import pytest
from analysis.legacy_rule_engine import LegacyBenchmarkRuleEngine
from analysis.rules import ACTIVE_RULES

CONTRACTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "analysis", "data", "contracts")


def test_legacy_benchmark_rule_engine_isolation():
    """Verify legacy engine explicitly identifies itself as benchmark-only."""
    engine = LegacyBenchmarkRuleEngine()
    assert engine.VERSION == "0.1.0-legacy-benchmark"

    # Test BM001
    bm001_path = os.path.join(CONTRACTS_DIR, "BM001_VulnerableEscrow.sol")
    if os.path.exists(bm001_path):
        with open(bm001_path, "r", encoding="utf-8") as f:
            code = f.read()
        res = engine.analyze_source(code, "BM001_VulnerableEscrow.sol")
        assert res["status"] == "completed"
        assert res["engineType"] == "legacy_benchmark_rule_engine"
        assert "LEGACY BENCHMARK ONLY" in res["disclaimer"]

        # Check that selfdestruct was flagged by benchmark rules
        rule_ids = [f["ruleId"] for f in res["findings"]]
        assert "RULE-TERM-01" in rule_ids
