"""RetroAgent: orchestrates the tools into a retrospective, with a trace.

The plan is intentionally explicit (not a black-box LLM loop) so it is
reproducible and testable: fetch -> metrics -> retrieve -> recall -> synthesize.
Each step appends to a human-readable trace returned with the report.
"""
from __future__ import annotations

from dataclasses import asdict
from typing import Any

from app.agent.tools import Toolbox
from app.cache import Cache
from app.config import Settings, get_settings
from app.llm.client import LLMClient
from app.rag.embeddings import Embedder
from app.schemas import ActionItem, RetroReport


class RetroAgent:
    def __init__(self, settings: Settings | None = None) -> None:
        self.s = settings or get_settings()
        self.llm = LLMClient(self.s)
        self.embedder = Embedder(self.s)
        self.cache = Cache(self.s.redis_url)
        self.tools = Toolbox(self.s, self.llm, self.embedder, self.cache)

    def run(self, period: str | None = None, connectors: list[str] | None = None,
            query: str | None = None) -> RetroReport:
        period = period or "latest"
        trace: list[str] = []

        r_fetch = self.tools.fetch_period_data(connectors, period)
        trace.append(f"fetch_period_data -> {r_fetch.summary}")
        docs = r_fetch.data or []

        r_metrics = self.tools.compute_metrics(docs)
        trace.append(f"compute_metrics -> {r_metrics.summary}")

        q = query or f"{period} retrospective issues root cause action items"
        r_rag = self.tools.retrieve_knowledge(q, k=4)
        trace.append(f"retrieve_knowledge -> {r_rag.summary}")

        r_last = self.tools.recall_last_retro(period)
        trace.append(f"recall_last_retro -> {r_last.summary}")

        brief: dict[str, Any] = {
            "period": period,
            "documents": [{"source": d.source, "title": d.title, "content": d.content}
                          for d in docs],
            "retrieved": [asdict(c) | {"snippet": c.snippet} for c in (r_rag.data or [])],
            "metrics": r_metrics.data,
            "last_summary": r_last.data,
        }
        return self._finish(period, brief, r_rag.data or [], r_metrics.data, trace)

    def _finish(self, period: str, brief: dict[str, Any], chunks: list[Any],
                metrics: dict[str, Any], trace: list[str]) -> RetroReport:
        r_syn = self.tools.synthesize_retro(brief)
        trace.append(f"synthesize_retro -> {r_syn.summary}")
        data = r_syn.data or {}
        report = RetroReport(
            period=period,
            summary=str(data.get("summary", "")),
            highlights=[str(x) for x in data.get("highlights", [])],
            issues=[str(x) for x in data.get("issues", [])],
            root_causes=[str(x) for x in data.get("root_causes", [])],
            action_items=[_coerce_action(a) for a in data.get("action_items", [])],
            metrics=metrics or {},
            evidence=list(chunks),
            model=self.llm.model,
            trace=trace,
        )
        self.cache.set("retro:last", {"summary": report.summary, "period": period})
        self.cache.set(f"retro:{period}", report.to_dict())
        return report


def _coerce_action(a: Any) -> ActionItem:
    if isinstance(a, str):
        return ActionItem(description=a)
    if isinstance(a, dict):
        return ActionItem(
            description=str(a.get("description") or a.get("task") or a),
            owner=str(a.get("owner", "unassigned")),
            priority=str(a.get("priority", "medium")),
            due=str(a.get("due", "")),
        )
    return ActionItem(description=str(a))
