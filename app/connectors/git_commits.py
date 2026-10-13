"""Connector: Git commit history (a real integration via `git log`).

If the path is not a git repo or git is unavailable, returns [] gracefully so
the rest of the pipeline (and CI) still runs.
"""
from __future__ import annotations

import subprocess

from app.config import Settings
from app.connectors.base import Connector
from app.schemas import Document


class GitCommitsConnector(Connector):
    name = "git_commits"

    def __init__(self, settings: Settings) -> None:
        self.repo = settings.git_repo_path

    def _git(self, *args: str) -> str:
        return subprocess.run(
            ["git", "-C", self.repo, *args],
            capture_output=True, text=True, timeout=15, check=True,
        ).stdout

    def fetch(self, period: str | None = None) -> list[Document]:
        try:
            # one line per commit: hash<TAB>ISO-date<TAB>subject
            out = self._git("log", "-n", "100", "--no-merges",
                            "--pretty=format:%h\t%cs\t%s")
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired,
                FileNotFoundError):
            return []
        lines = [ln for ln in out.splitlines() if ln.strip()]
        if not lines:
            return []
        body = "\n".join(ln.split("\t", 2)[-1] for ln in lines)
        return [Document(
            id="git:log", source=self.name,
            title=f"{len(lines)} recent commits", content=body,
            meta={"count": len(lines), "repo": self.repo},
        )]

    def health(self) -> dict[str, object]:
        try:
            self._git("rev-parse", "--is-inside-work-tree")
            return {"connector": self.name, "ok": True, "detail": f"repo={self.repo}"}
        except Exception as exc:  # noqa: BLE001
            return {"connector": self.name, "ok": False, "detail": str(exc)[:120]}
