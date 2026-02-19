# Research Agent

Autonomous technical research agent powered by LangGraph and Ollama (gemma3:12b).

## Quick Start

```bash
docker compose up -d --build    # or: make up
docker compose exec ollama ollama pull gemma3:12b  # or: make pull-model
```

Web UI at http://localhost:3000, API at http://localhost:8000/api/research.

## Architecture

LangGraph state machine with a Plan → Act → Observe → Reflect loop:

- **config.py** — Pydantic settings loaded from `.env` (model, host, timeout, limits)
- **graph/state.py** — `AgentState` Pydantic model carrying all state through the graph
- **graph/nodes.py** — Node functions: `plan_node`, `act_node`, `observe_node`, `reflect_node`, `write_report_node`
- **graph/builder.py** — Compiles the LangGraph `StateGraph`
- **graph/prompts.py** — All prompt templates
- **llm/client.py** — Low-level `OllamaClient` (httpx, `/api/generate`)
- **llm/adapter.py** — `LLMAdapter` singleton used by all nodes
- **tools/** — Tool implementations: `web_search`, `fetch_url`, `local_docs`, `elastic_rag`, `python_sandbox`
- **api/app.py** — FastAPI app (pure JSON API with CORS)
- **api/routers/research.py** — `/api/research` POST, `/api/runs` GET endpoints
- **cli/main.py** — Typer CLI entry point (`research-agent` command)
- **memory/store.py** — SQLite-backed run persistence
- **report/renderer.py** — Post-processes final report markdown

## Configuration

All config via env vars in `.env` (loaded by pydantic-settings):

| Variable | Default | Purpose |
|---|---|---|
| `OLLAMA_HOST` | `http://ollama:11434` | Ollama API endpoint |
| `OLLAMA_MODEL` | `gemma3:12b` | Model to use |
| `OLLAMA_TIMEOUT_SECONDS` | `300` | HTTP timeout for LLM calls |
| `LOG_LEVEL` | `INFO` | Logging level |

## Development

- **Python**: >=3.11, managed with `uv`
- **Linting**: `ruff check .` / `ruff format .` (or `make lint` / `make fmt`)
- **Tests**: `pytest -v` (or `make test`) — uses `pytest-asyncio` with `asyncio_mode = "auto"`
- **Type checking**: `mypy` with strict mode
- **Line length**: 100 chars
- **Ruff rules**: E, F, I, N, W, UP

## Frontend

React SPA in `frontend/`, built with Vite, served by nginx:

- **src/App.jsx** — Main component (form, spinner, report display)
- **src/components/ResearchForm.jsx** — Question input + audience select
- **src/components/ReportView.jsx** — Markdown (marked) + Mermaid diagram rendering
- **src/api.js** — API client (`POST /api/research`, `GET /api/runs`)
- **nginx.conf** — Serves static files, proxies `/api/` to backend, SPA fallback
- **Dockerfile** — Multi-stage: `node:22-alpine` build, `nginx:alpine` serve

## Docker

Three services in `docker-compose.yml`:
- **ollama** — Model server, models stored in `ollama_models` volume
- **api** — FastAPI app, source mounted at `/app`, `.env` loaded via `env_file`
- **frontend** — React SPA served by nginx (port 3000), proxies `/api/` to `api`

## Key Patterns

- All LLM calls go through `get_llm()` singleton from `llm/adapter.py`
- Tools are registered in `TOOL_REGISTRY` dict in `tools/__init__.py`
- Each tool's `.run()` returns a `ToolResult` with `.data` (str) and `.evidence` (list of `EvidenceItem`)
- Graph nodes return dicts that get merged into `AgentState`
- `write_report_node` is the heaviest node (max_tokens=8192); timeout must accommodate this
