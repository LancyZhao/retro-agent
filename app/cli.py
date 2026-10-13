"""Command-line entry point: generate a retrospective and print it.

    retro --period 2026-W41            # human-readable
    retro --period 2026-W41 --format json
"""
from __future__ import annotations

import argparse
import json

from app.agent.orchestrator import RetroAgent
from app.schemas import RetroReport


def render_text(r: RetroReport) -> str:
    lines = [f"# Retrospective — {r.period}   (model: {r.model})", "", r.summary, ""]
    lines.append("## Highlights")
    lines += [f"  + {h}" for h in r.highlights] or ["  (none)"]
    lines.append("## Issues")
    lines += [f"  - {i}" for i in r.issues] or ["  (none)"]
    if r.root_causes:
        lines.append("## Root causes")
        lines += [f"  * {c}" for c in r.root_causes]
    lines.append("## Action items")
    lines += [f"  [{a.priority}] {a.description} (owner: {a.owner})" for a in r.action_items] \
        or ["  (none)"]
    lines.append("## Metrics")
    lines.append("  " + json.dumps(r.metrics, ensure_ascii=False))
    lines.append("## Agent trace")
    lines += [f"  {n + 1}. {step}" for n, step in enumerate(r.trace)]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="retro", description="AI retrospective assistant")
    p.add_argument("--period", default="2026-W41")
    p.add_argument("--connectors", default="",
                   help="comma-separated connector names (default: all)")
    p.add_argument("--format", choices=["text", "json"], default="text")
    args = p.parse_args(argv)
    connectors = [c.strip() for c in args.connectors.split(",") if c.strip()] or None
    report = RetroAgent().run(period=args.period, connectors=connectors)
    if args.format == "json":
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(render_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
