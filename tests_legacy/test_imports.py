import importlib


MODULES = [
    "iqraa_agentic_platform.governance.gates.gate_base",
    "iqraa_agentic_platform.governance.gates.gate_0_request",
    "iqraa_agentic_platform.governance.gates.gate_1_policy",
    "iqraa_agentic_platform.governance.gates.gate_2_budget",
    "iqraa_agentic_platform.governance.gates.gate_3_execution",
    "iqraa_agentic_platform.governance.gates.gate_4_quality",
    "iqraa_agentic_platform.governance.gates.gate_5_audit",
    "iqraa_agentic_platform.governance.policy.policy_engine",
    "iqraa_agentic_platform.governance.budget.budget_enforcer",
    "iqraa_agentic_platform.governance.audit.audit_logger",
    "iqraa_agentic_platform.core.context",
    "iqraa_agentic_platform.core.orchestrator",
    "iqraa_agentic_platform.core.lifecycle",
    "iqraa_agentic_platform.execution.model_router",
    "iqraa_agentic_platform.execution.tool_runner",
    "iqraa_agentic_platform.execution.sandbox",
    "iqraa_agentic_platform.execution.job_manager",
    "iqraa_agentic_platform.agents.base_agent",
    "iqraa_agentic_platform.agents.research_agent",
    "iqraa_agentic_platform.agents.analysis_agent",
    "iqraa_agentic_platform.agents.writing_agent",
    "iqraa_agentic_platform.agents.reviewer_agent",
    "iqraa_agentic_platform.memory.short_term",
    "iqraa_agentic_platform.memory.long_term",
    "iqraa_agentic_platform.memory.memory_governance",
    "iqraa_agentic_platform.knowledge.knowledge_graph",
    "iqraa_agentic_platform.knowledge.retrieval",
    "iqraa_agentic_platform.observability.metrics",
    "iqraa_agentic_platform.observability.tracing",
    "iqraa_agentic_platform.observability.health",
    "iqraa_agentic_platform.security.prompt_defense",
    "iqraa_agentic_platform.security.isolation",
    "iqraa_agentic_platform.security.threat_scoring",
]


def test_imports():
    for module in MODULES:
        importlib.import_module(module)


# Phase Beta imports
from core.bootstrap import build_default_orchestrator, run_beta_smoke  # noqa: E402,F401
from core.decision import Decision, DecisionStatus  # noqa: E402,F401
from governance.gate_registry import GateRegistry  # noqa: E402,F401
from governance.gates.gate0_agent_definition import Gate0AgentDefinition  # noqa: E402,F401
from governance.gates.gate1_organization import Gate1Organization  # noqa: E402,F401
from governance.gates.gate2_values_incentives import Gate2ValuesIncentives  # noqa: E402,F401
from governance.gates.gate3_safety_shutdown import Gate3SafetyShutdown  # noqa: E402,F401
from governance.gates.gate4_quality_eval import Gate4QualityEval  # noqa: E402,F401
from governance.gates.gate5_budget_cost import Gate5BudgetCost  # noqa: E402,F401
