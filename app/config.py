"""Configuration loaded from environment variables (and an optional .env file).

Kept dependency-free on purpose: the core engine must import without
pydantic-settings installed. The web layer may still use pydantic separately.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _load_dotenv(path: str = ".env") -> None:
    """Minimal .env loader (no external dependency). Does not override real env."""
    p = Path(path)
    if not p.exists():
        return
    for raw in p.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key, val = key.strip(), val.strip().strip('"').strip("'")
        os.environ.setdefault(key, val)


@dataclass(frozen=True)
class Settings:
    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"
    llm_provider: str = "auto"  # auto | openai | mock

    embed_api_key: str = ""
    embed_base_url: str = ""
    embed_model: str = "text-embedding-3-small"

    redis_url: str = "redis://localhost:6379/0"

    worklogs_dir: str = "sample_data/worklogs"
    knowledge_base_dir: str = "sample_data/knowledge_base"
    git_repo_path: str = "."

    app_env: str = "dev"
    log_level: str = "INFO"

    @property
    def use_mock_llm(self) -> bool:
        return self.llm_provider == "mock" or not self.llm_api_key


def get_settings() -> Settings:
    _load_dotenv()
    g = os.environ.get
    return Settings(
        llm_api_key=g("LLM_API_KEY", ""),
        llm_base_url=g("LLM_BASE_URL", "https://api.openai.com/v1"),
        llm_model=g("LLM_MODEL", "gpt-4o-mini"),
        llm_provider=g("LLM_PROVIDER", "auto"),
        embed_api_key=g("EMBED_API_KEY", ""),
        embed_base_url=g("EMBED_BASE_URL", ""),
        embed_model=g("EMBED_MODEL", "text-embedding-3-small"),
        redis_url=g("REDIS_URL", "redis://localhost:6379/0"),
        worklogs_dir=g("WORKLOGS_DIR", "sample_data/worklogs"),
        knowledge_base_dir=g("KNOWLEDGE_BASE_DIR", "sample_data/knowledge_base"),
        git_repo_path=g("GIT_REPO_PATH", "."),
        app_env=g("APP_ENV", "dev"),
        log_level=g("LOG_LEVEL", "INFO"),
    )
