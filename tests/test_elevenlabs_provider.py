"""Tests for the ElevenLabs TTS provider (CEX-29)."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from src.providers.elevenlabs_provider import (
    API_BASE,
    DEFAULT_VOICE_SETTINGS,
    MAX_CHARACTERS,
    MAX_RETRIES,
    MODEL_ID,
    OUTPUT_FORMAT,
    ElevenLabsProvider,
    ProviderResult,
)
from src.shared.errors import RateLimitExceededError, ValidationError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FAKE_API_KEY = "test-api-key-123"
FAKE_VOICE_ID = "voice-abc-123"
FAKE_AUDIO = b"\xff\xfb\x90\x00" + b"\x00" * 100  # fake MP3 bytes


def _make_provider(**kwargs) -> ElevenLabsProvider:
    defaults = {"api_key": FAKE_API_KEY, "default_voice_id": FAKE_VOICE_ID}
    defaults.update(kwargs)
    return ElevenLabsProvider(**defaults)


def _mock_response(
    status_code: int = 200,
    content: bytes = FAKE_AUDIO,
) -> httpx.Response:
    return httpx.Response(
        status_code=status_code,
        content=content,
        request=httpx.Request("POST", "https://api.elevenlabs.io/v1/text-to-speech/voice-abc-123"),
    )


# ---------------------------------------------------------------------------
# Tests: ProviderResult dataclass
# ---------------------------------------------------------------------------

class TestProviderResult:
    def test_basic_creation(self):
        result = ProviderResult(
            data=b"audio-data",
            content_type="audio/mpeg",
            metadata={"voice_id_used": "v1"},
        )
        assert result.data == b"audio-data"
        assert result.content_type == "audio/mpeg"
        assert result.metadata["voice_id_used"] == "v1"


# ---------------------------------------------------------------------------
# Tests: Input validation
# ---------------------------------------------------------------------------

class TestElevenLabsValidation:
    async def test_rejects_empty_text(self):
        provider = _make_provider()
        with pytest.raises(ValidationError, match="Text is required"):
            await provider.execute({"text": ""})

    async def test_rejects_whitespace_only_text(self):
        provider = _make_provider()
        with pytest.raises(ValidationError, match="Text is required"):
            await provider.execute({"text": "   "})

    async def test_rejects_missing_text(self):
        provider = _make_provider()
        with pytest.raises(ValidationError, match="Text is required"):
            await provider.execute({})

    async def test_rejects_text_over_character_limit(self):
        provider = _make_provider()
        long_text = "x" * (MAX_CHARACTERS + 1)
        with pytest.raises(ValidationError, match="exceeds.*character limit"):
            await provider.execute({"text": long_text})

    async def test_accepts_text_at_character_limit(self):
        provider = _make_provider()
        text = "x" * MAX_CHARACTERS
        with patch("src.providers.elevenlabs_provider.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=_mock_response())
            mock_client_cls.return_value = mock_client

            result = await provider.execute({"text": text})
            assert isinstance(result, ProviderResult)

    async def test_rejects_no_voice_id(self):
        provider = ElevenLabsProvider(api_key=FAKE_API_KEY, default_voice_id="")
        with pytest.raises(ValidationError, match="No voice_id"):
            await provider.execute({"text": "Hello"})


# ---------------------------------------------------------------------------
# Tests: Successful TTS generation
# ---------------------------------------------------------------------------

class TestElevenLabsSuccess:
    async def test_returns_provider_result_with_audio(self):
        provider = _make_provider()
        with patch("src.providers.elevenlabs_provider.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=_mock_response())
            mock_client_cls.return_value = mock_client

            result = await provider.execute({"text": "Hello world"})

            assert isinstance(result, ProviderResult)
            assert result.data == FAKE_AUDIO
            assert result.content_type == "audio/mpeg"

    async def test_metadata_includes_voice_id(self):
        provider = _make_provider()
        with patch("src.providers.elevenlabs_provider.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=_mock_response())
            mock_client_cls.return_value = mock_client

            result = await provider.execute({"text": "Hello world"})

            assert result.metadata["voice_id_used"] == FAKE_VOICE_ID
            assert result.metadata["model_used"] == MODEL_ID
            assert result.metadata["output_format"] == OUTPUT_FORMAT

    async def test_metadata_includes_word_and_char_count(self):
        provider = _make_provider()
        text = "This is a test sentence with eight words"
        with patch("src.providers.elevenlabs_provider.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=_mock_response())
            mock_client_cls.return_value = mock_client

            result = await provider.execute({"text": text})

            assert result.metadata["word_count"] == 8
            assert result.metadata["character_count"] == len(text)
            assert result.metadata["duration_estimate_seconds"] > 0

    async def test_duration_estimate_based_on_word_count(self):
        provider = _make_provider()
        # 150 words = 60 seconds at 150 WPM
        text = " ".join(["word"] * 150)
        with patch("src.providers.elevenlabs_provider.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=_mock_response())
            mock_client_cls.return_value = mock_client

            result = await provider.execute({"text": text})

            assert result.metadata["duration_estimate_seconds"] == 60.0


# ---------------------------------------------------------------------------
# Tests: Voice settings
# ---------------------------------------------------------------------------

class TestElevenLabsVoiceSettings:
    async def test_uses_default_voice_settings(self):
        provider = _make_provider()
        with patch("src.providers.elevenlabs_provider.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=_mock_response())
            mock_client_cls.return_value = mock_client

            await provider.execute({"text": "Hello"})

            call_kwargs = mock_client.post.call_args
            body = call_kwargs.kwargs["json"]
            assert body["voice_settings"] == DEFAULT_VOICE_SETTINGS

    async def test_custom_voice_settings_override_defaults(self):
        provider = _make_provider()
        custom_settings = {"stability": 0.8, "style": 0.3}
        with patch("src.providers.elevenlabs_provider.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=_mock_response())
            mock_client_cls.return_value = mock_client

            await provider.execute({
                "text": "Hello",
                "voice_settings": custom_settings,
            })

            call_kwargs = mock_client.post.call_args
            body = call_kwargs.kwargs["json"]
            assert body["voice_settings"]["stability"] == 0.8
            assert body["voice_settings"]["style"] == 0.3
            # Non-overridden defaults remain
            assert body["voice_settings"]["similarity_boost"] == 0.75
            assert body["voice_settings"]["use_speaker_boost"] is True

    async def test_custom_voice_id_overrides_default(self):
        provider = _make_provider()
        custom_voice = "custom-voice-xyz"
        with patch("src.providers.elevenlabs_provider.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=_mock_response())
            mock_client_cls.return_value = mock_client

            result = await provider.execute({
                "text": "Hello",
                "voice_id": custom_voice,
            })

            call_kwargs = mock_client.post.call_args
            url = call_kwargs.args[0] if call_kwargs.args else call_kwargs.kwargs.get("url", "")
            assert custom_voice in url
            assert result.metadata["voice_id_used"] == custom_voice


# ---------------------------------------------------------------------------
# Tests: API request construction
# ---------------------------------------------------------------------------

class TestElevenLabsAPIRequest:
    async def test_sends_correct_url(self):
        provider = _make_provider()
        with patch("src.providers.elevenlabs_provider.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=_mock_response())
            mock_client_cls.return_value = mock_client

            await provider.execute({"text": "Hello"})

            call_kwargs = mock_client.post.call_args
            url = call_kwargs.args[0] if call_kwargs.args else call_kwargs.kwargs.get("url", "")
            expected_url = f"{API_BASE}/v1/text-to-speech/{FAKE_VOICE_ID}"
            assert url == expected_url

    async def test_sends_api_key_header(self):
        provider = _make_provider()
        with patch("src.providers.elevenlabs_provider.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=_mock_response())
            mock_client_cls.return_value = mock_client

            await provider.execute({"text": "Hello"})

            call_kwargs = mock_client.post.call_args
            headers = call_kwargs.kwargs["headers"]
            assert headers["xi-api-key"] == FAKE_API_KEY

    async def test_sends_model_id_in_body(self):
        provider = _make_provider()
        with patch("src.providers.elevenlabs_provider.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=_mock_response())
            mock_client_cls.return_value = mock_client

            await provider.execute({"text": "Hello"})

            call_kwargs = mock_client.post.call_args
            body = call_kwargs.kwargs["json"]
            assert body["model_id"] == MODEL_ID

    async def test_sends_output_format_as_query_param(self):
        provider = _make_provider()
        with patch("src.providers.elevenlabs_provider.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=_mock_response())
            mock_client_cls.return_value = mock_client

            await provider.execute({"text": "Hello"})

            call_kwargs = mock_client.post.call_args
            params = call_kwargs.kwargs["params"]
            assert params["output_format"] == OUTPUT_FORMAT


# ---------------------------------------------------------------------------
# Tests: Rate limit retries
# ---------------------------------------------------------------------------

class TestElevenLabsRateLimits:
    async def test_retries_on_429_then_succeeds(self):
        provider = _make_provider()

        rate_limit_response = _mock_response(status_code=429, content=b"rate limited")
        success_response = _mock_response(status_code=200, content=FAKE_AUDIO)

        call_count = 0

        async def mock_post(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                resp = rate_limit_response
                resp.raise_for_status = lambda: (_ for _ in ()).throw(
                    httpx.HTTPStatusError("429", request=resp.request, response=resp)
                )
                return resp
            return success_response

        with patch("src.providers.elevenlabs_provider.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = mock_post
            mock_client_cls.return_value = mock_client

            with patch("src.providers.elevenlabs_provider.asyncio.sleep", new_callable=AsyncMock):
                result = await provider.execute({"text": "Hello"})

            assert result.data == FAKE_AUDIO
            assert call_count == 2

    async def test_raises_rate_limit_after_max_retries(self):
        provider = _make_provider()

        rate_limit_response = _mock_response(status_code=429, content=b"rate limited")

        async def mock_post(*args, **kwargs):
            resp = rate_limit_response
            raise httpx.HTTPStatusError("429", request=resp.request, response=resp)

        with patch("src.providers.elevenlabs_provider.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = mock_post
            mock_client_cls.return_value = mock_client

            with patch("src.providers.elevenlabs_provider.asyncio.sleep", new_callable=AsyncMock):
                with pytest.raises(RateLimitExceededError, match="rate limit exceeded"):
                    await provider.execute({"text": "Hello"})


# ---------------------------------------------------------------------------
# Tests: HTTP error handling
# ---------------------------------------------------------------------------

class TestElevenLabsErrors:
    async def test_raises_on_401_unauthorized(self):
        provider = _make_provider()

        error_response = _mock_response(status_code=401, content=b"unauthorized")

        async def mock_post(*args, **kwargs):
            raise httpx.HTTPStatusError(
                "401", request=error_response.request, response=error_response
            )

        with patch("src.providers.elevenlabs_provider.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = mock_post
            mock_client_cls.return_value = mock_client

            with pytest.raises(httpx.HTTPStatusError):
                await provider.execute({"text": "Hello"})

    async def test_raises_on_500_server_error(self):
        provider = _make_provider()

        error_response = _mock_response(status_code=500, content=b"server error")

        async def mock_post(*args, **kwargs):
            raise httpx.HTTPStatusError(
                "500", request=error_response.request, response=error_response
            )

        with patch("src.providers.elevenlabs_provider.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = mock_post
            mock_client_cls.return_value = mock_client

            with pytest.raises(httpx.HTTPStatusError):
                await provider.execute({"text": "Hello"})


# ---------------------------------------------------------------------------
# Tests: Config overrides
# ---------------------------------------------------------------------------

class TestElevenLabsConfigOverrides:
    async def test_config_model_override(self):
        provider = _make_provider()
        with patch("src.providers.elevenlabs_provider.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=_mock_response())
            mock_client_cls.return_value = mock_client

            result = await provider.execute(
                {"text": "Hello"},
                config={"model_id": "eleven_flash_v2_5"},
            )

            call_kwargs = mock_client.post.call_args
            body = call_kwargs.kwargs["json"]
            assert body["model_id"] == "eleven_flash_v2_5"
            assert result.metadata["model_used"] == "eleven_flash_v2_5"

    async def test_config_output_format_override(self):
        provider = _make_provider()
        with patch("src.providers.elevenlabs_provider.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=_mock_response())
            mock_client_cls.return_value = mock_client

            result = await provider.execute(
                {"text": "Hello"},
                config={"output_format": "mp3_44100_192"},
            )

            call_kwargs = mock_client.post.call_args
            params = call_kwargs.kwargs["params"]
            assert params["output_format"] == "mp3_44100_192"
            assert result.metadata["output_format"] == "mp3_44100_192"


# ---------------------------------------------------------------------------
# Tests: Constructor defaults from settings
# ---------------------------------------------------------------------------

class TestElevenLabsConstructor:
    def test_uses_explicit_params(self):
        provider = ElevenLabsProvider(api_key="key1", default_voice_id="voice1")
        assert provider._api_key == "key1"
        assert provider._default_voice_id == "voice1"

    def test_falls_back_to_settings(self):
        with patch("src.providers.elevenlabs_provider.settings") as mock_settings:
            mock_settings.elevenlabs_api_key = "settings-key"
            mock_settings.elevenlabs_default_voice_id = "settings-voice"
            provider = ElevenLabsProvider()
            assert provider._api_key == "settings-key"
            assert provider._default_voice_id == "settings-voice"
