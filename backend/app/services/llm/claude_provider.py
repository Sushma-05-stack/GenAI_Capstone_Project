import time
from typing import List
import anthropic
from app.services.llm.base import BaseLLMProvider, LLMResponse
from app.core.config import settings

CLAUDE_PRICING = {
    "claude-3-5-sonnet-20241022": {"input": 3.0, "output": 15.0},
    "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
}


class ClaudeProvider(BaseLLMProvider):
    provider_name = "claude"

    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.CLAUDE_MODEL
        self.client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def generate(
        self,
        messages: List[dict],
        temperature: float = 0.0,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        # Separate system message from user messages for Claude API
        system_msg = ""
        chat_messages = []
        for m in messages:
            if m["role"] == "system":
                system_msg = m["content"]
            else:
                chat_messages.append(m)

        start = time.monotonic()
        try:
            response = await self.client.messages.create(
                model=self.model_name,
                system=system_msg,
                messages=chat_messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            latency = (time.monotonic() - start) * 1000
            input_tok = response.usage.input_tokens
            output_tok = response.usage.output_tokens
            return LLMResponse(
                content=response.content[0].text,
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
        pricing = CLAUDE_PRICING.get(self.model_name, {"input": 3.0, "output": 15.0})
        return (input_tokens * pricing["input"] + output_tokens * pricing["output"]) / 1_000_000
