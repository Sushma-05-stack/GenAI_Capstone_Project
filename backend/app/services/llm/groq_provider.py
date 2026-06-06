import time
from typing import List
from app.services.llm.base import BaseLLMProvider, LLMResponse
from app.core.config import settings
from app.core.logging import logger

GROQ_PRICING = {
    "llama3-70b-8192": {"input": 0.59, "output": 0.79},
    "llama3-8b-8192": {"input": 0.05, "output": 0.08},
    "llama-3.3-70b-versatile": {"input": 0.59, "output": 0.79},
    "mixtral-8x7b-32768": {"input": 0.24, "output": 0.24},
}


class GroqProvider(BaseLLMProvider):
    provider_name = "groq"

    def __init__(self, model_name: str = None):
        from groq import AsyncGroq
        self.model_name = model_name or settings.GROQ_MODEL
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)

    async def generate(
        self,
        messages: List[dict],
        temperature: float = 0.0,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        start = time.monotonic()
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
        pricing = GROQ_PRICING.get(self.model_name, {"input": 0.59, "output": 0.79})
        return (input_tokens * pricing["input"] + output_tokens * pricing["output"]) / 1_000_000
