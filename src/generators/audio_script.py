"""Audio script content generator.

CEX-22: Generates spoken-word scripts for voicemail drop and narration,
optimized for TTS rendering. NEW generator (not ported from paid-engine-x).
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

class AudioScriptOutput(BaseModel):
    script_text: str = Field(..., description="The spoken-word script text")
    duration_seconds: int = Field(..., description="Target duration in seconds")
    word_count: int = Field(..., description="Actual word count")
    cta_text: str = Field(..., description="The single call-to-action")
    tone_notes: str = Field(default="", description="Notes on delivery tone")


# ---------------------------------------------------------------------------
# Duration configs (150 words per minute)
# ---------------------------------------------------------------------------

DURATION_CONFIGS = {
    15: {"word_target": 38, "tolerance": 0.10},
    30: {"word_target": 75, "tolerance": 0.10},
    60: {"word_target": 150, "tolerance": 0.10},
}

VALID_DURATIONS = {15, 30, 60}


# ---------------------------------------------------------------------------
# Generator class
# ---------------------------------------------------------------------------

class AudioScriptGenerator(BaseGenerator):
    """Generator for voicemail drop and narration scripts."""

    generator_type = "audio_script"
    default_model = MODEL_FAST
    default_temperature = 0.5
    output_schema = AudioScriptOutput

    def build_asset_specific_instructions(
        self, content_props: dict, brand_context: BrandContext, spec: FormatSpec,
    ) -> str:
        duration = content_props.get("duration_seconds", 30)
        if duration not in VALID_DURATIONS:
            raise ValueError(f"Unknown duration '{duration}'. Valid: {sorted(VALID_DURATIONS)}")

        config = DURATION_CONFIGS[duration]
        word_target = config["word_target"]

        parts: list[str] = []

        parts.append(
            f"TASK: Generate a {duration}-second voicemail/narration script.\n\n"
            f"TARGET WORD COUNT: ~{word_target} words (±10%)\n"
            f"At 150 words per minute, {duration}s = approximately {word_target} words.\n"
        )

        parts.append(
            "SCRIPT REQUIREMENTS:\n"
            "- Natural speech patterns — use contractions, conversational tone\n"
            "- Appropriate pauses indicated by commas and periods\n"
            "- First-person singular preferred ('I wanted to reach out...')\n"
            "- Single CTA per script — avoid multiple asks\n"
            "- No hard sell language in opening 5 seconds\n"
            "- Script should sound natural when read aloud, not like reading from a page\n"
        )

        parts.append(
            "STRUCTURE:\n"
            "- Opening: Warm, personal greeting (name if available)\n"
            "- Body: Value statement — why you're reaching out, what's in it for them\n"
            "- CTA: One clear, specific action\n"
            "- Closing: Brief, friendly sign-off\n"
        )

        parts.append(
            "OUTPUT:\n"
            "- script_text: The complete spoken-word script\n"
            f"- duration_seconds: {duration}\n"
            "- word_count: Actual word count of script_text\n"
            "- cta_text: The CTA extracted from the script\n"
            "- tone_notes: Brief delivery guidance (pace, emotion, emphasis points)\n"
        )

        if content_props.get("topic"):
            parts.append(f"TOPIC: {content_props['topic']}")
        if content_props.get("recipient_name"):
            parts.append(f"RECIPIENT: {content_props['recipient_name']}")
        if content_props.get("sender_name"):
            parts.append(f"SENDER: {content_props['sender_name']}")

        return "\n\n".join(parts)

    async def generate(
        self,
        content_props: dict,
        brand_context: BrandContext,
        spec: FormatSpec,
        claude_client: ClaudeClient,
    ) -> GeneratedContent:
        """Generate audio script, or passthrough if script_text is provided."""
        # Passthrough mode: if script_text is provided, skip generation
        if content_props.get("script_text"):
            script_text = content_props["script_text"]
            word_count = len(script_text.split())
            duration = content_props.get("duration_seconds", 30)

            return GeneratedContent(
                content={
                    "script_text": script_text,
                    "duration_seconds": duration,
                    "word_count": word_count,
                    "cta_text": content_props.get("cta_text", ""),
                    "tone_notes": "Passthrough — user-provided script",
                },
                usage={"input_tokens": 0, "output_tokens": 0},
                model="passthrough",
                warnings=[],
                metadata={"spec_id": spec.spec_id, "generator_type": self.generator_type, "passthrough": True},
            )

        return await super().generate(content_props, brand_context, spec, claude_client)
