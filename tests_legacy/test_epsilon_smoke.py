from core.context import ExecutionContext
from core.bootstrap_knowledge import build_knowledge_stack
from memory.base import MemoryRecord


def test_epsilon_knowledge_and_memory():
    stack = build_knowledge_stack()
    ctx = ExecutionContext()
    stack["enricher"].enrich(ctx, "historical")

    assert "context" in ctx.outputs
    assert "historical" in ctx.outputs["context"]

    rec = MemoryRecord(key="k1", value={"v": 1}, confidence=0.7)
    assert stack["governance"].allow_write(rec) is True
    stack["short_term"].write(rec)
    assert stack["short_term"].read("k1") is not None
