"""Connector interface + registry.

A Connector adapts an external business system (OA/ERP/CRM/HR, Git, a ticket
system, ...) into a uniform list of `Document`s the agent can reason over.
Adding support for a new system = implement `fetch()` and `@register` it.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from app.schemas import Document


class Connector(ABC):
    #: short, unique id used in config and the API (e.g. "mock_oa").
    name: str = "base"

    @abstractmethod
    def fetch(self, period: str | None = None) -> list[Document]:
        """Return documents for the given period (free-form, e.g. '2026-W41')."""
        raise NotImplementedError

    def health(self) -> dict[str, object]:
        """Lightweight reachability check used by /health and ops tooling."""
        return {"connector": self.name, "ok": True, "detail": "ready"}
