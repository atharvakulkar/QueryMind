# QueryMind

Enterprise-oriented **Text-to-SQL BI agent** (resume / academic project). It connects natural language to **read-only** PostgreSQL queries using **MCP** for schema discovery, **LangChain + Groq** for generation, and **sqlglot** for policy validation before execution.

## What is implemented (Phases 0–5)

| Phase | What you get |
|-------|----------------|
| **0–2** | FastAPI app, asyncpg pool, health/readiness, demo dataset route, optional gated ad-hoc SQL, MCP stdio server (`list_tables`, `describe_table`, `export_schema_summary`) |
| **3** | NL→SQL **agent**: schema linking → SQL draft → **SqlPolicyValidator** (allowlisted identifiers, `LIMIT`, read-only) → execute → retry on failure (see `AGENT_MAX_RETRIES`) |
| **4** | **Streamlit** UI + modern **React / Vite** dashboard — both talk to the API (`POST /api/v1/agent/query`) — no database credentials in the browser |
| **5** | **Conversational memory** (multi-turn Q&A), LLM-generated **executive insights**, **chart PNG export**, improved SQL guardrails, **Docker** + **GitHub Actions CI** |

## Repository layout

```text
core/           Settings, logging, shared exceptions
database/       ConnectionManager, SchemaIntrospector, SchemaCatalog
backend/        FastAPI app, routers, Pydantic schemas, agent (LangChain + Groq)
mcp_server/     MCP stdio server + McpSchemaClient (used by the API agent)
frontend/       Streamlit app (api_client, components)
tests/          pytest (HTTP, SQL guard, introspection, agent mocks)
```

## Features

- **FastAPI** — Pydantic models, global `QueryMindError` handlers, OpenAPI at `/docs`
- **PostgreSQL** — `asyncpg` pool, `GET /ready`, statement timeout from settings
- **MCP** — separate process for schema tools; API spawns an MCP stdio session when the agent runs
- **Agent** — Groq (`GROQ_MODEL`), enforced JSON schema-link step, **sqlglot** AST checks against `SchemaCatalog`, configurable retries
- **Conversational Memory** — rolling window of prior Q&A turns passed to the LLM for multi-turn analysis
- **Executive Insights** — LLM generates a 1–2 sentence summary of each query result
- **React / Vite UI** — chat interface, data tables with CSV export, interactive charts with PNG export, session persistence via `localStorage`
- **Streamlit** — legacy question input, generated SQL + schema link, results table, CSV download, error messages from API
- **Docker** — multi-stage `Dockerfile` + `docker-compose.yml` for one-command local deployment
- **CI/CD** — GitHub Actions runs `pytest` and `eslint` on every PR
- **Tests** — `pytest` for routes, guards, introspector stub, agent (mocked LLM / MCP / DB)

## Requirements

- **Python 3.10+** (3.11+ recommended)
- **PostgreSQL** with a **read-only** role for production-style demos
- **Groq API key** for `POST /api/v1/agent/query` (set `GROQ_API_KEY`)

## Quick start

```powershell
cd D:\Atharva_Projects\QueryMind
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
copy .env.example .env
# Edit .env: DATABASE_URL, GROQ_API_KEY, and any optional tuning (see below)
```

### Environment variables (summary)

Copy from [`.env.example`](.env.example) and adjust. Common entries:

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | **Required.** Async PostgreSQL URL (read-only user recommended) |
| `GROQ_API_KEY` | **Required for the agent.** Groq Cloud API key |
| `GROQ_MODEL` | Groq chat model id (default: `llama-3.3-70b-versatile`) |
| `MAX_QUERY_ROWS` | Cap rows returned by the API / agent |
| `STATEMENT_TIMEOUT_SECONDS` | Server-side Postgres `statement_timeout` |
| `AGENT_MAX_RETRIES` | Max attempts for validate + execute loop (default `3`) |
| `ALLOW_ADHOC_SQL` | Set `true` only for local dev to enable `POST /api/v1/internal/execute-read` |
| `LOG_AGENT_SQL` | Log generated SQL (set `false` if prompts are sensitive) |
| `MCP_SERVER_CWD` | Working directory for MCP subprocess (defaults to project root) |
| `QUERYMIND_API_URL` | Streamlit: API base URL if not `http://127.0.0.1:8000` |

## Run the API

```powershell
uvicorn backend.main:create_app --factory --host 127.0.0.1 --port 8000
```

Useful endpoints:

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Liveness |
| `GET` | `/ready` | Readiness (DB ping) |
| `GET` | `/api/v1/demo/dataset` | Fixed safe query (`current_database`, `now`) |
| `POST` | `/api/v1/agent/query` | NL→SQL agent (`{"question": "..."}`, optional `max_rows`) |
| `POST` | `/api/v1/internal/execute-read` | Ad-hoc `SELECT` only if `ALLOW_ADHOC_SQL=true` |

Interactive docs: http://127.0.0.1:8000/docs

## Run the Streamlit UI

From the **project root** (same virtualenv):

```powershell
streamlit run frontend/app.py
```

Override the API URL via sidebar or `QUERYMIND_API_URL`. The UI never connects to Postgres directly.

## Run the MCP schema server (stdio)

For external MCP clients (Inspector, Claude Desktop, Cursor):

```powershell
python -m mcp_server.server
```

Uses `DATABASE_URL` from the environment. **Do not** print to stdout (protocol uses it); logs go to **stderr**.

Example **Cursor / Claude Desktop** configuration (adjust `cwd` and `DATABASE_URL`):

```json
{
  "mcpServers": {
    "querymind-schema": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "D:\\Atharva_Projects\\QueryMind",
      "env": {
        "DATABASE_URL": "postgresql://readonly:password@host:5432/dbname"
      }
    }
  }
}
```

## Tests

```powershell
python -m pytest tests -q
```

## Security notes

- Prefer a **read-only** PostgreSQL role; DB permissions are the primary control.
- Keyword guards in `ConnectionManager` are **best-effort**; the agent path adds **sqlglot** + catalog allowlisting.
- Keep `ALLOW_ADHOC_SQL=false` outside trusted local databases.
- Store **Groq** and **database** secrets only in environment variables or a secrets manager, not in the Streamlit app.

## Documentation

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — components, agent flow, trust boundaries

## Docker (one-command local stack)

Requires Docker and Docker Compose.

```powershell
# Set your Groq key on the host, then:
$env:GROQ_API_KEY="your_key"
docker-compose up --build
```

Visit http://localhost:8000 — the FastAPI server serves both the API and the compiled React UI.

## Roadmap

- Server-side conversation persistence (PostgreSQL-backed threads)
- Role-based access and user authentication
- Optional GitHub Actions workflow for Docker build + push
