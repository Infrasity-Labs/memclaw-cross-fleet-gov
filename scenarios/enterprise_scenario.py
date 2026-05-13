"""
Enterprise scenario dataset: 5 clients × 3 fleets = 15 memories.

Each client has:
  - 1 org-shared record  (account status, contract value — visible to all agents)
  - 1 sales-private record (negotiation tactics, discount authority — sales only)
  - 1 legal-private record (compliance flags, legal risk — legal only)

Imported by demo/seed_memories.py.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import (
    FLEET_ORG_SHARED, FLEET_SALES, FLEET_LEGAL,
    AGENT_SALES, AGENT_LEGAL,
)

MEMORIES = [
    # ── Client X ─────────────────────────────────────────────────────────────
    {
        "fleet_id": FLEET_ORG_SHARED,
        "agent_id": AGENT_SALES,
        "content": (
            "Client X account status: currently in renewal negotiation. "
            "Contract value $2.4M. Decision expected by end of Q3. "
            "Primary contact: Sarah Chen, VP of Engineering."
        ),
    },
    {
        "fleet_id": FLEET_SALES,
        "agent_id": AGENT_SALES,
        "content": (
            "Client X negotiation tactic: authorized to offer up to 20% discount "
            "if they commit to a 3-year term. Do not disclose discount ceiling upfront. "
            "Champion internally is Sarah Chen; economic buyer is CFO David Park."
        ),
    },
    {
        "fleet_id": FLEET_LEGAL,
        "agent_id": AGENT_LEGAL,
        "content": (
            "Client X compliance flag: GDPR Article 17 right-to-erasure request "
            "pending review. Risk level HIGH. Do not finalize renewal contract "
            "without legal sign-off from compliance team. "
            "Escalation owner: Maria Santos, Senior Counsel."
        ),
    },

    # ── TechCorp Industries ───────────────────────────────────────────────────
    {
        "fleet_id": FLEET_ORG_SHARED,
        "agent_id": AGENT_SALES,
        "content": (
            "TechCorp Industries account status: $5.1M enterprise deal in late-stage "
            "evaluation. Procurement committee review in progress. "
            "Decision timeline: 6-8 weeks. Key stakeholder: CTO James Rivera."
        ),
    },
    {
        "fleet_id": FLEET_SALES,
        "agent_id": AGENT_SALES,
        "content": (
            "TechCorp Industries negotiation tactic: deal blocked at procurement stage "
            "due to security questionnaire backlog. Approved to fast-track security review "
            "if they sign LOI. Authorized discount: up to 15% for 2-year commitment. "
            "NDA already executed. Do not offer professional services credits upfront."
        ),
    },
    {
        "fleet_id": FLEET_LEGAL,
        "agent_id": AGENT_LEGAL,
        "content": (
            "TechCorp Industries legal status: NDA executed 2024-11-03. "
            "Security questionnaire submitted; pending InfoSec sign-off. "
            "Data Processing Agreement (DPA) required before contract execution. "
            "Risk level MEDIUM. No active compliance flags."
        ),
    },

    # ── GlobalBank ────────────────────────────────────────────────────────────
    {
        "fleet_id": FLEET_ORG_SHARED,
        "agent_id": AGENT_SALES,
        "content": (
            "GlobalBank account status: $8.7M financial services contract under "
            "executive review. Regulated entity — all vendor agreements require "
            "compliance pre-clearance. Contact: Head of Procurement, Aditi Sharma."
        ),
    },
    {
        "fleet_id": FLEET_SALES,
        "agent_id": AGENT_SALES,
        "content": (
            "GlobalBank negotiation tactic: price sensitivity low — they prioritize "
            "SLA guarantees and regulatory coverage over cost. Do not lead with discount. "
            "Offer 99.99% uptime SLA and dedicated compliance support package. "
            "Executive sponsor engaged: our CEO met their CRO last quarter."
        ),
    },
    {
        "fleet_id": FLEET_LEGAL,
        "agent_id": AGENT_LEGAL,
        "content": (
            "GlobalBank legal status: GDPR Data Transfer Impact Assessment (DTIA) required "
            "under Chapter V. EU Standard Contractual Clauses (SCCs) must be appended to DPA. "
            "Risk level HIGH — financial regulator audit scheduled Q1 next year. "
            "Do not execute contract without DTIA approval and SCCs in place. "
            "Assigned counsel: external firm Meridian & Partners."
        ),
    },

    # ── RetailCo ──────────────────────────────────────────────────────────────
    {
        "fleet_id": FLEET_ORG_SHARED,
        "agent_id": AGENT_SALES,
        "content": (
            "RetailCo account status: existing customer, $1.2M contract up for renewal. "
            "Strong product satisfaction — NPS 72. Expansion opportunity identified: "
            "adding two new product lines could bring contract to $2.8M. "
            "Decision maker: COO Patricia Huang."
        ),
    },
    {
        "fleet_id": FLEET_SALES,
        "agent_id": AGENT_SALES,
        "content": (
            "RetailCo expansion tactic: upsell pitch approved for Demand Forecasting and "
            "Inventory Intelligence modules. Bundle pricing authorized at $2.8M total "
            "(vs $1.2M renewal-only). Offer 3-year lock-in for 10% additional discount. "
            "Patricia Huang responds well to ROI case studies — prepare retail benchmark report."
        ),
    },
    {
        "fleet_id": FLEET_LEGAL,
        "agent_id": AGENT_LEGAL,
        "content": (
            "RetailCo legal status: no active compliance flags. "
            "Standard MSA in place. Renewal uses existing contract terms — no redlines expected. "
            "PCI DSS scope: RetailCo processes card data; confirm our platform's PCI scope "
            "is addressed in the updated DPA before signing. Risk level LOW."
        ),
    },

    # ── HealthSystem ──────────────────────────────────────────────────────────
    {
        "fleet_id": FLEET_ORG_SHARED,
        "agent_id": AGENT_SALES,
        "content": (
            "HealthSystem account status: $3.6M contract on hold pending compliance review. "
            "Multi-site hospital network, 14 facilities. "
            "Engaged since Q2; technical evaluation complete and positive. "
            "Procurement lead: Director of IT, Marcus Webb."
        ),
    },
    {
        "fleet_id": FLEET_SALES,
        "agent_id": AGENT_SALES,
        "content": (
            "HealthSystem negotiation tactic: contract blocked on compliance — do not push "
            "pricing until legal clears HIPAA BAA. Once cleared, authorized up to 18% discount "
            "for 3-year term given strategic healthcare vertical importance. "
            "Executive sponsor: our VP of Healthcare, Lisa Tran, has direct line to their CISO."
        ),
    },
    {
        "fleet_id": FLEET_LEGAL,
        "agent_id": AGENT_LEGAL,
        "content": (
            "HealthSystem — COMPLIANCE HOLD ACTIVE. "
            "HIPAA Business Associate Agreement (BAA) not yet executed. "
            "CONTRACT EXECUTION BLOCKED. Do not allow the sales team to proceed with "
            "any contract signing or system access provisioning until BAA is fully "
            "executed and countersigned by both parties. "
            "SOC 2 Type II report available but withheld pending NDA execution. "
            "Risk level HIGH — PHI (Protected Health Information) in scope. "
            "Estimated BAA turnaround: 3 weeks from legal review start. "
            "Assigned counsel: internal privacy team. Escalation owner: Chief Privacy Officer."
        ),
    },
]

DEDUP_QUERIES = [
    # Client X
    "Client X account status renewal negotiation",
    "Client X negotiation tactic discount ceiling",
    "Client X GDPR Article 17 erasure request",
    # TechCorp
    "TechCorp Industries enterprise deal procurement",
    "TechCorp negotiation tactic security review LOI",
    "TechCorp legal NDA DPA security questionnaire",
    # GlobalBank
    "GlobalBank financial services contract compliance",
    "GlobalBank negotiation SLA regulatory coverage",
    "GlobalBank GDPR DTIA Standard Contractual Clauses",
    # RetailCo
    "RetailCo renewal upsell expansion opportunity",
    "RetailCo upsell Demand Forecasting bundle pricing",
    "RetailCo legal PCI DSS DPA renewal",
    # HealthSystem
    "HealthSystem contract hold compliance HIPAA",
    "HealthSystem negotiation BAA discount healthcare",
    "HealthSystem HIPAA BAA SOC 2 PHI legal review",
]
