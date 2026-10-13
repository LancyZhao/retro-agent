"""FastAPI service exposing the retrospective agent + a tiny web UI.

Run:  uvicorn app.main:app --reload   (needs the [web] extra installed)
The UI (web/templates/index.html) calls the JSON API with fetch(), so no
multipart/form dependency is required.
"""
from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import __version__
from app.agent.orchestrator import RetroAgent
from app.agent.tools import TOOL_CATALOG
from app.config import get_settings
from app.connectors import registry

settings = get_settings()
app = FastAPI(title="retro-agent", version=__version__,
              description="AI retrospective & summary assistant")
templates = Jinja2Templates(directory="web/templates")
app.mount("/static", StaticFiles(directory="web/static"), name="static")
agent = RetroAgent(settings)


@app.get("/health")
def health() -> dict[str, Any]:
    conns = registry.build(None, settings)
    return {
        "status": "ok",
        "llm": "mock" if agent.llm.is_mock else settings.llm_model,
        "embeddings": agent.embedder.name,
        "cache": agent.cache.backend,
        "connectors": [c.health() for c in conns],
    }


@app.get("/api/tools")
def tools() -> dict[str, Any]:
    return {"tools": list(TOOL_CATALOG)}


@app.get("/api/connectors")
def connectors() -> dict[str, Any]:
    return {"connectors": registry.available()}


@app.post("/api/retro")
def api_retro(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    report = agent.run(
        period=payload.get("period") or "2026-W41",
        connectors=payload.get("connectors") or None,
        query=payload.get("query"),
    )
    return report.to_dict()


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "connectors": registry.available(),
         "llm": "mock" if agent.llm.is_mock else settings.llm_model},
    )
