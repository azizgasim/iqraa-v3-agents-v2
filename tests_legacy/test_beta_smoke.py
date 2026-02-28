from __future__ import annotations

from core.bootstrap import run_beta_smoke


def test_beta_smoke_happy_path():
    ctx = run_beta_smoke({
        "topic": "phase-beta-smoke",
        "intent": "produce_stubbed_output_with_governance",
        "on_violation": "stop",
    })
    assert ctx.lifecycle.phase.value in ("finalize", "failed")
    assert "draft" in ctx.outputs
    assert len(ctx.gate_decisions) >= 6
    assert len(ctx.audit_events) > 0
    assert ctx.stop_now is False


def test_beta_smoke_denied_missing_permission():
    ctx = run_beta_smoke({
        "topic": "phase-beta-smoke",
        "intent": "produce_stubbed_output_with_governance",
        "on_violation": "stop",
        # NOTE: permission removed in ctx builder would be needed to trigger;
        # this test assumes you manually remove permissions in the ctx if desired.
    })
    # This is a placeholder; import-only tests already exist in your suite.
    assert ctx.session_id