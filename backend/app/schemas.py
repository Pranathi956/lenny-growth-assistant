from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class SessionCreate(BaseModel):
    user_label: Optional[str] = None
    llm_provider: Optional[Literal["groq", "ollama"]] = None


class SessionOut(BaseModel):
    id: str
    created_at: datetime
    user_label: Optional[str]
    llm_provider: str

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    session_id: str
    message: str = Field(..., min_length=1, max_length=8000)
    # allows a one-off override of provider per message, useful for demoing
    # the toggle without creating a new session
    llm_provider: Optional[Literal["groq", "ollama"]] = None


class SourceRef(BaseModel):
    transcript_id: str
    title: str
    snippet: str


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    sources: list[SourceRef]
    provider_used: str
    skill_used: Optional[str] = None


class ArtifactRequest(BaseModel):
    session_id: str
    kind: Literal["markdown", "html"]
    instructions: str = Field(..., min_length=1, max_length=4000)


class ArtifactOut(BaseModel):
    id: str
    session_id: str
    kind: str
    title: Optional[str]
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class HealthOut(BaseModel):
    status: str
    database: str
    llm_provider: str
    ollama_reachable: Optional[bool] = None
    transcripts_indexed: int
