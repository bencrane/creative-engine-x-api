"""Case study page content generator.

CEX-21: Transforms raw case study data into polished marketing copy with
4 narrative sections (Situation → Challenge → Solution → Results),
metric callouts, quote formatting. Uses Claude Opus for narrative quality.
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

class CaseStudyNarrativeSection(BaseModel):
    heading: str
    body: str
    bullets: list[str] | None = None


class CaseStudyMetricOutput(BaseModel):
    value: str
    label: str


class CaseStudyContentOutput(BaseModel):
    headline: str
    sections: list[CaseStudyNarrativeSection]
    metrics: list[CaseStudyMetricOutput]
    quote_text: str | None = None
    quote_author: str | None = None
    quote_title: str | None = None
    cta_text: str = "Get Similar Results"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

NARRATIVE_SECTIONS = ("situation", "challenge", "solution", "results")


def _format_case_study_input(cs_data: dict) -> str:
    """Format raw case study data for prompt injection."""
    lines = ["SOURCE CASE STUDY DATA:"]

    for key in ("customer_name", "customer_industry", "company_size", "problem", "solution"):
        val = cs_data.get(key)
        if val:
            label = key.replace("_", " ").title()
            lines.append(f"  {label}: {val}")

    results = cs_data.get("results")
    if results:
        if isinstance(results, dict):
            metrics = ", ".join(f"{k}: {v}" for k, v in results.items())
            lines.append(f"  Results: {metrics}")
        else:
            lines.append(f"  Results: {results}")

    quote = cs_data.get("quote")
    if quote and isinstance(quote, dict):
        q_text = quote.get("text", "")
        q_author = quote.get("author", "")
        q_title = quote.get("title", "")
        if q_text:
            lines.append(f'  Quote: "{q_text}" — {q_author}, {q_title}')
    elif quote and isinstance(quote, str):
        lines.append(f'  Quote: "{quote}"')

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generator class
# ---------------------------------------------------------------------------

class CaseStudyGenerator(BaseGenerator):
    """Generator for case study page content."""

    generator_type = "case_study"
    default_model = MODEL_QUALITY
    default_temperature = 0.6
    output_schema = CaseStudyContentOutput

    def _needs_social_proof(self) -> bool:
        return True

    def build_asset_specific_instructions(
        self, content_props: dict, brand_context: BrandContext, spec: FormatSpec,
    ) -> str:
        parts: list[str] = []

        parts.append(
            "TASK: Generate a compelling B2B case study page that turns raw data "
            "into a persuasive narrative.\n"
        )

        # Inject case study data
        case_study_data = content_props.get("case_study_data")
        case_study_index = content_props.get("case_study_index", 0)

        if case_study_data:
            parts.append(_format_case_study_input(case_study_data))
        elif brand_context.case_studies and case_study_index < len(brand_context.case_studies):
            cs = brand_context.case_studies[case_study_index]
            cs_dict = cs.model_dump() if hasattr(cs, "model_dump") else {"title": str(cs)}
            parts.append(_format_case_study_input(cs_dict))
        else:
            parts.append(
                "CASE STUDY DATA: No case study data available. "
                "Generate a compelling case study based on the company context. "
                "Use plausible but clearly marked placeholder data.\n"
            )

        parts.append(
            "HEADLINE:\n"
            "- Format: 'How [Customer] achieved [Key Result]'\n"
            "- Must be specific and compelling\n"
            "- Avoid generic headlines like 'A Success Story'\n"
        )

        parts.append(
            "NARRATIVE SECTIONS: Generate exactly 4 sections in this order:\n\n"
            "1. SITUATION — Company context, industry, size, goals. 200-400 words.\n"
            "2. CHALLENGE — Specific pain points, cost of status quo. 200-400 words.\n"
            "3. SOLUTION — How the product was used, implementation story. 200-400 words.\n"
            "4. RESULTS — Quantified outcomes with context. 200-400 words.\n"
        )

        parts.append(
            "METRICS:\n"
            "- Extract 2-4 key metrics from the results data\n"
            "- Each metric has 'value' (e.g., '3x', '47%') and 'label' (e.g., 'ROI increase')\n"
            "- Use specific numbers, not vague qualifiers\n"
        )

        parts.append(
            "QUOTE:\n"
            "- If a customer quote is available, include it\n"
            "- Set quote_text, quote_author, quote_title\n"
            "- If no quote is available, set all quote fields to null\n"
            "- Do NOT fabricate quotes\n"
        )

        parts.append(
            "CTA:\n"
            "- Contextual call-to-action text related to the results shown\n"
        )

        parts.append(
            "WRITING RULES:\n"
            "- Third person narrative throughout\n"
            "- Be specific — avoid 'significant improvement' when you can say '47% reduction'\n"
            "- Each section should flow naturally into the next\n"
        )

        return "\n\n".join(parts)
