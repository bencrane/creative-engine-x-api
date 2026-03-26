"""Video renderer for ad creatives and explainer videos.

CEX-34: Full pipeline — generate video script (if needed), map to Remotion
inputProps, trigger Lambda render, poll progress, copy S3→Supabase,
and return RenderedArtifact.
"""

from __future__ import annotations

import asyncio
import logging
import uuid

from src.brand.models import BrandContext
from src.generators.base import GeneratedContent
from src.generators.video_script import VideoScriptGenerator
from src.integrations.claude_client import ClaudeClient
from src.jobs.service import JobService
from src.providers.remotion_provider import RemotionProvider
from src.renderers.base import RenderedArtifact
from src.shared.errors import ValidationError
from src.specs.models import FormatSpec
from src.storage.service import StorageService

logger = logging.getLogger(__name__)

FPS = 30
DEFAULT_CTA_DURATION_SECONDS = 3
POLL_INTERVAL_SECONDS = 3
DEFAULT_TIMEOUT_SECONDS = 300
LONG_VIDEO_TIMEOUT_SECONDS = 900

# Mapping from spec surface/format to Remotion composition ID
COMPOSITION_MAP: dict[str, str] = {
    "meta_1x1": "meta-ad-1x1",
    "meta_9x16": "meta-ad-9x16",
    "meta_16x9": "meta-ad-16x9",
    "tiktok": "tiktok-ad",
    "generic_16x9": "generic-video-16x9",
    "generic_1x1": "generic-video-1x1",
    "generic_9x16": "generic-video-9x16",
}
DEFAULT_COMPOSITION = "generic-video-16x9"


