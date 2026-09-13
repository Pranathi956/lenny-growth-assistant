"""
Central configuration. Everything the evaluator might want to change
(model provider, DB URL, ports) lives here and is driven by env vars,
so the app never needs a code change to switch behavior.
"""
from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    # --- App ---
    app_name: str = "Lenny Growth Assistant"
    environment: str = "development"

    # --- Database ---
    database_url: str = "postgresql://postgres:postgres@localhost:5432/lenny_assistant"

    # --- LLM provider toggle ---
    # "groq" (cloud, free tier) or "ollama" (local). This is the single switch
    # that changes which model answers requests, with no code changes needed.
    llm_provider: Literal["groq", "ollama"] = "ollama"

    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"

    # If the configured provider is unavailable, fall back to the other one
    # rather than failing the whole request. Documented in architecture.md.
    enable_provider_fallback: bool = True

    # --- RAG ---
    transcripts_dir: str = "app/../data/transcripts"
    retrieval_top_k: int = 5

    # --- CORS ---
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
