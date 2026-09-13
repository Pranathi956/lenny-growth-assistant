"""
Provider-agnostic LLM call layer. This is the "flexible LLM configuration"
piece from the brief: callers ask for a completion and don't know or care
whether it's served by Groq's cloud API or a local Ollama model.

Toggle is controlled by Settings.llm_provider (env var LLM_PROVIDER), or
overridden per-request. If the configured provider fails and fallback is
enabled, we try the other one and tell the caller which was actually used
(ChatResponse.provider_used) so the UI can be honest about it.

Groq is used for the cloud path because it has a genuinely free tier with
no card required, and exposes an OpenAI-compatible REST endpoint -- so we
call it with plain httpx (same pattern as the Ollama call below) instead of
pulling in a separate SDK dependency.
"""
import logging
import httpx
from tenacity import retry, stop_after_attempt, wait_fixed
from ..config import settings

logger = logging.getLogger("lenny.llm")

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


class ProviderUnavailable(Exception):
    pass


@retry(stop=stop_after_attempt(2), wait=wait_fixed(1), reraise=True)
def _call_groq(system: str, user: str) -> str:
    if not settings.groq_api_key:
        raise ProviderUnavailable("GROQ_API_KEY is not set")
    try:
        r = httpx.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {settings.groq_api_key}"},
            json={
                "model": settings.groq_model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "max_tokens": 1500,
            },
            timeout=30.0,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        raise ProviderUnavailable("Groq API unreachable") from e
    except httpx.HTTPStatusError as e:
        # 401 = bad key, 429 = free-tier rate limit -- both are "provider
        # unavailable right now" from the caller's point of view, and both
        # get a clear message in the logs rather than a raw stack trace.
        raise ProviderUnavailable(f"Groq API error: {e.response.status_code} {e.response.text[:200]}") from e


@retry(stop=stop_after_attempt(2), wait=wait_fixed(1), reraise=True)
def _call_ollama(system: str, user: str) -> str:
    try:
        r = httpx.post(
            f"{settings.ollama_base_url}/api/chat",
            json={
                "model": settings.ollama_model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "stream": False,
            },
            timeout=90.0,
        )
        r.raise_for_status()
        return r.json()["message"]["content"]
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        raise ProviderUnavailable(f"Ollama unreachable at {settings.ollama_base_url}") from e


def complete(system: str, user: str, provider_override: str | None = None) -> tuple[str, str]:
    """Returns (text, provider_actually_used)."""
    provider = provider_override or settings.llm_provider
    other = "groq" if provider == "ollama" else "ollama"

    try:
        text = _call_groq(system, user) if provider == "groq" else _call_ollama(system, user)
        return text, provider
    except ProviderUnavailable as e:
        logger.warning(f"Primary provider '{provider}' unavailable: {e}")
        if not settings.enable_provider_fallback:
            raise
        try:
            text = _call_groq(system, user) if other == "groq" else _call_ollama(system, user)
            logger.warning(f"Fell back to '{other}'")
            return text, other
        except ProviderUnavailable as e2:
            logger.error(f"Both providers unavailable: {e2}")
            raise ProviderUnavailable("No LLM provider is currently reachable") from e2