class VideoRenderer:
    """Render video from script via Remotion Lambda.

    Implements RendererProtocol. Pipeline:
    1. If script not in content → generate via VideoScriptGenerator
    2. Map script to Remotion inputProps
    3. Trigger render via RemotionProvider
    4. Poll progress until complete
    5. Copy S3→Supabase Storage
    6. Return RenderedArtifact

    The render() method follows the standard RendererProtocol signature.
    For the full async pipeline with job progress and storage, use render_pipeline().
    """

    def __init__(
        self,
        remotion_provider: RemotionProvider | None = None,
        script_generator: VideoScriptGenerator | None = None,
    ):
        self._remotion = remotion_provider or RemotionProvider()
        self._script_generator = script_generator or VideoScriptGenerator()

    async def render(
        self,
        content: GeneratedContent,
        spec: FormatSpec,
        brand_context: BrandContext,
    ) -> RenderedArtifact:
        """Render video from generated content.

        Expects content.content to be a dict with either:
        - scenes: list[dict] (passthrough — skip generation)
        - topic + duration (generation mode)

        Plus optional: composition_id, cta_text, music_url
        """
        data = content.content
        if isinstance(data, dict):
            content_props = dict(data)
        else:
            content_props = data.__dict__.copy() if hasattr(data, "__dict__") else {}

        scenes = content_props.get("scenes")
        if not scenes:
            raise ValidationError("scenes are required for video rendering in render() mode")

        # Build inputProps for Remotion
        input_props = self._build_input_props(content_props, brand_context)
        composition_id = self._resolve_composition_id(content_props, spec)

        # Trigger render
        result = await self._remotion.execute({
            "composition_id": composition_id,
            "input_props": input_props,
        })

        spec_id = spec.spec_id if spec else "video"
        artifact_id = uuid.uuid4().hex
        filename = f"{spec_id}_{artifact_id[:8]}.mp4"

        return RenderedArtifact(
            data=b"",  # Video bytes available after polling in pipeline mode
            content_type="video/mp4",
            filename=filename,
            metadata={
                "renderer": "video",
                "render_id": result.data["render_id"],
                "bucket_name": result.data["bucket_name"],
                "composition_id": composition_id,
                **result.metadata,
            },
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
        """Full async pipeline with script generation, render, polling, and storage.

        Steps:
        1. If scenes not provided: generate via VideoScriptGenerator
        2. Map to Remotion inputProps
        3. Trigger render via RemotionProvider
        4. Poll progress until complete
        5. Copy rendered video to Supabase Storage
        6. Update job progress throughout
        """
        # Step 1: Script generation or passthrough
        if job_service and job_id:
            await job_service.update_status(job_id, "rendering", progress=0.05)

        scenes = content_props.get("scenes")
        script_generated = False

        if not scenes:
            if job_service and job_id:
                await job_service.update_status(job_id, "rendering", progress=0.1)

            generated = await self._script_generator.generate(
                content_props, brand_context, spec, claude_client
            )
            script_data = generated.content
            if isinstance(script_data, dict):
                scenes = self._extract_scenes_from_script(script_data)
                content_props = {**content_props, "scenes": scenes}
                if script_data.get("cta") and not content_props.get("cta_text"):
                    cta_segment = script_data["cta"]
                    if isinstance(cta_segment, dict):
                        content_props["cta_text"] = cta_segment.get("text_overlay") or cta_segment.get("spoken_text", "Learn More")
            script_generated = True

        if not scenes:
            raise ValidationError("No scenes available after script generation")

        if job_service and job_id:
            await job_service.update_status(job_id, "rendering", progress=0.2)

        # Step 2: Build inputProps and resolve composition
        input_props = self._build_input_props(content_props, brand_context)
        composition_id = self._resolve_composition_id(content_props, spec)

        # Step 3: Trigger render
        render_result = await self._remotion.execute({
            "composition_id": composition_id,
            "input_props": input_props,
        })

        render_id = render_result.data["render_id"]
        bucket_name = render_result.data["bucket_name"]

        if job_service and job_id:
            await job_service.update_status(job_id, "rendering", progress=0.3)

        # Step 4: Poll progress
        total_duration = sum(s.get("duration_seconds", 5) for s in scenes)
        timeout = LONG_VIDEO_TIMEOUT_SECONDS if total_duration > 60 else DEFAULT_TIMEOUT_SECONDS

        output_file = await self._poll_render_progress(
            render_id=render_id,
            bucket_name=bucket_name,
            timeout=timeout,
            job_service=job_service,
            job_id=job_id,
        )

        if job_service and job_id:
            await job_service.update_status(job_id, "rendering", progress=0.8)

        # Step 5: Copy S3→Supabase
        artifact_id = uuid.uuid4().hex
        content_url = None

        if storage_service and organization_id and output_file:
            video_data = await storage_service.download_from_url(output_file)
            content_url = await storage_service.upload_artifact(
                org_id=organization_id,
                artifact_type="video",
                artifact_id=artifact_id,
                data=video_data,
                content_type="video/mp4",
                ext="mp4",
            )

        if job_service and job_id:
            await job_service.update_status(job_id, "rendering", progress=0.9)

        # Build result
        metadata = {
            "renderer": "video",
            "script_generated_by_claude": script_generated,
            "artifact_id": artifact_id,
            "content_url": content_url,
            "composition_id": composition_id,
            "render_id": render_id,
            "s3_output_file": output_file,
            "scene_count": len(scenes),
            "total_duration_seconds": total_duration,
        }

        spec_id = spec.spec_id if spec else "video"
        filename = f"{spec_id}_{artifact_id[:8]}.mp4"

        artifact = RenderedArtifact(
            data=b"",  # Video stored in Supabase, referenced by content_url
            content_type="video/mp4",
            filename=filename,
            metadata=metadata,
        )

        # Mark job complete
        if job_service and job_id:
            await job_service.complete_job(
                job_id, artifact_id=artifact_id, content_url=content_url
            )

        return artifact

    async def _poll_render_progress(
        self,
        render_id: str,
        bucket_name: str,
        timeout: int,
        job_service: JobService | None = None,
        job_id: str | None = None,
    ) -> str | None:
        """Poll Remotion Lambda until render completes or times out."""
        elapsed = 0

        while elapsed < timeout:
            progress = await self._remotion.get_render_progress(render_id, bucket_name)

            if progress["fatalErrorEncountered"]:
                errors = progress.get("errors", [])
                error_msg = errors[0].get("message", "Unknown error") if errors else "Unknown error"
                raise RuntimeError(f"Video render failed: {error_msg}")

            if progress["done"]:
                return progress.get("outputFile")

            # Update job progress (map 0.3-0.8 range for render phase)
            if job_service and job_id:
                render_progress = progress.get("overallProgress", 0)
                job_progress = 0.3 + (render_progress * 0.5)
                await job_service.update_status(
                    job_id, "rendering", progress=min(job_progress, 0.79)
                )

            await asyncio.sleep(POLL_INTERVAL_SECONDS)
            elapsed += POLL_INTERVAL_SECONDS

        raise TimeoutError(
            f"Video render timed out after {timeout}s (render_id={render_id})"
        )

    def _build_input_props(self, content_props: dict, brand_context: BrandContext) -> dict:
        """Build Remotion inputProps from content props and brand context."""
        scenes = content_props.get("scenes", [])
        brand_guidelines = brand_context.brand_guidelines

        return {
            "scenes": [
                {
                    "text": s.get("text", s.get("spoken_text", "")),
                    "visual_direction": s.get("visual_direction", ""),
                    "duration_seconds": s.get("duration_seconds", 5),
                }
                for s in scenes
            ],
            "brand": {
                "primary_color": brand_guidelines.primary_color if brand_guidelines else "#0066FF",
                "secondary_color": brand_guidelines.secondary_color if brand_guidelines else "#09090b",
                "company_name": brand_context.company_name,
                "logo_url": brand_guidelines.logo_url if brand_guidelines and hasattr(brand_guidelines, "logo_url") else None,
                "font_family": brand_guidelines.font_family if brand_guidelines else None,
            },
            "cta_text": content_props.get("cta_text", "Learn More"),
            "music_url": content_props.get("music_url"),
        }

    def _resolve_composition_id(self, content_props: dict, spec: FormatSpec) -> str:
        """Resolve Remotion composition ID from content props or spec."""
        # Explicit composition_id takes priority
        if content_props.get("composition_id"):
            return content_props["composition_id"]

        # Try mapping from spec
        if spec and spec.spec_id:
            for key, comp_id in COMPOSITION_MAP.items():
                if key in spec.spec_id:
                    return comp_id

        # Try from platform/aspect_ratio
        platform = content_props.get("platform", "")
        aspect_ratio = content_props.get("aspect_ratio", "")

        if "tiktok" in platform.lower():
            return "tiktok-ad"
        if "meta" in platform.lower():
            if "9:16" in aspect_ratio:
                return "meta-ad-9x16"
            if "1:1" in aspect_ratio:
                return "meta-ad-1x1"
            return "meta-ad-16x9"

        return DEFAULT_COMPOSITION

    def _extract_scenes_from_script(self, script_data: dict) -> list[dict]:
        """Extract scenes from VideoScriptGenerator output."""
        scenes: list[dict] = []

        # Hook segment
        hook = script_data.get("hook")
        if hook and isinstance(hook, dict):
            scenes.append(self._segment_to_scene(hook))

        # Body segments
        body = script_data.get("body", [])
        for segment in body:
            if isinstance(segment, dict):
                scenes.append(self._segment_to_scene(segment))

        return scenes

    def _segment_to_scene(self, segment: dict) -> dict:
        """Convert a VideoScriptGenerator segment to a Remotion scene."""
        # Parse duration from timestamps if available
        duration = self._parse_segment_duration(segment)

        return {
            "text": segment.get("spoken_text", segment.get("text", "")),
            "visual_direction": segment.get("visual_direction", ""),
            "duration_seconds": duration,
        }

    def _parse_segment_duration(self, segment: dict) -> int:
        """Parse duration from timestamp_start and timestamp_end."""
        start = segment.get("timestamp_start", "")
        end = segment.get("timestamp_end", "")

        try:
            start_seconds = self._timestamp_to_seconds(start)
            end_seconds = self._timestamp_to_seconds(end)
            duration = end_seconds - start_seconds
            if duration > 0:
                return max(1, round(duration))
        except (ValueError, IndexError):
            pass

        return segment.get("duration_seconds", 5)

    @staticmethod
    def _timestamp_to_seconds(ts: str) -> int:
        """Convert M:SS timestamp to seconds."""
        if not ts or ":" not in ts:
            return 0
        parts = ts.split(":")
        return int(parts[0]) * 60 + int(parts[1])
