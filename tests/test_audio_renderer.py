"""Tests for the audio renderer — script generation + TTS pipeline (CEX-30)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.brand.models import BrandContext, BrandGuidelines
from src.generators.audio_script import AudioScriptGenerator
from src.generators.base import GeneratedContent
from src.providers.elevenlabs_provider import ElevenLabsProvider, MAX_CHARACTERS, ProviderResult
from src.renderers.audio_renderer import AudioRenderer
from src.renderers.base import RenderedArtifact, RendererProtocol
from src.shared.errors import ValidationError
from src.specs.models import FormatSpec


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

FAKE_AUDIO = b"\xff\xfb\x90\x00" + b"\x00" * 100

def _make_brand_context(**overrides) -> BrandContext:
    defaults = {
        "organization_id": "org-123",
        "company_name": "Acme Analytics",
        "brand_guidelines": BrandGuidelines(
            primary_color="#00e87b",
            secondary_color="#09090b",
            font_family="Inter, sans-serif",
        ),
    }
    defaults.update(overrides)
    return BrandContext(**defaults)


def _make_spec(**overrides) -> FormatSpec:
    defaults = {
        "spec_id": "audio__voice_channel",
        "artifact_type": "audio",
        "surface": "voice_channel",
        "version": "1.0",
    }
    defaults.update(overrides)
    return FormatSpec(**defaults)


def _make_content(script_text: str | None = None, **overrides) -> GeneratedContent:
    content = {
        "topic": "Follow-up after product demo",
        "duration_target": 30,
    }
    if script_text:
        content["script_text"] = script_text
    content.update(overrides)
    return GeneratedContent(content=content)


def _mock_elevenlabs() -> AsyncMock:
    mock = AsyncMock(spec=ElevenLabsProvider)
    mock.execute = AsyncMock(return_value=ProviderResult(
        data=FAKE_AUDIO,
        content_type="audio/mpeg",
        metadata={
            "voice_id_used": "voice-abc",
            "model_used": "eleven_multilingual_v2",
            "output_format": "mp3_44100_128",
            "word_count": 75,
            "character_count": 400,
            "duration_estimate_seconds": 30.0,
        },
    ))
    return mock


def _mock_script_generator() -> AsyncMock:
    mock = AsyncMock(spec=AudioScriptGenerator)
    mock.generate = AsyncMock(return_value=GeneratedContent(
        content={
            "script_text": "Hey, this is Alex from Acme. Just following up on our demo. Give me a call back.",
            "duration_seconds": 30,
            "word_count": 16,
            "cta_text": "Give me a call back.",
            "tone_notes": "Warm, conversational",
        },
        usage={"input_tokens": 100, "output_tokens": 50},
        model="claude-sonnet-4-20250514",
    ))
    return mock


def _mock_job_service() -> AsyncMock:
    mock = AsyncMock()
    mock.update_status = AsyncMock()
    mock.complete_job = AsyncMock()
    return mock


def _mock_storage_service() -> AsyncMock:
    mock = AsyncMock()
    mock.upload_artifact = AsyncMock(return_value="https://supabase.co/storage/audio/test.mp3")
    return mock


def _mock_claude_client() -> AsyncMock:
    return AsyncMock()


# ---------------------------------------------------------------------------
# Tests: Protocol compliance
# ---------------------------------------------------------------------------

class TestAudioRendererProtocol:
    def test_satisfies_renderer_protocol(self):
        renderer = AudioRenderer(
            elevenlabs_provider=_mock_elevenlabs(),
            script_generator=_mock_script_generator(),
        )
        assert isinstance(renderer, RendererProtocol)


# ---------------------------------------------------------------------------
# Tests: render() — passthrough with script_text
# ---------------------------------------------------------------------------

class TestAudioRendererPassthrough:
    async def test_renders_audio_with_script_text(self):
        mock_el = _mock_elevenlabs()
        renderer = AudioRenderer(elevenlabs_provider=mock_el)

        script = "Hello, this is a test voicemail script for rendering."
        content = _make_content(script_text=script)
        result = await renderer.render(content, _make_spec(), _make_brand_context())

        assert isinstance(result, RenderedArtifact)
        assert result.content_type == "audio/mpeg"
        assert result.data == FAKE_AUDIO

        # ElevenLabs was called with the script text
        mock_el.execute.assert_called_once()
        call_args = mock_el.execute.call_args
        assert call_args.args[0]["text"] == script

    async def test_passthrough_metadata_marks_not_generated(self):
        mock_el = _mock_elevenlabs()
        renderer = AudioRenderer(elevenlabs_provider=mock_el)

        content = _make_content(script_text="Hello world")
        result = await renderer.render(content, _make_spec(), _make_brand_context())

        assert result.metadata["script_generated_by_claude"] is False

    async def test_passthrough_with_custom_voice_id(self):
        mock_el = _mock_elevenlabs()
        renderer = AudioRenderer(elevenlabs_provider=mock_el)

        content = GeneratedContent(content={
            "script_text": "Hello world",
            "voice_id": "custom-voice-xyz",
        })
        await renderer.render(content, _make_spec(), _make_brand_context())

        call_args = mock_el.execute.call_args
        assert call_args.args[0]["voice_id"] == "custom-voice-xyz"

    async def test_passthrough_with_voice_settings_override(self):
        mock_el = _mock_elevenlabs()
        renderer = AudioRenderer(elevenlabs_provider=mock_el)

        content = GeneratedContent(content={
            "script_text": "Hello world",
            "voice_settings_override": {"stability": 0.8, "style": 0.3},
        })
        await renderer.render(content, _make_spec(), _make_brand_context())

        call_args = mock_el.execute.call_args
        assert call_args.args[0]["voice_settings"] == {"stability": 0.8, "style": 0.3}


# ---------------------------------------------------------------------------
# Tests: render() — validation
# ---------------------------------------------------------------------------

class TestAudioRendererValidation:
    async def test_rejects_script_over_character_limit(self):
        mock_el = _mock_elevenlabs()
        renderer = AudioRenderer(elevenlabs_provider=mock_el)

        long_script = "x" * (MAX_CHARACTERS + 1)
        content = _make_content(script_text=long_script)

        with pytest.raises(ValidationError, match="exceeds.*character limit"):
            await renderer.render(content, _make_spec(), _make_brand_context())

    async def test_accepts_script_at_character_limit(self):
        mock_el = _mock_elevenlabs()
        renderer = AudioRenderer(elevenlabs_provider=mock_el)

        script = "x" * MAX_CHARACTERS
        content = _make_content(script_text=script)
        result = await renderer.render(content, _make_spec(), _make_brand_context())

        assert isinstance(result, RenderedArtifact)


# ---------------------------------------------------------------------------
# Tests: render() — output format
# ---------------------------------------------------------------------------

class TestAudioRendererOutput:
    async def test_filename_contains_spec_id(self):
        mock_el = _mock_elevenlabs()
        renderer = AudioRenderer(elevenlabs_provider=mock_el)

        content = _make_content(script_text="Hello")
        result = await renderer.render(content, _make_spec(), _make_brand_context())

        assert result.filename.startswith("audio__voice_channel_")
        assert result.filename.endswith(".mp3")

    async def test_metadata_includes_renderer_tag(self):
        mock_el = _mock_elevenlabs()
        renderer = AudioRenderer(elevenlabs_provider=mock_el)

        content = _make_content(script_text="Hello")
        result = await renderer.render(content, _make_spec(), _make_brand_context())

        assert result.metadata["renderer"] == "audio"

    async def test_metadata_includes_tts_metadata(self):
        mock_el = _mock_elevenlabs()
        renderer = AudioRenderer(elevenlabs_provider=mock_el)

        content = _make_content(script_text="Hello")
        result = await renderer.render(content, _make_spec(), _make_brand_context())

        assert result.metadata["voice_id_used"] == "voice-abc"
        assert result.metadata["model_used"] == "eleven_multilingual_v2"
        assert result.metadata["output_format"] == "mp3_44100_128"


# ---------------------------------------------------------------------------
# Tests: render_pipeline() — script generation + TTS
# ---------------------------------------------------------------------------

class TestAudioRendererPipeline:
    async def test_generates_script_when_not_provided(self):
        mock_el = _mock_elevenlabs()
        mock_gen = _mock_script_generator()
        renderer = AudioRenderer(elevenlabs_provider=mock_el, script_generator=mock_gen)

        content_props = {
            "topic": "Follow-up after product demo",
            "duration_target": 30,
            "duration_seconds": 30,
        }

        result = await renderer.render_pipeline(
            content_props=content_props,
            spec=_make_spec(),
            brand_context=_make_brand_context(),
            claude_client=_mock_claude_client(),
        )

        # Script generator was called
        mock_gen.generate.assert_called_once()
        # ElevenLabs was called with generated script
        mock_el.execute.assert_called_once()
        call_text = mock_el.execute.call_args.args[0]["text"]
        assert "Alex from Acme" in call_text

        assert isinstance(result, RenderedArtifact)
        assert result.metadata["script_generated_by_claude"] is True

    async def test_skips_generation_when_script_provided(self):
        mock_el = _mock_elevenlabs()
        mock_gen = _mock_script_generator()
        renderer = AudioRenderer(elevenlabs_provider=mock_el, script_generator=mock_gen)

        content_props = {
            "script_text": "Pre-written script text here.",
            "duration_target": 30,
        }

        result = await renderer.render_pipeline(
            content_props=content_props,
            spec=_make_spec(),
            brand_context=_make_brand_context(),
            claude_client=_mock_claude_client(),
        )

        # Script generator was NOT called
        mock_gen.generate.assert_not_called()
        # ElevenLabs was called with provided script
        mock_el.execute.assert_called_once()
        call_text = mock_el.execute.call_args.args[0]["text"]
        assert call_text == "Pre-written script text here."

        assert result.metadata["script_generated_by_claude"] is False


# ---------------------------------------------------------------------------
# Tests: render_pipeline() — job progress updates
# ---------------------------------------------------------------------------

class TestAudioRendererJobProgress:
    async def test_updates_job_progress_during_generation(self):
        mock_el = _mock_elevenlabs()
        mock_gen = _mock_script_generator()
        mock_jobs = _mock_job_service()
        renderer = AudioRenderer(elevenlabs_provider=mock_el, script_generator=mock_gen)

        content_props = {
            "topic": "Test topic",
            "duration_target": 30,
            "duration_seconds": 30,
        }

        await renderer.render_pipeline(
            content_props=content_props,
            spec=_make_spec(),
            brand_context=_make_brand_context(),
            claude_client=_mock_claude_client(),
            job_service=mock_jobs,
            job_id="job-123",
        )

        # Job progress was updated multiple times
        assert mock_jobs.update_status.call_count >= 3
        # Job was completed
        mock_jobs.complete_job.assert_called_once()

    async def test_job_progress_increases_monotonically(self):
        mock_el = _mock_elevenlabs()
        mock_gen = _mock_script_generator()
        mock_jobs = _mock_job_service()
        renderer = AudioRenderer(elevenlabs_provider=mock_el, script_generator=mock_gen)

        content_props = {
            "topic": "Test topic",
            "duration_target": 30,
            "duration_seconds": 30,
        }

        await renderer.render_pipeline(
            content_props=content_props,
            spec=_make_spec(),
            brand_context=_make_brand_context(),
            claude_client=_mock_claude_client(),
            job_service=mock_jobs,
            job_id="job-123",
        )

        progress_values = [
            call.kwargs.get("progress") or call.args[2] if len(call.args) > 2 else call.kwargs.get("progress")
            for call in mock_jobs.update_status.call_args_list
        ]
        progress_values = [p for p in progress_values if p is not None]
        assert progress_values == sorted(progress_values)

    async def test_skips_job_updates_when_no_job_service(self):
        mock_el = _mock_elevenlabs()
        mock_gen = _mock_script_generator()
        renderer = AudioRenderer(elevenlabs_provider=mock_el, script_generator=mock_gen)

        content_props = {
            "topic": "Test",
            "duration_target": 30,
            "duration_seconds": 30,
        }

        # Should not raise even without job_service
        result = await renderer.render_pipeline(
            content_props=content_props,
            spec=_make_spec(),
            brand_context=_make_brand_context(),
            claude_client=_mock_claude_client(),
        )
        assert isinstance(result, RenderedArtifact)


# ---------------------------------------------------------------------------
# Tests: render_pipeline() — storage upload
# ---------------------------------------------------------------------------

class TestAudioRendererStorage:
    async def test_uploads_to_supabase_storage(self):
        mock_el = _mock_elevenlabs()
        mock_storage = _mock_storage_service()
        renderer = AudioRenderer(elevenlabs_provider=mock_el)

        content_props = {
            "script_text": "Hello, this is a test.",
            "duration_target": 30,
        }

        result = await renderer.render_pipeline(
            content_props=content_props,
            spec=_make_spec(),
            brand_context=_make_brand_context(),
            claude_client=_mock_claude_client(),
            storage_service=mock_storage,
            organization_id="org-123",
        )

        mock_storage.upload_artifact.assert_called_once()
        call_kwargs = mock_storage.upload_artifact.call_args.kwargs
        assert call_kwargs["org_id"] == "org-123"
        assert call_kwargs["artifact_type"] == "audio"
        assert call_kwargs["content_type"] == "audio/mpeg"
        assert call_kwargs["ext"] == "mp3"
        assert call_kwargs["data"] == FAKE_AUDIO

        assert result.metadata["content_url"] == "https://supabase.co/storage/audio/test.mp3"

    async def test_skips_storage_when_no_service(self):
        mock_el = _mock_elevenlabs()
        renderer = AudioRenderer(elevenlabs_provider=mock_el)

        content_props = {
            "script_text": "Hello test.",
            "duration_target": 30,
        }

        result = await renderer.render_pipeline(
            content_props=content_props,
            spec=_make_spec(),
            brand_context=_make_brand_context(),
            claude_client=_mock_claude_client(),
        )

        assert result.metadata["content_url"] is None
        assert isinstance(result, RenderedArtifact)


# ---------------------------------------------------------------------------
# Tests: render_pipeline() — validation errors
# ---------------------------------------------------------------------------

class TestAudioRendererPipelineValidation:
    async def test_rejects_empty_generated_script(self):
        mock_el = _mock_elevenlabs()
        mock_gen = AsyncMock(spec=AudioScriptGenerator)
        mock_gen.generate = AsyncMock(return_value=GeneratedContent(
            content={"script_text": "", "duration_seconds": 30, "word_count": 0, "cta_text": "", "tone_notes": ""},
        ))
        renderer = AudioRenderer(elevenlabs_provider=mock_el, script_generator=mock_gen)

        content_props = {"topic": "Test", "duration_target": 30, "duration_seconds": 30}

        with pytest.raises(ValidationError, match="Script text is empty"):
            await renderer.render_pipeline(
                content_props=content_props,
                spec=_make_spec(),
                brand_context=_make_brand_context(),
                claude_client=_mock_claude_client(),
            )

    async def test_rejects_over_limit_generated_script(self):
        mock_el = _mock_elevenlabs()
        long_script = "x" * (MAX_CHARACTERS + 1)
        mock_gen = AsyncMock(spec=AudioScriptGenerator)
        mock_gen.generate = AsyncMock(return_value=GeneratedContent(
            content={"script_text": long_script, "duration_seconds": 30, "word_count": 1000, "cta_text": "", "tone_notes": ""},
        ))
        renderer = AudioRenderer(elevenlabs_provider=mock_el, script_generator=mock_gen)

        content_props = {"topic": "Test", "duration_target": 30, "duration_seconds": 30}

        with pytest.raises(ValidationError, match="exceeds.*character limit"):
            await renderer.render_pipeline(
                content_props=content_props,
                spec=_make_spec(),
                brand_context=_make_brand_context(),
                claude_client=_mock_claude_client(),
            )

    async def test_rejects_over_limit_passthrough_script(self):
        mock_el = _mock_elevenlabs()
        renderer = AudioRenderer(elevenlabs_provider=mock_el)

        long_script = "x" * (MAX_CHARACTERS + 1)
        content_props = {"script_text": long_script, "duration_target": 30}

        with pytest.raises(ValidationError, match="exceeds.*character limit"):
            await renderer.render_pipeline(
                content_props=content_props,
                spec=_make_spec(),
                brand_context=_make_brand_context(),
                claude_client=_mock_claude_client(),
            )


# ---------------------------------------------------------------------------
# Tests: render_pipeline() — metadata
# ---------------------------------------------------------------------------

class TestAudioRendererPipelineMetadata:
    async def test_metadata_includes_script_text_used(self):
        mock_el = _mock_elevenlabs()
        renderer = AudioRenderer(elevenlabs_provider=mock_el)

        script = "Hello, this is a test script."
        content_props = {"script_text": script, "duration_target": 30}

        result = await renderer.render_pipeline(
            content_props=content_props,
            spec=_make_spec(),
            brand_context=_make_brand_context(),
            claude_client=_mock_claude_client(),
        )

        assert result.metadata["script_text_used"] == script

    async def test_metadata_includes_artifact_id(self):
        mock_el = _mock_elevenlabs()
        renderer = AudioRenderer(elevenlabs_provider=mock_el)

        content_props = {"script_text": "Hello", "duration_target": 30}

        result = await renderer.render_pipeline(
            content_props=content_props,
            spec=_make_spec(),
            brand_context=_make_brand_context(),
            claude_client=_mock_claude_client(),
        )

        assert "artifact_id" in result.metadata
        assert len(result.metadata["artifact_id"]) == 32  # hex UUID

    async def test_pipeline_voice_id_forwarded(self):
        mock_el = _mock_elevenlabs()
        renderer = AudioRenderer(elevenlabs_provider=mock_el)

        content_props = {
            "script_text": "Hello",
            "voice_id": "custom-voice-id",
            "duration_target": 30,
        }

        await renderer.render_pipeline(
            content_props=content_props,
            spec=_make_spec(),
            brand_context=_make_brand_context(),
            claude_client=_mock_claude_client(),
        )

        call_args = mock_el.execute.call_args
        assert call_args.args[0]["voice_id"] == "custom-voice-id"


# ---------------------------------------------------------------------------
# Tests: Constructor defaults
# ---------------------------------------------------------------------------

class TestAudioRendererConstructor:
    def test_uses_provided_dependencies(self):
        mock_el = _mock_elevenlabs()
        mock_gen = _mock_script_generator()
        renderer = AudioRenderer(elevenlabs_provider=mock_el, script_generator=mock_gen)
        assert renderer._elevenlabs is mock_el
        assert renderer._script_generator is mock_gen

    def test_creates_defaults_when_none_provided(self):
        with patch("src.renderers.audio_renderer.ElevenLabsProvider"), \
             patch("src.renderers.audio_renderer.AudioScriptGenerator"):
            renderer = AudioRenderer()
            assert renderer._elevenlabs is not None
            assert renderer._script_generator is not None
