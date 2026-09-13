import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from ..database import get_db
from .. import models, schemas
from ..config import settings
from ..agent.llm_provider import complete, ProviderUnavailable
from ..agent.rag import get_index

router = APIRouter(prefix="/artifacts", tags=["artifacts"])
logger = logging.getLogger("lenny.artifacts")

ARTIFACT_SYSTEM_PROMPT = """You generate a single self-contained artifact (Markdown \
document or HTML/CSS snippet) based on the conversation and instructions given.

If producing HTML: it will be rendered inside a SANDBOXED iframe with scripts \
disabled and no access to cookies/localStorage/parent frame. Do not rely on \
JavaScript for anything essential -- assume it will not execute. Keep styles \
inline or in a <style> tag. Do not include <script> tags, external resource \
requests, forms that submit anywhere, or iframes.

If producing Markdown: output clean, well-structured Markdown only.

Output ONLY the artifact content itself -- no explanation, no code fences around it."""


@router.post("", response_model=schemas.ArtifactOut)
def generate_artifact(payload: schemas.ArtifactRequest, db: DBSession = Depends(get_db)):
    session = db.query(models.Session).filter(models.Session.id == payload.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    index = get_index(settings.transcripts_dir)
    results = index.search(payload.instructions, top_k=settings.retrieval_top_k)
    excerpt_block = "\n\n".join(f"[Source: {c.title}]\n{c.text}" for c, _ in results)

    recent = "\n".join(f"{m.role}: {m.content}" for m in session.messages[-6:])

    user_prompt = f"""Requested artifact type: {payload.kind}
Instructions: {payload.instructions}

Recent conversation:
{recent or '(none)'}

Relevant grounded excerpts:
{excerpt_block or '(none found -- note any gaps rather than inventing content)'}"""

    try:
        content, provider_used = complete(ARTIFACT_SYSTEM_PROMPT, user_prompt)
    except ProviderUnavailable:
        raise HTTPException(status_code=503, detail="No LLM provider reachable for artifact generation.")

    # Basic server-side safety net on top of the sandboxed-iframe strategy
    # documented in architecture.md: strip obviously dangerous tags even
    # though the iframe sandbox is the primary defense.
    if payload.kind == "html":
        import re
        content = re.sub(r"<script.*?</script>", "", content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r"on\w+\s*=\s*\"[^\"]*\"", "", content, flags=re.IGNORECASE)

    artifact = models.Artifact(
        session_id=session.id,
        kind=payload.kind,
        title=payload.instructions[:80],
        content=content,
    )
    db.add(artifact)
    db.commit()
    db.refresh(artifact)
    return artifact
