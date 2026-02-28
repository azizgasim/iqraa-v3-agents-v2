"""
IQRAA V2 — Unified Run Context
================================
دمج RunContext (v2) + ExecutionContext (G4) في سياق واحد.
المبدأ: لا تشغيل بلا run_id + recipe + budget
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from .canonical_policy import POLICY_VERSION


class BudgetEnvelope(BaseModel):
    max_tokens: int = 50_000
    max_tool_calls: int = 50
    max_wall_ms: int = 120_000
    max_usd: float = 1.0
    used_tokens: int = 0
    used_tool_calls: int = 0
    used_wall_ms: int = 0
    used_usd: float = 0.0

    @property
    def usd_remaining(self) -> float:
        return max(0.0, self.max_usd - self.used_usd)

    @property
    def is_exhausted(self) -> bool:
        return self.used_usd >= self.max_usd or self.used_tokens >= self.max_tokens

    def record_cost(self, tokens: int = 0, usd: float = 0.0, tool_calls: int = 0, wall_ms: int = 0):
        self.used_tokens += tokens
        self.used_usd += usd
        self.used_tool_calls += tool_calls
        self.used_wall_ms += wall_ms


class UnifiedRunContext(BaseModel):
    run_id: str = Field(default_factory=lambda: f"run_{uuid4().hex[:12]}")
    project_id: str = "iqraa-12"
    user_id: str = "researcher"
    recipe_id: Optional[str] = None
    started_at: datetime = Field(default_factory=datetime.utcnow)
    session_id: str = Field(default_factory=lambda: uuid4().hex[:16])
    task_id: str = Field(default_factory=lambda: uuid4().hex[:12])
    actor_agent_id: str = "unknown-agent"
    actor_role: str = "unknown-role"
    permissions: list[str] = Field(default_factory=list)
    budget: BudgetEnvelope = Field(default_factory=BudgetEnvelope)
    mode: str = "standard"
    canonical_policy_version: str = POLICY_VERSION
    source_hashes: dict[str, str] = Field(default_factory=dict)
    gate_decisions: list[dict[str, Any]] = Field(default_factory=list)
    audit_events: list[dict[str, Any]] = Field(default_factory=list)
    stop_now: bool = False
    stop_reason: Optional[str] = None

    def record_gate(self, gate_id: str, passed: bool, details: dict[str, Any] | None = None):
        self.gate_decisions.append({"gate_id": gate_id, "passed": passed, "timestamp": datetime.utcnow().isoformat(), **(details or {})})

    def record_audit(self, event_type: str, agent_id: str, data: dict[str, Any] | None = None):
        self.audit_events.append({"event": event_type, "agent": agent_id, "timestamp": datetime.utcnow().isoformat(), **(data or {})})

    def register_source(self, source_id: str, source_hash: str):
        self.source_hashes[source_id] = source_hash

    def request_stop(self, reason: str):
        self.stop_now = True
        self.stop_reason = reason
