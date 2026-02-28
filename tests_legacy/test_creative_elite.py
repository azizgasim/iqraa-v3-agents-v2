from __future__ import annotations

from iqraa_agentic_platform.core.creative_elite import (
    CreativeELiteMachine,
    Orchestrator,
    OrchestratorELite,
    GLOBAL_LTM,
)


def test_elite_machine_trace_length():
    machine = CreativeELiteMachine(problem="p1")
    result = machine.run()
    assert len(result["genesis_trace"]) == 5
    assert result["result"]


def test_elite_orchestrator_wrapper():
    orch = Orchestrator()
    output = orch.run_creative("p2")
    assert output["state_machine"] == "E-LITE"
    assert len(output["genesis_trace"]) == 5


def test_elite_enhanced_memory_and_eval():
    GLOBAL_LTM.clear()
    orch = OrchestratorELite()
    out1 = orch.run_creative("q1")
    out2 = orch.run_creative("q2")

    assert out1["evaluation"]["plurality"] >= 2
    assert len(GLOBAL_LTM.problem_history) == 2
    assert out1["evaluation"]["novelty"] >= 0.0
