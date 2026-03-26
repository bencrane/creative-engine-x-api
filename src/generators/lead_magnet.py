"""Lead Magnet PDF content generator.

CEX-16: Five format-specific prompt templates, two-pass generation for long
formats, industry vertical handling. Constraints from spec YAML.
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

class LeadMagnetSectionOutput(BaseModel):
    heading: str
    body: str
    bullets: list[str] = Field(default_factory=list)
    callout_box: str | None = None


class LeadMagnetOutput(BaseModel):
    title: str
    subtitle: str
    sections: list[LeadMagnetSectionOutput]


# ---------------------------------------------------------------------------
# Industry vertical guidance
# ---------------------------------------------------------------------------

INDUSTRY_GUIDANCE: dict[str, str] = {
    "SaaS": (
        "INDUSTRY GUIDANCE (Tech/SaaS):\n"
        "- Tone: Casual-professional, technical but accessible\n"
        "- Include tool recommendations, integration references, and metric-driven examples\n"
        "- Use concrete SaaS metrics (MRR, churn, NRR, CAC payback) where relevant\n"
        "- CTA: Free trial, demo request, or 'Talk to an engineer'"
    ),
    "Healthcare": (
        "INDUSTRY GUIDANCE (Healthcare):\n"
        "- Tone: Formal, evidence-based, patient-safety awareness throughout\n"
        "- Reference relevant regulations (HIPAA, FDA, HITECH) where applicable\n"
        "- Use clinical language and cite peer-reviewed sources when possible\n"
        "- CTA: Consultation, white paper download, or ROI calculator"
    ),
    "Financial Services": (
        "INDUSTRY GUIDANCE (Financial Services):\n"
        "- Tone: Conservative, precise, data-heavy\n"
        "- Reference regulatory bodies (FinCEN, OCC, SEC, CFPB) as appropriate\n"
        "- Emphasize risk management, compliance, and quantifiable outcomes\n"
        "- CTA: Consultation, assessment, or custom report"
    ),
    "Manufacturing": (
        "INDUSTRY GUIDANCE (Manufacturing):\n"
        "- Tone: Practical, ROI-focused, process-oriented\n"
        "- Use quality/safety language (Six Sigma, ISO, lean manufacturing)\n"
        "- Include process flow references, measurement criteria, and ROI calculations\n"
        "- CTA: Plant tour, ROI assessment, or pilot program"
    ),
}

# ---------------------------------------------------------------------------
# Format-specific prompt instructions
# ---------------------------------------------------------------------------

FORMAT_INSTRUCTIONS: dict[str, str] = {
    "checklist": (
        "FORMAT: CHECKLIST\n\n"
        "Create a B2B checklist lead magnet:\n"
        "- 4–6 category sections, each with a descriptive heading\n"
        "- 15–25 total checklist items across all sections\n"
        "- Total word count: 2,000–4,000 words\n\n"
        "Each section: heading, brief intro body, bullets (checklist items starting with "
        "imperative action verbs), optional callout_box with pro tip or key stat.\n"
        "Every item must be specific enough to act on immediately.\n"
    ),
    "ultimate_guide": (
        "FORMAT: ULTIMATE GUIDE\n\n"
        "Create a comprehensive B2B ultimate guide:\n"
        "- 5 chapters, each 800–1,800 words\n"
        "- Total word count: 5,500–8,500 words\n"
        "- Chapter progression: Foundations → Framework → Tactical How-To → "
        "Advanced Strategies → Future Trends\n\n"
        "Each section: chapter title heading, educational prose body with concrete "
        "examples and data, 3-5 key takeaway bullets, callout_box with stat or insight.\n"
        "Write from deep expertise. Avoid buzzwords.\n"
    ),
    "benchmark_report": (
        "FORMAT: BENCHMARK REPORT\n\n"
        "Create a data-driven benchmark report:\n"
        "- Executive summary + 3–5 metric sections + Recommendations\n"
        "- Total word count: 4,000–8,000 words\n\n"
        "Each section: metric category heading, analytical narrative body, key findings "
        "bullets, callout_box with large stat. Lead with surprising findings.\n"
        "Only use statistics provided in context. Do not fabricate numbers.\n"
    ),
    "template_toolkit": (
        "FORMAT: TEMPLATE / TOOLKIT\n\n"
        "Create a practical template toolkit:\n"
        "- Introduction + 4–6 template sections\n"
        "- Total word count: 3,000–6,000 words\n\n"
        "Each section: template name heading, instructions and context body with "
        "[placeholders], numbered step bullets, optional callout_box with pro tips.\n"
        "Every template must be immediately usable.\n"
    ),
    "state_of_industry": (
        "FORMAT: STATE OF THE INDUSTRY REPORT\n\n"
        "Create an authoritative industry report:\n"
        "- Executive summary + 4–6 findings + Implications\n"
        "- Total word count: 6,000–10,000 words\n\n"
        "Each section: declarative finding heading, analytical narrative body, "
        "implication bullets, callout_box with big number. Position as thought leadership.\n"
        "Only use provided data. Include 12-24 month predictions grounded in evidence.\n"
    ),
}

VALID_FORMATS = set(FORMAT_INSTRUCTIONS.keys())


# ---------------------------------------------------------------------------
# Format selection helper
# ---------------------------------------------------------------------------

def select_lead_magnet_format(angle: str, objective: str, industry: str) -> str:
    """Suggest best lead magnet format based on campaign context."""
    combined = f"{(angle or '').lower()} {(objective or '').lower()} {(industry or '').lower()}"

    scores: dict[str, int] = {fmt: 0 for fmt in VALID_FORMATS}

    for kw in ("compliance", "audit", "checklist", "launch", "onboarding", "security", "setup"):
        if kw in combined:
            scores["checklist"] += 2
    for kw in ("guide", "education", "how to", "learn", "comprehensive", "strategy"):
        if kw in combined:
            scores["ultimate_guide"] += 2
    for kw in ("benchmark", "data", "metrics", "performance", "comparison", "analytics"):
        if kw in combined:
            scores["benchmark_report"] += 2
    for kw in ("template", "toolkit", "framework", "worksheet", "planner", "calculator"):
        if kw in combined:
            scores["template_toolkit"] += 2
    for kw in ("state of", "trends", "industry", "forecast", "outlook", "market", "survey"):
        if kw in combined:
            scores["state_of_industry"] += 2

    return max(scores, key=lambda k: (scores[k], k == "checklist"))


# ---------------------------------------------------------------------------
# Generator class
# ---------------------------------------------------------------------------

class LeadMagnetGenerator(BaseGenerator):
    """Generator for lead magnet PDF content across 5 formats."""

    generator_type = "lead_magnet"
    default_model = MODEL_QUALITY
    default_temperature = 0.5
    output_schema = LeadMagnetOutput

    def _needs_social_proof(self) -> bool:
        return True

    def build_asset_specific_instructions(
        self, content_props: dict, brand_context: BrandContext, spec: FormatSpec,
    ) -> str:
        fmt = content_props.get("format", content_props.get("subtype", "checklist"))
        if fmt not in FORMAT_INSTRUCTIONS:
            raise ValueError(f"Unknown lead magnet format '{fmt}'. Valid: {sorted(VALID_FORMATS)}")

        parts: list[str] = [FORMAT_INSTRUCTIONS[fmt]]

        # Industry guidance
        industry = content_props.get("industry", brand_context.industry or "")
        if industry in INDUSTRY_GUIDANCE:
            parts.append(INDUSTRY_GUIDANCE[industry])
        elif industry:
            parts.append(f"INDUSTRY CONTEXT: {industry} — tailor examples and language accordingly.")

        # Topic
        if content_props.get("topic"):
            parts.append(f"TOPIC: {content_props['topic']}")
        if content_props.get("target_audience"):
            parts.append(f"TARGET AUDIENCE: {content_props['target_audience']}")
        if content_props.get("key_points"):
            points = "\n".join(f"- {p}" for p in content_props["key_points"])
            parts.append(f"KEY POINTS TO INCLUDE:\n{points}")

        return "\n\n".join(parts)

    def _get_format_config(self, content_props: dict, spec: FormatSpec) -> dict:
        """Get format config from spec subtypes."""
        fmt = content_props.get("format", content_props.get("subtype", "checklist"))
        if spec.subtypes and fmt in spec.subtypes:
            return spec.subtypes[fmt]
        return {}

    async def generate(
        self,
        content_props: dict,
        brand_context: BrandContext,
        spec: FormatSpec,
        claude_client: ClaudeClient,
    ) -> GeneratedContent:
        """Generate lead magnet content, using two-pass for long formats."""
        fmt = content_props.get("format", content_props.get("subtype", "checklist"))
        fmt_config = self._get_format_config(content_props, spec)

        # Override temperature per format from spec
        original_temp = self.default_temperature
        if fmt_config.get("claude_temperature") is not None:
            self.default_temperature = float(fmt_config["claude_temperature"])

        try:
            is_two_pass = fmt_config.get("two_pass", False) or fmt in ("ultimate_guide", "state_of_industry")

            if is_two_pass:
                return await self._two_pass_generate(content_props, brand_context, spec, claude_client)
            else:
                return await super().generate(content_props, brand_context, spec, claude_client)
        finally:
            self.default_temperature = original_temp

    async def _two_pass_generate(
        self,
        content_props: dict,
        brand_context: BrandContext,
        spec: FormatSpec,
        claude_client: ClaudeClient,
    ) -> GeneratedContent:
        """Two-pass generation: outline first, then expand."""
        system_prompt = self.build_system_prompt(brand_context, spec)
        user_prompt = self.build_user_prompt(content_props, brand_context, spec)

        model = self._resolve_model(spec)
        temperature = self._resolve_temperature(spec)

        tools = None
        tool_choice = None
        if self.output_schema is not None:
            schema = self.output_schema.model_json_schema()
            tool_name = f"generate_{self.generator_type}"
            tools = [{"name": tool_name, "description": "Generate lead magnet content", "input_schema": schema}]
            tool_choice = {"type": "tool", "name": tool_name}

        # Pass 1: Generate outline
        outline_prompt = (
            user_prompt
            + "\n\nIMPORTANT: For this first pass, generate ONLY an outline.\n"
            "Return abbreviated content: full title and subtitle, but for each section "
            "include only the heading and a 2-3 sentence summary in the body. "
            "Bullets should be 3-5 key points to be expanded. callout_box should be null.\n"
        )

        outline_result = await claude_client.generate(
            messages=[{"role": "user", "content": outline_prompt}],
            system=system_prompt,
            model=model,
            temperature=max(temperature - 0.1, 0.0),
            max_tokens=self._resolve_max_tokens(spec),
            tools=tools,
            tool_choice=tool_choice,
        )

        # Build outline summary
        outline_content = outline_result.content
        outline_summary = ""
        if isinstance(outline_content, dict) and "sections" in outline_content:
            outline_summary = "\n".join(
                f"- {s.get('heading', '')}: {s.get('body', '')}"
                for s in outline_content["sections"]
            )

        # Pass 2: Expand
        expand_prompt = (
            user_prompt
            + f"\n\nOUTLINE (expand each section fully):\n{outline_summary}\n\n"
            "Now generate the COMPLETE content. Write full prose, detailed bullets, "
            "and callout boxes. Maintain section order from the outline. "
            "Do not abbreviate — write the full word count for each section."
        )

        result = await claude_client.generate(
            messages=[{"role": "user", "content": expand_prompt}],
            system=system_prompt,
            model=model,
            temperature=temperature,
            max_tokens=self._resolve_max_tokens(spec),
            tools=tools,
            tool_choice=tool_choice,
        )

        # Combine token usage
        total_input = outline_result.usage.input_tokens + result.usage.input_tokens
        total_output = outline_result.usage.output_tokens + result.usage.output_tokens

        content = result.content
        content, validation_warnings = self.validate_output(content, spec)

        return GeneratedContent(
            content=content,
            usage={
                "input_tokens": total_input,
                "output_tokens": total_output,
                "passes": 2,
            },
            model=result.model,
            warnings=validation_warnings,
            metadata={"spec_id": spec.spec_id, "generator_type": self.generator_type, "two_pass": True},
        )
