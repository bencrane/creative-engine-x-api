"""Audio renderer for voicemail drops and audio ads.

CEX-30: Two-step pipeline — generate script via AudioScriptGenerator (if needed),
then render audio via ElevenLabsProvider. Stores result in Supabase Storage
and updates job progress during pipeline steps.
"""

from __future__ import annotations

import logging
import uuid

from src.brand.models import BrandContext
from src.generators.audio_script import AudioScriptGenerator
from src.generators.base import GeneratedContent
from src.integrations.claude_client import ClaudeClient
from src.jobs.service import JobService
from src.providers.elevenlabs_provider import ElevenLabsProvider, MAX_CHARACTERS
from src.renderers.base import RenderedArtifact
from src.storage.service import StorageService
from src.shared.errors import ValidationError
from src.specs.models import FormatSpec

logger = logging.getLogger(__name__)


class AudioRenderer:
    """Render audio from script text via ElevenLabs TTS.

    Implements RendererProtocol. Two-step pipeline:
    1. If script_text not in content_props → generate via AudioScriptGenerator
    2. Call ElevenLabsProvider.execute() with text + voice config

    The render() method follows the standard RendererProtocol signature.
    For the full async pipeline with job progress and storage, use render_pipeline().
    """

    def __init__(
        self,
        elevenlabs_provider: ElevenLabsProvider | None = None,
        script_generator: AudioScriptGenerator | None = None,
    ):
        self._elevenlabs = elevenlabs_provider or ElevenLabsProvider()
        self._script_generator = script_generator or AudioScriptGenerator()

    async def render(
        self,
        content: GeneratedContent,
        spec: FormatSpec,
        brand_context: BrandContext,
    ) -> RenderedArtifact:
        """Render audio from generated content.

        Expects content.content to be a dict with either:
        - script_text: str (passthrough mode — skip generation)
        - topic + duration_target (generation mode)

        Plus optional: voice_id, voice_settings_override
        """
        data = content.content
        if isinstance(data, dict):
            content_props = dict(data)
        else:
            content_props = data.__dict__.copy() if hasattr(data, "__dict__") else {}

        script_text = content_props.get("script_text", "")

        # Validate script length
        if script_text and len(script_text) > MAX_CHARACTERS:
            raise ValidationError(
                f"Script text exceeds {MAX_CHARACTERS} character limit: "
                f"{len(script_text)} characters"
            )

        # Build TTS input
        voice_id = content_props.get("voice_id")
        voice_settings = content_props.get("voice_settings_override", {})

        input_data = {"text": script_text}
        if voice_id:
            input_data["voice_id"] = voice_id
        if voice_settings:
            input_data["voice_settings"] = voice_settings

        # Call ElevenLabs TTS
        result = await self._elevenlabs.execute(input_data)

        # Build metadata
        metadata = {
            "renderer": "audio",
            "script_generated_by_claude": not bool(content_props.get("script_text")),
            **result.metadata,
        }

        spec_id = spec.spec_id if spec else "audio"
        filename = f"{spec_id}_{uuid.uuid4().hex[:8]}.mp3"

        return RenderedArtifact(
            data=result.data,
            content_type="audio/mpeg",
            filename=filename,
            metadata=metadata,
        )

    async def render_pipeline(
        self,
        content_props: dict,
        spec: FormatSpec,
        brand_context: BrandContext,
        claude_client: ClaudeClient,
        job_service: JobService | None = None,
        job_id: str | None = None,
        storage_service: StorageService | None = None,
        organization_id: str | None = None,
    ) -> RenderedArtifact:
        """Full async pipeline with script generation, TTS, storage, and job progress.

        Steps:
        1. If script_text not provided: generate via AudioScriptGenerator
        2. Validate script ≤5000 chars
        3. Call ElevenLabsProvider for TTS
        4. Upload to Supabase Storage
        5. Update job progress throughout
        """
        # Step 1: Script generation or passthrough
        if job_service and job_id:
            await job_service.update_status(job_id, "rendering", progress=0.1)

        script_text = content_props.get("script_text")
        script_generated = False

        if not script_text:
            # Generate script via Claude
            if job_service and job_id:
                await job_service.update_status(job_id, "rendering", progress=0.2)

            generated = await self._script_generator.generate(
                content_props, brand_context, spec, claude_client
            )
            script_data = generated.content
            if isinstance(script_data, dict):
                script_text = script_data.get("script_text", "")
            else:
                script_text = str(script_data)
            script_generated = True

        # Step 2: Validate script length
        if not script_text or not script_text.strip():
            raise ValidationError("Script text is empty after generation")
        if len(script_text) > MAX_CHARACTERS:
            raise ValidationError(
                f"Script text exceeds {MAX_CHARACTERS} character limit: "
                f"{len(script_text)} characters"
            )

        if job_service and job_id:
            await job_service.update_status(job_id, "rendering", progress=0.4)

        # Step 3: TTS via ElevenLabs
        voice_id = content_props.get("voice_id")
        voice_settings = content_props.get("voice_settings_override", {})

        input_data = {"text": script_text}
        if voice_id:
            input_data["voice_id"] = voice_id
        if voice_settings:
            input_data["voice_settings"] = voice_settings

        tts_result = await self._elevenlabs.execute(input_data)

        if job_service and job_id:
            await job_service.update_status(job_id, "rendering", progress=0.7)

        # Step 4: Upload to Supabase Storage
        artifact_id = uuid.uuid4().hex
        content_url = None

        if storage_service and organization_id:
            content_url = await storage_service.upload_artifact(
                org_id=organization_id,
                artifact_type="audio",
                artifact_id=artifact_id,
                data=tts_result.data,
                content_type="audio/mpeg",
                ext="mp3",
            )

        if job_service and job_id:
            await job_service.update_status(job_id, "rendering", progress=0.9)

        # Build result
        metadata = {
            "renderer": "audio",
            "script_generated_by_claude": script_generated,
            "artifact_id": artifact_id,
            "content_url": content_url,
            "script_text_used": script_text,
            **tts_result.metadata,
        }

        spec_id = spec.spec_id if spec else "audio"
        filename = f"{spec_id}_{artifact_id[:8]}.mp3"

        artifact = RenderedArtifact(
            data=tts_result.data,
            content_type="audio/mpeg",
            filename=filename,
            metadata=metadata,
        )

        # Mark job complete
        if job_service and job_id:
            await job_service.complete_job(job_id, artifact_id=artifact_id, content_url=content_url)

        return artifact
