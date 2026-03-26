"""ElevenLabs TTS provider adapter.

CEX-29: Wraps the ElevenLabs REST TTS API for high-quality audio generation.
Uses eleven_multilingual_v2 model with mp3_44100_128 output format.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

import httpx

from src.config import settings
from src.shared.errors import RateLimitExceededError, ValidationError

logger = logging.getLogger(__name__)

API_BASE = "https://api.elevenlabs.io"
TTS_ENDPOINT = "/v1/text-to-speech/{voice_id}"
MODEL_ID = "eleven_multilingual_v2"
OUTPUT_FORMAT = "mp3_44100_128"
MAX_CHARACTERS = 5000
WORDS_PER_MINUTE = 150

DEFAULT_VOICE_SETTINGS = {
    "stability": 0.5,
    "similarity_boost": 0.75,
    "style": 0.15,
    "use_speaker_boost": True,
}

MAX_RETRIES = 3
INITIAL_BACKOFF = 1.0  # seconds


@dataclass
class ProviderResult:
    """Result from an ElevenLabs TTS call."""

    data: bytes
    content_type: str
    metadata: dict


class ElevenLabsProvider:
    """ElevenLabs TTS provider implementing the provider pattern.

    Calls POST /v1/text-to-speech/{voice_id} with eleven_multilingual_v2
    and returns MP3 audio bytes.
    """

    def __init__(self, api_key: str | None = None, default_voice_id: str | None = None):
        self._api_key = api_key or settings.elevenlabs_api_key
        self._default_voice_id = default_voice_id or settings.elevenlabs_default_voice_id

    async def execute(self, input_data: dict, config: dict | None = None) -> ProviderResult:
        """Generate TTS audio from text.

        Args:
            input_data: Must contain 'text'. Optional: 'voice_id', 'voice_settings'.
            config: Optional overrides for model_id, output_format.

        Returns:
            ProviderResult with MP3 audio bytes and metadata.

        Raises:
            ValidationError: If text is empty or exceeds character limit.
            RateLimitExceededError: If rate limit retries are exhausted.
            httpx.HTTPStatusError: For other API errors.
        """
        config = config or {}
        text = input_data.get("text", "")

        # Validate text
        if not text or not text.strip():
            raise ValidationError("Text is required for TTS generation")
        if len(text) > MAX_CHARACTERS:
            raise ValidationError(
                f"Text exceeds {MAX_CHARACTERS} character limit: {len(text)} characters"
            )

        # Resolve voice ID
        voice_id = input_data.get("voice_id") or self._default_voice_id
        if not voice_id:
            raise ValidationError("No voice_id provided and no default configured")

        # Resolve voice settings
        voice_settings = {**DEFAULT_VOICE_SETTINGS}
        if input_data.get("voice_settings"):
            voice_settings.update(input_data["voice_settings"])

        # Build request
        model_id = config.get("model_id", MODEL_ID)
        output_format = config.get("output_format", OUTPUT_FORMAT)

        url = f"{API_BASE}{TTS_ENDPOINT.format(voice_id=voice_id)}"
        headers = {
            "xi-api-key": self._api_key,
            "Content-Type": "application/json",
        }
        body = {
            "text": text,
            "model_id": model_id,
            "voice_settings": voice_settings,
        }
        params = {"output_format": output_format}

        # Call API with retry on rate limits
        audio_bytes = await self._call_with_retry(url, headers, body, params)

        # Estimate duration from word count
        word_count = len(text.split())
        duration_estimate = (word_count / WORDS_PER_MINUTE) * 60

        return ProviderResult(
            data=audio_bytes,
            content_type="audio/mpeg",
            metadata={
                "voice_id_used": voice_id,
                "model_used": model_id,
                "output_format": output_format,
                "word_count": word_count,
                "character_count": len(text),
                "duration_estimate_seconds": round(duration_estimate, 1),
            },
        )

    async def _call_with_retry(
        self,
        url: str,
        headers: dict,
        body: dict,
        params: dict,
    ) -> bytes:
        """Call the ElevenLabs API with exponential backoff on 429 responses."""
        last_exception: Exception | None = None

        for attempt in range(MAX_RETRIES):
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        url, headers=headers, json=body, params=params
                    )
                    response.raise_for_status()
                    return response.content
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 429:
                    last_exception = exc
                    backoff = INITIAL_BACKOFF * (2 ** attempt)
                    logger.warning(
                        "ElevenLabs rate limit hit (attempt %d/%d), retrying in %.1fs",
                        attempt + 1,
                        MAX_RETRIES,
                        backoff,
                    )
                    await asyncio.sleep(backoff)
                    continue
                raise
            except httpx.TimeoutException as exc:
                last_exception = exc
                if attempt < MAX_RETRIES - 1:
                    backoff = INITIAL_BACKOFF * (2 ** attempt)
                    logger.warning(
                        "ElevenLabs timeout (attempt %d/%d), retrying in %.1fs",
                        attempt + 1,
                        MAX_RETRIES,
                        backoff,
                    )
                    await asyncio.sleep(backoff)
                    continue
                raise

        raise RateLimitExceededError(
            f"ElevenLabs rate limit exceeded after {MAX_RETRIES} retries"
        )
