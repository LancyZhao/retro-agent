"""Connector: local Markdown worklogs (stand-in for OA/日报 exports)."""
from __future__ import annotations

from pathlib import Path

from app.config import Settings
from app.connectors.base import Connector
from app.schemas import Document


class MarkdownLogsConnector(Connector):
    name = "markdown_logs"

    def __init__(self, settings: Settings) -> None:
        self.dir = Path(settings.worklogs_dir)

    def fetch(self, period: str | None = None) -> list[Document]:
        if not self.dir.exists():
            return []
        docs: list[Document] = []
        for p in sorted(self.dir.glob("*.md")):
            if period and period not in p.stem:
                continue
            text = p.read_text(encoding="utf-8")
            docs.append(Document(
                id=f"md:{p.stem}", source=self.name, title=p.stem,
                content=text, timestamp=p.stem, meta={"path": str(p)},
            ))
        return docs

    def health(self) -> dict[str, object]:
        ok = self.dir.exists()
        return {"connector": self.name, "ok": ok,
                "detail": f"dir={self.dir} exists={ok}"}
