"""Connector registry: discover and instantiate connectors by name."""
from __future__ import annotations

from app.config import Settings
from app.connectors.base import Connector
from app.connectors.git_commits import GitCommitsConnector
from app.connectors.markdown_logs import MarkdownLogsConnector
from app.connectors.mock_oa import MockOAConnector

# name -> factory(settings) -> Connector
_FACTORIES = {
    MockOAConnector.name: MockOAConnector,
    MarkdownLogsConnector.name: MarkdownLogsConnector,
    GitCommitsConnector.name: GitCommitsConnector,
}


def available() -> list[str]:
    return sorted(_FACTORIES)


def build(names: list[str] | None, settings: Settings) -> list[Connector]:
    chosen = names or available()
    out: list[Connector] = []
    for n in chosen:
        factory = _FACTORIES.get(n)
        if factory is None:
            raise KeyError(f"unknown connector: {n!r} (available: {available()})")
        out.append(factory(settings))
    return out
