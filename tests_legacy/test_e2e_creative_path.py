from __future__ import annotations

from iqraa_agentic_platform.core.main_orchestrator import MainOrchestrator


def test_e2e_creative_path():
    orch = MainOrchestrator()

    plan = {
        "intent": "creative",
        "creative_problem": "كيف يتشكل الإبداع في الفكر الحضاري؟",
        "estimated_cost_usd": 1.0,
        "cap_usd": 5.0,
    }

    result = orch.execute(plan)

    assert result["intent"] == "creative"
    assert "run_id" in result
    assert "creative_result" in result
    assert "evaluation" in result
    assert "genesis_trace" in result
    assert len(result["genesis_trace"]) >= 5
