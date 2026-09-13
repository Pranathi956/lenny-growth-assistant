# Architecture

## Overview

```
┌──────────────┐      REST/JSON       ┌────────────────┐
│  React (Vite)│ ───────────────────► │   FastAPI       │
│  Chat + Artifact Viewer             │   backend       │
└──────────────┘ ◄─────────────────── └────────────────┘
                                          │        │
                             ┌────────────┘        └────────────┐
                             ▼                                    ▼
                   ┌───────────────────┐                ┌──────────────────┐
                   │ PostgreSQL         │                │ LLM provider      │
                   │ sessions/messages/ │                │ layer (toggle):   │
                   │ artifacts          │                │ Groq  | Ollama    │
                   └───────────────────┘                └──────────────────┘
                             ▲
                             │
                   ┌───────────────────┐
                   │ In-memory TF-IDF   │
                   │ index over local   │
                   │ transcript .txt    │
                   │ files              │
                   └───────────────────┘
```

## Database schema

- `sessions(id, created_at, user_label, llm_provider, meta)`
- `messages(id, session_id, role, content, sources[json], created_at)`
- `artifacts(id, session_id, kind, title, content, created_at)`

`sources` is stored per-message as JSON (`[{transcript_id, title, snippet}]`) so
a past conversation remains auditable — you can see exactly which transcript
excerpts justified a given answer, even after the transcript file changes.

## API endpoints

| Method | Path                        | Purpose |
|--------|------------------------------|---------|
| GET    | `/health`                   | DB, provider, and index status |
| POST   | `/sessions`                 | Create a session |
| GET    | `/sessions/{id}`            | Fetch session metadata |
| GET    | `/sessions/{id}/messages`   | Fetch conversation history |
| POST   | `/chat`                     | Send a message, get a grounded reply |
| POST   | `/artifacts`                | Generate a Markdown/HTML artifact |

Request/response contracts are enforced by Pydantic models in `app/schemas.py`;
FastAPI returns structured 422s on validation failure automatically, and a
global exception handler (`app/main.py`) turns unexpected errors into a
logged, clean 500 instead of leaking a stack trace to the client.

## Ingestion / retrieval flow

1. `.txt` files in `backend/data/transcripts/` (filename = episode title) are
   read at startup and split into ~800-word overlapping chunks
   (`agent/rag.py:_chunk_text`).
2. A TF-IDF vectorizer + cosine similarity provides retrieval
   (`agent/rag.py:TranscriptIndex`).
3. **Why TF-IDF instead of embeddings/pgvector:** the brief requires the demo
   to run fully on local Ollama, with no assumption of external API access.
   TF-IDF needs no network call and no model download, so retrieval keeps
   working even with zero internet access. It's a deliberate v1 trade-off —
   swapping in `pgvector` + a local embedding model (e.g. via Ollama's
   embedding endpoint) is a contained change limited to `agent/rag.py` and one
   new Alembic-style migration; nothing else in the system depends on TF-IDF
   specifically.
4. Refresh: calling `TranscriptIndex.load()` again (exposed via the ingestion
   script, or an admin endpoint you can add) re-reads the directory — no
   restart required for new transcripts.

## Agent layer & routing

`agent/llm_provider.py` exposes a single `complete(system, user, provider_override)`
function used by every route. Callers never know which provider actually
answered until they inspect the returned `provider_used` value. This is the
"agent layer" required by the brief — implemented directly against the
Groq's OpenAI-compatible API and Ollama's REST API rather than via the Claude Agent SDK/Pi
Coding Agent packages, to keep the dependency surface small enough to run
fully offline for the local-model demo; the seam (`complete()`) is exactly
where you'd swap in either SDK if the client's infra later requires it.

**Routing** (`routers/chat.py:_routing_decision`) is a small deterministic
keyword router: messages mentioning "ship 30" / "essay" go to the Ship 30
skill (`agent/skills/ship30.py`), everything else goes to grounded Q&A. This
was chosen over an LLM-based router for v1 because it's free, instant, and
fully predictable to test (`tests/test_chat_routing.py`) — an LLM router adds
latency and a second point of failure for a two-way decision that a keyword
match handles correctly in practice. If skill count grows past ~3-4, revisit.

## Model toggle & fallback

`Settings.llm_provider` (env var `LLM_PROVIDER`) sets the default; the
frontend's visible toggle sends a per-request override. If the selected
provider is unreachable and `ENABLE_PROVIDER_FALLBACK=true`, the layer
automatically retries on the other provider and reports which one actually
answered — so a demo doesn't silently fail if, say, Ollama isn't running yet.

## Security — artifact rendering

Generated HTML is treated as **fully untrusted**:
1. The system prompt instructs the model not to rely on JavaScript.
2. The backend strips `<script>` tags and inline `on*=` event handlers as a
   defense-in-depth net (`routers/artifacts.py`).
3. The frontend renders HTML artifacts inside `<iframe sandbox="allow-same-origin">`
   with **no `allow-scripts`** — so even if a script tag slipped through, the
   browser will not execute it. Markdown artifacts go through `react-markdown`,
   which does not execute embedded raw HTML by default.

The evaluator can verify this by asking the assistant to generate an HTML
artifact containing a `<script>alert(1)</script>` and confirming nothing fires.

## Deployment topology

Three containers via Docker Compose: `db` (Postgres), `backend` (FastAPI),
`frontend` (Vite dev server). `backend` reaches host-installed Ollama via
`host.docker.internal` (Linux needs the `extra_hosts` entry included in
`docker-compose.yml`; Docker Desktop on Mac/Windows supports this natively).

## Observability

Structured logs (`app/main.py` logging config) are emitted per-request with
module-scoped loggers (`lenny.chat`, `lenny.rag`, `lenny.llm`, etc.) so a log
line's source is immediately clear. The `/health` endpoint reports DB
reachability, which provider is configured, whether Ollama is actually
reachable right now, and how many transcript chunks are indexed — the three
things most likely to silently break a demo.

## Resilience

- Missing `ANTHROPIC_API_KEY` -> `ProviderUnavailable`, caught and either
  falls back or returns a clear 503 (never a raw exception).
- Ollama not running -> same path, with a message telling the operator
  exactly what to check.
- Empty retrieval results -> the system prompt explicitly handles "no
  excerpts found" rather than the model silently making something up.
- DB connection failure -> caught by the global exception handler, logged,
  clean 500 to the client instead of a stack trace or hang.

## Future improvements (out of scope for this submission)

- pgvector + real embeddings for semantic retrieval.
- Streaming token responses over SSE/WebSocket.
- User auth and per-user session ownership.
- A feedback endpoint feeding the "grounded and useful" success metric in the PRD.
