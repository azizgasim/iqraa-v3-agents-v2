"""
AGT-01 LLM Mode: Smart claim extraction using LLM
Falls back to rule-based if LLM unavailable or budget exhausted
"""
from __future__ import annotations
import json
from typing import Any, Optional
from core.base_agent import BaseAgent, AgentCard, AgentResult
from core.models import TextSpan, Evidence, Claim, AutonomyLevel, RiskTier
from core.run_context import UnifiedRunContext
from core.canonical_policy import canonicalize, text_hash, make_canonical_span, CanonicalPolicy
from core.llm_client import UnifiedLLMClient, get_llm_client, LLMResponse

EXTRACTION_PROMPT = """أنت محلل نصوص إسلامية متخصص. حلل النص التالي واستخرج الادعاءات (claims) الرئيسية.
لكل ادعاء حدد:
1. نص الادعاء
2. موقع البداية في النص الأصلي (char_start)
3. موقع النهاية (char_end)
4. درجة الثقة (0.0-1.0)
5. نوع الادعاء: factual/interpretive/attribution

أجب بـ JSON فقط بالشكل:
{"claims": [{"text": "...", "start": 0, "end": 10, "confidence": 0.8, "type": "factual"}]}

النص:
{text}
"""

def _build_card() -> AgentCard:
    return AgentCard(
        agent_id="AGT-01",
        name="Text Analysis Agent (LLM)",
        name_ar="وكيل التحليل النصي الذكي",
        version="2.1.0",
        description="LLM-powered claim extraction with rule-based fallback",
        category="extract",
        autonomy_level=AutonomyLevel.L1_SUGGEST,
        risk_tier=RiskTier.MEDIUM,
        operations=["extract_claims_llm", "extract_claims_rules"],
        non_use_cases=["entity_linking"],
        owner="iqraa-12",
    )

class SmartTextAnalysisAgent(BaseAgent):
    def __init__(self, use_llm: bool = True, model: str = "gemini-2.0-flash"):
        super().__init__(_build_card())
        self.policy = CanonicalPolicy()
        self.use_llm = use_llm
        self.model = model
        self.llm = get_llm_client(model) if use_llm else None

    async def perceive(self, params: dict[str, Any]) -> dict[str, Any]:
        raw_text = params.get("text", "")
        source_id = params.get("source_id", "unknown")
        if not raw_text.strip():
            raise ValueError("AGT-01: empty text")
        canonical = canonicalize(raw_text, self.policy)
        return {"raw_text": raw_text, "canonical_text": canonical, "source_id": source_id, "source_hash": text_hash(canonical)}

    async def think(self, perceived: dict, run_ctx: UnifiedRunContext) -> dict[str, Any]:
        run_ctx.register_source(perceived["source_id"], perceived["source_hash"])
        mode = "llm" if self.use_llm and self.llm and not run_ctx.budget.is_exhausted else "rules"
        return {**perceived, "mode": mode}

    async def act(self, plan: dict, run_ctx: UnifiedRunContext) -> dict[str, Any]:
        if plan["mode"] == "llm":
            return await self._act_llm(plan, run_ctx)
        return self._act_rules(plan, run_ctx)

    async def _act_llm(self, plan: dict, run_ctx: UnifiedRunContext) -> dict[str, Any]:
        prompt = EXTRACTION_PROMPT.replace("{text}", plan["raw_text"])
        resp = await self.llm.complete(prompt=prompt, system="Extract claims as JSON only.", budget=run_ctx.budget, model=self.model)
        if not resp.success:
            return self._act_rules(plan, run_ctx)
        try:
            text = resp.text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0]
            data = json.loads(text)
            raw_claims = data.get("claims", [])
        except (json.JSONDecodeError, KeyError):
            return self._act_rules(plan, run_ctx)
        evidences = []
        claims = []
        for i, rc in enumerate(raw_claims):
            span_data = make_canonical_span(plan["raw_text"], plan["source_id"], rc.get("start",0), rc.get("end",len(plan["raw_text"])), self.policy)
            span = TextSpan(doc_id=plan["source_id"], char_start=span_data["canonical_start"], char_end=span_data["canonical_end"], text=span_data["text_canonical"], context=span_data["text_raw"])
            ev = Evidence(spans=[span], confidence=rc.get("confidence",0.7), source_ref=f'{plan["source_id"]}#llm_{i}')
            evidences.append(ev)
            claims.append(Claim(text=rc.get("text", span_data["text_canonical"]), evidence_ids=[ev.evidence_id], confidence=rc.get("confidence",0.7), scope={"type": rc.get("type","unknown"), "method": "llm"}))
        return {"output": {"claims_count": len(claims), "claims": [c.model_dump() for c in claims], "method": "llm", "llm_cost": resp.cost_usd}, "evidence": evidences, "cost_usd": resp.cost_usd}

    def _act_rules(self, plan: dict, run_ctx: UnifiedRunContext) -> dict[str, Any]:
        from agents.agt01_text_analysis import TextAnalysisAgent
        import asyncio
        fallback = TextAnalysisAgent()
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(fallback.run(run_ctx, {"text": plan["raw_text"], "source_id": plan["source_id"]}))
        return {"output": {**result.output, "method": "rules"}, "evidence": result.evidence, "cost_usd": 0.0}
