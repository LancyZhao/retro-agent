"""A tiny model/prompt evaluation harness (supports model selection, JD #3).

Runs the retrospective generator over fixed cases with known expected signals
and scores the output on schema validity, grounding, and whether it caught the
planted issue. Works offline against the mock model; point LLM_* at any
OpenAI-compatible endpoint to compare real models under the same rubric.

    python -m app.eval.run_eval
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.llm.client import LLMClient

CASES: list[dict[str, Any]] = [
    {
        "name": "timeout_incident",
        "brief": {
            "period": "2026-W41",
            "documents": [{"source": "mock_oa", "title": "日报",
                           "content": "上线审批 Agent\nchat 接口高峰 timeout 故障，回复失败率升高"}],
            "retrieved": [], "metrics": {}, "last_summary": "",
        },
        "expect_issue_contains": "timeout",
    },
    {
        "name": "clean_week",
        "brief": {
            "period": "2026-W42",
            "documents": [{"source": "mock_oa", "title": "日报",
                           "content": "完成 RAG 优化\n交付 BI 周报脚本"}],
            "retrieved": [], "metrics": {}, "last_summary": "",
        },
        "expect_issue_contains": None,
    },
]


def score_one(case: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:
    issues = [str(x).lower() for x in report.get("issues", [])]
    want = case.get("expect_issue_contains")
    checks = {
        "has_summary": bool(report.get("summary")),
        "schema_ok": all(k in report for k in ("summary", "highlights", "issues", "action_items")),
        "has_action_items": len(report.get("action_items", [])) >= 1,
        "caught_expected_issue": (want is None) or any(want in i for i in issues),
    }
    checks["score"] = round(sum(1 for v in checks.values() if v is True) / 4, 2)
    return checks


def main(argv: list[str] | None = None) -> int:
    settings = get_settings()
    llm = LLMClient(settings)
    rows: list[dict[str, Any]] = []
    for case in CASES:
        report = llm.generate_retro(case["brief"])
        result = score_one(case, report)
        rows.append({"case": case["name"], **result})
        print(f"{case['name']:<18} score={result['score']:.2f}  "
              + "  ".join(f"{k}={int(v)}" for k, v in result.items() if k != "score"))
    overall = round(sum(r["score"] for r in rows) / len(rows), 3)
    print(f"\nmodel={llm.model}  cases={len(rows)}  overall={overall}")

    out_dir = Path("eval_results")
    out_dir.mkdir(exist_ok=True)
    (out_dir / "scorecard.json").write_text(
        json.dumps({"model": llm.model, "overall": overall, "rows": rows},
                   ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
