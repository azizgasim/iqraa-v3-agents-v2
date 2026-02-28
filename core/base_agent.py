"""
IQRA-12 BaseAgent v2 — Brain-Perception-Action Pattern
كل وكيل = إدراك → دماغ → فعل
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4
from pydantic import BaseModel, Field
from .models import (
    AutonomyLevel, RiskTier,
    OperationInput, OperationOutput, Evidence
)
from .run_context import UnifiedRunContext

class AgentCard(BaseModel):
    """بطاقة تعريف إجبارية — ناقصة = خفض استقلالية"""
    agent_id: str
    name: str
    name_ar: str
    version: str = "2.0.0"
    description: str
    category: str
    autonomy_level: AutonomyLevel = AutonomyLevel.L1_SUGGEST
    risk_tier: RiskTier = RiskTier.MEDIUM
    operations: list[str] = []
    non_use_cases: list[str] = []
    owner: str = "iqraa-12"

class AgentResult(BaseModel):
    """نتيجة موحدة لكل وكيل"""
    agent_id: str
    run_id: str
    success: bool
    output: dict[str, Any] = {}
    evidence: list[Evidence] = []
    cost_usd: float = 0.0
    duration_ms: int = 0
    errors: list[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

class BaseAgent(ABC):
    """الوكيل الأساسي — كل وكيل يرث من هنا"""

    def __init__(self, card: AgentCard):
        self.card = card
        self._validate_card()

    def _validate_card(self):
        """بطاقة ناقصة = خفض الاستقلالية تلقائياً"""
        if not self.card.description or not self.card.operations:
            self.card.autonomy_level = AutonomyLevel.L0_READ

    async def run(self, run_ctx: UnifiedRunContext, params: dict[str, Any] = {}) -> AgentResult:
        """التنفيذ الرئيسي: إدراك → دماغ → فعل"""
        start = datetime.utcnow()
        try:
            # 1. إدراك (Perception)
            perceived = await self.perceive(params)
            # 2. دماغ (Brain) — تخطيط + تفكير + قرار
            plan = await self.think(perceived, run_ctx)
            # 3. فعل (Action)
            result = await self.act(plan, run_ctx)
            elapsed = int((datetime.utcnow() - start).total_seconds() * 1000)
            return AgentResult(
                agent_id=self.card.agent_id,
                run_id=run_ctx.run_id,
                success=True,
                output=result.get("output", {}),
                evidence=result.get("evidence", []),
                cost_usd=result.get("cost_usd", 0.0),
                duration_ms=elapsed,
            )
        except Exception as e:
            elapsed = int((datetime.utcnow() - start).total_seconds() * 1000)
            return AgentResult(
                agent_id=self.card.agent_id,
                run_id=run_ctx.run_id,
                success=False,
                errors=[str(e)],
                duration_ms=elapsed,
            )

    @abstractmethod
    async def perceive(self, params: dict[str, Any]) -> dict[str, Any]:
        """إدراك المدخلات وتحويلها لبنية داخلية"""
        ...

    @abstractmethod
    async def think(self, perceived: dict, run_ctx: UnifiedRunContext) -> dict[str, Any]:
        """التخطيط والتفكير واتخاذ القرار"""
        ...

    @abstractmethod
    async def act(self, plan: dict, run_ctx: UnifiedRunContext) -> dict[str, Any]:
        """تنفيذ الخطة وإنتاج المخرجات"""
        ...
