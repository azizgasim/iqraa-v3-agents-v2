from release.bootstrap_release import run_release
from release.snapshot import SystemSnapshot


def test_omega_release_ready():
    snap = SystemSnapshot(
        agents={
            "a1": {"role": "research"},
            "a2": {"role": "analysis"},
            "a3": {"role": "review"},
        },
        plan={"intent": "finalize", "on_violation": "stop"},
        quality={"ok": True},
        cost={"caps": {"usd": 5}},
        infra={"health": "ok"},
        knowledge={"enabled": True},
    )

    res = run_release(snap)
    assert res["ready"] is True
    assert any(g["gate_id"] == "gate-8" for g in res["gate_results"])
