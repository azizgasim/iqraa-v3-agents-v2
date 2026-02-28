from ops.bootstrap_ops import build_ops
from ops.hotfix import Hotfix


def test_zeta_ops_flow():
    ops = build_ops()
    snap = ops["monitor"].snapshot({"cost_usd": 3.0, "latency_ms": 1200.0, "error_rate": 0.01})
    signals = ops["drift"].evaluate({"cost_usd": 12.0})
    assert signals["cost_usd"].breached is True

    plan = ops["rollback"].prepare("v1.1.0", "v1.0.0", "cost spike")
    res = ops["rollback"].execute(plan)
    assert res["status"] == "rolled_back"

    hf = Hotfix(fix_id="hf-001", description="patch caps", patch={"caps": {"usd": 8}})
    assert ops["hotfix"].apply(hf)["applied"] is True
