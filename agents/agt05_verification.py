"""
AGT-05: Verification Agent — وكيل التحقق
==========================================
Thin Slice: يستقبل claims + evidence → يتحقق من:
1. صحة الربط (claim ↔ evidence)
2. صحة الـ offsets (canonical_start/end ضمن النص)
3. تطابق النص المقتبس مع المصدر

لا يستخدم LLM في هذه المرحلة — تحقق قاعدي rule-based.
"""
from __future__ import annotations
from typing import Any
from core.base_agent import BaseAgent, AgentCard, AgentResult
from core.models import TextSpan, Evidence, Claim, AutonomyLevel, RiskTier
from core.run_context import UnifiedRunContext
from core.canonical_policy import canonicalize, CanonicalPolicy


def _build_card() -> AgentCard:
    return AgentCard(
        agent_id="AGT-05",
        name="Verification Agent",
        name_ar="وكيل التحقق",
        version="2.0.0",
        description="Verifies claim-evidence linkage and offset integrity",
        category="verify",
        autonomy_level=AutonomyLevel.L1_SUGGEST,
        risk_tier=RiskTier.HIGH,
        operations=["verify_offsets", "verify_linkage", "verify_canonical"],
        non_use_cases=["text_extraction", "entity_linking"],
        owner="iqraa-12",
    )


class VerificationAgent(BaseAgent):
    """AGT-05: يتحقق من سلامة الأدلة والربط"""

    def __init__(self):
        super().__init__(_build_card())
        self.policy = CanonicalPolicy()

    async def perceive(self, params: dict[str, Any]) -> dict[str, Any]:
        claims = params.get("claims", [])
        evidences = params.get("evidences", [])
        canonical_text = params.get("canonical_text", "")
        source_id = params.get("source_id", "unknown")
        if not claims:
            raise ValueError("AGT-05: no claims to verify")
        return {
            "claims": claims,
            "evidences": evidences,
            "canonical_text": canonical_text,
            "source_id": source_id,
        }

    async def think(self, perceived: dict, run_ctx: UnifiedRunContext) -> dict[str, Any]:
        ev_map = {}
        for ev in perceived["evidences"]:
            if isinstance(ev, Evidence):
                ev_map[ev.evidence_id] = ev
            elif isinstance(ev, dict):
                ev_map[ev.get("evidence_id", "")] = ev
        return {
            "claims": perceived["claims"],
            "ev_map": ev_map,
            "canonical_text": perceived["canonical_text"],
            "source_id": perceived["source_id"],
            "checks": ["linkage", "offsets", "text_match"],
        }

    async def act(self, plan: dict, run_ctx: UnifiedRunContext) -> dict[str, Any]:
        results = []
        all_passed = True
        for i, claim_data in enumerate(plan["claims"]):
            if isinstance(claim_data, dict):
                ev_ids = claim_data.get("evidence_ids", [])
                claim_text = claim_data.get("text", "")
            else:
                ev_ids = claim_data.evidence_ids
                claim_text = claim_data.text

            check = {"claim_index": i, "claim_text": claim_text[:50], "issues": [], "passed": True}

            # Check 1: linkage
            for eid in ev_ids:
                if eid not in plan["ev_map"]:
                    check["issues"].append(f"evidence {eid} not found")
                    check["passed"] = False

            # Check 2: offset validity
            for eid in ev_ids:
                ev = plan["ev_map"].get(eid)
                if ev is None:
                    continue
                spans = ev.spans if isinstance(ev, Evidence) else ev.get("spans", [])
                for sp in spans:
                    if isinstance(sp, TextSpan):
                        cs, ce, txt = sp.char_start, sp.char_end, sp.text
                    else:
                        cs, ce, txt = sp.get("char_start", -1), sp.get("char_end", -1), sp.get("text", "")
                    if cs < 0 or ce <= cs:
                        check["issues"].append(f"invalid offsets [{cs}:{ce}]")
                        check["passed"] = False
                    # Check 3: text match against canonical
                    if plan["canonical_text"] and cs >= 0 and ce > cs:
                        expected = plan["canonical_text"][cs:ce]
                        if expected != txt:
                            check["issues"].append(f"text mismatch at [{cs}:{ce}]")
                            check["passed"] = False

            if not check["passed"]:
                all_passed = False
            results.append(check)

        verified_count = sum(1 for r in results if r["passed"])
        run_ctx.record_audit("verification_complete", "AGT-05", {
            "total": len(results), "verified": verified_count, "all_passed": all_passed
        })

        return {
            "output": {
                "all_passed": all_passed,
                "total_claims": len(results),
                "verified_count": verified_count,
                "results": results,
            },
            "evidence": [],
            "cost_usd": 0.0,
        }
