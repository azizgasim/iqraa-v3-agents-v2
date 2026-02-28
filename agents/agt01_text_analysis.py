"""
AGT-01: Text Analysis Agent — وكيل التحليل النصي
==================================================
Thin Slice: يستقبل نصاً عربياً → يستخرج Claims مع Evidence + Canonical offsets

المبادئ:
- لا claim بلا evidence
- لا evidence بلا offsets + canonical policy
- كل span يحمل raw + canonical forms
"""
from __future__ import annotations

from typing import Any, Optional
from core.base_agent import BaseAgent, AgentCard, AgentResult
from core.models import TextSpan, Evidence, Claim, AutonomyLevel, RiskTier
from core.run_context import UnifiedRunContext
from core.canonical_policy import (
    canonicalize, text_hash, make_canonical_span, CanonicalPolicy
)


def _build_card() -> AgentCard:
    return AgentCard(
        agent_id="AGT-01",
        name="Text Analysis Agent",
        name_ar="وكيل التحليل النصي",
        version="2.0.0",
        description="Extracts claims with evidence spans from Arabic text using canonical offsets",
        category="extract",
        autonomy_level=AutonomyLevel.L1_SUGGEST,
        risk_tier=RiskTier.MEDIUM,
        operations=["extract_claims", "extract_spans"],
        non_use_cases=["entity_linking", "cross_ref_verification"],
        owner="iqraa-12",
    )


class TextAnalysisAgent(BaseAgent):
    """AGT-01: يحلل النص العربي ويستخرج ادعاءات مع أدلة موثقة بـ offsets"""

    def __init__(self):
        super().__init__(_build_card())
        self.policy = CanonicalPolicy()

    async def perceive(self, params: dict[str, Any]) -> dict[str, Any]:
        raw_text = params.get("text", "")
        source_id = params.get("source_id", "unknown")
        if not raw_text.strip():
            raise ValueError("AGT-01: empty text input")
        canonical_text = canonicalize(raw_text, self.policy)
        source_hash = text_hash(canonical_text)
        return {
            "raw_text": raw_text,
            "canonical_text": canonical_text,
            "source_id": source_id,
            "source_hash": source_hash,
            "char_count_raw": len(raw_text),
            "char_count_canonical": len(canonical_text),
        }

    async def think(self, perceived: dict, run_ctx: UnifiedRunContext) -> dict[str, Any]:
        run_ctx.register_source(perceived["source_id"], perceived["source_hash"])
        sentences = self._split_sentences(perceived["raw_text"])
        plan = {
            "sentences": sentences,
            "source_id": perceived["source_id"],
            "raw_text": perceived["raw_text"],
            "canonical_text": perceived["canonical_text"],
            "strategy": "sentence_level_extraction",
        }
        return plan

    async def act(self, plan: dict, run_ctx: UnifiedRunContext) -> dict[str, Any]:
        evidences = []
        claims = []
        for i, sent in enumerate(plan["sentences"]):
            if not sent["text"].strip():
                continue
            span_data = make_canonical_span(
                raw_text=plan["raw_text"],
                source_id=plan["source_id"],
                raw_start=sent["start"],
                raw_end=sent["end"],
                policy=self.policy,
            )
            span = TextSpan(
                doc_id=plan["source_id"],
                char_start=span_data["canonical_start"],
                char_end=span_data["canonical_end"],
                text=span_data["text_canonical"],
                context=span_data["text_raw"],
            )
            ev = Evidence(
                spans=[span],
                confidence=0.7,
                source_ref=f'{plan["source_id"]}#sent_{i}',
            )
            evidences.append(ev)
            claim = Claim(
                text=span_data["text_canonical"],
                evidence_ids=[ev.evidence_id],
                confidence=0.7,
            )
            claims.append(claim)

        return {
            "output": {
                "claims_count": len(claims),
                "evidence_count": len(evidences),
                "claims": [c.model_dump() for c in claims],
            },
            "evidence": evidences,
            "cost_usd": 0.0,
        }

    def _split_sentences(self, text: str) -> list[dict]:
        separators = [".", "۔", "؟", "!", "\n"]
        sentences = []
        current_start = 0
        for i, ch in enumerate(text):
            if ch in ".۔؟!\n" or (i == len(text) - 1):
                end = i + 1
                seg = text[current_start:end].strip()
                if seg:
                    real_start = text.index(seg, current_start)
                    sentences.append({
                        "text": seg,
                        "start": real_start,
                        "end": real_start + len(seg),
                        "index": len(sentences),
                    })
                current_start = end
        if not sentences and text.strip():
            sentences.append({"text": text.strip(), "start": 0, "end": len(text.strip()), "index": 0})
        return sentences
