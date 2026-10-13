"""Prompt templates (prompt engineering lives here, not scattered in code)."""
from __future__ import annotations

import json
from typing import Any

SYSTEM_RETRO = (
    "You are a meticulous engineering/operations retrospective assistant for a "
    "company's internal Agent platform. You are given work-period data pulled "
    "from business systems (OA reports, Git commits, tickets) plus retrieved "
    "knowledge-base context. Produce an HONEST, evidence-grounded retrospective. "
    "Never invent facts that are not supported by the provided context. "
    "If evidence is thin, say so. Respond with STRICT JSON only, no prose, "
    "matching exactly this schema:\n"
    "{\n"
    '  "summary": string,                      // 3-5 sentences\n'
    '  "highlights": [string],                 // concrete wins, each cites what happened\n'
    '  "issues": [string],                     // problems observed\n'
    '  "root_causes": [string],                // why the issues happened\n'
    '  "action_items": [                       // concrete, assignable next steps\n'
    '     {"description": string, "owner": string, "priority": "high|medium|low", "due": string}\n'
    "  ]\n"
    "}\n"
)


def build_retro_messages(brief: dict[str, Any]) -> list[dict[str, str]]:
    """Render the structured brief into chat messages for an OpenAI-compatible API."""
    docs = brief.get("documents", [])
    doc_block = "\n\n".join(
        f"[{i + 1}] source={d['source']} title={d['title']}\n{d['content'][:1200]}"
        for i, d in enumerate(docs)
    ) or "(no period documents)"

    kb = brief.get("retrieved", [])
    kb_block = "\n".join(
        f"- ({c['source']}:{c['title']}, score={c['score']:.2f}) {c['snippet'][:280]}"
        for c in kb
    ) or "(no knowledge-base matches)"

    metrics = json.dumps(brief.get("metrics", {}), ensure_ascii=False)
    last = brief.get("last_summary") or "(no previous retrospective)"

    user = (
        f"PERIOD: {brief.get('period', 'unknown')}\n\n"
        f"=== PERIOD DATA (from connectors) ===\n{doc_block}\n\n"
        f"=== KNOWLEDGE-BASE CONTEXT (RAG) ===\n{kb_block}\n\n"
        f"=== QUANTITATIVE METRICS ===\n{metrics}\n\n"
        f"=== PREVIOUS RETROSPECTIVE SUMMARY ===\n{last}\n\n"
        "Write the retrospective as strict JSON per the schema. "
        "Prefer action items that address the stated root causes, and reference "
        "the previous retrospective to note what improved or regressed."
    )
    return [
        {"role": "system", "content": SYSTEM_RETRO},
        {"role": "user", "content": user},
    ]
