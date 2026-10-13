"""Provider-agnostic LLM client.

- With an API key: talks to any OpenAI-compatible `/chat/completions` endpoint
  (OpenAI, vLLM/SGLang `--served-model`, Ollama, DashScope, etc.) via urllib,
  so model selection is a config change, not a code change.
- Without a key (or LLM_PROVIDER=mock): a deterministic offline model so the
  whole app runs in CI / demos with no network and no secrets.
"""
from __future__ import annotations

import json
import re
import urllib.request
from typing import Any

from app.config import Settings
from app.llm.prompts import build_retro_messages


class LLMClient:
    def __init__(self, settings: Settings) -> None:
        self.s = settings
        self.model = "mock-retro-v1" if settings.use_mock_llm else settings.llm_model

    @property
    def is_mock(self) -> bool:
        return self.s.use_mock_llm

    # ---- public API -------------------------------------------------------
    def chat(self, messages: list[dict[str, str]], temperature: float = 0.2,
             json_mode: bool = False) -> str:
        if self.s.use_mock_llm:
            return self._mock_chat(messages)
        return self._openai_chat(messages, temperature, json_mode)

    def generate_retro(self, brief: dict[str, Any]) -> dict[str, Any]:
        if self.s.use_mock_llm:
            return _mock_retro(brief)
        raw = self._openai_chat(build_retro_messages(brief), 0.2, json_mode=True)
        return self._safe_json(raw)

    # ---- OpenAI-compatible transport -------------------------------------
    def _openai_chat(self, messages: list[dict[str, str]], temperature: float,
                     json_mode: bool) -> str:
        url = self.s.llm_base_url.rstrip("/") + "/chat/completions"
        payload: dict[str, Any] = {
            "model": self.s.llm_model, "messages": messages, "temperature": temperature,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        req = urllib.request.Request(
            url, data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {self.s.llm_api_key}"},
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        return body["choices"][0]["message"]["content"]

    @staticmethod
    def _safe_json(raw: str) -> dict[str, Any]:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            m = re.search(r"\{.*\}", raw, re.DOTALL)
            return json.loads(m.group(0)) if m else {"summary": raw.strip()}

    def _mock_chat(self, messages: list[dict[str, str]]) -> str:
        last = messages[-1]["content"] if messages else ""
        return f"[mock-retro-v1] {last[:160]}"


_ISSUE_WORDS = ("fail", "error", "bug", "blocked", "block", "delay", "regress",
                "timeout", "incident", "故障", "错误", "失败", "阻塞", "延期", "回退", "超时")
_WIN_WORDS = ("完成", "交付", "上线", "发布", "Done", "Shipped", "Launched", "Delivered")


def _mock_retro(brief: dict[str, Any]) -> dict[str, Any]:
    """Deterministic retrospective derived from the brief (offline, no network)."""
    docs = brief.get("documents", [])
    period = brief.get("period", "unknown")
    retrieved = brief.get("retrieved", [])
    highlights: list[str] = []
    issues: list[str] = []
    commits: list[str] = []
    for d in docs:
        src = d.get("source", "")
        for raw in d.get("content", "").splitlines():
            s = raw.strip("-*• \t")
            if not s or s.startswith("#"):
                continue
            if src == "git_commits":
                commits.append(s)
            if any(w in s.lower() for w in _ISSUE_WORDS) and s not in issues:
                issues.append(s)
            elif any(k in s for k in _WIN_WORDS) and s not in highlights:
                highlights.append(s)
    for c in commits[:3]:
        if (h := f"Shipped: {c}") not in highlights:
            highlights.append(h)
    highlights = highlights[:6] or ["No explicit wins recorded this period."]
    real_issues = issues[:6]
    root_causes = [f"Probable cause behind: {i}" for i in real_issues[:3]]
    if real_issues:
        action_items = [{"description": f"Investigate and resolve: {i}",
                         "owner": "unassigned",
                         "priority": "high" if n == 0 else "medium", "due": ""}
                        for n, i in enumerate(real_issues[:3])]
    else:
        action_items = [{"description": "Maintain cadence; schedule the next retrospective.",
                         "owner": "unassigned", "priority": "low", "due": ""}]
    kb = f" {len(retrieved)} knowledge-base note(s) retrieved for grounding." if retrieved else ""
    summary = (
        f"Retrospective for {period}: ingested {len(docs)} source document(s)"
        f"{f' including {len(commits)} commits' if commits else ''}. "
        f"{len(highlights)} highlight(s) and {len(real_issues)} issue(s) identified.{kb} "
        "(Offline deterministic model; set LLM_API_KEY for a full LLM write-up.)"
    )
    return {"summary": summary, "highlights": highlights,
            "issues": real_issues or ["No blocking issues surfaced in the period data."],
            "root_causes": root_causes, "action_items": action_items}
