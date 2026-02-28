"""
IQRAA V2 - Thin Slice Pipeline (LangGraph)
AGT-01 > G1 > AGT-05 > result
"""
from __future__ import annotations
import asyncio
from typing import Any, TypedDict
from langgraph.graph import StateGraph, END
from core.run_context import UnifiedRunContext
from core.canonical_policy import canonicalize, CanonicalPolicy
from agents.agt01_text_analysis import TextAnalysisAgent
from agents.agt05_verification import VerificationAgent
from governance.g1_quality_gate import run_g1_gate

class PipelineState(TypedDict, total=False):
    text: str
    source_id: str
    run_ctx_dict: dict
    claims: list
    evidences: list
    canonical_text: str
    agt01_success: bool
    g1_passed: bool
    g1_score: float
    g1_issues: list
    verification_passed: bool
    verified_count: int
    verification_results: list
    pipeline_success: bool
    errors: list

async def node_agt01(state: PipelineState) -> dict:
    agent = TextAnalysisAgent()
    ctx = UnifiedRunContext(**state.get("run_ctx_dict", {}))
    result = await agent.run(ctx, {"text": state["text"], "source_id": state.get("source_id", "unknown")})
    if not result.success:
        return {"agt01_success": False, "errors": result.errors, "pipeline_success": False}
    canonical_text = canonicalize(state["text"])
    return {"claims": result.output.get("claims", []), "evidences": [e.model_dump() for e in result.evidence], "canonical_text": canonical_text, "agt01_success": True, "run_ctx_dict": ctx.model_dump(mode="json")}

async def node_g1_gate(state: PipelineState) -> dict:
    from core.models import Evidence
    evidences = [Evidence(**e) if isinstance(e, dict) else e for e in state.get("evidences", [])]
    result = run_g1_gate(state.get("claims", []), evidences)
    return {"g1_passed": result.passed, "g1_score": result.score, "g1_issues": result.issues}

def route_after_g1(state: PipelineState) -> str:
    if state.get("g1_passed"):
        return "agt05_verify"
    return "fail_end"

async def node_agt05(state: PipelineState) -> dict:
    from core.models import Evidence
    agent = VerificationAgent()
    ctx = UnifiedRunContext(**state.get("run_ctx_dict", {}))
    evidences = [Evidence(**e) if isinstance(e, dict) else e for e in state.get("evidences", [])]
    result = await agent.run(ctx, {"claims": state.get("claims", []), "evidences": evidences, "canonical_text": state.get("canonical_text", ""), "source_id": state.get("source_id", "unknown")})
    return {"verification_passed": result.output.get("all_passed", False), "verified_count": result.output.get("verified_count", 0), "verification_results": result.output.get("results", []), "pipeline_success": result.output.get("all_passed", False), "run_ctx_dict": ctx.model_dump(mode="json")}

async def node_fail(state: PipelineState) -> dict:
    return {"pipeline_success": False, "errors": state.get("g1_issues", []) + state.get("errors", [])}

def build_thin_slice_graph() -> StateGraph:
    graph = StateGraph(PipelineState)
    graph.add_node("agt01_analyze", node_agt01)
    graph.add_node("g1_quality", node_g1_gate)
    graph.add_node("agt05_verify", node_agt05)
    graph.add_node("fail_end", node_fail)
    graph.set_entry_point("agt01_analyze")
    graph.add_edge("agt01_analyze", "g1_quality")
    graph.add_conditional_edges("g1_quality", route_after_g1, {"agt05_verify": "agt05_verify", "fail_end": "fail_end"})
    graph.add_edge("agt05_verify", END)
    graph.add_edge("fail_end", END)
    return graph

def compile_thin_slice():
    return build_thin_slice_graph().compile()

async def run_thin_slice(text: str, source_id: str = "test_source") -> dict:
    app = compile_thin_slice()
    initial_state = {"text": text, "source_id": source_id, "run_ctx_dict": {}, "errors": []}
    result = await app.ainvoke(initial_state)
    return result
