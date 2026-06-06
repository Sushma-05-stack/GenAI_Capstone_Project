import time
import asyncio
from typing import List
import google.generativeai as genai
from app.services.llm.base import BaseLLMProvider, LLMResponse
from app.core.config import settings
from app.core.logging import logger

GEMINI_PRICING = {
    "gemini-1.5-pro": {"input": 3.5, "output": 10.5},
    "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
}


class GeminiProvider(BaseLLMProvider):
    provider_name = "gemini"

    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.GEMINI_MODEL
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self._model = genai.GenerativeModel(self.model_name)

    async def generate(
        self,
        messages: List[dict],
        temperature: float = 0.0,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        # Convert OpenAI-style messages to Gemini format
        prompt = "\n".join(
            f"{m['role'].upper()}: {m['content']}" for m in messages
        )
        start = time.monotonic()
        try:
            # Run sync Gemini call in thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self._model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=temperature,
                        max_output_tokens=max_tokens,
                    ),
                ),
            )
            latency = (time.monotonic() - start) * 1000
            text = response.text
            # Gemini doesn't always return token counts in free tier
            input_tok = getattr(response.usage_metadata, "prompt_token_count", 0) or 0
            output_tok = getattr(response.usage_metadata, "candidates_token_count", 0) or 0
            return LLMResponse(
                content=text,
                model=self.model_name,
                provider=self.provider_name,
                input_tokens=input_tok,
                output_tokens=output_tok,
                cost_usd=self.estimate_cost(input_tok, output_tok),
                latency_ms=latency,
            )
        except Exception as e:
            raise

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        pricing = GEMINI_PRICING.get(self.model_name, {"input": 3.5, "output": 10.5})
        return (input_tokens * pricing["input"] + output_tokens * pricing["output"]) / 1_000_000
