"""Domain models as plain dataclasses (stdlib only) so the core engine stays
framework-agnostic and unit-testable without pydantic installed."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Document:
    """A unit of context ingested from a connector or the knowledge base."""
    id: str
    source: str              # e.g. "mock_oa", "git_commits", "knowledge_base"
    title: str
    content: str
    timestamp: str = ""      # ISO-8601 when known
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class RetrievedChunk:
    document_id: str
    source: str
    title: str
    snippet: str
    score: float


@dataclass
class ActionItem:
    description: str
    owner: str = "unassigned"
    priority: str = "medium"   # high | medium | low
    due: str = ""


@dataclass
class RetroReport:
    period: str
    summary: str
    highlights: list[str] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)
    root_causes: list[str] = field(default_factory=list)
    action_items: list[ActionItem] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    evidence: list[RetrievedChunk] = field(default_factory=list)
    model: str = ""
    trace: list[str] = field(default_factory=list)  # agent step log

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
