"""Tests for all generators (CEX-15 through CEX-23)."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.brand.models import BrandContext, BrandGuidelines, ICPDefinition, CaseStudy, Testimonial
from src.generators.base import BaseGenerator, GeneratedContent, GeneratorProtocol
from src.integrations.claude_client import ClaudeClient, GenerationResult, TokenUsage, MODEL_FAST, MODEL_QUALITY
from src.specs.models import FormatSpec, Pipeline


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

def _brand_context(**overrides) -> BrandContext:
    defaults = {
        "organization_id": "org-123",
        "company_name": "Acme Analytics",
        "brand_voice": "Direct, data-driven, confident.",
        "value_proposition": "Cut reporting time by 80%.",
        "brand_guidelines": BrandGuidelines(
            primary_color="#1A73E8",
            secondary_color="#0D47A1",
            accent_color="#FF6D00",
        ),
        "icp_definition": ICPDefinition(
            title="VP of Sales", industry="SaaS",
            pain_points=["Manual reporting"], goals=["Automate forecasting"],
        ),
        "target_persona": "VP of Sales at mid-market SaaS",
        "case_studies": [
            CaseStudy(title="BigCo Success", company="BigCo", result="3x ROI"),
        ],
        "testimonials": [
            Testimonial(quote="Saved us 40 hours/month", author="Jane Doe", role="CRO", company="BigCo"),
        ],
        "customer_logos": ["logo1.png"],
        "competitor_differentiators": ["Real-time sync"],
        "angle": "AI-powered forecasting",
        "objective": "lead_gen",
        "industry": "SaaS",
    }
    defaults.update(overrides)
    return BrandContext(**defaults)


def _spec(surface="linkedin", **overrides) -> FormatSpec:
    defaults = {
        "spec_id": f"structured_text__{surface}",
        "artifact_type": "structured_text",
        "surface": surface,
        "version": "1.0",
        "pipeline": Pipeline(
            generator="generators.ad_copy.AdCopyGenerator",
            claude_model="claude-sonnet-4-20250514",
            claude_temperature=0.7,
            claude_max_tokens=1024,
        ),
    }
    defaults.update(overrides)
    return FormatSpec(**defaults)


def _gen_result(content=None, **overrides) -> GenerationResult:
    return GenerationResult(
        content=content or {"placeholder": True},
        tool_results=[{"id": "t1", "name": "gen", "input": content or {"placeholder": True}}],
        usage=TokenUsage(input_tokens=100, output_tokens=50),
        model="claude-sonnet-4-20250514",
        stop_reason="end_turn",
        **overrides,
    )


def _mock_client(content=None) -> ClaudeClient:
    client = MagicMock(spec=ClaudeClient)
    client.generate = AsyncMock(return_value=_gen_result(content))
    return client


# ============================================================================
# CEX-15: Ad Copy Generator
# ============================================================================

class TestAdCopyGenerator:
    def test_satisfies_protocol(self):
        from src.generators.ad_copy import AdCopyGenerator
        assert isinstance(AdCopyGenerator(), GeneratorProtocol)

    def test_linkedin_instructions(self):
        from src.generators.ad_copy import AdCopyGenerator
        gen = AdCopyGenerator()
        ctx = _brand_context()
        spec = _spec(surface="linkedin")
        instructions = gen.build_asset_specific_instructions(
            {"platform": "linkedin", "topic": "AI forecasting"}, ctx, spec
        )
        assert "LINKEDIN" in instructions
        assert "3 ad copy variants" in instructions
        assert "AI forecasting" in instructions

    def test_meta_instructions(self):
        from src.generators.ad_copy import AdCopyGenerator
        gen = AdCopyGenerator()
        ctx = _brand_context()
        spec = _spec(surface="meta")
        instructions = gen.build_asset_specific_instructions(
            {"platform": "meta"}, ctx, spec
        )
        assert "META" in instructions
        assert "125 characters" in instructions

    def test_google_instructions(self):
        from src.generators.ad_copy import AdCopyGenerator
        gen = AdCopyGenerator()
        ctx = _brand_context()
        spec = _spec(surface="google")
        instructions = gen.build_asset_specific_instructions(
            {"platform": "google"}, ctx, spec
        )
        assert "GOOGLE" in instructions
        assert "30 characters" in instructions

    def test_invalid_platform_raises(self):
        from src.generators.ad_copy import AdCopyGenerator
        gen = AdCopyGenerator()
        ctx = _brand_context()
        spec = _spec()
        with pytest.raises(ValueError, match="Unknown ad platform"):
            gen.build_asset_specific_instructions({"platform": "tiktok"}, ctx, spec)

    async def test_generate_linkedin(self):
        from src.generators.ad_copy import AdCopyGenerator
        gen = AdCopyGenerator()
        content = {"variants": [
            {"introductory_text": "Test", "headline": "Test", "description": "Test"}
            for _ in range(3)
        ]}
        client = _mock_client(content)
        result = await gen.generate(
            {"platform": "linkedin"}, _brand_context(), _spec(surface="linkedin"), client
        )
        assert isinstance(result, GeneratedContent)
        assert result.content["variants"] is not None

    async def test_generate_google(self):
        from src.generators.ad_copy import AdCopyGenerator
        gen = AdCopyGenerator()
        content = {
            "headlines": ["H" * 25] * 10,
            "descriptions": ["D" * 80] * 4,
            "path1": "test",
            "path2": "demo",
        }
        client = _mock_client(content)
        result = await gen.generate(
            {"platform": "google"}, _brand_context(), _spec(surface="google"), client
        )
        assert isinstance(result, GeneratedContent)


class TestAdCopyValidation:
    def test_truncate_at_word_boundary(self):
        from src.generators.ad_copy import _truncate_at_word_boundary
        assert _truncate_at_word_boundary("hello world", 20) == "hello world"
        assert _truncate_at_word_boundary("hello world foo", 12) == "hello world"
        assert _truncate_at_word_boundary("short", 3) == "sho"  # no space found

    def test_validate_linkedin_limits(self):
        from src.generators.ad_copy import validate_ad_copy_limits
        content = {"variants": [
            {"introductory_text": "A" * 700, "headline": "B" * 250, "description": "C" * 150},
        ]}
        spec = _spec(surface="linkedin")
        fixed, warnings = validate_ad_copy_limits("linkedin", content, spec)
        assert len(warnings) == 3  # all 3 fields over limit

    def test_validate_google_limits(self):
        from src.generators.ad_copy import validate_ad_copy_limits
        content = {
            "headlines": ["H" * 40, "Short"],
            "descriptions": ["D" * 100],
            "path1": "a" * 20,
            "path2": "ok",
        }
        spec = _spec(surface="google")
        fixed, warnings = validate_ad_copy_limits("google", content, spec)
        assert len(warnings) >= 2  # headline + description + path1

    def test_validate_meta_limits(self):
        from src.generators.ad_copy import validate_ad_copy_limits
        content = {"variants": [
            {"primary_text": "A" * 200, "headline": "B" * 50, "description": "C" * 40},
        ]}
        spec = _spec(surface="meta")
        fixed, warnings = validate_ad_copy_limits("meta", content, spec)
        assert len(warnings) == 3


# ============================================================================
# CEX-16: Lead Magnet Generator
# ============================================================================

class TestLeadMagnetGenerator:
    def test_satisfies_protocol(self):
        from src.generators.lead_magnet import LeadMagnetGenerator
        assert isinstance(LeadMagnetGenerator(), GeneratorProtocol)

    def test_checklist_instructions(self):
        from src.generators.lead_magnet import LeadMagnetGenerator
        gen = LeadMagnetGenerator()
        instructions = gen.build_asset_specific_instructions(
            {"format": "checklist", "topic": "Security"}, _brand_context(),
            _spec(spec_id="pdf__generic", artifact_type="pdf", surface="generic")
        )
        assert "CHECKLIST" in instructions
        assert "Security" in instructions

    def test_ultimate_guide_instructions(self):
        from src.generators.lead_magnet import LeadMagnetGenerator
        gen = LeadMagnetGenerator()
        instructions = gen.build_asset_specific_instructions(
            {"format": "ultimate_guide"}, _brand_context(),
            _spec(spec_id="pdf__generic", artifact_type="pdf", surface="generic")
        )
        assert "ULTIMATE GUIDE" in instructions

    def test_all_five_formats(self):
        from src.generators.lead_magnet import LeadMagnetGenerator, VALID_FORMATS
        gen = LeadMagnetGenerator()
        ctx = _brand_context()
        spec = _spec(spec_id="pdf__generic", artifact_type="pdf", surface="generic")
        for fmt in VALID_FORMATS:
            instructions = gen.build_asset_specific_instructions(
                {"format": fmt}, ctx, spec
            )
            assert instructions  # non-empty

    def test_invalid_format_raises(self):
        from src.generators.lead_magnet import LeadMagnetGenerator
        gen = LeadMagnetGenerator()
        with pytest.raises(ValueError, match="Unknown lead magnet format"):
            gen.build_asset_specific_instructions(
                {"format": "nonexistent"}, _brand_context(), _spec()
            )

    def test_industry_guidance_injected(self):
        from src.generators.lead_magnet import LeadMagnetGenerator
        gen = LeadMagnetGenerator()
        instructions = gen.build_asset_specific_instructions(
            {"format": "checklist", "industry": "SaaS"}, _brand_context(),
            _spec(spec_id="pdf__generic", artifact_type="pdf", surface="generic")
        )
        assert "SaaS" in instructions

    def test_format_selection(self):
        from src.generators.lead_magnet import select_lead_magnet_format
        assert select_lead_magnet_format("compliance audit", "lead_gen", "") == "checklist"
        assert select_lead_magnet_format("comprehensive guide", "education", "") == "ultimate_guide"
        assert select_lead_magnet_format("benchmark data", "analytics", "") == "benchmark_report"

    async def test_generate_single_pass(self):
        from src.generators.lead_magnet import LeadMagnetGenerator
        gen = LeadMagnetGenerator()
        content = {
            "title": "Test Guide",
            "subtitle": "Subtitle",
            "sections": [{"heading": "Intro", "body": "Content", "bullets": [], "callout_box": None}],
        }
        client = _mock_client(content)
        spec = _spec(spec_id="pdf__generic", artifact_type="pdf", surface="generic")
        result = await gen.generate({"format": "checklist"}, _brand_context(), spec, client)
        assert isinstance(result, GeneratedContent)
        client.generate.assert_called_once()

    async def test_generate_two_pass(self):
        from src.generators.lead_magnet import LeadMagnetGenerator
        gen = LeadMagnetGenerator()
        content = {
            "title": "Ultimate Guide",
            "subtitle": "Subtitle",
            "sections": [{"heading": "Ch1", "body": "Content", "bullets": [], "callout_box": None}],
        }
        client = _mock_client(content)
        spec = _spec(spec_id="pdf__generic", artifact_type="pdf", surface="generic")
        result = await gen.generate({"format": "ultimate_guide"}, _brand_context(), spec, client)
        assert isinstance(result, GeneratedContent)
        assert client.generate.call_count == 2  # two passes
        assert result.metadata.get("two_pass") is True


# ============================================================================
# CEX-17: Landing Page Generator
# ============================================================================

class TestLandingPageGenerator:
    def test_satisfies_protocol(self):
        from src.generators.landing_page import LandingPageGenerator
        assert isinstance(LandingPageGenerator(), GeneratorProtocol)

    def test_all_template_types(self):
        from src.generators.landing_page import LandingPageGenerator, VALID_TEMPLATE_TYPES
        gen = LandingPageGenerator()
        ctx = _brand_context()
        spec = _spec(spec_id="html_page__web", artifact_type="html_page", surface="web")
        for tt in VALID_TEMPLATE_TYPES:
            instructions = gen.build_asset_specific_instructions(
                {"template_type": tt}, ctx, spec
            )
            assert instructions

    def test_invalid_template_raises(self):
        from src.generators.landing_page import LandingPageGenerator
        gen = LandingPageGenerator()
        with pytest.raises(ValueError, match="Unknown landing page template"):
            gen.build_asset_specific_instructions(
                {"template_type": "nonexistent"}, _brand_context(), _spec()
            )

    def test_template_selection_webinar(self):
        from src.generators.landing_page import select_landing_page_template
        ctx = _brand_context(objective="webinar registration")
        assert select_landing_page_template(ctx) == "webinar"

    def test_template_selection_demo(self):
        from src.generators.landing_page import select_landing_page_template
        ctx = _brand_context(objective="request demo")
        assert select_landing_page_template(ctx) == "demo_request"

    def test_template_selection_case_study(self):
        from src.generators.landing_page import select_landing_page_template
        ctx = _brand_context(objective="case study page")
        assert select_landing_page_template(ctx) == "case_study"

    def test_template_selection_default(self):
        from src.generators.landing_page import select_landing_page_template
        ctx = _brand_context(objective="download", angle="general")
        assert select_landing_page_template(ctx) == "lead_magnet_download"

    def test_webinar_instructions_include_speakers(self):
        from src.generators.landing_page import LandingPageGenerator
        gen = LandingPageGenerator()
        ctx = _brand_context()
        spec = _spec(spec_id="html_page__web", artifact_type="html_page", surface="web")
        instructions = gen.build_asset_specific_instructions(
            {"template_type": "webinar", "speakers": [{"name": "John"}], "event_date": "2026-04-15"},
            ctx, spec,
        )
        assert "John" in instructions
        assert "2026-04-15" in instructions

    async def test_generate_lead_magnet_page(self):
        from src.generators.landing_page import LandingPageGenerator
        gen = LandingPageGenerator()
        content = {
            "headline": "Download Guide",
            "subhead": "Learn more",
            "value_props": ["Prop 1", "Prop 2"],
            "cta_text": "Get It Now",
        }
        client = _mock_client(content)
        spec = _spec(spec_id="html_page__web", artifact_type="html_page", surface="web")
        result = await gen.generate(
            {"template_type": "lead_magnet_download"}, _brand_context(), spec, client
        )
        assert isinstance(result, GeneratedContent)

    async def test_auto_select_template(self):
        from src.generators.landing_page import LandingPageGenerator
        gen = LandingPageGenerator()
        content = {"headline": "Test", "subhead": "Sub", "value_props": ["V1"], "cta_text": "CTA"}
        client = _mock_client(content)
        spec = _spec(spec_id="html_page__web", artifact_type="html_page", surface="web")
        result = await gen.generate(
            {}, _brand_context(objective="lead_gen"), spec, client
        )
        assert isinstance(result, GeneratedContent)


# ============================================================================
# CEX-18: Document Slides Generator
# ============================================================================

class TestDocumentSlidesGenerator:
    def test_satisfies_protocol(self):
        from src.generators.document_slides import DocumentSlidesGenerator
        assert isinstance(DocumentSlidesGenerator(), GeneratorProtocol)

    def test_all_patterns(self):
        from src.generators.document_slides import DocumentSlidesGenerator, VALID_PATTERNS
        gen = DocumentSlidesGenerator()
        ctx = _brand_context()
        spec = _spec(spec_id="document_slides__linkedin", artifact_type="document_slides", surface="linkedin")
        for pattern in VALID_PATTERNS:
            instructions = gen.build_asset_specific_instructions(
                {"pattern": pattern}, ctx, spec
            )
            assert instructions

    def test_invalid_pattern_raises(self):
        from src.generators.document_slides import DocumentSlidesGenerator
        gen = DocumentSlidesGenerator()
        with pytest.raises(ValueError, match="Unknown carousel pattern"):
            gen.build_asset_specific_instructions({"pattern": "invalid"}, _brand_context(), _spec())

    def test_validate_slide_limits(self):
        from src.generators.document_slides import DocumentSlidesGenerator
        gen = DocumentSlidesGenerator()
        spec = _spec(spec_id="document_slides__linkedin", artifact_type="document_slides", surface="linkedin")
        content = {"slides": [
            {"headline": "H" * 60, "body": "B" * 130, "is_cta_slide": False},
            {"headline": "Short", "body": "OK", "is_cta_slide": False},
        ]}
        fixed, warnings = gen.validate_output(content, spec)
        assert len(fixed["slides"][0]["headline"]) == 50
        assert len(fixed["slides"][0]["body"]) == 120
        assert "truncated" in warnings[0]

    def test_validate_forces_last_slide_cta(self):
        from src.generators.document_slides import DocumentSlidesGenerator
        gen = DocumentSlidesGenerator()
        spec = _spec()
        content = {"slides": [
            {"headline": "Slide 1", "is_cta_slide": False},
            {"headline": "Slide 2", "is_cta_slide": False},
        ]}
        fixed, warnings = gen.validate_output(content, spec)
        assert fixed["slides"][-1]["is_cta_slide"] is True
        assert "CTA" in warnings[-1]

    async def test_generate(self):
        from src.generators.document_slides import DocumentSlidesGenerator
        gen = DocumentSlidesGenerator()
        content = {"slides": [
            {"headline": "H", "body": "B", "is_cta_slide": False} for _ in range(6)
        ] + [{"headline": "CTA", "is_cta_slide": True, "cta_text": "Learn More"}],
            "aspect_ratio": "1:1"
        }
        client = _mock_client(content)
        spec = _spec(spec_id="document_slides__linkedin", artifact_type="document_slides", surface="linkedin")
        result = await gen.generate({"pattern": "problem_solution"}, _brand_context(), spec, client)
        assert isinstance(result, GeneratedContent)


# ============================================================================
# CEX-19: Video Script Generator
# ============================================================================

class TestVideoScriptGenerator:
    def test_satisfies_protocol(self):
        from src.generators.video_script import VideoScriptGenerator
        assert isinstance(VideoScriptGenerator(), GeneratorProtocol)

    def test_30s_instructions(self):
        from src.generators.video_script import VideoScriptGenerator
        gen = VideoScriptGenerator()
        instructions = gen.build_asset_specific_instructions(
            {"duration": "30s", "platform": "linkedin"}, _brand_context(), _spec()
        )
        assert "30 seconds" in instructions
        assert "75 words" in instructions
        assert "LinkedIn" in instructions

    def test_60s_instructions(self):
        from src.generators.video_script import VideoScriptGenerator
        gen = VideoScriptGenerator()
        instructions = gen.build_asset_specific_instructions(
            {"duration": "60s", "platform": "youtube"}, _brand_context(), _spec()
        )
        assert "60 seconds" in instructions
        assert "150 words" in instructions
        assert "16:9" in instructions

    def test_invalid_duration_raises(self):
        from src.generators.video_script import VideoScriptGenerator
        gen = VideoScriptGenerator()
        with pytest.raises(ValueError, match="Unknown duration"):
            gen.build_asset_specific_instructions({"duration": "90s"}, _brand_context(), _spec())

    def test_invalid_platform_raises(self):
        from src.generators.video_script import VideoScriptGenerator
        gen = VideoScriptGenerator()
        with pytest.raises(ValueError, match="Unknown platform"):
            gen.build_asset_specific_instructions(
                {"duration": "30s", "platform": "tiktok"}, _brand_context(), _spec()
            )

    def test_platform_aspect_ratios(self):
        from src.generators.video_script import VideoScriptGenerator
        gen = VideoScriptGenerator()
        for platform, expected_ratio in [("linkedin", "4:5"), ("meta", "4:5"), ("youtube", "16:9")]:
            instructions = gen.build_asset_specific_instructions(
                {"duration": "30s", "platform": platform}, _brand_context(), _spec()
            )
            assert expected_ratio in instructions

    async def test_generate(self):
        from src.generators.video_script import VideoScriptGenerator
        gen = VideoScriptGenerator()
        content = {
            "title": "Test Script",
            "duration": "30s",
            "aspect_ratio": "4:5",
            "hook": {"timestamp_start": "0:00", "timestamp_end": "0:03", "spoken_text": "Hook", "visual_direction": "CU", "caption_text": "Hook"},
            "body": [],
            "cta": {"timestamp_start": "0:20", "timestamp_end": "0:30", "spoken_text": "CTA", "visual_direction": "Wide", "caption_text": "CTA"},
            "total_word_count": 75,
            "music_direction": "Upbeat",
            "target_platform": "linkedin",
        }
        client = _mock_client(content)
        result = await gen.generate(
            {"duration": "30s", "platform": "linkedin"}, _brand_context(), _spec(), client
        )
        assert isinstance(result, GeneratedContent)


# ============================================================================
# CEX-20: Image Brief Generator
# ============================================================================

class TestImageBriefGenerator:
    def test_satisfies_protocol(self):
        from src.generators.image_brief import ImageBriefGenerator
        assert isinstance(ImageBriefGenerator(), GeneratorProtocol)

    def test_all_platforms(self):
        from src.generators.image_brief import ImageBriefGenerator, VALID_PLATFORMS
        gen = ImageBriefGenerator()
        ctx = _brand_context()
        spec = _spec(spec_id="structured_text__generic", artifact_type="structured_text", surface="generic")
        for platform in VALID_PLATFORMS:
            instructions = gen.build_asset_specific_instructions(
                {"platforms": [platform]}, ctx, spec
            )
            assert instructions

    def test_invalid_platform_raises(self):
        from src.generators.image_brief import ImageBriefGenerator
        gen = ImageBriefGenerator()
        with pytest.raises(ValueError, match="Unknown image platform"):
            gen.build_asset_specific_instructions(
                {"platforms": ["invalid"]}, _brand_context(), _spec()
            )

    def test_multi_platform_instructions(self):
        from src.generators.image_brief import ImageBriefGenerator
        gen = ImageBriefGenerator()
        instructions = gen.build_asset_specific_instructions(
            {"platforms": ["linkedin_sponsored", "meta_feed"]}, _brand_context(), _spec()
        )
        assert "LinkedIn Sponsored" in instructions
        assert "Meta Feed" in instructions

    def test_brand_colors_in_instructions(self):
        from src.generators.image_brief import ImageBriefGenerator
        gen = ImageBriefGenerator()
        instructions = gen.build_asset_specific_instructions(
            {"platforms": ["linkedin_sponsored"]}, _brand_context(), _spec()
        )
        assert "#1A73E8" in instructions

    def test_validate_hex_colors(self):
        from src.generators.image_brief import ImageBriefGenerator
        gen = ImageBriefGenerator()
        content = {"briefs": [{"color_palette": ["1A73E8", "#FF0000"]}]}
        fixed, warnings = gen.validate_output(content, _spec())
        assert fixed["briefs"][0]["color_palette"][0] == "#1A73E8"
        assert fixed["briefs"][0]["color_palette"][1] == "#FF0000"

    async def test_generate(self):
        from src.generators.image_brief import ImageBriefGenerator
        gen = ImageBriefGenerator()
        content = {"briefs": [
            {"concept_name": "Hero", "intended_use": "landing_page_hero",
             "dimensions": "1920x1080", "visual_description": "Wide shot",
             "color_palette": ["#1A73E8"], "mood": "confident",
             "style_reference": "Apple", "do_not_include": ["handshakes"]},
        ]}
        client = _mock_client(content)
        spec = _spec(spec_id="structured_text__generic", artifact_type="structured_text", surface="generic")
        result = await gen.generate(
            {"platforms": ["landing_page_hero"]}, _brand_context(), spec, client
        )
        assert isinstance(result, GeneratedContent)


# ============================================================================
# CEX-21: Case Study Generator
# ============================================================================

class TestCaseStudyGenerator:
    def test_satisfies_protocol(self):
        from src.generators.case_study import CaseStudyGenerator
        assert isinstance(CaseStudyGenerator(), GeneratorProtocol)

    def test_instructions_with_case_study_data(self):
        from src.generators.case_study import CaseStudyGenerator
        gen = CaseStudyGenerator()
        instructions = gen.build_asset_specific_instructions(
            {"case_study_data": {
                "customer_name": "BigCo",
                "problem": "Slow reporting",
                "solution": "Automated dashboards",
                "results": {"roi": "3x", "time_saved": "40%"},
            }},
            _brand_context(),
            _spec(spec_id="html_page__web", artifact_type="html_page", surface="web"),
        )
        assert "BigCo" in instructions
        assert "Slow reporting" in instructions
        assert "3x" in instructions

    def test_instructions_without_data(self):
        from src.generators.case_study import CaseStudyGenerator
        gen = CaseStudyGenerator()
        instructions = gen.build_asset_specific_instructions(
            {}, _brand_context(case_studies=[]), _spec()
        )
        assert "placeholder" in instructions.lower()

    def test_instructions_from_brand_context(self):
        from src.generators.case_study import CaseStudyGenerator
        gen = CaseStudyGenerator()
        instructions = gen.build_asset_specific_instructions(
            {}, _brand_context(), _spec()
        )
        assert "4 sections" in instructions

    def test_uses_opus_model(self):
        from src.generators.case_study import CaseStudyGenerator
        gen = CaseStudyGenerator()
        assert gen.default_model == MODEL_QUALITY

    async def test_generate(self):
        from src.generators.case_study import CaseStudyGenerator
        gen = CaseStudyGenerator()
        content = {
            "headline": "How BigCo Cut Audit Time by 40%",
            "sections": [
                {"heading": "Situation", "body": "BigCo is...", "bullets": None},
                {"heading": "Challenge", "body": "They faced...", "bullets": None},
                {"heading": "Solution", "body": "Using Acme...", "bullets": None},
                {"heading": "Results", "body": "After 90 days...", "bullets": None},
            ],
            "metrics": [{"value": "3x", "label": "ROI"}, {"value": "40%", "label": "time saved"}],
            "quote_text": "Great product",
            "quote_author": "Jane Doe",
            "quote_title": "CRO",
            "cta_text": "Get Similar Results",
        }
        client = _mock_client(content)
        spec = _spec(spec_id="html_page__web", artifact_type="html_page", surface="web")
        result = await gen.generate({}, _brand_context(), spec, client)
        assert isinstance(result, GeneratedContent)


# ============================================================================
# CEX-22: Audio Script Generator
# ============================================================================

class TestAudioScriptGenerator:
    def test_satisfies_protocol(self):
        from src.generators.audio_script import AudioScriptGenerator
        assert isinstance(AudioScriptGenerator(), GeneratorProtocol)

    def test_15s_instructions(self):
        from src.generators.audio_script import AudioScriptGenerator
        gen = AudioScriptGenerator()
        instructions = gen.build_asset_specific_instructions(
            {"duration_seconds": 15}, _brand_context(),
            _spec(spec_id="audio__voice_channel", artifact_type="audio", surface="voice_channel"),
        )
        assert "15-second" in instructions
        assert "38 words" in instructions

    def test_30s_instructions(self):
        from src.generators.audio_script import AudioScriptGenerator
        gen = AudioScriptGenerator()
        instructions = gen.build_asset_specific_instructions(
            {"duration_seconds": 30}, _brand_context(),
            _spec(spec_id="audio__voice_channel", artifact_type="audio", surface="voice_channel"),
        )
        assert "30-second" in instructions
        assert "75 words" in instructions

    def test_60s_instructions(self):
        from src.generators.audio_script import AudioScriptGenerator
        gen = AudioScriptGenerator()
        instructions = gen.build_asset_specific_instructions(
            {"duration_seconds": 60}, _brand_context(),
            _spec(spec_id="audio__voice_channel", artifact_type="audio", surface="voice_channel"),
        )
        assert "60-second" in instructions
        assert "150 words" in instructions

    def test_invalid_duration_raises(self):
        from src.generators.audio_script import AudioScriptGenerator
        gen = AudioScriptGenerator()
        with pytest.raises(ValueError, match="Unknown duration"):
            gen.build_asset_specific_instructions(
                {"duration_seconds": 45}, _brand_context(), _spec()
            )

    def test_instructions_contain_natural_speech(self):
        from src.generators.audio_script import AudioScriptGenerator
        gen = AudioScriptGenerator()
        instructions = gen.build_asset_specific_instructions(
            {"duration_seconds": 30}, _brand_context(), _spec()
        )
        assert "contractions" in instructions.lower() or "natural" in instructions.lower()

    def test_instructions_single_cta(self):
        from src.generators.audio_script import AudioScriptGenerator
        gen = AudioScriptGenerator()
        instructions = gen.build_asset_specific_instructions(
            {"duration_seconds": 30}, _brand_context(), _spec()
        )
        assert "Single CTA" in instructions or "single CTA" in instructions.lower()

    async def test_passthrough_mode(self):
        from src.generators.audio_script import AudioScriptGenerator
        gen = AudioScriptGenerator()
        spec = _spec(spec_id="audio__voice_channel", artifact_type="audio", surface="voice_channel")
        client = _mock_client()

        result = await gen.generate(
            {"script_text": "Hi, this is a test script with exactly ten words here.", "duration_seconds": 15},
            _brand_context(), spec, client,
        )
        assert result.content["script_text"] == "Hi, this is a test script with exactly ten words here."
        assert result.model == "passthrough"
        assert result.metadata.get("passthrough") is True
        client.generate.assert_not_called()

    async def test_generation_mode(self):
        from src.generators.audio_script import AudioScriptGenerator
        gen = AudioScriptGenerator()
        content = {
            "script_text": "Generated script",
            "duration_seconds": 30,
            "word_count": 75,
            "cta_text": "Visit us",
            "tone_notes": "Warm, conversational",
        }
        client = _mock_client(content)
        spec = _spec(spec_id="audio__voice_channel", artifact_type="audio", surface="voice_channel")
        result = await gen.generate(
            {"duration_seconds": 30, "topic": "demo"}, _brand_context(), spec, client
        )
        assert isinstance(result, GeneratedContent)
        client.generate.assert_called_once()


# ============================================================================
# CEX-23: Physical Mail Generator
# ============================================================================

class TestPhysicalMailGenerator:
    def test_satisfies_protocol(self):
        from src.generators.physical_mail import PhysicalMailGenerator
        assert isinstance(PhysicalMailGenerator(), GeneratorProtocol)

    def test_postcard_4x6_instructions(self):
        from src.generators.physical_mail import PhysicalMailGenerator
        gen = PhysicalMailGenerator()
        instructions = gen.build_asset_specific_instructions(
            {"subtype": "postcard_4x6"}, _brand_context(),
            _spec(spec_id="physical_mail__direct_mail", artifact_type="physical_mail", surface="direct_mail"),
        )
        assert "4×6" in instructions or "4x6" in instructions.lower() or "Postcard" in instructions
        assert "50" in instructions  # max headline chars

    def test_postcard_6x9_instructions(self):
        from src.generators.physical_mail import PhysicalMailGenerator
        gen = PhysicalMailGenerator()
        instructions = gen.build_asset_specific_instructions(
            {"subtype": "postcard_6x9"}, _brand_context(),
            _spec(spec_id="physical_mail__direct_mail", artifact_type="physical_mail", surface="direct_mail"),
        )
        assert "6×9" in instructions or "6x9" in instructions.lower() or "Postcard" in instructions

    def test_letter_instructions(self):
        from src.generators.physical_mail import PhysicalMailGenerator
        gen = PhysicalMailGenerator()
        instructions = gen.build_asset_specific_instructions(
            {"subtype": "letter"}, _brand_context(),
            _spec(spec_id="physical_mail__direct_mail", artifact_type="physical_mail", surface="direct_mail"),
        )
        assert "LETTER" in instructions
        assert "salutation" in instructions.lower()
        assert "2-3" in instructions

    def test_invalid_subtype_raises(self):
        from src.generators.physical_mail import PhysicalMailGenerator
        gen = PhysicalMailGenerator()
        with pytest.raises(ValueError, match="Unknown mail subtype"):
            gen.build_asset_specific_instructions(
                {"subtype": "billboard"}, _brand_context(), _spec()
            )

    def test_validate_postcard_limits(self):
        from src.generators.physical_mail import PhysicalMailGenerator
        gen = PhysicalMailGenerator()
        content = {
            "mail_type": "postcard_4x6",
            "postcard": {
                "headline": "H" * 60,
                "body_copy": "B" * 300,
                "cta_text": "Visit us",
                "subtype": "postcard_4x6",
            },
        }
        fixed, warnings = gen.validate_output(content, _spec())
        assert len(fixed["postcard"]["headline"]) == 50
        assert len(fixed["postcard"]["body_copy"]) == 200
        assert len(warnings) == 2

    def test_validate_letter_no_truncation(self):
        from src.generators.physical_mail import PhysicalMailGenerator
        gen = PhysicalMailGenerator()
        content = {
            "mail_type": "letter",
            "letter": {
                "salutation": "Dear John,",
                "body_paragraphs": ["Para 1", "Para 2"],
                "cta_text": "Visit us",
                "sign_off": "Best regards,",
                "sender_name": "Jane",
            },
        }
        fixed, warnings = gen.validate_output(content, _spec())
        assert warnings == []

    def test_personal_tone_in_instructions(self):
        from src.generators.physical_mail import PhysicalMailGenerator
        gen = PhysicalMailGenerator()
        instructions = gen.build_asset_specific_instructions(
            {"subtype": "postcard_4x6"}, _brand_context(), _spec()
        )
        assert "personal" in instructions.lower() or "human" in instructions.lower()

    async def test_generate_postcard(self):
        from src.generators.physical_mail import PhysicalMailGenerator
        gen = PhysicalMailGenerator()
        content = {
            "mail_type": "postcard_4x6",
            "postcard": {
                "headline": "Get Your Free Audit",
                "body_copy": "We help SaaS companies save time.",
                "cta_text": "Scan to claim",
                "subtype": "postcard_4x6",
            },
            "letter": None,
        }
        client = _mock_client(content)
        spec = _spec(spec_id="physical_mail__direct_mail", artifact_type="physical_mail", surface="direct_mail")
        result = await gen.generate({"subtype": "postcard_4x6"}, _brand_context(), spec, client)
        assert isinstance(result, GeneratedContent)

    async def test_generate_letter(self):
        from src.generators.physical_mail import PhysicalMailGenerator
        gen = PhysicalMailGenerator()
        content = {
            "mail_type": "letter",
            "postcard": None,
            "letter": {
                "salutation": "Dear John,",
                "body_paragraphs": ["We noticed...", "Our solution..."],
                "cta_text": "Visit acme.com",
                "sign_off": "Best regards,",
                "sender_name": "Jane Smith",
            },
        }
        client = _mock_client(content)
        spec = _spec(spec_id="physical_mail__direct_mail", artifact_type="physical_mail", surface="direct_mail")
        result = await gen.generate({"subtype": "letter"}, _brand_context(), spec, client)
        assert isinstance(result, GeneratedContent)
