"""Landing page content generator.

CEX-17: Four template types (lead magnet download, case study, webinar,
demo request), template selection logic, per-template output schemas.
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
# Output schemas (per template type)
# ---------------------------------------------------------------------------

class LandingPageSectionOutput(BaseModel):
    heading: str
    body: str
    bullets: list[str] | None = None
    callout: str | None = None


class LeadMagnetPageOutput(BaseModel):
    headline: str
    subhead: str
    value_props: list[str]
    cta_text: str = "Download Now"


class CaseStudyPageOutput(BaseModel):
    customer_name: str
    headline: str
    sections: list[LandingPageSectionOutput]
    metrics: list[dict]
    quote_text: str | None = None
    quote_author: str | None = None
    quote_title: str | None = None
    cta_text: str = "Get Similar Results"


class WebinarPageOutput(BaseModel):
    event_name: str
    headline: str
    agenda: list[str]
    cta_text: str = "Register Now"


class DemoRequestPageOutput(BaseModel):
    headline: str
    subhead: str
    benefits: list[LandingPageSectionOutput]
    cta_text: str = "Request Demo"


VALID_TEMPLATE_TYPES = {
    "lead_magnet_download",
    "case_study",
    "webinar",
    "demo_request",
}

_OUTPUT_SCHEMAS: dict[str, type[BaseModel]] = {
    "lead_magnet_download": LeadMagnetPageOutput,
    "case_study": CaseStudyPageOutput,
    "webinar": WebinarPageOutput,
    "demo_request": DemoRequestPageOutput,
}


# ---------------------------------------------------------------------------
# Template selection logic
# ---------------------------------------------------------------------------

def select_landing_page_template(brand_context: BrandContext) -> str:
    """Select best landing page template based on context."""
    objective = (brand_context.objective or "").lower()
    angle = (brand_context.angle or "").lower()
    combined = f"{objective} {angle}"

    if any(kw in combined for kw in ("webinar", "event", "registration")):
        return "webinar"
    if any(kw in combined for kw in ("demo", "consultation", "request demo", "trial")):
        return "demo_request"
    if brand_context.case_studies and any(
        kw in combined for kw in ("case study", "customer story", "success story")
    ):
        return "case_study"
    return "lead_magnet_download"


# ---------------------------------------------------------------------------
# Template-specific prompt instructions
# ---------------------------------------------------------------------------

def _lead_magnet_download_instructions(content_props: dict, brand_context: BrandContext) -> str:
    return (
        "TEMPLATE: LEAD MAGNET DOWNLOAD PAGE\n\n"
        "Create a high-converting lead magnet download landing page.\n\n"
        "GENERATE:\n"
        "- headline: Benefit-driven headline communicating the specific value.\n"
        "- subhead: Curiosity-gap subhead, 1-2 sentences.\n"
        "- value_props: 3-4 specific, concrete value propositions.\n"
        "- cta_text: Action-oriented button text (first-person: 'Get My Free Checklist').\n\n"
        "RULES:\n"
        "- Focus on value to the reader, not features\n"
        "- Use specificity — numbers, timeframes, outcomes\n"
        "- Keep subhead under 30 words\n"
    )


def _case_study_instructions(content_props: dict, brand_context: BrandContext) -> str:
    case_study_context = ""
    if brand_context.case_studies:
        cs = brand_context.case_studies[0]
        parts = [f"\nCASE STUDY DATA:\n- Customer: {cs.company or cs.title}"]
        if cs.result:
            parts.append(f"- Results: {cs.result}")
        case_study_context = "\n".join(parts)

    return (
        "TEMPLATE: CASE STUDY PAGE\n\n"
        "Create a compelling case study landing page.\n\n"
        "GENERATE:\n"
        "- customer_name: The customer's company name\n"
        "- headline: 'How [Customer] achieved [Result]' format\n"
        "- sections: 4 narrative sections (Situation → Challenge → Solution → Results)\n"
        "- metrics: 2-4 metric callouts as {value, label}\n"
        "- quote_text, quote_author, quote_title: Customer testimonial if available\n"
        "- cta_text: Outcome-focused CTA\n\n"
        "RULES:\n"
        "- Tell a story, not a sales pitch\n"
        "- Use specific numbers and timelines\n"
        f"{case_study_context}"
    )


def _webinar_instructions(content_props: dict, brand_context: BrandContext) -> str:
    extra = ""
    if content_props.get("speakers"):
        speakers_str = ", ".join(
            s.get("name", "") for s in content_props["speakers"] if isinstance(s, dict)
        )
        extra += f"\nSPEAKERS: {speakers_str}"
    if content_props.get("event_date"):
        extra += f"\nEVENT DATE: {content_props['event_date']}"

    return (
        "TEMPLATE: WEBINAR REGISTRATION PAGE\n\n"
        "Create a webinar registration landing page.\n\n"
        "GENERATE:\n"
        "- event_name: Professional event name\n"
        "- headline: FOMO-driven headline emphasizing what attendees will gain\n"
        "- agenda: 5-7 specific learning outcomes\n"
        "- cta_text: Urgency-driven CTA ('Reserve My Spot')\n\n"
        "RULES:\n"
        "- Focus on what attendees will learn\n"
        "- Create urgency without being pushy\n"
        f"{extra}"
    )


def _demo_request_instructions(content_props: dict, brand_context: BrandContext) -> str:
    return (
        "TEMPLATE: DEMO REQUEST PAGE\n\n"
        "Create a demo request page using problem-agitation-solution structure.\n\n"
        "GENERATE:\n"
        "- headline: Pain-point headline naming the reader's problem\n"
        "- subhead: Agitate then resolve, 1-2 sentences\n"
        "- benefits: 3 benefit sections (heading, body, optional bullets/callout)\n"
        "- cta_text: Low-friction CTA ('See It in Action')\n\n"
        "RULES:\n"
        "- Lead with problems, not features\n"
        "- Each benefit section addresses a different pain point\n"
        "- Include trust signals\n"
    )


_TEMPLATE_BUILDERS = {
    "lead_magnet_download": _lead_magnet_download_instructions,
    "case_study": _case_study_instructions,
    "webinar": _webinar_instructions,
    "demo_request": _demo_request_instructions,
}


# ---------------------------------------------------------------------------
# Generator class
# ---------------------------------------------------------------------------

class LandingPageGenerator(BaseGenerator):
    """Generator for landing page content across 4 template types."""

    generator_type = "landing_page"
    default_model = MODEL_QUALITY
    default_temperature = 0.5
    output_schema = LeadMagnetPageOutput

    def _needs_social_proof(self) -> bool:
        return True

    def build_asset_specific_instructions(
        self, content_props: dict, brand_context: BrandContext, spec: FormatSpec,
    ) -> str:
        template_type = content_props.get("template_type")
        if not template_type:
            template_type = select_landing_page_template(brand_context)

        if template_type not in _TEMPLATE_BUILDERS:
            raise ValueError(
                f"Unknown landing page template '{template_type}'. "
                f"Valid: {sorted(VALID_TEMPLATE_TYPES)}"
            )
        builder = _TEMPLATE_BUILDERS[template_type]
        return builder(content_props, brand_context)

    async def generate(
        self,
        content_props: dict,
        brand_context: BrandContext,
        spec: FormatSpec,
        claude_client: ClaudeClient,
    ) -> GeneratedContent:
        """Generate with correct output schema per template type."""
        template_type = content_props.get("template_type")
        if not template_type:
            template_type = select_landing_page_template(brand_context)

        if template_type not in _OUTPUT_SCHEMAS:
            raise ValueError(
                f"Unknown landing page template '{template_type}'. "
                f"Valid: {sorted(VALID_TEMPLATE_TYPES)}"
            )

        return await super().generate(
            content_props, brand_context, spec, claude_client,
            output_schema_override=_OUTPUT_SCHEMAS[template_type],
        )
