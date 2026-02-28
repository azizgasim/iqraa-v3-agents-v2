from __future__ import annotations

from iqraa_agentic_platform.core.bootstrap_final import run_final


def test_final_success_path():
    plan = {
        "intent": "e2e-test",
        "query": "knowledge test",
        "estimated_cost_usd": 1.0,
        "cap_usd": 5.0,
        "baseline_quality": 0.5,
    }
    ctx = run_final(plan)
    assert ctx.stop_now is False
    assert ctx.outputs["execution"]["result"] == "EXECUTION_OK"
    assert "evaluation" in ctx.outputs


def test_final_cost_block():
    plan = {
        "intent": "e2e-test",
        "estimated_cost_usd": 10.0,
        "cap_usd": 1.0,
    }
    ctx = run_final(plan)
    assert ctx.stop_now is True
    assert ctx.stop_reason == "COST_CAP_EXCEEDED"


def test_final_missing_plan():
    ctx = run_final({})
    assert ctx.stop_now is True
    assert ctx.stop_reason == "MISSING_PLAN_INTENT"
