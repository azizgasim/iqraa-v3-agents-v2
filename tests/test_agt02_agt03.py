"""IQRAA V2 — Extra tests for AGT-02 and AGT-03"""
import asyncio
import pytest
from agents.agt02_entity_linking import EntityLinkingAgent
from agents.agt03_cross_reference import CrossReferenceAgent
from core.run_context import UnifiedRunContext

# AGT-02 tests
def test_agt02_card():
    a = EntityLinkingAgent()
    assert a.card.agent_id == "AGT-02"

def test_agt02_basic():
    a = EntityLinkingAgent()
    ctx = UnifiedRunContext()
    r = asyncio.get_event_loop().run_until_complete(
        a.run(ctx, {"text": "قال ابن خلدون في المقدمة", "source_id": "s1"}))
    assert r.success
    assert r.output["entity_count"] >= 1

def test_agt02_empty_fails():
    a = EntityLinkingAgent()
    ctx = UnifiedRunContext()
    r = asyncio.get_event_loop().run_until_complete(
        a.run(ctx, {"text": "", "source_id": "s1"}))
    assert not r.success

def test_agt02_all_suggested_not_approved():
    a = EntityLinkingAgent()
    ctx = UnifiedRunContext()
    r = asyncio.get_event_loop().run_until_complete(
        a.run(ctx, {"text": "ابن تيمية والإمام الشافعي", "source_id": "s1"}))
    assert r.output["none_approved"] is True

def test_agt02_audit_recorded():
    a = EntityLinkingAgent()
    ctx = UnifiedRunContext()
    asyncio.get_event_loop().run_until_complete(
        a.run(ctx, {"text": "ابن خلدون", "source_id": "s1"}))
    assert len(ctx.audit_events) >= 1

# AGT-03 tests
def test_agt03_card():
    a = CrossReferenceAgent()
    assert a.card.agent_id == "AGT-03"

def test_agt03_basic():
    a = CrossReferenceAgent()
    ctx = UnifiedRunContext()
    r = asyncio.get_event_loop().run_until_complete(
        a.run(ctx, {"claims_a": [{"text": "العمران"}], "claims_b": [{"text": "العمران"}]}))
    assert r.success

def test_agt03_identical_claims_match():
    a = CrossReferenceAgent()
    ctx = UnifiedRunContext()
    r = asyncio.get_event_loop().run_until_complete(
        a.run(ctx, {"claims_a": [{"text": "العمران البشري ضروري"}], "claims_b": [{"text": "العمران البشري ضروري"}]}))
    assert r.output["cross_ref_count"] >= 1

def test_agt03_empty_fails():
    a = CrossReferenceAgent()
    ctx = UnifiedRunContext()
    r = asyncio.get_event_loop().run_until_complete(
        a.run(ctx, {"claims_a": [], "claims_b": [{"text": "test"}]}))
    assert not r.success

def test_agt03_audit():
    a = CrossReferenceAgent()
    ctx = UnifiedRunContext()
    asyncio.get_event_loop().run_until_complete(
        a.run(ctx, {"claims_a": [{"text": "نص"}], "claims_b": [{"text": "نص"}]}))
    assert len(ctx.audit_events) >= 1
