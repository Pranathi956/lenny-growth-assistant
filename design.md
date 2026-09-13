# Design notes

## UI/UX principles

1. **Grounding is visible, not implicit.** Every assistant message that used
   transcript excerpts shows a collapsible "N sources" section with the
   episode title and a snippet — the user can verify a claim without leaving
   the chat.
2. **The model choice is a first-class, visible control**, not a hidden
   config flag — a two-button toggle in the header, with a live health dot
   showing DB/provider status. Forward-deployed tools live or die on the
   operator trusting what's actually running.
3. **The artifact viewer sits beside the chat, not behind a redirect** — a
   dedicated panel so generated Markdown/HTML is inspectable and comparable
   against the conversation that produced it, mirroring the brief's explicit
   ask for a Claude-Artifacts-like experience.
4. **Failure states say what to do next.** A 503 from a missing Ollama model
   is surfaced as an error banner with the actual remediation step ("confirm
   `ollama serve` is running…"), not a generic "something went wrong."

## Information architecture

- Header: app name, model toggle + health indicator, "New chat."
- Left panel (chat): message history (grouped by role, sources collapsed by
  default to keep the thread skimmable), input box, two artifact-generation
  buttons.
- Right panel (artifact viewer): empty state with a hint when nothing's been
  generated yet; once generated, shows title/kind, rendered content, and a
  "view raw source" disclosure for the underlying Markdown/HTML.

## Key interaction states

- **Empty session**: chat panel empty, artifact panel shows a hint.
- **Sending**: input disabled, a lightweight "Thinking…" placeholder message
  appears so the user isn't staring at a static screen.
- **Provider unreachable**: error banner with the specific fix, chat input
  re-enabled so the user can retry after starting Ollama/adding a key.
- **Artifact generated**: right panel populates; user can close it and
  generate a new one without losing chat history.

## Responsive behavior

Two-column layout (chat + artifact) collapses conceptually to a single
scrollable column on narrow viewports by giving both panels `flex` sizing and
`min-width: 0` (prevents the classic CSS overflow trap); the artifact panel
is intended to stack below the chat panel on small screens in a future CSS
breakpoint pass — flagged here rather than silently shipped as broken on
mobile.

## Accessibility considerations

- Semantic elements (`<form>`, `<textarea>`, `<button>`, `<details>/<summary>`
  for sources and raw-source disclosure) instead of div-soup, so screen
  readers get native behavior for free.
- Enter-to-send / Shift+Enter-for-newline matches common chat UX expectations.
- Color contrast: light text on dark panels chosen to meet WCAG AA for body
  text; the artifact body intentionally renders on a white background
  (`--text: #111` inside `.artifact-body`) since generated documents are meant
  to be read as documents, not chat bubbles.
- Not yet done, flagged honestly: no live-region announcement when a new
  assistant message arrives, and iframe content accessibility depends on
  what the model generates. Both are reasonable next steps, not silently
  ignored gaps.

## Design decisions worth calling out

- Dark chat UI / light artifact-document UI is intentional, not an
  inconsistency — it signals "this panel is an app" vs. "this panel is a
  document you'd actually export," which matches how the artifact is meant
  to be used (copied out, shared, published).
