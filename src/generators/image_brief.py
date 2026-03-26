"""Image concept brief content generator.

CEX-20: Platform-aware image briefs with dimensions, brand color palette,
anti-cliché guidance, and multi-platform parallel generation.
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

class ImageBriefOutput(BaseModel):
    concept_name: str
    intended_use: str
    dimensions: str
    visual_description: str
    text_overlay: str | None = None
    color_palette: list[str] = Field(default_factory=list, description="Hex colors")
    mood: str
    style_reference: str
    do_not_include: list[str] = Field(default_factory=list)


class ImageBriefSetOutput(BaseModel):
    briefs: list[ImageBriefOutput]


# ---------------------------------------------------------------------------
# Platform / format dimensions
# ---------------------------------------------------------------------------

PLATFORM_DIMENSIONS: dict[str, dict[str, str]] = {
    "linkedin_sponsored": {
        "label": "LinkedIn Sponsored Content",
        "dimensions": "1200x628",
        "aspect_ratio": "1.91:1",
        "notes": "Landscape format. Text overlay must be large enough to read in-feed.",
    },
    "linkedin_carousel": {
        "label": "LinkedIn Carousel Card",
        "dimensions": "1080x1080",
        "aspect_ratio": "1:1",
        "notes": "Square cards. Keep key visuals centred.",
    },
    "meta_feed": {
        "label": "Meta Feed (Facebook / Instagram)",
        "dimensions": "1080x1080",
        "aspect_ratio": "1:1",
        "notes": "Square format. Minimal text overlay (Meta 20% rule).",
    },
    "meta_story": {
        "label": "Meta Story / Reels",
        "dimensions": "1080x1920",
        "aspect_ratio": "9:16",
        "notes": "Full-screen vertical. Keep text in safe zone (middle 80%).",
    },
    "landing_page_hero": {
        "label": "Landing Page Hero Image",
        "dimensions": "1920x1080",
        "aspect_ratio": "16:9",
        "notes": "Wide hero banner. Works with text overlay on left or right half.",
    },
}

VALID_PLATFORMS = set(PLATFORM_DIMENSIONS.keys())


# ---------------------------------------------------------------------------
# Generator class
# ---------------------------------------------------------------------------

class ImageBriefGenerator(BaseGenerator):
    """Generator for image concept briefs."""

    generator_type = "image_brief"
    default_model = MODEL_FAST
    default_temperature = 0.6
    output_schema = ImageBriefSetOutput

    def build_asset_specific_instructions(
        self, content_props: dict, brand_context: BrandContext, spec: FormatSpec,
    ) -> str:
        platforms = content_props.get("platforms", ["linkedin_sponsored"])

        parts: list[str] = []

        parts.append(
            "TASK: Generate image concept briefs for the following platform/format "
            "combinations. Produce exactly 1 brief per platform.\n"
        )

        for platform in platforms:
            if platform not in PLATFORM_DIMENSIONS:
                raise ValueError(f"Unknown image platform '{platform}'. Valid: {sorted(VALID_PLATFORMS)}")
            info = PLATFORM_DIMENSIONS[platform]
            parts.append(
                f"PLATFORM: {info['label']}\n"
                f"- Dimensions: {info['dimensions']} ({info['aspect_ratio']})\n"
                f"- Notes: {info['notes']}\n"
            )

        # Brand color guidance
        if brand_context.brand_guidelines:
            bg = brand_context.brand_guidelines
            guidelines_parts = []
            if bg.primary_color:
                guidelines_parts.append(f"primary_color: {bg.primary_color}")
            if bg.secondary_color:
                guidelines_parts.append(f"secondary_color: {bg.secondary_color}")
            if bg.accent_color:
                guidelines_parts.append(f"accent_color: {bg.accent_color}")
            if guidelines_parts:
                parts.append(
                    "BRAND COLORS:\n" + "\n".join(f"  {g}" for g in guidelines_parts) + "\n\n"
                    "Derive color_palette from these brand guidelines. Use hex codes. 3-5 colours.\n"
                )
        else:
            parts.append(
                "BRAND COLORS: No brand guidelines provided. "
                "Choose a cohesive, professional colour palette (3-5 hex codes).\n"
            )

        parts.append(
            "VISUAL DESCRIPTION RULES:\n"
            "- Be SPECIFIC. Describe exact scene, subjects, composition, lighting.\n"
            "- BAD: 'A professional image showing teamwork'\n"
            "- GOOD: 'Overhead shot of four people around a whiteboard, warm natural light, "
            "shallow depth of field focusing on hands placing a sticky note'\n"
            "- Include camera angle, lighting, depth of field, colour temperature\n"
        )

        parts.append(
            "DO NOT INCLUDE (anti-cliché list):\n"
            "Populate do_not_include with stock-photo clichés to avoid:\n"
            "- Handshake photos\n"
            "- Generic office scenes with no context\n"
            "- Overly posed group shots with forced smiles\n"
            "- Floating holographic UI screens\n"
            "- Abstract puzzle pieces or gears representing 'teamwork'\n"
        )

        parts.append(
            "MOOD & STYLE:\n"
            "- mood: one concise phrase\n"
            "- style_reference: specific visual style or technique reference\n"
        )

        if content_props.get("topic"):
            parts.append(f"TOPIC: {content_props['topic']}")

        return "\n\n".join(parts)

    def validate_output(self, content: Any, spec: FormatSpec) -> tuple[Any, list[str]]:
        """Validate hex colors in briefs."""
        warnings: list[str] = []
        if isinstance(content, dict) and "briefs" in content:
            for i, brief in enumerate(content["briefs"]):
                palette = brief.get("color_palette", [])
                for j, color in enumerate(palette):
                    if isinstance(color, str) and not color.startswith("#"):
                        brief["color_palette"][j] = f"#{color}"
                        warnings.append(f"brief {i} color {j}: added # prefix")
        return content, warnings
