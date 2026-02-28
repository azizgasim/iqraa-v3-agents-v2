from platform.bootstrap_infra import build_platform


def test_delta_platform_bootstrap():
    p = build_platform()
    assert "tools" in p
    assert p["health"].status()["status"] == "ok"
    res = p["adapter"].invoke(
        ctx=type("C", (), {"permissions": ["tool.noop"]})(),
        tool_name="noop",
        args={"x": 1},
    )
    assert res["status"] == "ok"
