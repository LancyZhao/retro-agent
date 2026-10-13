"""Tools the retrospective agent can invoke.

Each method is a discrete, independently testable capability with a uniform
`ToolResult`. The orchestrator sequences them and records a trace, which is the
"agent platform + tool integration" surface a production system would expose.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from app.cache import Cache
from app.config import Settings
from app.connectors import registry
from app.llm.client import LLMClient
from app.rag.embeddings import Embedder
from app.rag.store import VectorStore
from app.schemas import Document, RetrievedChunk

_ISSUE_RE = re.compile(
    r"fail|error|bug|block|delay|regress|timeout|incident|故障|错误|失败|阻塞|延期|回退|超时",
    re.IGNORECASE,
)
_WIN_RE = re.compile(r"完成|交付|上线|发布|done|shipped|launched|delivered", re.IGNORECASE)


@dataclass
class ToolResult:
    name: str
    ok: bool
    summary: str
    data: Any = field(default=None)


class Toolbox:
    def __init__(self, settings: Settings, llm: LLMClient,
                 embedder: Embedder, cache: Cache) -> None:
        self.s = settings
        self.llm = llm
        self.embedder = embedder
        self.cache = cache
        self._store: VectorStore | None = None

    # --- tool: pull data from business-system connectors ------------------
    def fetch_period_data(self, connector_names: list[str] | None,
                          period: str | None) -> ToolResult:
        conns = registry.build(connector_names, self.s)
        docs: list[Document] = []
        used: list[str] = []
        for c in conns:
            got = c.fetch(period)
            if got:
                used.append(f"{c.name}:{len(got)}")
            docs.extend(got)
        return ToolResult("fetch_period_data", bool(docs),
                          f"pulled {len(docs)} docs from [{', '.join(used) or 'none'}]", docs)

    # --- tool: index + retrieve knowledge-base context (RAG) --------------
    def _load_kb(self) -> list[Document]:
        from pathlib import Path

        d = Path(self.s.knowledge_base_dir)
        if not d.exists():
            return []
        return [
            Document(id=f"kb:{p.stem}", source="knowledge_base", title=p.stem,
                     content=p.read_text(encoding="utf-8"), meta={"path": str(p)})
            for p in sorted(d.glob("*.md"))
        ]

    def retrieve_knowledge(self, query: str, k: int = 4) -> ToolResult:
        if self._store is None:
            self._store = VectorStore(self.embedder)
            self._store.add(self._load_kb())
        chunks: list[RetrievedChunk] = self._store.search(query, k) if len(self._store) else []
        return ToolResult("retrieve_knowledge", True,
                          f"retrieved {len(chunks)} chunk(s) from {len(self._store)} indexed", chunks)

    # --- tool: quantitative metrics over the period data ------------------
    def compute_metrics(self, documents: list[Document]) -> ToolResult:
        text = "\n".join(d.content for d in documents)
        lines = [ln for ln in text.splitlines() if ln.strip()]
        commits = sum(d.meta.get("count", 0) for d in documents if d.source == "git_commits")
        metrics = {
            "documents": len(documents),
            "sources": sorted({d.source for d in documents}),
            "commits": commits,
            "issues_detected": sum(bool(_ISSUE_RE.search(ln)) for ln in lines),
            "wins_detected": sum(bool(_WIN_RE.search(ln)) for ln in lines),
        }
        return ToolResult("compute_metrics", True,
                          f"{metrics['wins_detected']} wins / {metrics['issues_detected']} issues", metrics)

    # --- tool: recall the previous retrospective for trend comparison -----
    def recall_last_retro(self, period: str) -> ToolResult:
        prev = self.cache.get("retro:last")
        summary = prev.get("summary", "") if isinstance(prev, dict) else ""
        return ToolResult("recall_last_retro", bool(summary),
                          "found previous retro" if summary else "no previous retro", summary)

    # --- tool: LLM synthesis into the final structured report -------------
    def synthesize_retro(self, brief: dict[str, Any]) -> ToolResult:
        report = self.llm.generate_retro(brief)
        return ToolResult("synthesize_retro", True, f"model={self.llm.model}", report)

    def describe(self) -> list[dict[str, str]]:
        return list(TOOL_CATALOG)


TOOL_CATALOG = (
    {"name": "fetch_period_data", "description": "Pull work-period documents from business-system connectors."},
    {"name": "retrieve_knowledge", "description": "RAG: retrieve relevant knowledge-base chunks for grounding."},
    {"name": "compute_metrics", "description": "Compute quantitative metrics (commits, wins, issues) over the data."},
    {"name": "recall_last_retro", "description": "Recall the previous retrospective to compare trends."},
    {"name": "synthesize_retro", "description": "Synthesize the final structured retrospective via the LLM."},
)
