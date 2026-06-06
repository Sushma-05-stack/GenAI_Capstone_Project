import time
from typing import List
from app.services.llm.base import BaseLLMProvider, LLMResponse
from app.core.config import settings
from app.core.logging import logger

OPENAI_PRICING = {
    "gpt-4o": {"input": 5.0, "output": 15.0},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
}


class OpenAIProvider(BaseLLMProvider):
    provider_name = "openai"

    def __init__(self, model_name: str = None):
        from openai import AsyncOpenAI
        self.model_name = model_name or settings.OPENAI_MODEL
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def generate(
        self,
        messages: List[dict],
        temperature: float = 0.0,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        start = time.monotonic()
        # Let all exceptions propagate — router handles fallback
        response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        latency = (time.monotonic() - start) * 1000
        input_tok = response.usage.prompt_tokens if response.usage else 0
        output_tok = response.usage.completion_tokens if response.usage else 0
        return LLMResponse(
            content=response.choices[0].message.content,
            model=self.model_name,
            provider=self.provider_name,
            input_tokens=input_tok,
            output_tokens=output_tok,
            cost_usd=self.estimate_cost(input_tok, output_tok),
            latency_ms=latency,
        )

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        pricing = OPENAI_PRICING.get(self.model_name, {"input": 5.0, "output": 15.0})
        return (
            input_tokens * pricing["input"] + output_tokens * pricing["output"]
        ) / 1_000_000
