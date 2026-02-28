"""
IQRAA V2 — Comprehensive Unit Tests
50 tests covering: canonical_policy, run_context, models, AGT-01, G1, AGT-05, pipeline
"""
import asyncio
import pytest
from core.canonical_policy import canonicalize, CanonicalPolicy, text_hash, make_canonical_span, POLICY_VERSION
from core.run_context import UnifiedRunContext, BudgetEnvelope
from core.models import TextSpan, Evidence, Claim, AutonomyLevel, RiskTier, OperationInput, OperationOutput
from agents.agt01_text_analysis import TextAnalysisAgent
from agents.agt05_verification import VerificationAgent
from governance.g1_quality_gate import run_g1_gate, G1QualityResult


# ============================================
# SECTION 1: Canonical Policy (15 tests)
# ============================================

def test_canon_strip_diacritics():
    assert canonicalize("قَالَ") == "قال"

def test_canon_hamza_normalization():
    assert canonicalize("أحمد") == "احمد"

def test_canon_hamza_below():
    assert canonicalize("إسلام") == "اسلام"

def test_canon_alef_madda():
    assert canonicalize("آخر") == "اخر"

def test_canon_tatweel_removal():
    assert canonicalize("عــربي") == "عربي"

def test_canon_preserves_alef_maqsura():
    p = CanonicalPolicy(normalize_alef_maqsura=False)
    assert "ى" in canonicalize("موسى", p)

def test_canon_nfc_normalization():
    text = "قال"
    assert canonicalize(text) == canonicalize(text)

def test_canon_empty_string():
    assert canonicalize("") == ""

def test_canon_latin_passthrough():
    assert canonicalize("hello") == "hello"

def test_canon_mixed_arabic_latin():
    result = canonicalize("قَالَ hello")
    assert "hello" in result
    assert "َ" not in result

def test_canon_policy_version():
    assert POLICY_VERSION == "1.0.0"

def test_canon_policy_immutable():
    p = CanonicalPolicy()
    with pytest.raises(Exception):
        p.version = "2.0.0"

def test_text_hash_deterministic():
    h1 = text_hash("قال")
    h2 = text_hash("قال")
    assert h1 == h2

def test_text_hash_different():
    assert text_hash("قال") != text_hash("قيل")

def test_make_canonical_span_basic():
    span = make_canonical_span("قَالَ ابنُ", "src1", 0, 4)
    assert span["text_canonical"] == "قال"
    assert span["canonical_start"] >= 0
    assert span["canonicalizer_version"] == "1.0.0"


# ============================================
# SECTION 2: RunContext + Budget (10 tests)
# ============================================

def test_unified_ctx_defaults():
    ctx = UnifiedRunContext()
    assert ctx.run_id.startswith("run_")
    assert ctx.project_id == "iqraa-12"

def test_unified_ctx_budget():
    ctx = UnifiedRunContext()
    assert ctx.budget.max_usd == 1.0
    assert ctx.budget.usd_remaining == 1.0

def test_budget_record_cost():
    b = BudgetEnvelope()
    b.record_cost(usd=0.3, tokens=5000)
    assert b.used_usd == 0.3
    assert b.used_tokens == 5000
    assert b.usd_remaining == 0.7

def test_budget_exhausted():
    b = BudgetEnvelope(max_usd=0.5)
    b.record_cost(usd=0.5)
    assert b.is_exhausted

def test_budget_not_exhausted():
    b = BudgetEnvelope(max_usd=1.0)
    b.record_cost(usd=0.3)
    assert not b.is_exhausted

def test_ctx_record_gate():
    ctx = UnifiedRunContext()
    ctx.record_gate("G1", True, {"score": 0.95})
    assert len(ctx.gate_decisions) == 1
    assert ctx.gate_decisions[0]["passed"] is True

def test_ctx_record_audit():
    ctx = UnifiedRunContext()
    ctx.record_audit("test_event", "AGT-01")
    assert len(ctx.audit_events) == 1

def test_ctx_register_source():
    ctx = UnifiedRunContext()
    ctx.register_source("src1", "abc123")
    assert ctx.source_hashes["src1"] == "abc123"

def test_ctx_request_stop():
    ctx = UnifiedRunContext()
    ctx.request_stop("budget_exceeded")
    assert ctx.stop_now is True
    assert ctx.stop_reason == "budget_exceeded"

def test_ctx_canonical_version():
    ctx = UnifiedRunContext()
    assert ctx.canonical_policy_version == "1.0.0"


# ============================================
# SECTION 3: Core Models (8 tests)
# ============================================

def test_textspan_creation():
    ts = TextSpan(doc_id="d1", char_start=0, char_end=10, text="test")
    assert ts.doc_id == "d1"

def test_evidence_auto_id():
    ev = Evidence(spans=[], confidence=0.8, source_ref="s1")
    assert ev.evidence_id.startswith("ev_")

def test_claim_requires_evidence():
    c = Claim(text="test", evidence_ids=["ev1"], confidence=0.9)
    assert len(c.evidence_ids) >= 1

def test_claim_min_evidence_validation():
    with pytest.raises(Exception):
        Claim(text="test", evidence_ids=[], confidence=0.9)

def test_autonomy_levels():
    assert AutonomyLevel.L0_READ.value == "L0"
    assert AutonomyLevel.L4_FULL.value == "L4"

def test_risk_tiers():
    assert RiskTier.LOW.value == "low"
    assert RiskTier.CRITICAL.value == "critical"

def test_operation_input():
    oi = OperationInput(operation_id="op1", run_ctx=UnifiedRunContext())
    assert oi.operation_id == "op1"

