# retro-agent

[![CI](https://github.com/LancyZhao/retro-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/LancyZhao/retro-agent/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

> An AI **retrospective & summary assistant**: a small, pluggable **Agent platform**
> that pulls work-period data from business systems (OA / Git / ticket connectors),
> grounds it with **RAG** over a knowledge base, and produces a structured
> retrospective — summary, highlights, issues, root causes, and action items.

Runs **fully offline with zero secrets** (deterministic mock model) so anyone can
`docker compose up` and see it work; point the config at any OpenAI-compatible
endpoint to use a real LLM.

```
                 ┌─────────────── Connectors (pluggable) ───────────────┐
   OA / 日报 ──▶ │  mock_oa      markdown_logs      git_commits   ...    │
   Git / Jira ─▶ └───────────────────────┬──────────────────────────────┘
                                          ▼  Documents
                        ┌──────────────  RetroAgent  ──────────────┐
                        │  fetch → metrics → RAG retrieve →          │
   Knowledge base ─▶ RAG│  recall last retro → LLM synthesize        │ ─▶ RetroReport
   (vector store)       │  (every step recorded in a trace)          │     (JSON / Web / CLI)
                        └───────────────────┬───────────────────────┘
                              LLM (OpenAI-compatible)  ·  Redis cache (optional)
```

## Quickstart (offline, no API key)

```bash
pip install -e ".[web,dev]"      # or: make dev
pytest -q                        # core engine is stdlib-only; tests need no network
python -m app.cli --period 2026-W41          # generate a retrospective on the CLI
uvicorn app.main:app --reload                # then open http://localhost:8000
```

Or everything in containers (app + Redis):

```bash
docker compose up --build        # open http://localhost:8000
```

## 对应岗位能力（JD → 实现）

| 岗位要求 | 在本项目中的落点 |
| --- | --- |
| 基于 Agent 平台构建 AI 智能体 | `app/agent/orchestrator.py` 显式编排 5 个工具并记录 trace |
| 与 OA/ERP/CRM/HR 等业务系统集成 | `app/connectors/` 可插拔连接器 + 注册表，新增系统=实现 `fetch()` |
| 知识库 / RAG | `app/rag/`（嵌入 + 内存向量库，离线确定性可跑） |
| Prompt 工程 | `app/llm/prompts.py` 统一管理，强制 JSON Schema 输出 |
| 模型技术调研 / 评估 / 选型 | `app/eval/run_eval.py` 固定用例打分，换模型只改配置 |
| 模型推理部署 / provider 适配 | `app/llm/client.py` 对接任意 OpenAI 兼容端点（vLLM/SGLang/Ollama/云 API） |
| Web 开发（python web） | FastAPI 服务 + 极简前端 `web/` |
| 平台运维 / 故障排查 | `/health` 探活、连接器自检、Redis 不可用自动降级为内存缓存 |
| Docker / K8S / Redis | `Dockerfile`、`docker-compose.yml`、`deploy/k8s.yaml`、`app/cache.py` |
| 自动化办公 / 决策质量 | 把分散的日报/提交/工单自动汇成可执行的复盘与 action items |

## Using a real LLM

Everything defaults to an offline deterministic model. To use a real one, set
environment variables (see `.env.example`) — no code change:

```bash
export LLM_API_KEY=sk-...            # your key
export LLM_BASE_URL=https://api.openai.com/v1   # or a vLLM/SGLang/Ollama endpoint
export LLM_MODEL=gpt-4o-mini
```

The client calls a standard `/chat/completions` with JSON mode, so any
OpenAI-compatible server works. Embeddings are offline by default; set
`EMBED_BASE_URL` + `EMBED_API_KEY` to use a hosted embedding model.

## Add a connector (e.g. a real CRM/ERP)

```python
# app/connectors/my_crm.py
from app.connectors.base import Connector
from app.schemas import Document

class MyCRMConnector(Connector):
    name = "my_crm"
    def __init__(self, settings): self.s = settings
    def fetch(self, period=None) -> list[Document]:
        rows = call_crm_api(period)          # your integration
        return [Document(id=r.id, source=self.name, title=r.title,
                         content=r.body, timestamp=r.ts) for r in rows]
```

Register it in `app/connectors/registry.py` and it immediately shows up in the
CLI, API (`/api/connectors`) and web UI.

## Model evaluation

```bash
python -m app.eval.run_eval      # scores schema validity, grounding, issue recall
# writes eval_results/scorecard.json; swap LLM_MODEL to compare models fairly
```

## Project layout

```
app/
  config.py          settings (stdlib, .env loader)
  schemas.py         dataclasses: Document, RetroReport, ActionItem, ...
  llm/               provider-agnostic client (+ offline mock) & prompts
  rag/               embeddings (offline hash / remote) + in-memory vector store
  connectors/        base + registry + mock_oa / markdown_logs / git_commits
  agent/             Toolbox (5 tools) + RetroAgent orchestrator (with trace)
  eval/              model/prompt scoring harness
  cache.py           Redis cache with in-memory fallback
  main.py / cli.py   FastAPI service / CLI
web/                 minimal UI (templates + static)
deploy/k8s.yaml      Deployment + Service + Redis (readiness/liveness probes)
tests/               stdlib-only core tests + importorskip'd API test
```

## Status & limitations (honest)

- A **portfolio/demo** project, not a production system. The default model is a
  deterministic mock; the vector store is in-memory; connectors other than
  `git_commits` use sample data.
- No auth on the API — add a reverse proxy / token before any real deployment.

## Roadmap

- Real connectors (Jira, 企业微信/飞书 OA) behind the same interface
- Rerank + a persistent vector DB; scheduled weekly retros
- Function-calling agent loop when run against a tool-capable model
- Simple BI charts for the metrics block

## License

MIT © LancyZhao

