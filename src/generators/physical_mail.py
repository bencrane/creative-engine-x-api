"""Physical mail content generator.

CEX-23: Generates content for postcards and letters. NEW generator
(not ported from paid-engine-x). Uses Claude Sonnet for short-form copy.
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

class PostcardOutput(BaseModel):
    headline: str = Field(..., description="Max 50 chars for 4x6, 60 chars for 6x9")
    body_copy: str = Field(..., description="Max 200 chars for 4x6, 400 chars for 6x9")
    cta_text: str = Field(..., description="Clear call-to-action")
    subtype: str = Field(default="postcard_4x6")


class LetterOutput(BaseModel):
    salutation: str = Field(..., description="Personal greeting")
    body_paragraphs: list[str] = Field(..., min_length=2, max_length=3)
    cta_text: str = Field(..., description="Clear call-to-action")
    sign_off: str = Field(..., description="Professional closing")
    sender_name: str = Field(default="")


class PhysicalMailOutput(BaseModel):
    mail_type: str = Field(..., description="postcard_4x6, postcard_6x9, or letter")
    postcard: PostcardOutput | None = None
    letter: LetterOutput | None = None


# ---------------------------------------------------------------------------
# Subtype configs
# ---------------------------------------------------------------------------

VALID_SUBTYPES = {"postcard_4x6", "postcard_6x9", "letter"}

SUBTYPE_CONFIGS = {
    "postcard_4x6": {
        "label": "Postcard 4×6",
        "headline_max": 50,
        "body_max": 200,
        "description": "Standard USPS postcard. High visual impact, short message.",
    },
    "postcard_6x9": {
        "label": "Postcard 6×9",
        "headline_max": 60,
        "body_max": 400,
        "description": "Large format postcard. More room for messaging.",
    },
    "letter": {
        "label": "Letter 8.5×11",
        "body_words": "250-400",
        "paragraphs": "2-3",
        "description": "Formal letter format with salutation, body paragraphs, and sign-off.",
    },
}


# ---------------------------------------------------------------------------
# Generator class
# ---------------------------------------------------------------------------

class PhysicalMailGenerator(BaseGenerator):
    """Generator for physical mail content (postcards and letters)."""

    generator_type = "physical_mail"
    default_model = MODEL_FAST
    default_temperature = 0.4
    output_schema = PhysicalMailOutput

    def build_asset_specific_instructions(
        self, content_props: dict, brand_context: BrandContext, spec: FormatSpec,
    ) -> str:
        subtype = content_props.get("subtype", "postcard_4x6")
        if subtype not in VALID_SUBTYPES:
            raise ValueError(f"Unknown mail subtype '{subtype}'. Valid: {sorted(VALID_SUBTYPES)}")

        config = SUBTYPE_CONFIGS[subtype]

        parts: list[str] = []

        parts.append(
            f"TASK: Generate content for a {config['label']} direct mail piece.\n\n"
            f"Set mail_type to '{subtype}'.\n"
        )

        if subtype.startswith("postcard"):
            parts.append(
                f"FORMAT: {config['label'].upper()}\n"
                f"Description: {config['description']}\n\n"
                "GENERATE (populate the 'postcard' field):\n"
                f"- headline: Max {config['headline_max']} characters. Bold, attention-grabbing.\n"
                f"- body_copy: Max {config['body_max']} characters. Concise value proposition.\n"
                "- cta_text: Clear, actionable CTA (e.g., 'Scan to claim your free audit').\n"
                f"- subtype: '{subtype}'\n\n"
                "RULES:\n"
                "- Direct, personal tone — physical mail should feel human\n"
                "- High-contrast headline for visual impact\n"
                "- Single CTA — don't dilute with multiple asks\n"
                "- Copy must fit within print safe area\n"
            )
        else:
            parts.append(
                "FORMAT: LETTER (8.5×11)\n"
                f"Description: {config['description']}\n\n"
                "GENERATE (populate the 'letter' field):\n"
                "- salutation: Personal greeting (e.g., 'Dear [Name],' or 'Hi [Name],')\n"
                f"- body_paragraphs: {config['paragraphs']} paragraphs, {config['body_words']} words total.\n"
                "  - Paragraph 1: Why you're writing — hook and value statement\n"
                "  - Paragraph 2: Supporting evidence or specific benefit\n"
                "  - Paragraph 3 (optional): Social proof or urgency\n"
                "- cta_text: Clear call-to-action\n"
                "- sign_off: Professional closing (e.g., 'Best regards,' or 'Sincerely,')\n"
                "- sender_name: Name of the sender\n\n"
                "RULES:\n"
                "- Tone: Personal, direct, not mass-produced\n"
                "- Write as if one person is writing to another\n"
                "- Avoid marketing jargon\n"
                "- The letter should feel like it deserves to be read, not recycled\n"
            )

        if content_props.get("topic"):
            parts.append(f"TOPIC: {content_props['topic']}")
        if content_props.get("recipient_name"):
            parts.append(f"RECIPIENT: {content_props['recipient_name']}")
        if content_props.get("sender_name"):
            parts.append(f"SENDER: {content_props['sender_name']}")
        if content_props.get("offer"):
            parts.append(f"OFFER: {content_props['offer']}")

        return "\n\n".join(parts)

    def validate_output(self, content: Any, spec: FormatSpec) -> tuple[Any, list[str]]:
        """Enforce character limits for postcards."""
        warnings: list[str] = []
        if not isinstance(content, dict):
            return content, warnings

        postcard = content.get("postcard")
        if postcard and isinstance(postcard, dict):
            subtype = postcard.get("subtype", content.get("mail_type", "postcard_4x6"))
            config = SUBTYPE_CONFIGS.get(subtype, SUBTYPE_CONFIGS["postcard_4x6"])

            headline = postcard.get("headline", "")
            headline_max = config.get("headline_max", 50)
            if len(headline) > headline_max:
                postcard["headline"] = headline[:headline_max]
                warnings.append(f"headline truncated to {headline_max} chars")

            body = postcard.get("body_copy", "")
            body_max = config.get("body_max", 200)
            if len(body) > body_max:
                postcard["body_copy"] = body[:body_max]
                warnings.append(f"body_copy truncated to {body_max} chars")

        return content, warnings