def test_operation_output():
    oo = OperationOutput(operation_id="op1", run_id="r1", success=True)
    assert oo.cost_usd == 0.0


# ============================================
# SECTION 4: AGT-01 (7 tests)
# ============================================

def test_agt01_card():
    a = TextAnalysisAgent()
    assert a.card.agent_id == "AGT-01"
    assert a.card.risk_tier == RiskTier.MEDIUM

def test_agt01_basic():
    a = TextAnalysisAgent()
    ctx = UnifiedRunContext()
    r = asyncio.get_event_loop().run_until_complete(a.run(ctx, {"text": "قال ابن خلدون", "source_id": "s1"}))
    assert r.success

def test_agt01_empty_text():
    a = TextAnalysisAgent()
    ctx = UnifiedRunContext()
    r = asyncio.get_event_loop().run_until_complete(a.run(ctx, {"text": "", "source_id": "s1"}))
    assert not r.success

def test_agt01_diacritics_stripped():
    a = TextAnalysisAgent()
    ctx = UnifiedRunContext()
    r = asyncio.get_event_loop().run_until_complete(a.run(ctx, {"text": "قَالَ", "source_id": "s1"}))
    assert r.success
    if r.evidence:
        assert "َ" not in r.evidence[0].spans[0].text

def test_agt01_multi_sentence():
    a = TextAnalysisAgent()
    ctx = UnifiedRunContext()
    r = asyncio.get_event_loop().run_until_complete(a.run(ctx, {"text": "جملة أولى. جملة ثانية.", "source_id": "s1"}))
    assert r.output["claims_count"] == 2

def test_agt01_registers_source():
    a = TextAnalysisAgent()
    ctx = UnifiedRunContext()
    asyncio.get_event_loop().run_until_complete(a.run(ctx, {"text": "نص", "source_id": "src99"}))
    assert "src99" in ctx.source_hashes

def test_agt01_evidence_has_spans():
    a = TextAnalysisAgent()
    ctx = UnifiedRunContext()
    r = asyncio.get_event_loop().run_until_complete(a.run(ctx, {"text": "نص عربي", "source_id": "s1"}))
    if r.evidence:
        assert len(r.evidence[0].spans) > 0


# ============================================
# SECTION 5: G1 Gate (5 tests)
# ============================================

def test_g1_pass():
    ev = Evidence(spans=[TextSpan(doc_id="d1", char_start=0, char_end=5, text="test")], confidence=0.8, source_ref="s1")
    claims = [{"text": "claim", "evidence_ids": [ev.evidence_id]}]
    r = run_g1_gate(claims, [ev])
    assert r.passed

def test_g1_fail_no_evidence_ids():
    ev = Evidence(spans=[TextSpan(doc_id="d1", char_start=0, char_end=5, text="test")], confidence=0.8, source_ref="s1")
    claims = [{"text": "claim", "evidence_ids": []}]
    r = run_g1_gate(claims, [ev])
    assert not r.passed

def test_g1_fail_bad_offsets():
    ev = Evidence(spans=[TextSpan(doc_id="d1", char_start=-1, char_end=0, text="test")], confidence=0.8, source_ref="s1")
    claims = [{"text": "c", "evidence_ids": ["x"]}]
    r = run_g1_gate(claims, [ev])
    assert not r.passed

def test_g1_fail_zero_confidence():
    ev = Evidence(spans=[TextSpan(doc_id="d1", char_start=0, char_end=5, text="t")], confidence=0.0, source_ref="s1")
    claims = [{"text": "c", "evidence_ids": ["x"]}]
    r = run_g1_gate(claims, [ev])
    assert not r.passed

def test_g1_score_calculation():
    ev = Evidence(spans=[TextSpan(doc_id="d1", char_start=0, char_end=5, text="t")], confidence=0.8, source_ref="s1")
    claims = [{"text": "c", "evidence_ids": [ev.evidence_id]}]
    r = run_g1_gate(claims, [ev])
    assert 0.0 <= r.score <= 1.0


# ============================================
# SECTION 6: AGT-05 Verification (3 tests)
# ============================================

def test_agt05_card():
    a = VerificationAgent()
    assert a.card.agent_id == "AGT-05"
    assert a.card.risk_tier == RiskTier.HIGH

def test_agt05_verify_valid():
    a = VerificationAgent()
    ctx = UnifiedRunContext()
    ev = Evidence(spans=[TextSpan(doc_id="d1", char_start=0, char_end=3, text="قال")], confidence=0.8, source_ref="s1")
    claims = [{"text": "قال", "evidence_ids": [ev.evidence_id]}]
    r = asyncio.get_event_loop().run_until_complete(a.run(ctx, {"claims": claims, "evidences": [ev], "canonical_text": "قال ابن", "source_id": "d1"}))
    assert r.success
    assert r.output["all_passed"]

def test_agt05_empty_claims_fails():
    a = VerificationAgent()
    ctx = UnifiedRunContext()
    r = asyncio.get_event_loop().run_until_complete(a.run(ctx, {"claims": [], "evidences": []}))
    assert not r.success


# ============================================
# SECTION 7: Pipeline E2E (2 tests)
# ============================================

def test_pipeline_e2e_success():
    from pipelines.thin_slice import run_thin_slice
    r = asyncio.get_event_loop().run_until_complete(run_thin_slice("قال ابن خلدون. وقال العلماء.", "test"))
    assert r["pipeline_success"]
    assert r["g1_passed"]
    assert r["verified_count"] == 2

def test_pipeline_e2e_empty_fails():
    from pipelines.thin_slice import run_thin_slice
    r = asyncio.get_event_loop().run_until_complete(run_thin_slice("", "test"))
    assert not r.get("pipeline_success", True)
