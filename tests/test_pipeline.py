"""Integration tests for the pipeline orchestrator and registry.

Tests the wiring: registry resolution → generator → renderer → storage → DB insert.
Uses mocks for external services (Claude, Supabase, DB) but verifies the full
internal call chain works end-to-end.
"""

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.brand.models import BrandContext
from src.generators.base import GeneratedContent
from src.integrations.claude_client import GenerationResult, TokenUsage
from src.pipeline.registry import (
    GENERATOR_REGISTRY,
    RENDERER_REGISTRY,
    resolve_generator,
    resolve_renderer,
)
from src.pipeline.orchestrator import run_sync_pipeline, run_async_pipeline, execute_async_job
from src.renderers.base import RenderedArtifact
from src.specs.models import FormatSpec, Pipeline


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_spec(artifact_type="structured_text", surface="linkedin", **overrides) -> FormatSpec:
    defaults = {
        "spec_id": f"{artifact_type}__{surface}",
        "artifact_type": artifact_type,
        "surface": surface,
        "version": "1.0",
        "pipeline": Pipeline(
            generator="test",
            claude_model="claude-sonnet-4-20250514",
            claude_temperature=0.7,
        ),
    }
    defaults.update(overrides)
    return FormatSpec(**defaults)


def _make_brand_context(**overrides) -> BrandContext:
    defaults = {
        "company_name": "TestCo",
        "brand_voice": "Direct and clear.",
        "value_proposition": "Save time.",
    }
    defaults.update(overrides)
    return BrandContext(**defaults)


def _mock_claude_result(content: dict) -> GenerationResult:
    return GenerationResult(
        content=content,
        model="claude-sonnet-4-20250514",
        usage=TokenUsage(
            input_tokens=100,
            output_tokens=200,
            cache_creation_input_tokens=0,
            cache_read_input_tokens=0,
        ),
    )


# ---------------------------------------------------------------------------
# Registry tests
# ---------------------------------------------------------------------------

class TestPipelineRegistry:
    def test_all_generator_entries_are_importable(self):
        """Every class in GENERATOR_REGISTRY should be instantiable."""
        for key, cls in GENERATOR_REGISTRY.items():
            instance = cls()
            assert hasattr(instance, "generate"), f"{cls.__name__} missing generate()"

    def test_all_renderer_entries_are_importable(self):
        """Every non-None class in RENDERER_REGISTRY should be instantiable."""
        for key, cls in RENDERER_REGISTRY.items():
            if cls is not None:
                instance = cls()
                assert hasattr(instance, "render"), f"{cls.__name__} missing render()"

    def test_every_generator_has_renderer(self):
        """Every (artifact_type, surface) in GENERATOR_REGISTRY has a RENDERER_REGISTRY entry."""
        for key in GENERATOR_REGISTRY:
            assert key in RENDERER_REGISTRY, f"No renderer entry for {key}"

    def test_resolve_generator_with_subtype_override(self):
        from src.generators.video_script import VideoScriptGenerator
        cls = resolve_generator("structured_text", "generic", "video_script")
        assert cls is VideoScriptGenerator

    def test_resolve_generator_fallback_without_subtype(self):
        from src.generators.image_brief import ImageBriefGenerator
        cls = resolve_generator("structured_text", "generic")
        assert cls is ImageBriefGenerator

    def test_resolve_generator_unknown_raises(self):
        with pytest.raises(ValueError, match="No generator registered"):
            resolve_generator("nonexistent", "nowhere")

    def test_resolve_renderer_returns_none_for_json_only(self):
        assert resolve_renderer("structured_text", "linkedin") is None

    def test_resolve_renderer_returns_class_for_pdf(self):
        from src.renderers.pdf_renderer import PDFRenderer
        assert resolve_renderer("pdf", "generic") is PDFRenderer


# ---------------------------------------------------------------------------
# Sync pipeline integration tests
# ---------------------------------------------------------------------------

class TestSyncPipeline:
    @pytest.mark.asyncio
    @patch("src.pipeline.orchestrator.get_pool")
    @patch("src.pipeline.orchestrator.ClaudeClient")
    async def test_json_only_pipeline(self, MockClaude, mock_get_pool):
        """structured_text artifacts skip rendering and return JSON."""
        # Mock Claude
        mock_client = AsyncMock()
        mock_client.generate.return_value = _mock_claude_result({
            "variants": [
                {"introductory_text": "Test", "headline": "H1", "description": "D1"},
                {"introductory_text": "Test2", "headline": "H2", "description": "D2"},
                {"introductory_text": "Test3", "headline": "H3", "description": "D3"},
            ]
        })
        MockClaude.return_value = mock_client

        # Mock DB
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock()
        mock_pool = MagicMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_get_pool.return_value = mock_pool

        spec = _make_spec("structured_text", "linkedin")
        result = await run_sync_pipeline(
            spec=spec,
            content_props={"topic": "test"},
            brand_context=_make_brand_context(),
            org_id="org-1",
        )

        assert result["status"] == "completed"
        assert result["content"] is not None
        assert result["content_url"] is None
        assert "artifact_id" in result
        # DB insert was called
        mock_conn.execute.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.pipeline.orchestrator.StorageService")
    @patch("src.pipeline.orchestrator.SupabaseClient")
    @patch("src.pipeline.orchestrator.get_pool")
    @patch("src.pipeline.orchestrator.ClaudeClient")
    async def test_rendered_pipeline_uploads_to_storage(
        self, MockClaude, mock_get_pool, MockSupabase, MockStorage
    ):
        """PDF artifacts go through render + upload."""
        # Mock Claude
        mock_client = AsyncMock()
        mock_client.generate.return_value = _mock_claude_result({
            "title": "Test Guide",
            "executive_summary": "Summary",
            "sections": [{"heading": "Intro", "body": "Body text"}],
            "key_takeaways": ["Takeaway 1"],
        })
        MockClaude.return_value = mock_client

        # Mock storage
        mock_storage_instance = AsyncMock()
        mock_storage_instance.upload_artifact.return_value = "https://storage.example.com/test.pdf"
        MockStorage.return_value = mock_storage_instance

        # Mock DB
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock()
        mock_pool = MagicMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_get_pool.return_value = mock_pool

        spec = _make_spec("pdf", "generic")

        # Mock the renderer to avoid ReportLab dependency issues in test
        with patch("src.pipeline.orchestrator.resolve_renderer") as mock_resolve_renderer:
            mock_renderer_cls = MagicMock()
            mock_renderer = AsyncMock()
            mock_renderer.render.return_value = RenderedArtifact(
                data=b"%PDF-fake", content_type="application/pdf", filename="test.pdf"
            )
            mock_renderer_cls.return_value = mock_renderer
            mock_resolve_renderer.return_value = mock_renderer_cls

            result = await run_sync_pipeline(
                spec=spec,
                content_props={"topic": "test"},
                brand_context=_make_brand_context(),
                org_id="org-1",
            )

        assert result["status"] == "completed"
        assert result["content_url"] == "https://storage.example.com/test.pdf"
        mock_storage_instance.upload_artifact.assert_called_once()


