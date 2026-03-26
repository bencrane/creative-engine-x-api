from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.integrations.claude_client import ClaudeClient, GenerationResult, TokenUsage, MODEL_QUALITY, MODEL_FAST


def _make_mock_response(text="Hello", tool_use=None):
    response = MagicMock()
    response.model = "claude-sonnet-4-20250514"
    response.stop_reason = "end_turn"
    response.usage = MagicMock()
    response.usage.input_tokens = 100
    response.usage.output_tokens = 50
    response.usage.cache_creation_input_tokens = 0
    response.usage.cache_read_input_tokens = 0

    blocks = []
    if text:
        text_block = MagicMock()
        text_block.type = "text"
        text_block.text = text
        blocks.append(text_block)
    if tool_use:
        tool_block = MagicMock()
        tool_block.type = "tool_use"
        tool_block.id = "tool_1"
        tool_block.name = tool_use["name"]
        tool_block.input = tool_use["input"]
        blocks.append(tool_block)

    response.content = blocks
    return response


class TestClaudeClient:
    @patch("src.integrations.claude_client.settings")
    async def test_generate_text_response(self, mock_settings):
        mock_settings.anthropic_api_key = "test-key"
        client = ClaudeClient(api_key="test-key")

        mock_response = _make_mock_response(text="Generated text")
        client._client = MagicMock()
        client._client.messages = MagicMock()
        client._client.messages.create = AsyncMock(return_value=mock_response)

        result = await client.generate(
            messages=[{"role": "user", "content": "Hello"}]
        )
        assert isinstance(result, GenerationResult)
        assert result.content == "Generated text"
        assert result.usage.input_tokens == 100
        assert result.usage.output_tokens == 50

    @patch("src.integrations.claude_client.settings")
    async def test_generate_tool_use_response(self, mock_settings):
        mock_settings.anthropic_api_key = "test-key"
        client = ClaudeClient(api_key="test-key")

        tool_use = {"name": "generate_ad_copy", "input": {"headline": "Test"}}
        mock_response = _make_mock_response(text=None, tool_use=tool_use)
        client._client = MagicMock()
        client._client.messages = MagicMock()
        client._client.messages.create = AsyncMock(return_value=mock_response)

        result = await client.generate(
            messages=[{"role": "user", "content": "Generate ad copy"}],
            tools=[{"name": "generate_ad_copy", "description": "Generate ad", "input_schema": {"type": "object"}}],
        )
        assert result.content == {"headline": "Test"}
        assert len(result.tool_results) == 1
        assert result.tool_results[0]["name"] == "generate_ad_copy"

    @patch("src.integrations.claude_client.settings")
    async def test_token_tracking_accumulates(self, mock_settings):
        mock_settings.anthropic_api_key = "test-key"
        client = ClaudeClient(api_key="test-key")

        mock_response = _make_mock_response(text="Response")
        client._client = MagicMock()
        client._client.messages = MagicMock()
        client._client.messages.create = AsyncMock(return_value=mock_response)

        await client.generate(messages=[{"role": "user", "content": "Hello"}])
        await client.generate(messages=[{"role": "user", "content": "World"}])

        assert client.total_usage.input_tokens == 200
        assert client.total_usage.output_tokens == 100


class TestTokenUsage:
    def test_defaults(self):
        usage = TokenUsage()
        assert usage.input_tokens == 0
        assert usage.output_tokens == 0

    def test_with_values(self):
        usage = TokenUsage(input_tokens=100, output_tokens=50)
        assert usage.input_tokens == 100


class TestGenerationResult:
    def test_defaults(self):
        result = GenerationResult()
        assert result.content is None
        assert result.tool_results == []


class TestModelTierConstants:
    def test_model_quality_is_opus(self):
        assert "opus" in MODEL_QUALITY

    def test_model_fast_is_sonnet(self):
        assert "sonnet" in MODEL_FAST

    def test_generate_defaults_to_fast(self):
        import inspect
        sig = inspect.signature(ClaudeClient.generate)
        assert sig.parameters["model"].default == MODEL_FAST
