"""Tests for the generator base class and protocol (CEX-14)."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.brand.models import BrandContext, BrandGuidelines, ICPDefinition, CaseStudy, Testimonial
from src.generators.base import (
    BaseGenerator,
    GeneratedContent,
    GeneratorProtocol,
    _truncate_block,
)
from src.integrations.claude_client import ClaudeClient, GenerationResult, TokenUsage, MODEL_FAST, MODEL_QUALITY
from src.specs.models import FormatSpec, Pipeline


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_brand_context(**overrides) -> BrandContext:
    defaults = {
        "organization_id": "org-123",
        "company_name": "Acme Analytics",
        "brand_voice": "Direct, data-driven, and confident.",
        "value_proposition": "Cut reporting time by 80%.",
        "icp_definition": ICPDefinition(
            title="VP of Sales",
            industry="SaaS",
            company_size="50-500",
            pain_points=["Manual reporting", "Slow pipeline"],
            goals=["Automate forecasting"],
        ),
        "target_persona": "VP of Sales at mid-market SaaS companies",
        "case_studies": [
            CaseStudy(title="BigCo Success", company="BigCo", result="3x ROI"),
        ],
        "testimonials": [
            Testimonial(quote="Saved us 40 hours/month", author="Jane Doe", role="CRO", company="BigCo"),
        ],
        "customer_logos": ["logo1.png", "logo2.png"],
        "competitor_differentiators": ["Only solution with real-time sync"],
        "angle": "AI-powered forecasting",
        "objective": "lead_gen",
    }
    defaults.update(overrides)
    return BrandContext(**defaults)


def _make_spec(**overrides) -> FormatSpec:
    defaults = {
        "spec_id": "structured_text__linkedin",
        "artifact_type": "structured_text",
        "surface": "linkedin",
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


def _make_generation_result(**overrides) -> GenerationResult:
    defaults = {
        "content": {"headline": "Test Output"},
        "tool_results": [{"id": "t1", "name": "generate_test", "input": {"headline": "Test Output"}}],
        "usage": TokenUsage(input_tokens=100, output_tokens=50),
        "model": "claude-sonnet-4-20250514",
        "stop_reason": "end_turn",
    }
    defaults.update(overrides)
    return GenerationResult(**defaults)


class ConcreteGenerator(BaseGenerator):
    """Minimal concrete generator for testing."""

    generator_type = "test_generator"
    default_model = MODEL_FAST
    default_temperature = 0.5

    def build_asset_specific_instructions(self, content_props, brand_context, spec):
        topic = content_props.get("topic", "general")
        return f"TASK: Generate test content about {topic}."


class ValidatingGenerator(BaseGenerator):
    """Generator with custom validation."""

    generator_type = "validating_generator"

    def build_asset_specific_instructions(self, content_props, brand_context, spec):
        return "TASK: Generate content."

    def validate_output(self, content, spec):
        warnings = []
        if isinstance(content, dict) and "headline" in content:
            if len(content["headline"]) > 50:
                content["headline"] = content["headline"][:50]
                warnings.append("headline truncated to 50 chars")
        return content, warnings


# ---------------------------------------------------------------------------
# Tests: GeneratorProtocol
# ---------------------------------------------------------------------------

class TestGeneratorProtocol:
    def test_concrete_generator_satisfies_protocol(self):
        gen = ConcreteGenerator()
        assert isinstance(gen, GeneratorProtocol)

    def test_non_generator_does_not_satisfy_protocol(self):
        class NotAGenerator:
            pass

        assert not isinstance(NotAGenerator(), GeneratorProtocol)


# ---------------------------------------------------------------------------
# Tests: GeneratedContent
# ---------------------------------------------------------------------------

class TestGeneratedContent:
    def test_defaults(self):
        gc = GeneratedContent(content={"key": "value"})
        assert gc.content == {"key": "value"}
        assert gc.usage == {}
        assert gc.model == ""
        assert gc.warnings == []
        assert gc.metadata == {}

    def test_with_all_fields(self):
        gc = GeneratedContent(
            content={"headline": "Test"},
            usage={"input_tokens": 100},
            model="claude-sonnet-4-20250514",
            warnings=["truncated"],
            metadata={"spec_id": "test"},
        )
        assert gc.usage["input_tokens"] == 100
        assert gc.model == "claude-sonnet-4-20250514"
        assert gc.warnings == ["truncated"]
        assert gc.metadata["spec_id"] == "test"


# ---------------------------------------------------------------------------
# Tests: BaseGenerator system prompt
# ---------------------------------------------------------------------------

class TestBuildSystemPrompt:
    def test_includes_company_name(self):
        gen = ConcreteGenerator()
        ctx = _make_brand_context()
        spec = _make_spec()
        prompt = gen.build_system_prompt(ctx, spec)
        assert "Acme Analytics" in prompt

    def test_includes_brand_voice(self):
        gen = ConcreteGenerator()
        ctx = _make_brand_context()
        spec = _make_spec()
        prompt = gen.build_system_prompt(ctx, spec)
        assert "Direct, data-driven" in prompt

    def test_includes_value_proposition(self):
        gen = ConcreteGenerator()
        ctx = _make_brand_context()
        spec = _make_spec()
        prompt = gen.build_system_prompt(ctx, spec)
        assert "Cut reporting time by 80%" in prompt

    def test_includes_differentiators(self):
        gen = ConcreteGenerator()
        ctx = _make_brand_context()
        spec = _make_spec()
        prompt = gen.build_system_prompt(ctx, spec)
        assert "Only solution with real-time sync" in prompt

    def test_includes_core_rules(self):
        gen = ConcreteGenerator()
        ctx = _make_brand_context()
        spec = _make_spec()
        prompt = gen.build_system_prompt(ctx, spec)
        assert "IMPORTANT RULES:" in prompt

    def test_fallback_company_name(self):
        gen = ConcreteGenerator()
        ctx = _make_brand_context(company_name="")
        spec = _make_spec()
        prompt = gen.build_system_prompt(ctx, spec)
        assert "the client" in prompt

    def test_brand_guidelines_extra_fields(self):
        gen = ConcreteGenerator()
        bg = BrandGuidelines(primary_color="#000", tone="Professional and authoritative")
        ctx = _make_brand_context(brand_guidelines=bg)
        spec = _make_spec()
        prompt = gen.build_system_prompt(ctx, spec)
        assert "TONE" in prompt


# ---------------------------------------------------------------------------
# Tests: BaseGenerator user prompt
# ---------------------------------------------------------------------------

class TestBuildUserPrompt:
    def test_includes_target_audience(self):
        gen = ConcreteGenerator()
        ctx = _make_brand_context()
        spec = _make_spec()
        prompt = gen.build_user_prompt({"topic": "AI"}, ctx, spec)
        assert "TARGET AUDIENCE:" in prompt
        assert "VP of Sales" in prompt

    def test_includes_campaign_context(self):
        gen = ConcreteGenerator()
        ctx = _make_brand_context()
        spec = _make_spec()
        prompt = gen.build_user_prompt({"topic": "AI"}, ctx, spec)
        assert "CAMPAIGN CONTEXT:" in prompt
        assert "AI-powered forecasting" in prompt
        assert "lead_gen" in prompt

    def test_includes_asset_specific_instructions(self):
        gen = ConcreteGenerator()
        ctx = _make_brand_context()
        spec = _make_spec()
        prompt = gen.build_user_prompt({"topic": "pipelines"}, ctx, spec)
        assert "Generate test content about pipelines" in prompt

    def test_social_proof_for_relevant_types(self):
        gen = ConcreteGenerator()
        gen.generator_type = "landing_page"
        ctx = _make_brand_context()
        spec = _make_spec()
        prompt = gen.build_user_prompt({"topic": "test"}, ctx, spec)
        assert "AVAILABLE SOCIAL PROOF:" in prompt
        assert "BigCo" in prompt

    def test_no_social_proof_for_irrelevant_types(self):
        gen = ConcreteGenerator()
        gen.generator_type = "ad_copy"
        ctx = _make_brand_context()
        spec = _make_spec()
        prompt = gen.build_user_prompt({"topic": "test"}, ctx, spec)
        assert "AVAILABLE SOCIAL PROOF:" not in prompt


# ---------------------------------------------------------------------------
# Tests: Model/temperature resolution
# ---------------------------------------------------------------------------

class TestResolution:
    def test_resolve_model_from_spec(self):
        gen = ConcreteGenerator()
        spec = _make_spec()
        assert gen._resolve_model(spec) == "claude-sonnet-4-20250514"

    def test_resolve_model_fallback(self):
        gen = ConcreteGenerator()
        spec = _make_spec(pipeline=None)
        assert gen._resolve_model(spec) == MODEL_FAST

    def test_resolve_temperature_from_spec(self):
        gen = ConcreteGenerator()
        spec = _make_spec()
        assert gen._resolve_temperature(spec) == 0.7

    def test_resolve_temperature_fallback(self):
        gen = ConcreteGenerator()
        spec = _make_spec(pipeline=None)
        assert gen._resolve_temperature(spec) == 0.5

    def test_resolve_max_tokens_from_spec(self):
        gen = ConcreteGenerator()
        spec = _make_spec()
        assert gen._resolve_max_tokens(spec) == 1024

    def test_resolve_max_tokens_fallback(self):
        gen = ConcreteGenerator()
        spec = _make_spec(pipeline=None)
        assert gen._resolve_max_tokens(spec) == 4096


# ---------------------------------------------------------------------------
# Tests: Post-generation validation
# ---------------------------------------------------------------------------

class TestValidateOutput:
    def test_default_validation_passes_through(self):
        gen = ConcreteGenerator()
        spec = _make_spec()
        content = {"headline": "Test"}
        validated, warnings = gen.validate_output(content, spec)
        assert validated == content
        assert warnings == []

    def test_custom_validation_truncates(self):
        gen = ValidatingGenerator()
        spec = _make_spec()
        content = {"headline": "A" * 60}
        validated, warnings = gen.validate_output(content, spec)
        assert len(validated["headline"]) == 50
        assert "truncated" in warnings[0]

    def test_custom_validation_no_truncation_needed(self):
        gen = ValidatingGenerator()
        spec = _make_spec()
        content = {"headline": "Short"}
        validated, warnings = gen.validate_output(content, spec)
        assert validated["headline"] == "Short"
        assert warnings == []


# ---------------------------------------------------------------------------
# Tests: Full generate pipeline
# ---------------------------------------------------------------------------

class TestGenerate:
    async def test_generate_calls_claude_and_returns_content(self):
        gen = ConcreteGenerator()
        ctx = _make_brand_context()
        spec = _make_spec()

        mock_client = MagicMock(spec=ClaudeClient)
        mock_client.generate = AsyncMock(return_value=_make_generation_result())

        result = await gen.generate({"topic": "AI"}, ctx, spec, mock_client)

        assert isinstance(result, GeneratedContent)
        assert result.content == {"headline": "Test Output"}
        assert result.usage["input_tokens"] == 100
        assert result.usage["output_tokens"] == 50
        assert result.model == "claude-sonnet-4-20250514"
        assert result.metadata["spec_id"] == "structured_text__linkedin"
        assert result.metadata["generator_type"] == "test_generator"

    async def test_generate_passes_model_from_spec(self):
        gen = ConcreteGenerator()
        ctx = _make_brand_context()
        spec = _make_spec()

        mock_client = MagicMock(spec=ClaudeClient)
        mock_client.generate = AsyncMock(return_value=_make_generation_result())

        await gen.generate({"topic": "AI"}, ctx, spec, mock_client)

        call_kwargs = mock_client.generate.call_args[1]
        assert call_kwargs["model"] == "claude-sonnet-4-20250514"
        assert call_kwargs["temperature"] == 0.7

    async def test_generate_with_validation(self):
        gen = ValidatingGenerator()
        ctx = _make_brand_context()
        spec = _make_spec()

        mock_result = _make_generation_result(content={"headline": "A" * 60})
        mock_client = MagicMock(spec=ClaudeClient)
        mock_client.generate = AsyncMock(return_value=mock_result)

        result = await gen.generate({"topic": "AI"}, ctx, spec, mock_client)
        assert len(result.content["headline"]) == 50
        assert len(result.warnings) == 1

    async def test_generate_with_output_schema(self):
        from pydantic import BaseModel as PydanticBaseModel

        class TestOutput(PydanticBaseModel):
            headline: str
            body: str

        gen = ConcreteGenerator()
        gen.output_schema = TestOutput
        ctx = _make_brand_context()
        spec = _make_spec()

        mock_client = MagicMock(spec=ClaudeClient)
        mock_client.generate = AsyncMock(return_value=_make_generation_result())

        await gen.generate({"topic": "AI"}, ctx, spec, mock_client)

        call_kwargs = mock_client.generate.call_args[1]
        assert call_kwargs["tools"] is not None
        assert len(call_kwargs["tools"]) == 1
        assert call_kwargs["tools"][0]["name"] == "generate_test_generator"
        assert call_kwargs["tool_choice"]["type"] == "tool"


# ---------------------------------------------------------------------------
# Tests: Truncation utility
# ---------------------------------------------------------------------------

class TestTruncateBlock:
    def test_no_truncation_needed(self):
        text = "Short text"
        assert _truncate_block(text, "test") == text

    def test_truncation_applied(self):
        text = "A" * 20_000
        result = _truncate_block(text, "test", max_chars=100)
        assert len(result) < 20_000
        assert result.endswith("[...truncated]")

    def test_empty_string(self):
        assert _truncate_block("", "test") == ""
