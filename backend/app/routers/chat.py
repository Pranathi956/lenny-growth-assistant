import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from ..database import get_db
from .. import models, schemas
from ..config import settings
from ..agent.rag import get_index
from ..agent.llm_provider import complete, ProviderUnavailable
from ..agent.prompts import RAG_SYSTEM_PROMPT, build_rag_user_prompt
from ..agent.skills.ship30 import SHIP30_SYSTEM_PROMPT, build_ship30_user_prompt

router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger("lenny.chat")

SHIP30_TRIGGERS = ("ship 30", "ship30", "write an essay", "turn this into an essay")


def _routing_decision(message: str) -> str:
    """Very small deterministic router: keyword match against the Ship 30
    skill, default to the grounded Q&A skill otherwise. Kept simple and
    explainable on purpose -- see architecture.md 'Agent routing' for why
    we didn't use an LLM-based router for v1."""
    lowered = message.lower()
    if any(trigger in lowered for trigger in SHIP30_TRIGGERS):
        return "ship30_essay"
    return "grounded_qa"


@router.post("", response_model=schemas.ChatResponse)
def chat(payload: schemas.ChatRequest, db: DBSession = Depends(get_db)):
    session = db.query(models.Session).filter(models.Session.id == payload.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found. Create one via POST /sessions first.")

    # Persist the user's message before calling the model, so it's never lost
    # even if the LLM call fails.
    user_msg = models.Message(session_id=session.id, role="user", content=payload.message)
    db.add(user_msg)
    db.commit()

    index = get_index(settings.transcripts_dir)
    results = index.search(payload.message, top_k=settings.retrieval_top_k)
    excerpts = [{"title": c.title, "text": c.text, "transcript_id": c.transcript_id} for c, _ in results]

    history = [
        {"role": m.role, "content": m.content}
        for m in session.messages[-8:]
        if m.role in ("user", "assistant")
    ]

    skill = _routing_decision(payload.message)

    if skill == "ship30_essay":
        system = SHIP30_SYSTEM_PROMPT
        user_prompt = build_ship30_user_prompt(payload.message, excerpts)
    else:
        system = RAG_SYSTEM_PROMPT
        user_prompt = build_rag_user_prompt(payload.message, history, excerpts)

    try:
        text, provider_used = complete(system, user_prompt, provider_override=payload.llm_provider)
    except ProviderUnavailable as e:
        logger.error(f"Chat failed, no provider reachable: {e}")
        raise HTTPException(
            status_code=503,
            detail="No LLM provider is currently reachable. If using local mode, confirm "
                   "`ollama serve` is running and the model is pulled (see README).",
        )

    sources = [schemas.SourceRef(transcript_id=e["transcript_id"], title=e["title"], snippet=e["text"][:220]) for e in excerpts]

    assistant_msg = models.Message(
        session_id=session.id,
        role="assistant",
        content=text,
        sources=[s.model_dump() for s in sources],
    )
    db.add(assistant_msg)
    db.commit()

    return schemas.ChatResponse(
        session_id=session.id,
        reply=text,
        sources=sources,
        provider_used=provider_used,
        skill_used=skill,
    )
