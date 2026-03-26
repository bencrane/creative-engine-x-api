"""LinkedIn Document Slides (Carousel) content generator.

CEX-18: Three narrative patterns (problem_solution, listicle, data_story),
5-8 slides with character limits, CTA enforcement on last slide.
"""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, Field

from src.brand.models import BrandContext
from src.generators.base import BaseGenerator, GeneratedContent
from src.integrations.claude_client import ClaudeClient, MODEL_QUALITY
from src.specs.models import FormatSpec

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Output schemas
# ---------------------------------------------------------------------------

class SlideOutput(BaseModel):
    headline: str = Field(..., description="Max 50 chars")
    body: str | None = Field(None, description="Max 120 chars")
    stat_callout: str | None = None
    stat_label: str | None = None
    is_cta_slide: bool = False
    cta_text: str | None = None


class DocumentSlidesOutput(BaseModel):
    slides: list[SlideOutput] = Field(..., min_length=5, max_length=8)
    aspect_ratio: str = "1:1"


# ---------------------------------------------------------------------------
# Narrative patterns
# ---------------------------------------------------------------------------

VALID_PATTERNS = {"problem_solution", "listicle", "data_story"}

_PATTERN_INSTRUCTIONS: dict[str, str] = {
    "problem_solution": (
        "NARRATIVE PATTERN: Problem → Solution → Proof\n\n"
        "Follow this narrative arc across 5-8 slides:\n"
        "1. Hook slide — provocative question or stat that stops the scroll\n"
        "2-3. Problem slides — describe the pain points. Be specific and relatable.\n"
        "4-5. Solution slides — present the framework/approach. Focus on methodology.\n"
        "6-7. Proof slides — concrete stats, case study snippet, or customer result.\n"
        "8. CTA slide — clear call to action with urgency.\n"
    ),
    "listicle": (
        "NARRATIVE PATTERN: Listicle\n\n"
        "Follow this arc across 5-8 slides:\n"
        "1. Title slide — number + topic (e.g., '5 Signs Your Pipeline Is Leaking')\n"
        "2-6. One sign per slide — punchy headline with brief explanation.\n"
        "7. Summary slide — tie the signs together\n"
        "8. CTA slide — clear call to action.\n"
    ),
    "data_story": (
        "NARRATIVE PATTERN: Data Story\n\n"
        "Follow this arc across 5-8 slides:\n"
        "1. Big stat hook — one jaw-dropping number\n"
        "2-5. Supporting data points — each with context. Use stat_callout for number.\n"
        "6-7. Implications / what to do — translate data into action items\n"
        "8. CTA slide — clear call to action.\n"
    ),
}


# ---------------------------------------------------------------------------
# Generator class
# ---------------------------------------------------------------------------

class DocumentSlidesGenerator(BaseGenerator):
    """Generator for LinkedIn Document Ad (Carousel) content."""

    generator_type = "document_slides"
    default_model = MODEL_QUALITY
    default_temperature = 0.4
    output_schema = DocumentSlidesOutput

    def _needs_social_proof(self) -> bool:
        return True

    def build_asset_specific_instructions(
        self, content_props: dict, brand_context: BrandContext, spec: FormatSpec,
    ) -> str:
        pattern = content_props.get("pattern", content_props.get("subtype", "problem_solution"))
        if pattern not in VALID_PATTERNS:
            raise ValueError(f"Unknown carousel pattern '{pattern}'. Valid: {sorted(VALID_PATTERNS)}")

        parts: list[str] = []

        parts.append(
            "TASK: Generate a LinkedIn Document Ad (carousel) with a compelling "
            "narrative arc that keeps the viewer swiping.\n"
        )
        parts.append(_PATTERN_INSTRUCTIONS[pattern])

        parts.append(
            "SLIDE CONSTRAINTS:\n"
            "- Total slides: 5-8 (inclusive)\n"
            "- headline: max 50 characters — punchy, scannable\n"
            "- body: max 120 characters — supporting detail (null if not needed)\n"
            "- stat_callout: a specific number or metric (e.g., '3x', '47%', '$2M')\n"
            "- stat_label: label for the stat. Required when stat_callout is set.\n"
            "- The LAST slide MUST have is_cta_slide=True and a cta_text value\n"
            "- Only the last slide should have is_cta_slide=True\n"
        )

        parts.append(
            "ASPECT RATIO:\n"
            "- Default: '1:1' (square) — works best for most carousels\n"
            "- Use '4:5' when slides need more vertical space\n"
        )

        parts.append(
            "QUALITY RULES:\n"
            "- Each slide must advance the narrative — no filler slides\n"
            "- Headlines should be readable in 2 seconds at mobile size\n"
            "- Stats must be specific numbers, not vague qualifiers\n"
            "- The carousel must tell a coherent story from first to last slide\n"
        )

        if content_props.get("topic"):
            parts.append(f"TOPIC: {content_props['topic']}")

        return "\n\n".join(parts)

    def validate_output(self, content: Any, spec: FormatSpec) -> tuple[Any, list[str]]:
        """Enforce slide character limits and CTA on last slide."""
        warnings: list[str] = []
        if not isinstance(content, dict) or "slides" not in content:
            return content, warnings

        slides = content["slides"]

        # Enforce character limits
        for i, slide in enumerate(slides):
            headline = slide.get("headline", "")
            if len(headline) > 50:
                slide["headline"] = headline[:50]
                warnings.append(f"slide {i} headline truncated to 50 chars")

            body = slide.get("body")
            if body and len(body) > 120:
                slide["body"] = body[:120]
                warnings.append(f"slide {i} body truncated to 120 chars")

        # Ensure last slide is CTA
        if slides:
            last = slides[-1]
            if not last.get("is_cta_slide"):
                last["is_cta_slide"] = True
                if not last.get("cta_text"):
                    last["cta_text"] = "Learn More"
                warnings.append("Last slide forced to CTA")

        return content, warnings
