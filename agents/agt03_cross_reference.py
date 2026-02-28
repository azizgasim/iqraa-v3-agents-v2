"""
AGT-03: Cross-Reference Agent — وكيل المراجع التقاطعية
========================================================
يستقبل claims من مصادر متعددة → يبحث عن تقاطعات وتأييدات وتناقضات.

Thin Slice: مقارنة بسيطة بالتطابق النصي (canonical).
التوسع: semantic similarity عبر embeddings.
"""
from __future__ import annotations

from typing import Any
from core.base_agent import BaseAgent, AgentCard, AgentResult
from core.models import TextSpan, Evidence, Claim, AutonomyLevel, RiskTier
from core.run_context import UnifiedRunContext
from core.canonical_policy import canonicalize, CanonicalPolicy


def _build_card() -> AgentCard:
    return AgentCard(
        agent_id="AGT-03",
        name="Cross-Reference Agent",
        name_ar="وكيل المراجع التقاطعية",
        version="2.0.0",
        description="Finds cross-references, corroborations, and contradictions across sources",
        category="trace",
        autonomy_level=AutonomyLevel.L1_SUGGEST,
        risk_tier=RiskTier.HIGH,
        operations=["find_cross_refs", "detect_corroboration", "detect_contradiction"],
        non_use_cases=["text_extraction", "entity_linking"],
        owner="iqraa-12",
    )


class CrossRefResult:
    def __init__(self, claim_a_idx: int, claim_b_idx: int, 
                 relation: str, overlap_score: float, shared_terms: list[str]):
        self.claim_a_idx = claim_a_idx
        self.claim_b_idx = claim_b_idx
        self.relation = relation
        self.overlap_score = overlap_score
        self.shared_terms = shared_terms

    def to_dict(self) -> dict:
        return {
            "claim_a": self.claim_a_idx,
            "claim_b": self.claim_b_idx,
            "relation": self.relation,
            "overlap_score": self.overlap_score,
            "shared_terms": self.shared_terms,
        }


class CrossReferenceAgent(BaseAgent):
    """AGT-03: يبحث عن تقاطعات بين claims من مصادر مختلفة"""

    def __init__(self):
        super().__init__(_build_card())
        self.policy = CanonicalPolicy()

    async def perceive(self, params: dict[str, Any]) -> dict[str, Any]:
        claims_a = params.get("claims_a", [])
        claims_b = params.get("claims_b", [])
        if not claims_a or not claims_b:
            raise ValueError("AGT-03: needs claims from at least 2 sources")
        return {"claims_a": claims_a, "claims_b": claims_b}

    async def think(self, perceived: dict, run_ctx: UnifiedRunContext) -> dict[str, Any]:
        return {
            "claims_a": perceived["claims_a"],
            "claims_b": perceived["claims_b"],
            "method": "term_overlap",
            "threshold": 0.3,
        }

    async def act(self, plan: dict, run_ctx: UnifiedRunContext) -> dict[str, Any]:
        cross_refs = []
        for i, ca in enumerate(plan["claims_a"]):
            text_a = ca.get("text", "") if isinstance(ca, dict) else ca.text
            terms_a = set(self._extract_terms(text_a))
            for j, cb in enumerate(plan["claims_b"]):
                text_b = cb.get("text", "") if isinstance(cb, dict) else cb.text
                terms_b = set(self._extract_terms(text_b))
                shared = terms_a & terms_b
                if not terms_a or not terms_b:
                    continue
                overlap = len(shared) / max(len(terms_a), len(terms_b))
                if overlap >= plan["threshold"]:
                    relation = "corroboration" if overlap > 0.5 else "partial_overlap"
                    cross_refs.append(CrossRefResult(
                        claim_a_idx=i, claim_b_idx=j,
                        relation=relation, overlap_score=round(overlap, 3),
                        shared_terms=list(shared),
                    ))

        run_ctx.record_audit("cross_ref_complete", "AGT-03", {
            "pairs_checked": len(plan["claims_a"]) * len(plan["claims_b"]),
            "refs_found": len(cross_refs),
        })

        return {
            "output": {
                "cross_ref_count": len(cross_refs),
                "cross_refs": [r.to_dict() for r in cross_refs],
            },
            "evidence": [],
            "cost_usd": 0.0,
        }

    def _extract_terms(self, text: str) -> list[str]:
        canonical = canonicalize(text, self.policy)
        stop_words = {"في", "من", "الى", "على", "عن", "ان", "لا", "ما", "هو", "هي", "كل", "بل", "او", "اذا", "لم", "قد", "بد", "له", "بها"}
        terms = [w for w in canonical.split() if len(w) > 2 and w not in stop_words]
        return terms
