"""
IQRA-12 Core Models — Pydantic v2
المبادئ غير القابلة للتفاوض:
1. لا claim بلا evidence
2. لا evidence بلا offsets وسياق
3. لا تشغيل بلا run_id + recipe
4. لا ربط كيانات بلا Suggest→Approve
5. لا نشر بلا بوابات الثقة (V1+V2+V4)
"""
from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Optional, Any
from uuid import uuid4
from pydantic import BaseModel, Field

# === Enums ===
class AutonomyLevel(str, Enum):
    L0_READ = "L0"
    L1_SUGGEST = "L1"
    L2_LIMITED = "L2"
    L3_AUTONOMOUS = "L3"
    L4_FULL = "L4"

class RiskTier(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class OperationCategory(str, Enum):
    EXTRACT = "extract"
    LINK = "link"
    TRACE = "trace"
    ANALYZE = "analyze"
    CONSTRUCT = "construct"
    SYNTHESIZE = "synthesize"
    WRITE = "write"
    VERIFY = "verify"

# === Core Models ===
class TextSpan(BaseModel):
    """الحقيقة = موقع دقيق في النص الأصلي"""
    doc_id: str
    char_start: int
    char_end: int
    text: str
    context: str = ""

class Evidence(BaseModel):
    """لا claim بلا evidence — لا evidence بلا offsets"""
    evidence_id: str = Field(default_factory=lambda: f"ev_{uuid4().hex[:12]}")
    spans: list[TextSpan]
    confidence: float = Field(ge=0.0, le=1.0)
    source_ref: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Claim(BaseModel):
    """كل ادعاء مربوط بحزمة أدلة"""
    claim_id: str = Field(default_factory=lambda: f"clm_{uuid4().hex[:12]}")
    text: str
    evidence_ids: list[str] = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    scope: dict[str, Any] = {}
    counter_evidence_ids: list[str] = []
    approved: bool = False

# RunContext moved to run_context.py as UnifiedRunContext
# Re-export for backward compatibility
from .run_context import UnifiedRunContext as RunContext, UnifiedRunContext, BudgetEnvelope

class OperationInput(BaseModel):
    """عقد موحد لمدخلات كل عملية"""
    operation_id: str
    run_ctx: RunContext
    params: dict[str, Any] = {}

class OperationOutput(BaseModel):
    """عقد موحد لمخرجات كل عملية"""
    operation_id: str
    run_id: str
    success: bool
    result: dict[str, Any] = {}
    evidence: list[Evidence] = []
    cost_usd: float = 0.0
    duration_ms: int = 0
    errors: list[str] = []
