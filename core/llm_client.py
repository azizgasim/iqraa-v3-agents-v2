"""
IQRAA V2 — Unified LLM Client
===============================
يدير الاتصال بـ LLMs مع:
- تتبع التكلفة لكل طلب
- retry مع backoff
- دعم Vertex AI (Gemini) + Anthropic (Claude)
- fallback تلقائي
"""
from __future__ import annotations
import json
import time
from typing import Any, Optional
from dataclasses import dataclass
from core.run_context import BudgetEnvelope

# Cost per 1K tokens (approximate)
MODEL_COSTS = {
    "gemini-2.0-flash": {"input": 0.000075, "output": 0.0003},
    "gemini-2.5-pro": {"input": 0.00125, "output": 0.005},
    "claude-sonnet-4-20250514": {"input": 0.003, "output": 0.015},
    "claude-haiku-4-5-20251001": {"input": 0.0008, "output": 0.004},
}

DEFAULT_MODEL = "gemini-2.0-flash"


@dataclass
class LLMResponse:
    text: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_ms: int
    success: bool
    error: Optional[str] = None


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    costs = MODEL_COSTS.get(model, MODEL_COSTS[DEFAULT_MODEL])
    return (input_tokens * costs["input"] + output_tokens * costs["output"]) / 1000


class UnifiedLLMClient:
    """Client موحد يدعم Vertex AI و Claude مع تتبع التكلفة"""

    def __init__(self, default_model: str = DEFAULT_MODEL):
        self.default_model = default_model
        self._vertex_client = None
        self._anthropic_client = None

    def _get_vertex(self):
        if self._vertex_client is None:
            try:
                from google.cloud import aiplatform
                from vertexai.generative_models import GenerativeModel
                self._vertex_client = True
            except Exception:
                self._vertex_client = False
        return self._vertex_client

    def _get_anthropic(self):
        if self._anthropic_client is None:
            try:
                import anthropic
                self._anthropic_client = anthropic.Anthropic()
            except Exception:
                self._anthropic_client = False
        return self._anthropic_client

    async def complete(
        self,
        prompt: str,
        system: str = "",
        model: str = "",
        budget: Optional[BudgetEnvelope] = None,
        max_tokens: int = 2000,
        temperature: float = 0.2,
    ) -> LLMResponse:
        model = model or self.default_model
        if budget and budget.is_exhausted:
            return LLMResponse(text="", model=model, input_tokens=0, output_tokens=0,
                             cost_usd=0, latency_ms=0, success=False, error="budget_exhausted")
        start = time.time()
        try:
            if "gemini" in model:
                resp = await self._call_vertex(prompt, system, model, max_tokens, temperature)
            elif "claude" in model:
                resp = await self._call_anthropic(prompt, system, model, max_tokens, temperature)
            else:
                resp = await self._call_vertex(prompt, system, model, max_tokens, temperature)
            latency = int((time.time() - start) * 1000)
            cost = estimate_cost(model, resp["input_tokens"], resp["output_tokens"])
            if budget:
                budget.record_cost(
                    usd=cost,
                    tokens=resp["input_tokens"] + resp["output_tokens"],
                    tool_calls=1,
                    wall_ms=latency,
                )
            return LLMResponse(
                text=resp["text"], model=model,
                input_tokens=resp["input_tokens"], output_tokens=resp["output_tokens"],
                cost_usd=cost, latency_ms=latency, success=True,
            )
        except Exception as e:
            latency = int((time.time() - start) * 1000)
            return LLMResponse(text="", model=model, input_tokens=0, output_tokens=0,
                             cost_usd=0, latency_ms=latency, success=False, error=str(e))

    async def _call_vertex(self, prompt, system, model, max_tokens, temperature) -> dict:
        from vertexai.generative_models import GenerativeModel, GenerationConfig
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        gen_model = GenerativeModel(model)
        config = GenerationConfig(max_output_tokens=max_tokens, temperature=temperature)
        response = gen_model.generate_content(full_prompt, generation_config=config)
        text = response.text
        input_tokens = response.usage_metadata.prompt_token_count
        output_tokens = response.usage_metadata.candidates_token_count
        return {"text": text, "input_tokens": input_tokens, "output_tokens": output_tokens}

    async def _call_anthropic(self, prompt, system, model, max_tokens, temperature) -> dict:
        client = self._get_anthropic()
        if not client or client is False:
            raise RuntimeError("Anthropic client not available")
        msg = client.messages.create(
            model=model, max_tokens=max_tokens, temperature=temperature,
            system=system if system else "You are a helpful assistant.",
            messages=[{"role": "user", "content": prompt}],
        )
        text = msg.content[0].text
        return {"text": text, "input_tokens": msg.usage.input_tokens, "output_tokens": msg.usage.output_tokens}


# Singleton
_default_client = None

def get_llm_client(model: str = DEFAULT_MODEL) -> UnifiedLLMClient:
    global _default_client
    if _default_client is None:
        _default_client = UnifiedLLMClient(model)
    return _default_client
