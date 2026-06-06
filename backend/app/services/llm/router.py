"""
Multi-LLM Fallback Router
Tries primary model first; on timeout / rate-limit / quota / error,
cascades through the fallback chain automatically.
Every fallback event is logged to MongoDB.
"""
import asyncio
import time
from typing import List, Optional
from app.services.llm.base import BaseLLMProvider, LLMResponse
from app.services.llm.openai_provider import OpenAIProvider
from app.services.llm.gemini_provider import GeminiProvider
from app.services.llm.groq_provider import GroqProvider
from app.services.llm.claude_provider import ClaudeProvider
from app.models.fallback import FallbackEvent, FallbackReason
from app.core.config import settings
from app.core.logging import logger

PROVIDER_MAP = {
    "openai": OpenAIProvider,
    "gemini": GeminiProvider,
    "groq": GroqProvider,
    "claude": ClaudeProvider,
}

DEFAULT_FALLBACK_CHAIN = ["openai", "gemini", "groq", "claude"]
TIMEOUT_SECONDS = 30


def _classify_error(e: Exception) -> FallbackReason:
    err = str(e).lower()
    if "timeout" in err or "timed out" in err:
        return FallbackReason.TIMEOUT
    if "rate limit" in err or "rate_limit" in err or "429" in err:
        return FallbackReason.RATE_LIMIT
    if "quota" in err or "insufficient_quota" in err or "billing" in err:
        return FallbackReason.RATE_LIMIT  # treat quota as rate limit for routing
    if "context" in err and "length" in err:
        return FallbackReason.CONTEXT_LENGTH
    if "content" in err and ("filter" in err or "policy" in err):
        return FallbackReason.CONTENT_FILTER
    return FallbackReason.UNKNOWN


def _is_retryable(e: Exception) -> bool:
    """Return True if this error should trigger a fallback."""
    err = str(e).lower()
    non_retryable = ["invalid_api_key", "authentication", "invalid api key"]
    return not any(kw in err for kw in non_retryable)


async def _is_provider_available(provider: str) -> bool:
    key_map = {
        "openai": settings.OPENAI_API_KEY,
        "gemini": settings.GOOGLE_API_KEY,
        "groq": settings.GROQ_API_KEY,
        "claude": settings.ANTHROPIC_API_KEY,
    }
    key = key_map.get(provider, "")
    # Key must exist and not be a placeholder
    return bool(key and not key.startswith("sk-ant-...") and len(key) > 10)


def _get_provider(provider: str, model: Optional[str] = None) -> BaseLLMProvider:
    cls = PROVIDER_MAP.get(provider)
    if not cls:
        raise ValueError(f"Unknown provider: {provider}")
    return cls(model_name=model)


async def route_llm(
    messages: List[dict],
    provider: str = "auto",
    model_name: Optional[str] = None,
    temperature: float = 0.0,
    max_tokens: int = 1024,
    query_id: Optional[str] = None,
) -> LLMResponse:
    """
    Route an LLM request with automatic fallback.
    - provider='auto'  → tries full chain: openai → gemini → groq → claude
    - provider='openai' → tries openai first, then falls back on failure
    """
    # Build the ordered chain
    if provider == "auto":
        chain = [p for p in DEFAULT_FALLBACK_CHAIN if await _is_provider_available(p)]
    else:
        available_fallbacks = [
            p for p in DEFAULT_FALLBACK_CHAIN
            if p != provider and await _is_provider_available(p)
        ]
        primary_available = await _is_provider_available(provider)
        chain = ([provider] if primary_available else []) + available_fallbacks

    if not chain:
        raise RuntimeError(
            "No LLM providers are configured. "
            "Please set OPENAI_API_KEY, GROQ_API_KEY, or GOOGLE_API_KEY in backend/.env"
        )

    logger.info("LLM fallback chain", chain=chain)

    last_error = None
    primary_provider = chain[0]

    for i, current_provider in enumerate(chain):
        is_fallback = i > 0
        try:
            # Use specified model only for the primary; let fallbacks use their default
            current_model = model_name if not is_fallback else None
            llm = _get_provider(current_provider, current_model)

            logger.info(
                "Trying LLM provider",
                provider=current_provider,
                model=llm.model_name,
                fallback=is_fallback,
                attempt=i + 1,
            )

            response = await asyncio.wait_for(
                llm.generate(messages, temperature=temperature, max_tokens=max_tokens),
                timeout=TIMEOUT_SECONDS,
            )
            response.fallback_used = is_fallback

            # Log fallback event to MongoDB
            if is_fallback and last_error is not None:
                await _log_fallback(
                    query_id=query_id,
                    primary_provider=primary_provider,
                    primary_model=model_name or "",
                    fallback_provider=current_provider,
                    fallback_model=response.model,
                    reason=_classify_error(last_error),
                    error_message=str(last_error)[:500],
                    latency_after=response.latency_ms,
                )

            return response

        except asyncio.TimeoutError:
            last_error = TimeoutError(
                f"Provider {current_provider} timed out after {TIMEOUT_SECONDS}s"
            )
            logger.warning("LLM timeout — trying next", provider=current_provider)

        except Exception as e:
            last_error = e
            if not _is_retryable(e):
                logger.error(
                    "Non-retryable LLM error — skipping chain",
                    provider=current_provider,
                    error=str(e)[:200],
                )
                # Still continue to next provider for non-auth errors
            logger.warning(
                "LLM error — trying next provider",
                provider=current_provider,
                error=str(e)[:200],
            )

    raise RuntimeError(
        f"All LLM providers failed. Last error: {str(last_error)[:300]}"
    )


async def _log_fallback(
    query_id, primary_provider, primary_model,
    fallback_provider, fallback_model,
    reason, error_message, latency_after,
):
    """Persist fallback event — never raises."""
    try:
        event = FallbackEvent(
            query_id=query_id,
            primary_provider=primary_provider,
            primary_model=primary_model,
            fallback_provider=fallback_provider,
            fallback_model=fallback_model,
            reason=reason,
            error_message=error_message,
            latency_after_fallback_ms=latency_after,
            success=True,
        )
        await event.insert()
        logger.info(
            "Fallback event logged",
            from_=primary_provider,
            to=fallback_provider,
            reason=reason,
        )
    except Exception as e:
        logger.error("Failed to log fallback event", error=str(e))
