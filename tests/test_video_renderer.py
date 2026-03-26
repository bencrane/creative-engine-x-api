"""Tests for the video renderer — script generation + Remotion pipeline (CEX-34)."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.brand.models import BrandContext, BrandGuidelines
from src.generators.base import GeneratedContent
from src.generators.video_script import VideoScriptGenerator
from src.providers.remotion_provider import RemotionProvider, ProviderResult
from src.renderers.base import RenderedArtifact, RendererProtocol
from src.renderers.video_renderer import (
    COMPOSITION_MAP,
    DEFAULT_COMPOSITION,
    DEFAULT_TIMEOUT_SECONDS,
    LONG_VIDEO_TIMEOUT_SECONDS,
    VideoRenderer,
)
from src.shared.errors import ValidationError
from src.specs.models import FormatSpec


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

FAKE_RENDER_ID = "render-abc123"
FAKE_BUCKET_NAME = "remotionlambda-test-bucket"
FAKE_OUTPUT_FILE = "https://s3.amazonaws.com/bucket/renders/abc/out.mp4"
FAKE_VIDEO_DATA = b"\x00\x00\x00\x1cftypisom" + b"\x00" * 100


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
        "spec_id": "meta_1x1",
        "artifact_type": "video",
        "surface": "meta",
        "version": "1.0",
    }
    defaults.update(overrides)
    return FormatSpec(**defaults)


def _make_content(scenes: list[dict] | None = None, **overrides) -> GeneratedContent:
    content: dict = {}
    if scenes is not None:
        content["scenes"] = scenes
    content.update(overrides)
    return GeneratedContent(content=content)


def _make_scenes(count: int = 3, duration: int = 5) -> list[dict]:
    return [
        {
            "text": f"Scene {i + 1} text",
            "visual_direction": f"Direction for scene {i + 1}",
            "duration_seconds": duration,
        }
        for i in range(count)
    ]


def _mock_remotion_provider() -> AsyncMock:
    mock = AsyncMock(spec=RemotionProvider)
    mock.execute = AsyncMock(return_value=ProviderResult(
        data={
            "render_id": FAKE_RENDER_ID,
            "bucket_name": FAKE_BUCKET_NAME,
            "function_name": "remotion-render-fn",
            "region": "us-east-1",
        },
        content_type="video/mp4",
        metadata={
            "composition_id": "meta-ad-1x1",
            "codec": "h264",
            "render_id": FAKE_RENDER_ID,
            "bucket_name": FAKE_BUCKET_NAME,
        },
    ))
    mock.get_render_progress = AsyncMock(return_value={
        "done": True,
        "overallProgress": 1.0,
        "outputFile": FAKE_OUTPUT_FILE,
        "fatalErrorEncountered": False,
        "errors": [],
    })
    return mock


def _mock_script_generator() -> AsyncMock:
    mock = AsyncMock(spec=VideoScriptGenerator)
    mock.generate = AsyncMock(return_value=GeneratedContent(
        content={
            "hook": {
                "spoken_text": "Tired of slow analytics?",
                "visual_direction": "Quick zoom into dashboard",
                "timestamp_start": "0:00",
                "timestamp_end": "0:04",
            },
            "body": [
                {
                    "spoken_text": "Acme Analytics gives you real-time insights.",
                    "visual_direction": "Split screen showing metrics",
                    "timestamp_start": "0:04",
                    "timestamp_end": "0:10",
                },
                {
                    "spoken_text": "Track everything that matters.",
                    "visual_direction": "Dashboard flyover animation",
                    "timestamp_start": "0:10",
                    "timestamp_end": "0:16",
                },
            ],
            "cta": {
                "spoken_text": "Get started free today.",
                "visual_direction": "CTA button pulse",
                "text_overlay": "Start Free Trial",
                "timestamp_start": "0:16",
                "timestamp_end": "0:20",
            },
        },
        usage={"input_tokens": 200, "output_tokens": 150},
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
    mock.download_from_url = AsyncMock(return_value=FAKE_VIDEO_DATA)
    mock.upload_artifact = AsyncMock(return_value="https://supabase.co/storage/video/test.mp4")
    return mock


def _mock_claude_client() -> AsyncMock:
    return AsyncMock()


# ---------------------------------------------------------------------------
# Tests: Protocol compliance
# ---------------------------------------------------------------------------

class TestVideoRendererProtocol:
    def test_satisfies_renderer_protocol(self):
        renderer = VideoRenderer(
            remotion_provider=_mock_remotion_provider(),
            script_generator=_mock_script_generator(),
        )
        assert isinstance(renderer, RendererProtocol)


# ---------------------------------------------------------------------------
# Tests: render() — passthrough with scenes
# ---------------------------------------------------------------------------

class TestVideoRendererPassthrough:
    async def test_renders_video_with_scenes(self):
        mock_remotion = _mock_remotion_provider()
        renderer = VideoRenderer(remotion_provider=mock_remotion)

        scenes = _make_scenes(3)
        content = _make_content(scenes=scenes)
        result = await renderer.render(content, _make_spec(), _make_brand_context())

        assert isinstance(result, RenderedArtifact)
        assert result.content_type == "video/mp4"
        mock_remotion.execute.assert_called_once()

    async def test_render_metadata_includes_render_id(self):
        mock_remotion = _mock_remotion_provider()
        renderer = VideoRenderer(remotion_provider=mock_remotion)

        scenes = _make_scenes(2)
        content = _make_content(scenes=scenes)
        result = await renderer.render(content, _make_spec(), _make_brand_context())

        assert result.metadata["renderer"] == "video"
        assert result.metadata["render_id"] == FAKE_RENDER_ID
        assert result.metadata["bucket_name"] == FAKE_BUCKET_NAME

    async def test_render_rejects_missing_scenes(self):
        renderer = VideoRenderer(remotion_provider=_mock_remotion_provider())
        content = _make_content()  # No scenes
        with pytest.raises(ValidationError, match="scenes are required"):
            await renderer.render(content, _make_spec(), _make_brand_context())

    async def test_filename_contains_spec_id(self):
        mock_remotion = _mock_remotion_provider()
        renderer = VideoRenderer(remotion_provider=mock_remotion)

        scenes = _make_scenes(1)
        content = _make_content(scenes=scenes)
        result = await renderer.render(content, _make_spec(), _make_brand_context())

        assert result.filename.startswith("meta_1x1_")
        assert result.filename.endswith(".mp4")


# ---------------------------------------------------------------------------
# Tests: _build_input_props
# ---------------------------------------------------------------------------

class TestVideoRendererInputProps:
    def test_builds_input_props_with_scenes(self):
        renderer = VideoRenderer(remotion_provider=_mock_remotion_provider())
        scenes = _make_scenes(2)
        content_props = {"scenes": scenes, "cta_text": "Buy Now"}
        brand = _make_brand_context()

        props = renderer._build_input_props(content_props, brand)

        assert len(props["scenes"]) == 2
        assert props["scenes"][0]["text"] == "Scene 1 text"
        assert props["scenes"][0]["visual_direction"] == "Direction for scene 1"
        assert props["scenes"][0]["duration_seconds"] == 5
        assert props["cta_text"] == "Buy Now"

    def test_includes_brand_context(self):
        renderer = VideoRenderer(remotion_provider=_mock_remotion_provider())
        brand = _make_brand_context()
        content_props = {"scenes": _make_scenes(1)}

        props = renderer._build_input_props(content_props, brand)

        assert props["brand"]["primary_color"] == "#00e87b"
        assert props["brand"]["secondary_color"] == "#09090b"
        assert props["brand"]["company_name"] == "Acme Analytics"

    def test_defaults_cta_text(self):
        renderer = VideoRenderer(remotion_provider=_mock_remotion_provider())
        content_props = {"scenes": _make_scenes(1)}
        brand = _make_brand_context()

        props = renderer._build_input_props(content_props, brand)
        assert props["cta_text"] == "Learn More"

    def test_includes_music_url(self):
        renderer = VideoRenderer(remotion_provider=_mock_remotion_provider())
        content_props = {"scenes": _make_scenes(1), "music_url": "https://music.example.com/track.mp3"}
        brand = _make_brand_context()

        props = renderer._build_input_props(content_props, brand)
        assert props["music_url"] == "https://music.example.com/track.mp3"

    def test_brand_defaults_when_no_guidelines(self):
        renderer = VideoRenderer(remotion_provider=_mock_remotion_provider())
        brand = _make_brand_context(brand_guidelines=None)
        content_props = {"scenes": _make_scenes(1)}

        props = renderer._build_input_props(content_props, brand)
        assert props["brand"]["primary_color"] == "#0066FF"
        assert props["brand"]["secondary_color"] == "#09090b"


# ---------------------------------------------------------------------------
# Tests: _resolve_composition_id
# ---------------------------------------------------------------------------

class TestVideoRendererComposition:
    def test_explicit_composition_id(self):
        renderer = VideoRenderer(remotion_provider=_mock_remotion_provider())
        content_props = {"composition_id": "custom-comp"}
        spec = _make_spec()

        result = renderer._resolve_composition_id(content_props, spec)
        assert result == "custom-comp"

    def test_resolves_from_spec_id(self):
        renderer = VideoRenderer(remotion_provider=_mock_remotion_provider())
        for key, comp_id in COMPOSITION_MAP.items():
            spec = _make_spec(spec_id=f"video__{key}_format")
            result = renderer._resolve_composition_id({}, spec)
            assert result == comp_id

    def test_resolves_tiktok_platform(self):
        renderer = VideoRenderer(remotion_provider=_mock_remotion_provider())
        content_props = {"platform": "TikTok"}
        spec = _make_spec(spec_id="custom_spec")

        result = renderer._resolve_composition_id(content_props, spec)
        assert result == "tiktok-ad"

    def test_resolves_meta_platform_with_aspect_ratio(self):
        renderer = VideoRenderer(remotion_provider=_mock_remotion_provider())

        result = renderer._resolve_composition_id(
            {"platform": "Meta", "aspect_ratio": "9:16"},
            _make_spec(spec_id="custom_spec"),
        )
        assert result == "meta-ad-9x16"

        result = renderer._resolve_composition_id(
            {"platform": "Meta", "aspect_ratio": "1:1"},
            _make_spec(spec_id="custom_spec"),
        )
        assert result == "meta-ad-1x1"

        result = renderer._resolve_composition_id(
            {"platform": "Meta", "aspect_ratio": "16:9"},
            _make_spec(spec_id="custom_spec"),
        )
        assert result == "meta-ad-16x9"

    def test_falls_back_to_default(self):
        renderer = VideoRenderer(remotion_provider=_mock_remotion_provider())
        result = renderer._resolve_composition_id({}, _make_spec(spec_id="unknown_spec"))
        assert result == DEFAULT_COMPOSITION


# ---------------------------------------------------------------------------
# Tests: _extract_scenes_from_script
# ---------------------------------------------------------------------------

class TestVideoRendererScriptExtraction:
    def test_extracts_hook_and_body(self):
        renderer = VideoRenderer(remotion_provider=_mock_remotion_provider())
        script_data = {
            "hook": {
                "spoken_text": "Hook text",
                "visual_direction": "Hook visual",
                "timestamp_start": "0:00",
                "timestamp_end": "0:04",
            },
            "body": [
                {
                    "spoken_text": "Body segment 1",
                    "visual_direction": "Body visual 1",
                    "timestamp_start": "0:04",
                    "timestamp_end": "0:10",
                },
            ],
        }
        scenes = renderer._extract_scenes_from_script(script_data)

        assert len(scenes) == 2
        assert scenes[0]["text"] == "Hook text"
        assert scenes[0]["duration_seconds"] == 4
        assert scenes[1]["text"] == "Body segment 1"
        assert scenes[1]["duration_seconds"] == 6

    def test_handles_empty_body(self):
        renderer = VideoRenderer(remotion_provider=_mock_remotion_provider())
        script_data = {
            "hook": {
                "spoken_text": "Just a hook",
                "timestamp_start": "0:00",
                "timestamp_end": "0:05",
            },
            "body": [],
        }
        scenes = renderer._extract_scenes_from_script(script_data)
        assert len(scenes) == 1

    def test_handles_missing_hook(self):
        renderer = VideoRenderer(remotion_provider=_mock_remotion_provider())
        script_data = {
            "body": [
                {
                    "spoken_text": "Body only",
                    "timestamp_start": "0:00",
                    "timestamp_end": "0:05",
                },
            ],
        }
        scenes = renderer._extract_scenes_from_script(script_data)
        assert len(scenes) == 1
        assert scenes[0]["text"] == "Body only"


# ---------------------------------------------------------------------------
# Tests: _parse_segment_duration and _timestamp_to_seconds
# ---------------------------------------------------------------------------

class TestVideoRendererTimestamps:
    def test_parses_simple_timestamps(self):
        renderer = VideoRenderer(remotion_provider=_mock_remotion_provider())
        segment = {"timestamp_start": "0:00", "timestamp_end": "0:10"}
        assert renderer._parse_segment_duration(segment) == 10

    def test_parses_minute_timestamps(self):
        renderer = VideoRenderer(remotion_provider=_mock_remotion_provider())
        segment = {"timestamp_start": "1:00", "timestamp_end": "1:30"}
        assert renderer._parse_segment_duration(segment) == 30

    def test_falls_back_to_duration_seconds(self):
        renderer = VideoRenderer(remotion_provider=_mock_remotion_provider())
        segment = {"duration_seconds": 8}
        assert renderer._parse_segment_duration(segment) == 8

    def test_falls_back_to_default_5(self):
        renderer = VideoRenderer(remotion_provider=_mock_remotion_provider())
        segment = {}
        assert renderer._parse_segment_duration(segment) == 5

    def test_minimum_duration_is_1(self):
        renderer = VideoRenderer(remotion_provider=_mock_remotion_provider())
        # 0-second range → fallback
        segment = {"timestamp_start": "0:05", "timestamp_end": "0:05", "duration_seconds": 3}
        assert renderer._parse_segment_duration(segment) == 3

    def test_timestamp_to_seconds(self):
        assert VideoRenderer._timestamp_to_seconds("0:00") == 0
        assert VideoRenderer._timestamp_to_seconds("0:30") == 30
        assert VideoRenderer._timestamp_to_seconds("1:00") == 60
        assert VideoRenderer._timestamp_to_seconds("2:15") == 135
        assert VideoRenderer._timestamp_to_seconds("") == 0
        assert VideoRenderer._timestamp_to_seconds("no-colon") == 0


# ---------------------------------------------------------------------------
# Tests: render_pipeline() — script generation + render
# ---------------------------------------------------------------------------

class TestVideoRendererPipeline:
    async def test_generates_script_when_no_scenes(self):
        mock_remotion = _mock_remotion_provider()
        mock_gen = _mock_script_generator()
        renderer = VideoRenderer(remotion_provider=mock_remotion, script_generator=mock_gen)

        content_props = {
            "topic": "Product launch video",
            "duration": 20,
        }

        with patch("src.renderers.video_renderer.asyncio.sleep", new_callable=AsyncMock):
            result = await renderer.render_pipeline(
                content_props=content_props,
                spec=_make_spec(),
                brand_context=_make_brand_context(),
                claude_client=_mock_claude_client(),
            )

        mock_gen.generate.assert_called_once()
        mock_remotion.execute.assert_called_once()
        assert isinstance(result, RenderedArtifact)
        assert result.metadata["script_generated_by_claude"] is True

    async def test_skips_generation_when_scenes_provided(self):
        mock_remotion = _mock_remotion_provider()
        mock_gen = _mock_script_generator()
        renderer = VideoRenderer(remotion_provider=mock_remotion, script_generator=mock_gen)

        content_props = {
            "scenes": _make_scenes(2),
        }

        with patch("src.renderers.video_renderer.asyncio.sleep", new_callable=AsyncMock):
            result = await renderer.render_pipeline(
                content_props=content_props,
                spec=_make_spec(),
                brand_context=_make_brand_context(),
                claude_client=_mock_claude_client(),
            )

        mock_gen.generate.assert_not_called()
        mock_remotion.execute.assert_called_once()
        assert result.metadata["script_generated_by_claude"] is False

    async def test_extracts_cta_from_script(self):
        mock_remotion = _mock_remotion_provider()
        mock_gen = _mock_script_generator()
        renderer = VideoRenderer(remotion_provider=mock_remotion, script_generator=mock_gen)

        content_props = {"topic": "Product demo"}

        with patch("src.renderers.video_renderer.asyncio.sleep", new_callable=AsyncMock):
            result = await renderer.render_pipeline(
                content_props=content_props,
                spec=_make_spec(),
                brand_context=_make_brand_context(),
                claude_client=_mock_claude_client(),
            )

        # The CTA text_overlay from the script should be used
        call_args = mock_remotion.execute.call_args
        input_props = call_args.args[0]["input_props"]
        assert input_props["cta_text"] == "Start Free Trial"

    async def test_raises_when_no_scenes_after_generation(self):
        mock_remotion = _mock_remotion_provider()
        mock_gen = AsyncMock(spec=VideoScriptGenerator)
        mock_gen.generate = AsyncMock(return_value=GeneratedContent(
            content={"hook": None, "body": []},
        ))
        renderer = VideoRenderer(remotion_provider=mock_remotion, script_generator=mock_gen)

        with pytest.raises(ValidationError, match="No scenes available"):
            await renderer.render_pipeline(
                content_props={"topic": "Empty script"},
                spec=_make_spec(),
                brand_context=_make_brand_context(),
                claude_client=_mock_claude_client(),
            )


# ---------------------------------------------------------------------------
# Tests: render_pipeline() — polling
# ---------------------------------------------------------------------------

class TestVideoRendererPolling:
    async def test_polls_until_done(self):
        mock_remotion = _mock_remotion_provider()
        # Simulate 2 in-progress polls then done
        mock_remotion.get_render_progress = AsyncMock(side_effect=[
            {"done": False, "overallProgress": 0.3, "outputFile": None, "fatalErrorEncountered": False, "errors": []},
            {"done": False, "overallProgress": 0.7, "outputFile": None, "fatalErrorEncountered": False, "errors": []},
            {"done": True, "overallProgress": 1.0, "outputFile": FAKE_OUTPUT_FILE, "fatalErrorEncountered": False, "errors": []},
        ])
        renderer = VideoRenderer(remotion_provider=mock_remotion)

        content_props = {"scenes": _make_scenes(2)}

        with patch("src.renderers.video_renderer.asyncio.sleep", new_callable=AsyncMock):
            result = await renderer.render_pipeline(
                content_props=content_props,
                spec=_make_spec(),
                brand_context=_make_brand_context(),
                claude_client=_mock_claude_client(),
            )

        assert mock_remotion.get_render_progress.call_count == 3
        assert result.metadata["s3_output_file"] == FAKE_OUTPUT_FILE

    async def test_raises_on_fatal_error(self):
        mock_remotion = _mock_remotion_provider()
        mock_remotion.get_render_progress = AsyncMock(return_value={
            "done": False,
            "overallProgress": 0.2,
            "outputFile": None,
            "fatalErrorEncountered": True,
            "errors": [{"message": "Composition rendering failed"}],
        })
        renderer = VideoRenderer(remotion_provider=mock_remotion)

        content_props = {"scenes": _make_scenes(2)}

        with patch("src.renderers.video_renderer.asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(RuntimeError, match="Composition rendering failed"):
                await renderer.render_pipeline(
                    content_props=content_props,
                    spec=_make_spec(),
                    brand_context=_make_brand_context(),
                    claude_client=_mock_claude_client(),
                )

    async def test_raises_on_timeout(self):
        mock_remotion = _mock_remotion_provider()
        mock_remotion.get_render_progress = AsyncMock(return_value={
            "done": False,
            "overallProgress": 0.5,
            "outputFile": None,
            "fatalErrorEncountered": False,
            "errors": [],
        })
        renderer = VideoRenderer(remotion_provider=mock_remotion)

        content_props = {"scenes": _make_scenes(1, duration=1)}

        with patch("src.renderers.video_renderer.asyncio.sleep", new_callable=AsyncMock), \
             patch("src.renderers.video_renderer.DEFAULT_TIMEOUT_SECONDS", 6), \
             patch("src.renderers.video_renderer.POLL_INTERVAL_SECONDS", 3):
            with pytest.raises(TimeoutError, match="timed out"):
                await renderer.render_pipeline(
                    content_props=content_props,
                    spec=_make_spec(),
                    brand_context=_make_brand_context(),
                    claude_client=_mock_claude_client(),
                )

    async def test_uses_long_timeout_for_long_videos(self):
        mock_remotion = _mock_remotion_provider()
        # Track timeout used in _poll_render_progress
        original_poll = VideoRenderer._poll_render_progress
        captured_timeout = []

        async def capture_poll(self, **kwargs):
            captured_timeout.append(kwargs.get("timeout"))
            return FAKE_OUTPUT_FILE

        renderer = VideoRenderer(remotion_provider=mock_remotion)
        content_props = {"scenes": _make_scenes(15, duration=5)}  # 75s total > 60s

        with patch.object(VideoRenderer, "_poll_render_progress", capture_poll):
            await renderer.render_pipeline(
                content_props=content_props,
                spec=_make_spec(),
                brand_context=_make_brand_context(),
                claude_client=_mock_claude_client(),
            )

        assert captured_timeout[0] == LONG_VIDEO_TIMEOUT_SECONDS


# ---------------------------------------------------------------------------
# Tests: render_pipeline() — job progress updates
# ---------------------------------------------------------------------------

class TestVideoRendererJobProgress:
    async def test_updates_job_progress(self):
        mock_remotion = _mock_remotion_provider()
        mock_jobs = _mock_job_service()
        renderer = VideoRenderer(remotion_provider=mock_remotion)

        content_props = {"scenes": _make_scenes(2)}

        with patch("src.renderers.video_renderer.asyncio.sleep", new_callable=AsyncMock):
            await renderer.render_pipeline(
                content_props=content_props,
                spec=_make_spec(),
                brand_context=_make_brand_context(),
                claude_client=_mock_claude_client(),
                job_service=mock_jobs,
                job_id="job-123",
            )

        assert mock_jobs.update_status.call_count >= 3
        mock_jobs.complete_job.assert_called_once()

    async def test_job_progress_increases_monotonically(self):
        mock_remotion = _mock_remotion_provider()
        mock_jobs = _mock_job_service()
        renderer = VideoRenderer(remotion_provider=mock_remotion)

        content_props = {"scenes": _make_scenes(2)}

        with patch("src.renderers.video_renderer.asyncio.sleep", new_callable=AsyncMock):
            await renderer.render_pipeline(
                content_props=content_props,
                spec=_make_spec(),
                brand_context=_make_brand_context(),
                claude_client=_mock_claude_client(),
                job_service=mock_jobs,
                job_id="job-123",
            )

        progress_values = [
            call.kwargs.get("progress") or (call.args[2] if len(call.args) > 2 else None)
            for call in mock_jobs.update_status.call_args_list
        ]
        progress_values = [p for p in progress_values if p is not None]
        assert progress_values == sorted(progress_values)

    async def test_skips_job_updates_when_no_job_service(self):
        mock_remotion = _mock_remotion_provider()
        renderer = VideoRenderer(remotion_provider=mock_remotion)

        content_props = {"scenes": _make_scenes(2)}

        with patch("src.renderers.video_renderer.asyncio.sleep", new_callable=AsyncMock):
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

class TestVideoRendererStorage:
    async def test_uploads_to_supabase_storage(self):
        mock_remotion = _mock_remotion_provider()
        mock_storage = _mock_storage_service()
        renderer = VideoRenderer(remotion_provider=mock_remotion)

        content_props = {"scenes": _make_scenes(2)}

        with patch("src.renderers.video_renderer.asyncio.sleep", new_callable=AsyncMock):
            result = await renderer.render_pipeline(
                content_props=content_props,
                spec=_make_spec(),
                brand_context=_make_brand_context(),
                claude_client=_mock_claude_client(),
                storage_service=mock_storage,
                organization_id="org-123",
            )

        mock_storage.download_from_url.assert_called_once_with(FAKE_OUTPUT_FILE)
        mock_storage.upload_artifact.assert_called_once()
        call_kwargs = mock_storage.upload_artifact.call_args.kwargs
        assert call_kwargs["org_id"] == "org-123"
        assert call_kwargs["artifact_type"] == "video"
        assert call_kwargs["content_type"] == "video/mp4"
        assert call_kwargs["ext"] == "mp4"
        assert call_kwargs["data"] == FAKE_VIDEO_DATA

        assert result.metadata["content_url"] == "https://supabase.co/storage/video/test.mp4"

    async def test_skips_storage_when_no_service(self):
        mock_remotion = _mock_remotion_provider()
        renderer = VideoRenderer(remotion_provider=mock_remotion)

        content_props = {"scenes": _make_scenes(2)}

        with patch("src.renderers.video_renderer.asyncio.sleep", new_callable=AsyncMock):
            result = await renderer.render_pipeline(
                content_props=content_props,
                spec=_make_spec(),
                brand_context=_make_brand_context(),
                claude_client=_mock_claude_client(),
            )

        assert result.metadata["content_url"] is None
        assert isinstance(result, RenderedArtifact)


# ---------------------------------------------------------------------------
# Tests: render_pipeline() — metadata
# ---------------------------------------------------------------------------

class TestVideoRendererPipelineMetadata:
    async def test_metadata_includes_scene_count(self):
        mock_remotion = _mock_remotion_provider()
        renderer = VideoRenderer(remotion_provider=mock_remotion)

        scenes = _make_scenes(4)
        content_props = {"scenes": scenes}

        with patch("src.renderers.video_renderer.asyncio.sleep", new_callable=AsyncMock):
            result = await renderer.render_pipeline(
                content_props=content_props,
                spec=_make_spec(),
                brand_context=_make_brand_context(),
                claude_client=_mock_claude_client(),
            )

        assert result.metadata["scene_count"] == 4
        assert result.metadata["total_duration_seconds"] == 20

    async def test_metadata_includes_artifact_id(self):
        mock_remotion = _mock_remotion_provider()
        renderer = VideoRenderer(remotion_provider=mock_remotion)

        content_props = {"scenes": _make_scenes(1)}

        with patch("src.renderers.video_renderer.asyncio.sleep", new_callable=AsyncMock):
            result = await renderer.render_pipeline(
                content_props=content_props,
                spec=_make_spec(),
                brand_context=_make_brand_context(),
                claude_client=_mock_claude_client(),
            )

        assert "artifact_id" in result.metadata
        assert len(result.metadata["artifact_id"]) == 32

    async def test_metadata_includes_composition_and_render_id(self):
        mock_remotion = _mock_remotion_provider()
        renderer = VideoRenderer(remotion_provider=mock_remotion)

        content_props = {"scenes": _make_scenes(1)}

        with patch("src.renderers.video_renderer.asyncio.sleep", new_callable=AsyncMock):
            result = await renderer.render_pipeline(
                content_props=content_props,
                spec=_make_spec(),
                brand_context=_make_brand_context(),
                claude_client=_mock_claude_client(),
            )

        assert result.metadata["composition_id"] is not None
        assert result.metadata["render_id"] == FAKE_RENDER_ID

    async def test_filename_format(self):
        mock_remotion = _mock_remotion_provider()
        renderer = VideoRenderer(remotion_provider=mock_remotion)

        content_props = {"scenes": _make_scenes(1)}

        with patch("src.renderers.video_renderer.asyncio.sleep", new_callable=AsyncMock):
            result = await renderer.render_pipeline(
                content_props=content_props,
                spec=_make_spec(),
                brand_context=_make_brand_context(),
                claude_client=_mock_claude_client(),
            )

        assert result.filename.startswith("meta_1x1_")
        assert result.filename.endswith(".mp4")


# ---------------------------------------------------------------------------
# Tests: Constructor defaults
# ---------------------------------------------------------------------------

class TestVideoRendererConstructor:
    def test_uses_provided_dependencies(self):
        mock_remotion = _mock_remotion_provider()
        mock_gen = _mock_script_generator()
        renderer = VideoRenderer(remotion_provider=mock_remotion, script_generator=mock_gen)
        assert renderer._remotion is mock_remotion
        assert renderer._script_generator is mock_gen

    def test_creates_defaults_when_none_provided(self):
        with patch("src.renderers.video_renderer.RemotionProvider"), \
             patch("src.renderers.video_renderer.VideoScriptGenerator"):
            renderer = VideoRenderer()
            assert renderer._remotion is not None
            assert renderer._script_generator is not None
