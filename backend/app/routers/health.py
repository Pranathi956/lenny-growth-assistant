import logging
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session as DBSession
import httpx

from ..database import get_db
from ..config import settings
from ..schemas import HealthOut
from ..agent.rag import get_index

router = APIRouter(tags=["health"])
logger = logging.getLogger("lenny.health")


@router.get("/health", response_model=HealthOut)
def health(db: DBSession = Depends(get_db)):
    db_status = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(f"DB health check failed: {e}")
        db_status = "unreachable"

    ollama_ok = None
    if settings.llm_provider == "ollama" or settings.enable_provider_fallback:
        try:
            r = httpx.get(f"{settings.ollama_base_url}/api/tags", timeout=2.0)
            ollama_ok = r.status_code == 200
        except Exception:
            ollama_ok = False

    index = get_index(settings.transcripts_dir)

    return HealthOut(
        status="ok" if db_status == "ok" else "degraded",
        database=db_status,
        llm_provider=settings.llm_provider,
        ollama_reachable=ollama_ok,
        transcripts_indexed=len(index.chunks),
    )
