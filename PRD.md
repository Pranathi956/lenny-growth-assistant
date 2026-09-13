# PRD — The Lenny Growth Assistant

## 1. Forward Deployment Brief

**User and problem.** The primary user is an internal product/growth team member
(PM, growth marketer, founder) who wants a fast, trustworthy answer to a product
or growth question grounded in Lenny's Podcast, without listening to hours of
episodes or trusting an LLM's unverified general knowledge. The job-to-be-done:
"give me a defensible, source-linked answer to a growth question, and let me turn
it into shareable content, in one sitting."

**Success metric.** Primary: **% of assistant answers the user rates as
"grounded and useful"** via a lightweight thumbs-up/down (not built in this
version, but the `sources` field on every response is the foundation for it —
see Scope choices). A secondary operational metric: **p95 response latency
under 8s on local Ollama**, since a forward-deployed tool that feels slow will
simply not get used.

**Assumptions** (brief was incomplete on these):
- "The client" is a small internal team, not end-customers — so no auth/multi-
  tenant user system was required; sessions are anonymous and identified by a
  session ID, with an optional free-text `user_label`.
- "Transcripts from Lenny's Podcast" means the user/evaluator supplies their own
  `.txt` transcript files (one per episode) into `backend/data/transcripts/` —
  we do not scrape or redistribute copyrighted transcript text ourselves. The
  repo ships with clearly-labeled synthetic placeholder transcripts so the
  pipeline is testable out of the box.
- "Local model that works comfortably on your machine" means an 8B-class model
  (default: `llama3.1:8b`) rather than assuming access to a GPU workstation.
- Ship 30 essay requests are triggered by explicit user intent (keyword match),
  not silently auto-triggered on every question.

**Scope choices.**
- Included: session-based chat with persistence, TF-IDF retrieval over local
  transcripts, source citations on every answer, a Ship 30 essay skill, Markdown/
  HTML artifact generation with a sandboxed in-app viewer, cloud/local model
  toggle with automatic fallback, structured logging, health endpoint, tests,
  Docker Compose.
- Excluded (documented, not silently dropped): user auth/accounts, streaming
  token-by-token responses, a vector database (pgvector) in favor of in-memory
  TF-IDF (see architecture.md), automated transcript scraping, a feedback/
  rating UI (the data model supports adding it later).
- Why: the brief rewards judgment about what to simplify. Auth and streaming
  add real engineering surface without changing whether the core loop —
  grounded answer -> essay -> artifact -> handoff — actually works.

**Risks and trade-offs.**
- *Hallucination*: mitigated by strict "answer only from provided excerpts"
  system prompting and an explicit instruction to say when material is
  missing — but not eliminated. A production version would add a citation-
  verification pass.
- *Retrieval quality*: TF-IDF is lexical, not semantic — it will miss
  paraphrased questions that don't share vocabulary with the transcript. Traded
  off deliberately for zero external dependencies and full offline operation
  during the local-model demo (see architecture.md).
- *Local-model quality*: an 8B local model will produce noticeably weaker
  essays/answers than a frontier cloud model. This is surfaced to the user via
  the visible model toggle rather than hidden.
- *Latency*: local inference on modest hardware can be slow; the health
  endpoint and structured logs make this diagnosable rather than a silent hang.
- *Unsafe artifact rendering*: model-generated HTML is untrusted by
  construction — see architecture.md "Security."
- *Data leakage*: transcripts are the only external content ingested; no
  customer/PII data flows through the system in this version.

## 2. Flows

1. User opens the app -> a session is created automatically.
2. User asks a question -> backend retrieves top-k relevant transcript chunks
   -> LLM (per the configured/toggled provider) answers, grounded, with
   sources -> reply + sources render in chat.
3. User asks for an essay ("turn this into an essay for ship 30") -> router
   selects the Ship 30 skill instead of plain Q&A -> essay is generated from
   the same retrieved grounding.
4. User clicks "+ Markdown artifact" or "+ HTML artifact" -> backend generates
   the artifact from the conversation -> it renders in the Artifact Viewer
   panel beside the chat (HTML in a sandboxed iframe).
5. User switches the model toggle -> subsequent messages use the newly
   selected provider; if that provider is unreachable, the app clearly
   reports the failure and (if enabled) falls back automatically.

## 3. Acceptance criteria

- A fresh clone + `docker compose up` (with a real transcript set dropped in
  and either `ANTHROPIC_API_KEY` set or local Ollama running) results in a
  working chat at `localhost:5173` within a few minutes.
- Every assistant answer to a factual question includes at least one source
  when relevant transcript content exists, and explicitly says so when it
  doesn't.
- Switching the model toggle changes `provider_used` in the API response.
- Killing the database mid-request returns a clear 5xx with a logged cause,
  not a hang or an opaque crash.
- `pytest` passes with no real external services running (SQLite + mocked
  provider paths).
