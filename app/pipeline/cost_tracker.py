"""Cost Tracking and Financial Telemetry for Pipeline Executions.

Tracks actual or clearly estimated API costs across search providers,
generative AI assistants, content generators, and audit operations.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.schemas.pipeline import CostBreakdownItem, PipelineCostSummary

# Standard published API unit costs (USD per single query/call or per 1,000 tokens)
RATE_CARDS: Dict[str, Dict[str, Any]] = {
    "google_search": {
        "unit_cost_usd": 0.005,  # $5.00 per 1,000 queries (Google Custom Search API)
        "cost_model": "per_query",
        "description": "Google Custom Search JSON API ($5.00/1k queries)",
    },
    "google_ai_overview": {
        "unit_cost_usd": 0.005,
        "cost_model": "per_query",
        "description": "Google AI Overview live search evaluation ($5.00/1k queries)",
    },
    "perplexity": {
        "unit_cost_usd": 0.005,  # ~$5.00 per 1,000 queries (Sonar small/medium)
        "cost_model": "per_query",
        "description": "Perplexity Sonar API online search synthesis ($5.00/1k queries)",
    },
    "chatgpt": {
        "unit_cost_usd": 0.001,  # ~ $1.00 per 1,000 queries (~1k tokens GPT-4o-mini)
        "cost_model": "per_query",
        "description": "OpenAI GPT-4o-mini evaluation (~$1.00/1k queries)",
    },
    "claude": {
        "unit_cost_usd": 0.005,  # Claude 3.5 Sonnet (~$3.00/M in, $15.00/M out)
        "cost_model": "per_query",
        "description": "Anthropic Claude 3.5 Sonnet generative answer evaluation",
    },
    "gemini": {
        "unit_cost_usd": 0.0005,  # Gemini 1.5 Flash with search grounding
        "cost_model": "per_query",
        "description": "Google Gemini 1.5 Flash Search Grounding (~$0.50/1k queries)",
    },
    "bing_copilot": {
        "unit_cost_usd": 0.000,
        "cost_model": "free_or_manual",
        "description": "Manual evidence / web UI import (no API cost)",
    },
    "content_generation_llm": {
        "unit_cost_usd": 0.015,  # 1k in tokens + 1.5k out tokens on frontier model
        "cost_model": "per_page",
        "description": "Configurable LLM AEO page generation (~$0.015/page)",
    },
    "content_generation_deterministic": {
        "unit_cost_usd": 0.000,
        "cost_model": "local_compute",
        "description": "Deterministic knowledge-base template generator ($0.00)",
    },
    "technical_audit": {
        "unit_cost_usd": 0.000,
        "cost_model": "local_compute",
        "description": "Local DOM parsing and polite inspection ($0.00)",
    },
    "manual_import": {
        "unit_cost_usd": 0.000,
        "cost_model": "manual",
        "description": "Human operator evidence submission ($0.00)",
    },
}


class CostTracker:
    """Tracks and calculates estimated and actual costs across pipeline operations."""

    def __init__(self) -> None:
        self._items: List[CostBreakdownItem] = []
        self._calls_by_key: Dict[str, Dict[str, Any]] = {}

    def record_call(
        self,
        provider: str,
        operation: str,
        stage: str,
        actual_cost_usd: Optional[float] = None,
        tokens_in: Optional[int] = None,
        tokens_out: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> float:
        """Record a single provider or engine operation and compute cost."""
        provider_clean = provider.lower().strip()
        key = f"{provider_clean}:{operation}:{stage}"

        if actual_cost_usd is not None:
            cost = max(0.0, float(actual_cost_usd))
            is_estimated = False
        else:
            rate_info = RATE_CARDS.get(provider_clean, {
                "unit_cost_usd": 0.002,
                "cost_model": "default_estimate",
                "description": f"Standard estimated query cost for {provider_clean}",
            })
            cost = rate_info["unit_cost_usd"]
            is_estimated = True

        if key not in self._calls_by_key:
            self._calls_by_key[key] = {
                "provider": provider_clean,
                "operation": operation,
                "stage": stage,
                "call_count": 0,
                "cost_usd": 0.0,
                "is_estimated": is_estimated,
                "details": metadata or {},
            }

        self._calls_by_key[key]["call_count"] += 1
        self._calls_by_key[key]["cost_usd"] += cost
        if tokens_in:
            self._calls_by_key[key]["details"]["tokens_in"] = (
                self._calls_by_key[key]["details"].get("tokens_in", 0) + tokens_in
            )
        if tokens_out:
            self._calls_by_key[key]["details"]["tokens_out"] = (
                self._calls_by_key[key]["details"].get("tokens_out", 0) + tokens_out
            )

        return cost

    def get_summary(self) -> PipelineCostSummary:
        """Compile a structured cost summary across all recorded operations."""
        total_cost = 0.0
        total_calls = 0
        by_provider: Dict[str, float] = {}
        by_stage: Dict[str, float] = {}
        items: List[CostBreakdownItem] = []

        for data in self._calls_by_key.values():
            p = data["provider"]
            s = data["stage"]
            c = round(data["cost_usd"], 5)
            cnt = data["call_count"]

            total_cost += c
            total_calls += cnt

            by_provider[p] = round(by_provider.get(p, 0.0) + c, 5)
            by_stage[s] = round(by_stage.get(s, 0.0) + c, 5)

            items.append(
                CostBreakdownItem(
                    provider=p,
                    operation=data["operation"],
                    call_count=cnt,
                    estimated_cost_usd=c,
                    is_estimated=data["is_estimated"],
                    details=data["details"],
                )
            )

        return PipelineCostSummary(
            total_cost_usd=round(total_cost, 5),
            total_calls=total_calls,
            by_provider=by_provider,
            by_stage=by_stage,
            items=items,
        )
