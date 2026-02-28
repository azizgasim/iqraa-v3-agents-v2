from __future__ import annotations

from iqraa_agentic_platform.core.bootstrap import build_default_orchestrator
from core.context import ExecutionContext


def test_orchestrator_creative_path_success():
    orch = build_default_orchestrator()
    ctx = ExecutionContext(
        actor_agent_id="agent-orchestrator-01",
        actor_role="orchestrator",
        permissions=["orchestrate"],
        request={"intent": "creative"},
        plan={
            "intent": "creative",
            "creative_problem": "اختبار مسار الابداع",
            "estimated_cost_usd": 1.0,
            "cap_usd": 5.0,
            "alternatives": [
                {"path": "lean", "tradeoff": "lower_cost"},
                {"path": "standard", "tradeoff": "balanced"},
            ],
            "on_violation": "stop",
            "quality_checklist": ["traceability", "policy_ok", "budget_ok"],
            "steps": [
                {"kind": "creative", "agent_id": "agent-creative"},
            ],
        },
    )

    result = orch.run(ctx)

    assert result.stop_now is False
    assert "creative_result" in result.outputs
    assert "genesis_trace" in result.outputs
    assert len(result.outputs["genesis_trace"]) >= 1
