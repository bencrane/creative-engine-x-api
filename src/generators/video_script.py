"""Video script content generator.

CEX-19: Duration-specific video scripts (30s / 60s) with platform guidance,
aspect ratio selection, and word-count-aware segment templates.
"""

from __future__ import annotations

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

class ScriptSegment(BaseModel):
    timestamp_start: str
    timestamp_end: str
    spoken_text: str
    visual_direction: str
    text_overlay: str | None = None
    caption_text: str


class VideoScriptOutput(BaseModel):
    title: str
    duration: str
    aspect_ratio: str
    hook: ScriptSegment
    body: list[ScriptSegment]
    cta: ScriptSegment
    total_word_count: int
    music_direction: str
    target_platform: str


# ---------------------------------------------------------------------------
# Duration configs
# ---------------------------------------------------------------------------

VALID_DURATIONS = {"30s", "60s"}

_DURATION_STRUCTURES: dict[str, str] = {
    "30s": (
        "DURATION: 30 seconds (~75 words total spoken text)\n\n"
        "SEGMENT STRUCTURE:\n"
        "1. Hook (0:00–0:03) — 1 sentence, max 10 words. Grab attention.\n"
        "2. Problem (0:03–0:10) — 2 sentences. Name the pain.\n"
        "3. Solution (0:10–0:20) — 2-3 sentences. ONE key benefit.\n"
        "4. CTA (0:20–0:30) — 1-2 sentences. Clear next step.\n\n"
        "Hook is first ScriptSegment. Problem and Solution go in body. CTA is final.\n"
    ),
    "60s": (
        "DURATION: 60 seconds (~150 words total spoken text)\n\n"
        "SEGMENT STRUCTURE:\n"
        "1. Hook (0:00–0:03) — 1 sentence, max 10 words.\n"
        "2. Problem (0:03–0:15) — 3-4 sentences. Deep dive into pain.\n"
        "3. Solution (0:15–0:35) — 4-5 sentences. Concrete example.\n"
        "4. Proof (0:35–0:50) — 2-3 sentences. Social proof or stat.\n"
        "5. CTA (0:50–1:00) — 1-2 sentences. Clear next step.\n\n"
        "Hook is first ScriptSegment. Problem, Solution, Proof go in body. CTA is final.\n"
    ),
}

# ---------------------------------------------------------------------------
# Platform guidance
# ---------------------------------------------------------------------------

VALID_PLATFORMS = {"linkedin", "meta", "youtube"}

_PLATFORM_GUIDANCE: dict[str, str] = {
    "linkedin": (
        "PLATFORM: LinkedIn Video\n"
        "- Aspect ratio: 4:5 (portrait)\n"
        "- Tone: Professional, authoritative, conversational\n"
        "- Caption-heavy: assume sound-off viewing\n"
        "- Text overlays: bold key stats or pull-quotes\n"
    ),
    "meta": (
        "PLATFORM: Meta (Facebook / Instagram Reels)\n"
        "- Aspect ratio: 4:5 for feed, 9:16 for Reels\n"
        "- Tone: Punchy, fast-paced, scroll-stopping\n"
        "- Hook MUST be visually disruptive\n"
        "- Short sentences, fast cuts\n"
    ),
    "youtube": (
        "PLATFORM: YouTube\n"
        "- Aspect ratio: 16:9 (landscape)\n"
        "- Tone: Educational, value-first\n"
        "- Hook should promise specific takeaway\n"
        "- End screen CTA: mention subscribe + link\n"
    ),
}

_PLATFORM_ASPECT_RATIOS: dict[str, str] = {
    "linkedin": "4:5",
    "meta": "4:5",
    "youtube": "16:9",
}


# ---------------------------------------------------------------------------
# Generator class
# ---------------------------------------------------------------------------

class VideoScriptGenerator(BaseGenerator):
    """Generator for video scripts."""

    generator_type = "video_script"
    default_model = MODEL_FAST
    default_temperature = 0.5
    output_schema = VideoScriptOutput

    def build_asset_specific_instructions(
        self, content_props: dict, brand_context: BrandContext, spec: FormatSpec,
    ) -> str:
        duration = content_props.get("duration", "30s")
        platform = content_props.get("platform", "linkedin")

        if duration not in VALID_DURATIONS:
            raise ValueError(f"Unknown duration '{duration}'. Valid: {sorted(VALID_DURATIONS)}")
        if platform not in VALID_PLATFORMS:
            raise ValueError(f"Unknown platform '{platform}'. Valid: {sorted(VALID_PLATFORMS)}")

        parts: list[str] = []

        parts.append(_DURATION_STRUCTURES[duration])
        parts.append(_PLATFORM_GUIDANCE[platform])

        aspect_ratio = _PLATFORM_ASPECT_RATIOS[platform]
        parts.append(f"Set aspect_ratio to '{aspect_ratio}'.")
        parts.append(f"Set target_platform to '{platform}'.")
        parts.append(f"Set duration to '{duration}'.")

        parts.append(
            "SEGMENT RULES:\n"
            "- timestamp_start / timestamp_end: 'M:SS' format\n"
            "- spoken_text: exact words the speaker says\n"
            "- visual_direction: describe the shot specifically\n"
            "- text_overlay: on-screen text (null if none)\n"
            "- caption_text: subtitle text for sound-off viewing\n"
        )

        word_target = 75 if duration == "30s" else 150
        parts.append(
            f"WORD COUNT:\n"
            f"- Target ~{word_target} total words across all spoken_text.\n"
            f"- Set total_word_count to actual count.\n"
        )

        parts.append(
            "MUSIC DIRECTION:\n"
            "- Brief music direction (genre, tempo, mood).\n"
        )

        if content_props.get("topic"):
            parts.append(f"TOPIC: {content_props['topic']}")

        return "\n\n".join(parts)
