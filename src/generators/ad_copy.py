"""Ad copy content generator.

CEX-15: Multi-platform ad copy (LinkedIn, Meta, Google RSA) with strict
character limits, per-platform schemas, and post-generation validation.
Constraints sourced from spec YAML, not hardcoded.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from pydantic import BaseModel, Field

from src.brand.models import BrandContext
from src.generators.base import BaseGenerator, GeneratedContent
from src.integrations.claude_client import ClaudeClient, MODEL_FAST
from src.specs.models import FormatSpec

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Output schemas
# ---------------------------------------------------------------------------

class LinkedInAdCopyVariant(BaseModel):
    introductory_text: str = Field(..., description="Max 600 chars (150 visible before fold)")
    headline: str = Field(..., description="Max 70 chars recommended")
    description: str = Field(..., description="Max 100 chars")


class LinkedInAdCopyOutput(BaseModel):
    variants: list[LinkedInAdCopyVariant] = Field(..., min_length=3, max_length=3)


class MetaAdCopyVariant(BaseModel):
    primary_text: str = Field(..., description="Max 125 chars recommended")
    headline: str = Field(..., description="Max 40 chars")
    description: str = Field(..., description="Max 30 chars")


class MetaAdCopyOutput(BaseModel):
    variants: list[MetaAdCopyVariant] = Field(..., min_length=3, max_length=3)


class GoogleRSACopyOutput(BaseModel):
    headlines: list[str] = Field(
        ..., min_length=3, max_length=15,
        description="3-15 headlines, each max 30 chars",
    )
    descriptions: list[str] = Field(
        ..., min_length=2, max_length=4,
        description="2-4 descriptions, each max 90 chars",
    )
    path1: str = Field(..., description="Max 15 chars")
    path2: str = Field(..., description="Max 15 chars")


_OUTPUT_SCHEMAS: dict[str, type[BaseModel]] = {
    "linkedin": LinkedInAdCopyOutput,
    "meta": MetaAdCopyOutput,
    "google": GoogleRSACopyOutput,
}

VALID_PLATFORMS = {"linkedin", "meta", "google"}


# ---------------------------------------------------------------------------
# Character limit validation
# ---------------------------------------------------------------------------

from src.shared.text import truncate_at_word_boundary as _truncate_at_word_boundary


def _get_char_limits(spec: FormatSpec) -> dict[str, int]:
    """Extract character limits from spec constraints."""
    limits = {}
    constraints = spec.constraints or {}
    hard = constraints.get("hard", {}) if isinstance(constraints, dict) else {}
    if isinstance(hard, dict):
        for field_name, field_config in hard.items():
            if isinstance(field_config, dict) and "max_chars" in field_config:
                limits[field_name] = field_config["max_chars"]
    return limits


def validate_ad_copy_limits(
    platform: str, content: dict, spec: FormatSpec,
) -> tuple[dict, list[str]]:
    """Validate and fix character limits. Returns (fixed_content, warnings)."""
    warnings: list[str] = []
    limits = _get_char_limits(spec)

    if platform == "linkedin" and "variants" in content:
        for i, v in enumerate(content["variants"]):
            for field_name, spec_field in [
                ("introductory_text", "introductory_text"),
                ("headline", "headline"),
                ("description", "description"),
            ]:
                limit = limits.get(spec_field, 600 if field_name == "introductory_text" else 200 if field_name == "headline" else 100)
                val = v.get(field_name, "")
                if len(val) > limit:
                    fixed = _truncate_at_word_boundary(val, limit)
                    warnings.append(
                        f"linkedin variant {i} {field_name}: {len(val)} chars "
                        f"→ truncated to {len(fixed)} (limit {limit})"
                    )
                    v[field_name] = fixed

    elif platform == "meta" and "variants" in content:
        for i, v in enumerate(content["variants"]):
            for field_name, limit in [
                ("primary_text", 125),
                ("headline", 40),
                ("description", 30),
            ]:
                val = v.get(field_name, "")
                if len(val) > limit:
                    fixed = _truncate_at_word_boundary(val, limit)
                    warnings.append(
                        f"meta variant {i} {field_name}: {len(val)} chars "
                        f"→ truncated to {len(fixed)} (limit {limit})"
                    )
                    v[field_name] = fixed

    elif platform == "google":
        for i, h in enumerate(content.get("headlines", [])):
            if len(h) > 30:
                fixed = _truncate_at_word_boundary(h, 30)
                warnings.append(f"google headline {i}: {len(h)} chars → truncated to {len(fixed)}")
                content["headlines"][i] = fixed
        for i, d in enumerate(content.get("descriptions", [])):
            if len(d) > 90:
                fixed = _truncate_at_word_boundary(d, 90)
                warnings.append(f"google description {i}: {len(d)} chars → truncated to {len(fixed)}")
                content["descriptions"][i] = fixed
        for path_field in ("path1", "path2"):
            val = content.get(path_field, "")
            if len(val) > 15:
                fixed = _truncate_at_word_boundary(val, 15)
                warnings.append(f"google {path_field}: truncated to {len(fixed)}")
                content[path_field] = fixed

    if warnings:
        for w in warnings:
            logger.warning("ad_copy_limit_exceeded: %s", w)

    return content, warnings


# ---------------------------------------------------------------------------
# Platform-specific prompt instructions
# ---------------------------------------------------------------------------

def _linkedin_instructions() -> str:
    return (
        "PLATFORM: LINKEDIN SPONSORED CONTENT\n\n"
        "Generate exactly 3 ad copy variants for LinkedIn Sponsored Content.\n\n"
        "CHARACTER LIMITS (strict — do not exceed):\n"
        "- introductory_text: max 600 characters. The first 150 characters appear "
        "before the 'see more' fold — front-load the hook.\n"
        "- headline: max 70 characters. Benefit-driven, not feature-driven. "
        "Use specific outcomes and numbers.\n"
        "- description: max 100 characters. Supporting context or proof point.\n\n"
        "VARIANT STRATEGY:\n"
        "- Variant 1: Problem-agitation — name the pain directly\n"
        "- Variant 2: Social proof — lead with a result or customer outcome\n"
        "- Variant 3: Curiosity — ask a question or tease an insight\n\n"
        "RULES:\n"
        "- Professional B2B tone appropriate for LinkedIn\n"
        "- Each variant must be distinct in approach, not just rewording\n"
        "- Front-load value in the first 150 chars of introductory_text\n"
        "- Use concrete numbers and specific outcomes, not vague promises\n"
        "- No clickbait, no ALL CAPS, no excessive punctuation\n"
    )


def _meta_instructions() -> str:
    return (
        "PLATFORM: META (FACEBOOK / INSTAGRAM)\n\n"
        "Generate exactly 3 ad copy variants for Meta (Facebook/Instagram) ads.\n\n"
        "CHARACTER LIMITS (strict — do not exceed):\n"
        "- primary_text: max 125 characters recommended (gets cut off on mobile)\n"
        "- headline: max 40 characters. Punchy, scroll-stopping.\n"
        "- description: max 30 characters. Brief supporting text.\n\n"
        "VARIANT STRATEGY:\n"
        "- Variant 1: Outcome-focused — lead with the transformation\n"
        "- Variant 2: Question hook — ask something the audience cares about\n"
        "- Variant 3: Stat/proof — lead with a compelling number\n\n"
        "RULES:\n"
        "- Shorter is better — users scroll fast on Meta\n"
        "- Conversational but professional tone\n"
        "- Each variant must be distinct in approach\n"
        "- Use emojis sparingly (max 1 per variant, only if appropriate for brand)\n"
        "- Avoid B2B jargon — write like a human, not a brochure\n"
    )


def _google_instructions() -> str:
    return (
        "PLATFORM: GOOGLE RESPONSIVE SEARCH AD (RSA)\n\n"
        "Generate a complete RSA ad asset set.\n\n"
        "CHARACTER LIMITS (strict — do not exceed):\n"
        "- headlines: 10 headlines, each max 30 characters\n"
        "- descriptions: 4 descriptions, each max 90 characters\n"
        "- path1: max 15 characters (URL display path segment 1)\n"
        "- path2: max 15 characters (URL display path segment 2)\n\n"
        "HEADLINE REQUIREMENTS:\n"
        "- Each headline must be self-contained (any combination must work)\n"
        "- At least 1 headline with a specific number or statistic\n"
        "- At least 1 headline as a question\n"
        "- Include the company name in at least 1 headline\n"
        "- Mix: benefit headlines, feature headlines, CTA headlines, social proof\n"
        "- No duplicate meanings — each headline adds unique value\n\n"
        "DESCRIPTION REQUIREMENTS:\n"
        "- Each description should work independently\n"
        "- Include a clear CTA in at least 1 description\n"
        "- Mix benefit-driven and proof-driven descriptions\n\n"
        "RULES:\n"
        "- Every character counts — no filler words\n"
        "- Use title case for headlines\n"
        "- path1/path2 should be short, keyword-rich URL segments\n"
        "- No exclamation marks in headlines (Google policy)\n"
    )


_PLATFORM_BUILDERS: dict[str, Any] = {
    "linkedin": _linkedin_instructions,
    "meta": _meta_instructions,
    "google": _google_instructions,
}


# ---------------------------------------------------------------------------
# Generator class
# ---------------------------------------------------------------------------

class AdCopyGenerator(BaseGenerator):
    """Generator for multi-platform ad copy."""

    generator_type = "ad_copy"
    default_model = MODEL_FAST
    default_temperature = 0.7
    output_schema = LinkedInAdCopyOutput  # default; overridden per platform

    def build_asset_specific_instructions(
        self, content_props: dict, brand_context: BrandContext, spec: FormatSpec,
    ) -> str:
        platform = content_props.get("platform", spec.surface)
        if platform not in _PLATFORM_BUILDERS:
            raise ValueError(
                f"Unknown ad platform '{platform}'. Valid: {sorted(VALID_PLATFORMS)}"
            )
        builder = _PLATFORM_BUILDERS[platform]
        parts = [builder()]

        # Add content props context
        if content_props.get("topic"):
            parts.append(f"TOPIC: {content_props['topic']}")
        if content_props.get("value_proposition"):
            parts.append(f"VALUE PROPOSITION: {content_props['value_proposition']}")
        if content_props.get("target_audience"):
            parts.append(f"TARGET AUDIENCE: {content_props['target_audience']}")
        if content_props.get("cta_text"):
            parts.append(f"CTA TO ECHO: {content_props['cta_text']}")

        return "\n\n".join(parts)

    def validate_output(self, content: Any, spec: FormatSpec) -> tuple[Any, list[str]]:
        """Post-generation character limit validation."""
        if not isinstance(content, dict):
            return content, []
        platform = spec.surface
        return validate_ad_copy_limits(platform, content, spec)

    async def generate(
        self,
        content_props: dict,
        brand_context: BrandContext,
        spec: FormatSpec,
        claude_client: ClaudeClient,
    ) -> GeneratedContent:
        """Generate ad copy with the correct output schema per platform."""
        platform = content_props.get("platform", spec.surface)
        if platform not in _OUTPUT_SCHEMAS:
            raise ValueError(
                f"Unknown ad platform '{platform}'. Valid: {sorted(VALID_PLATFORMS)}"
            )

        return await super().generate(
            content_props, brand_context, spec, claude_client,
            output_schema_override=_OUTPUT_SCHEMAS[platform],
        )