# ---------------------------------------------------------------------------
# Async pipeline integration tests
# ---------------------------------------------------------------------------

class TestSourceUrlPreprocessing:
    @pytest.mark.asyncio
    async def test_source_content_takes_precedence_over_source_url(self):
        """When both source_content and source_url are provided, source_content wins."""
        from src.pipeline.orchestrator import _preprocess_source_url
        props = {
            "source_content": "Already provided",
            "source_url": "https://youtu.be/dQw4w9WgXcQ",
        }
        result = await _preprocess_source_url(props)
        assert result["source_content"] == "Already provided"

    @pytest.mark.asyncio
    async def test_no_source_url_returns_props_unchanged(self):
        from src.pipeline.orchestrator import _preprocess_source_url
        props = {"format": "checklist", "topic": "Test"}
        result = await _preprocess_source_url(props)
        assert result == props

    @pytest.mark.asyncio
    async def test_source_url_extracts_transcript(self):
        from src.pipeline.orchestrator import _preprocess_source_url
        with patch("src.extractors.youtube.extract_transcript", new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = "Extracted transcript text"
            props = {
                "format": "checklist",
                "topic": "Test",
                "source_url": "https://youtu.be/dQw4w9WgXcQ",
            }
            result = await _preprocess_source_url(props)
        mock_extract.assert_called_once_with("https://youtu.be/dQw4w9WgXcQ")
        assert result["source_content"] == "Extracted transcript text"
        assert result["source_url"] == "https://youtu.be/dQw4w9WgXcQ"  # preserved

    @pytest.mark.asyncio
    async def test_source_url_does_not_mutate_original(self):
        from src.pipeline.orchestrator import _preprocess_source_url
        with patch("src.extractors.youtube.extract_transcript", new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = "Transcript"
            original = {"source_url": "https://youtu.be/dQw4w9WgXcQ"}
            result = await _preprocess_source_url(original)
        assert "source_content" not in original
        assert "source_content" in result


class TestAsyncPipeline:
    @pytest.mark.asyncio
    @patch("src.pipeline.orchestrator.get_pool")
    @patch("src.pipeline.orchestrator.JobService")
    async def test_creates_job_and_returns_poll_url(self, MockJobService, mock_get_pool):
        mock_job = MagicMock()
        mock_job.id = "job-123"
        mock_service = AsyncMock()
        mock_service.create_job.return_value = mock_job
        MockJobService.return_value = mock_service
        mock_get_pool.return_value = MagicMock()

        spec = _make_spec("video", "generic")
        result = await run_async_pipeline(
            spec=spec,
            content_props={"concept": "test"},
            brand_context=_make_brand_context(),
            org_id="org-1",
            webhook_url="https://example.com/hook",
        )

        assert result["job_id"] == "job-123"
        assert result["status"] == "queued"
        assert result["poll_url"] == "/jobs/job-123"
        assert result["webhook_url"] == "https://example.com/hook"
        mock_service.create_job.assert_called_once()


# ---------------------------------------------------------------------------
# Shared text utility tests
# ---------------------------------------------------------------------------

class TestTruncateAtWordBoundary:
    def test_short_text_unchanged(self):
        from src.shared.text import truncate_at_word_boundary
        assert truncate_at_word_boundary("hello", 10) == "hello"

    def test_exact_length_unchanged(self):
        from src.shared.text import truncate_at_word_boundary
        assert truncate_at_word_boundary("hello", 5) == "hello"

    def test_truncates_at_word_boundary(self):
        from src.shared.text import truncate_at_word_boundary
        result = truncate_at_word_boundary("hello world foo", 12)
        assert result == "hello world"
        assert len(result) <= 12

    def test_single_long_word_truncated_at_limit(self):
        from src.shared.text import truncate_at_word_boundary
        result = truncate_at_word_boundary("superlongword", 5)
        assert result == "super"

    def test_empty_string(self):
        from src.shared.text import truncate_at_word_boundary
        assert truncate_at_word_boundary("", 10) == ""

    def test_truncates_before_last_space(self):
        from src.shared.text import truncate_at_word_boundary
        result = truncate_at_word_boundary("one two three four five", 15)
        # "one two three f" -> last space at 13 -> "one two three"
        assert result == "one two three"
        assert len(result) <= 15
