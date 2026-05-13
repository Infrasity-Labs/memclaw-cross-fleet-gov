"""
Structural conflict detector for the Admin Agent.

Performs deterministic keyword pattern matching against fleet memory content
retrieved from fleet-sales and fleet-legal. No LLM required — findings are
reproducible and testable.

Rules are loaded from policies/governance_rules.yaml.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from runtime.policy_loader import PolicyLoader

_REPO_ROOT = os.path.join(os.path.dirname(__file__), "..")

FLEET_SALES = "fleet-sales"
FLEET_LEGAL = "fleet-legal"

_SEVERITY_LABELS = {"HIGH": "[HIGH]", "MEDIUM": "[MED]", "LOW": "[LOW]"}


class ConflictDetector:
    """Keyword-based governance conflict detector loaded from YAML rules."""

    def __init__(self, rules_path: str = "policies/governance_rules.yaml"):
        resolved = os.path.normpath(os.path.join(_REPO_ROOT, rules_path))
        policy = PolicyLoader.load(resolved)
        self._rules = policy.get("rules", [])

    def detect(self, memories_by_fleet: dict) -> list:
        """Scan fleet memories for governance conflicts.

        Returns a list of finding dicts. Returns [] when either private fleet
        is absent — safe to call for non-Admin agents.
        """
        sales_texts = memories_by_fleet.get(FLEET_SALES, [])
        legal_texts = memories_by_fleet.get(FLEET_LEGAL, [])

        if not sales_texts or not legal_texts:
            return []

        sales_text = " ".join(sales_texts).lower()
        legal_text = " ".join(legal_texts).lower()

        findings = []
        for rule in self._rules:
            sales_patterns = rule.get("sales_signal_patterns", [])
            legal_patterns = rule.get("legal_signal_patterns", [])

            sales_match = next((p for p in sales_patterns if p in sales_text), None)
            legal_match = next((p for p in legal_patterns if p in legal_text), None)

            if sales_match and legal_match:
                findings.append({
                    "rule_id": rule["rule_id"],
                    "description": rule["description"],
                    "severity": rule["severity"],
                    "sales_signal": sales_match,
                    "legal_signal": legal_match,
                })

        return findings

    def format_findings(self, findings: list) -> str:
        if not findings:
            return "No governance conflicts detected."
        lines = [f"GOVERNANCE CONFLICT — {len(findings)} rule(s) triggered:"]
        for f in findings:
            label = _SEVERITY_LABELS.get(f["severity"], "[?]")
            lines.append(f"  {label} {f['rule_id']}: {f['description']}")
            lines.append(f"       Sales signal : '{f['sales_signal']}'")
            lines.append(f"       Legal signal : '{f['legal_signal']}'")
        return "\n".join(lines)
