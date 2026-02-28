"""
AGT-02: Entity Linking Agent — وكيل ربط الكيانات
===================================================
يستقبل claims مع evidence → يستخرج الكيانات (أشخاص، أماكن، كتب، مفاهيم)
ويربطها بمعرّفات فريدة.

المبادئ:
- لا ربط كيانات بلا Suggest > Approve
- كل كيان يحمل type + confidence + source spans
- Suggest فقط في L1، الربط النهائي يحتاج موافقة
"""
from __future__ import annotations

import re
from typing import Any, Optional
from core.base_agent import BaseAgent, AgentCard, AgentResult
from core.models import TextSpan, Evidence, AutonomyLevel, RiskTier
from core.run_context import UnifiedRunContext
from core.canonical_policy import canonicalize, CanonicalPolicy


class EntityType:
    PERSON = "person"
    PLACE = "place"
    BOOK = "book"
    CONCEPT = "concept"
    EVENT = "event"
    TERM = "term"


class EntityMention:
    def __init__(self, text: str, entity_type: str, confidence: float,
                 canonical_start: int, canonical_end: int, source_id: str,
                 suggested_id: Optional[str] = None):
        self.text = text
        self.entity_type = entity_type
        self.confidence = confidence
        self.canonical_start = canonical_start
        self.canonical_end = canonical_end
        self.source_id = source_id
        self.suggested_id = suggested_id
        self.approved = False

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "entity_type": self.entity_type,
            "confidence": self.confidence,
            "canonical_start": self.canonical_start,
            "canonical_end": self.canonical_end,
            "source_id": self.source_id,
            "suggested_id": self.suggested_id,
            "approved": self.approved,
        }


# Rule-based Arabic entity patterns (expandable with LLM later)
PERSON_PATTERNS = [
    r"(?:ابن|أبو|أبي)\s+\w+",
    r"(?:الإمام|الشيخ|العلامة|الحافظ)\s+\w+",
]
BOOK_PATTERNS = [
    r"(?:كتاب|المقدمة|الرسالة|المختصر|الموطأ|الصحيح)",
]
CONCEPT_PATTERNS = [
    r"(?:العمران|الاجتماع|العصبية|الملك|الخلافة|الحضارة)",
]


def _build_card() -> AgentCard:
    return AgentCard(
        agent_id="AGT-02",
        name="Entity Linking Agent",
        name_ar="وكيل ربط الكيانات",
        version="2.0.0",
        description="Extracts and links named entities from Arabic text with Suggest-Approve pattern",
        category="link",
        autonomy_level=AutonomyLevel.L1_SUGGEST,
        risk_tier=RiskTier.MEDIUM,
        operations=["extract_entities", "suggest_links"],
        non_use_cases=["text_analysis", "verification"],
        owner="iqraa-12",
    )


class EntityLinkingAgent(BaseAgent):
    """AGT-02: يستخرج الكيانات ويقترح ربطها — Suggest فقط"""

    def __init__(self):
        super().__init__(_build_card())
        self.policy = CanonicalPolicy()

    async def perceive(self, params: dict[str, Any]) -> dict[str, Any]:
        text = params.get("text", "")
        source_id = params.get("source_id", "unknown")
        if not text.strip():
            raise ValueError("AGT-02: empty text input")
        canonical_text = canonicalize(text, self.policy)
        return {
            "raw_text": text,
            "canonical_text": canonical_text,
            "source_id": source_id,
        }

    async def think(self, perceived: dict, run_ctx: UnifiedRunContext) -> dict[str, Any]:
        return {
            "canonical_text": perceived["canonical_text"],
            "source_id": perceived["source_id"],
            "patterns": {
                EntityType.PERSON: PERSON_PATTERNS,
                EntityType.BOOK: BOOK_PATTERNS,
                EntityType.CONCEPT: CONCEPT_PATTERNS,
            },
        }

    async def act(self, plan: dict, run_ctx: UnifiedRunContext) -> dict[str, Any]:
        mentions = []
        text = plan["canonical_text"]
        source_id = plan["source_id"]

        for etype, patterns in plan["patterns"].items():
            for pattern in patterns:
                for match in re.finditer(pattern, text):
                    mention = EntityMention(
                        text=match.group(),
                        entity_type=etype,
                        confidence=0.6,
                        canonical_start=match.start(),
                        canonical_end=match.end(),
                        source_id=source_id,
                        suggested_id=f"ent_{etype}_{match.group()[:10]}",
                    )
                    mentions.append(mention)

        run_ctx.record_audit("entities_extracted", "AGT-02", {
            "count": len(mentions),
            "types": list(set(m.entity_type for m in mentions)),
        })

        return {
            "output": {
                "entity_count": len(mentions),
                "entities": [m.to_dict() for m in mentions],
                "all_suggested": True,
                "none_approved": True,
            },
            "evidence": [],
            "cost_usd": 0.0,
        }
