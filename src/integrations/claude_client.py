import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any

import anthropic

from src.config import settings

logger = logging.getLogger(__name__)


@dataclass
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0


@dataclass
class GenerationResult:
    content: Any = None
    tool_results: list[dict] = field(default_factory=list)
    usage: TokenUsage = field(default_factory=TokenUsage)
    model: str = ""
    stop_reason: str = ""


class ClaudeClient:
    def __init__(self, api_key: str | None = None):
        self._client = anthropic.AsyncAnthropic(
            api_key=api_key or settings.anthropic_api_key
        )
        self._total_usage = TokenUsage()

    @property
    def total_usage(self) -> TokenUsage:
        return self._total_usage

    async def generate(
        self,
        messages: list[dict],
        system: str | list[dict] | None = None,
        model: str = "claude-sonnet-4-20250514",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: list[dict] | None = None,
        tool_choice: dict | None = None,
        max_retries: int = 3,
    ) -> GenerationResult:
        """
        Call Claude with tool_use pattern for structured output.
        Retries on 429 and 500+ with exponential backoff.
        """
        kwargs: dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }
        if system:
            kwargs["system"] = system
        if tools:
            kwargs["tools"] = tools
        if tool_choice:
            kwargs["tool_choice"] = tool_choice

        last_error = None
        for attempt in range(max_retries):
            try:
                response = await self._client.messages.create(**kwargs)
                return self._process_response(response)
            except anthropic.RateLimitError as e:
                last_error = e
                wait = 2 ** attempt
                logger.warning(f"Rate limited, retrying in {wait}s (attempt {attempt + 1})")
                await asyncio.sleep(wait)
            except anthropic.APIStatusError as e:
                if e.status_code >= 500:
                    last_error = e
                    wait = 2 ** attempt
                    logger.warning(f"Server error {e.status_code}, retrying in {wait}s")
                    await asyncio.sleep(wait)
                else:
                    raise

        raise last_error  # type: ignore[misc]

    def _process_response(self, response) -> GenerationResult:
        usage = TokenUsage(
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            cache_creation_input_tokens=getattr(response.usage, "cache_creation_input_tokens", 0) or 0,
            cache_read_input_tokens=getattr(response.usage, "cache_read_input_tokens", 0) or 0,
        )
        self._total_usage.input_tokens += usage.input_tokens
        self._total_usage.output_tokens += usage.output_tokens

        tool_results = []
        text_content = ""

        for block in response.content:
            if block.type == "text":
                text_content = block.text
            elif block.type == "tool_use":
                tool_results.append(
                    {"id": block.id, "name": block.name, "input": block.input}
                )

        return GenerationResult(
            content=text_content if not tool_results else tool_results[0]["input"],
            tool_results=tool_results,
            usage=usage,
            model=response.model,
            stop_reason=response.stop_reason,
        )
