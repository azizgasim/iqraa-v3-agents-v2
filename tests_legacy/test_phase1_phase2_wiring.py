def test_phase1_phase2_import_and_flow():
	from iqraa_agentic_platform.core import OrchestratorWiring

	wiring = OrchestratorWiring()

	decision = wiring.preflight_cost(estimate_usd=1.0, cap_usd=5.0)
	assert decision.allowed is True

	ctx = wiring.enrich_context({"query": "test"})
	assert "knowledge" in ctx

	result = wiring.post_evaluate(output="x", baseline={"quality": 0.5})
	assert "quality" in result
	assert "roi" in result
