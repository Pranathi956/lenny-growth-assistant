# The Lenny Growth Assistant

A full-stack, grounded conversational assistant over Lenny's Podcast
transcripts, with a Ship 30 for 30 essay skill, an in-app Markdown/HTML
artifact viewer, and a visible cloud/local model toggle.

See also: [PRD.md](PRD.md) · [architecture.md](architecture.md) · [design.md](design.md)

## Architecture at a glance

React (Vite) chat UI + artifact viewer ⟷ FastAPI backend ⟷ PostgreSQL, with
a pluggable LLM layer that talks to either the Groq API (free tier) or a local
Ollama model, and an in-memory TF-IDF retrieval index over transcript text
files. Full detail in [architecture.md](architecture.md).

## Prerequisites

- Docker + Docker Compose (recommended path), **or** Python 3.11+ and
  Node.js 20+ to run services natively.
- [Ollama](https://ollama.com) installed on your **host machine** (not
  inside Docker) — the local-model demo is mandatory per the assignment.
- A free Groq API key if you want to demo the cloud path too (optional) — get one at https://console.groq.com/keys, no card required.
- Real transcript `.txt` files for Lenny's Podcast/Newsletter — **the repo
  ships only synthetic placeholder transcripts** in
  `backend/data/transcripts/` (see the README inside that folder). Replace
  them with real content you have rights to use before your actual demo.

## Quickstart (Docker Compose — recommended)

```bash
git clone <your-repo-url>
cd lenny-growth-assistant

cp .env.example .env
# Optional but recommended: get a free Groq API key (no card needed) at
# https://console.groq.com/keys, then set GROQ_API_KEY in .env. This gives
# you the cloud path and automatic fallback if Ollama has a bad day.

# On your HOST machine (not in Docker):
ollama pull llama3.1:8b
ollama serve   # if it isn't already running as a service

docker compose up --build
```

Then open:
- Frontend: http://localhost:5173
- Backend health check: http://localhost:8000/health
- API docs (Swagger): http://localhost:8000/docs

## Running natively (no Docker)

**Backend**
```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env   # edit DATABASE_URL to point at your own Postgres
                           # (Supabase/Railway connection string works fine)
uvicorn app.main:app --reload --port 8000
```

**Frontend** (separate terminal)
```bash
cd frontend
npm install
npm run dev
```

## Environment variables

See [`.env.example`](.env.example) — every variable is documented inline,
including which are required vs. optional and their safe defaults.
`LLM_PROVIDER=ollama` is the default so a clone-and-run demo works fully
offline once a model is pulled.

## Using a hosted Postgres (Supabase / Railway) instead of the Docker `db` service

Create a free Supabase or Railway Postgres instance, copy its connection
string into `DATABASE_URL` in `.env`, and either remove the `db` service
from `docker-compose.yml` or just leave `backend` pointed at the external
URL — `SQLAlchemy` doesn't care which Postgres it talks to.

## Tests

```bash
cd backend
DATABASE_URL="sqlite:///./test.db" python3 -m pytest tests/ -v
```

Tests run against SQLite and don't require Postgres, Ollama, or a Groq
key — they cover health, session CRUD, retrieval correctness, and skill
routing. See `architecture.md` and `PRD.md` for what's *not* covered by
automated tests (an intentional scope choice) plus a manual test plan below.

### Manual test plan (UI)

1. Load the app — confirm the health dot is green and a new session is
   created (network tab: `POST /sessions` returns 200).
2. Ask a question that matches the placeholder transcripts, e.g. *"How should
   I pick an activation metric?"* — confirm a "sources" disclosure appears.
3. Ask something unrelated to the transcripts — confirm the assistant says
   the material doesn't cover it, rather than fabricating an answer.
4. Say *"turn this into an essay for ship 30"* — confirm a longer, structured
   Markdown-formatted response comes back.
5. Click **+ HTML artifact** — confirm it renders in the right panel inside
   an iframe, and that "view raw source" shows the underlying HTML with no
   `<script>` tag able to execute (open dev tools, confirm no alert fires
   even if you ask the model to include one).
6. Toggle the model switch to **Cloud (Groq)** with no API key set —
   confirm you get a clear error, not a silent hang.
7. Stop the `db` container mid-session and send a message — confirm a clean
   5xx with a logged cause (`docker compose logs backend`).

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `/health` shows `ollama_reachable: false` | Ollama not running, or wrong `OLLAMA_BASE_URL` | `ollama serve`; in Docker, confirm `host.docker.internal` resolves (Linux needs the `extra_hosts` entry already in `docker-compose.yml`) |
| Chat returns 503 "No LLM provider reachable" | Both providers unavailable | Check `.env`: is `ANTHROPIC_API_KEY` set (if using cloud), is Ollama serving, is the model pulled (`ollama list`) |
| `sessions` / `messages` tables missing | DB not migrated | Tables auto-create on startup via SQLAlchemy `create_all` — check `docker compose logs backend` for a DB connection error first |
| Frontend can't reach backend | CORS or wrong `VITE_API_BASE_URL` | Confirm backend is on port 8000 and `cors_origins` in `backend/app/config.py` includes your frontend origin |
| `transcripts_indexed: 0` in `/health` | No `.txt` files in `backend/data/transcripts/` | Add transcript files, restart the backend (or wire up the refresh endpoint described in architecture.md) |

## Agent transcripts

Coding-agent session logs go in [`agent-transcripts/`](agent-transcripts/) —
see the README there.

## Demo video checklist

- Camera on, 2–3 minutes.
- State the problem and primary user (from PRD.md).
- Show the product: ask a grounded question, generate an artifact, toggle
  the model.
- Explicitly demonstrate the **local Ollama path working**.
- Cover one real trade-off out loud (e.g. TF-IDF vs. embeddings, or the
  keyword router vs. an LLM router) — pick whichever one you can explain in
  your own words most confidently.
