"""Generator base class and protocol.

CEX-14: Defines the GeneratorProtocol contract and BaseGenerator abstract base
class that all content generators implement. Handles brand context → system prompt
conversion, spec constraint injection, post-generation validation, and token tracking.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel

from src.brand.models import BrandContext
from src.integrations.claude_client import ClaudeClient, GenerationResult, MODEL_FAST, MODEL_QUALITY
from src.specs.models import FormatSpec

logger = logging.getLogger(__name__)

# Maximum approximate token budget for context injection (~8K tokens ≈ 32K chars)
_MAX_CONTEXT_CHARS = 32_000


@dataclass
class GeneratedContent:
    """Container for generated content with metadata."""

    content: Any  # The structured output (dict or Pydantic model)
    usage: dict = field(default_factory=dict)  # Token usage info
    model: str = ""
    warnings: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


@runtime_checkable
class GeneratorProtocol(Protocol):
    """Protocol defining the generator contract.

    All generators must implement this interface.
    """

    async def generate(
        self,
        content_props: dict,
        brand_context: BrandContext,
        spec: FormatSpec,
        claude_client: ClaudeClient,
    ) -> GeneratedContent: ...


class BaseGenerator(ABC):
    """Abstract base class for all content generators.

    Provides common logic for:
    - Building system prompts from brand context
    - Applying spec constraints to prompts
    - Calling Claude with structured output (tool_use pattern)
    - Post-generation validation against spec constraints
    - Token usage tracking
    """

    # Subclasses set these
    generator_type: str = ""
    default_model: str = MODEL_FAST
    default_temperature: float = 0.7
    output_schema: type[BaseModel] | None = None

    def build_system_prompt(self, brand_context: BrandContext, spec: FormatSpec) -> str:
        """Build system prompt from brand context.

        System prompt structure:
        - Role definition
        - Brand context block
        - Tone and voice guidelines
        - Output rules
        """
        company = brand_context.company_name or "the client"
        asset_label = self.generator_type.replace("_", " ")

        system = (
            f"You are an expert B2B content strategist creating {asset_label} "
            f"content for {company}.\n\n"
        )

        # Brand context block
        brand_block = self._format_brand_context(brand_context)
        if brand_block:
            system += f"BRAND CONTEXT:\n{brand_block}\n\n"

        # Tone and voice
        if brand_context.brand_voice:
            system += f"TONE AND VOICE:\n{brand_context.brand_voice}\n\n"

        # Core rules
        system += (
            "IMPORTANT RULES:\n"
            "- All content must be specific to this company and audience — never generic\n"
            "- Use concrete examples, real numbers, and specific outcomes\n"
            "- Match the brand voice consistently\n"
            "- Focus on value to the reader, not features of the product\n"
        )

        return system

    def build_user_prompt(
        self,
        content_props: dict,
        brand_context: BrandContext,
        spec: FormatSpec,
    ) -> str:
        """Build user prompt with content props, persona context, and asset-specific instructions.

        User prompt structure:
        - Target audience (persona block)
        - Campaign context (angle, objective)
        - Asset-specific instructions (from subclass)
        - Social proof (when needed)
        """
        parts: list[str] = []

        # Persona
        persona_block = self._format_persona(brand_context)
        if persona_block:
            parts.append(f"TARGET AUDIENCE:\n{persona_block}")

        # Campaign context
        campaign_lines = []
        if brand_context.angle:
            campaign_lines.append(f"- Angle: {brand_context.angle}")
        if brand_context.objective:
            campaign_lines.append(f"- Objective: {brand_context.objective}")
        if brand_context.industry:
            campaign_lines.append(f"- Industry: {brand_context.industry}")
        if campaign_lines:
            parts.append("CAMPAIGN CONTEXT:\n" + "\n".join(campaign_lines))

        # Asset-specific instructions from subclass
        specific = self.build_asset_specific_instructions(content_props, brand_context, spec)
        if specific:
            parts.append(specific)

        # Social proof for asset types that need it
        if self._needs_social_proof():
            proof_block = self._format_social_proof(brand_context)
            if proof_block:
                parts.append(f"AVAILABLE SOCIAL PROOF:\n{proof_block}")

        return "\n\n".join(parts)

    @abstractmethod
    def build_asset_specific_instructions(
        self,
        content_props: dict,
        brand_context: BrandContext,
        spec: FormatSpec,
    ) -> str:
        """Return asset-specific instructions for the user prompt.

        Subclasses must implement this with their format-specific prompts.
        """
        ...

    def validate_output(self, content: Any, spec: FormatSpec) -> tuple[Any, list[str]]:
        """Post-generation validation against spec constraints.

        Returns (validated_content, warnings). Override in subclasses for
        custom validation (e.g., character limit truncation).
        """
        return content, []

    async def generate(
        self,
        content_props: dict,
        brand_context: BrandContext,
        spec: FormatSpec,
        claude_client: ClaudeClient,
        output_schema_override: type[BaseModel] | None = None,
    ) -> GeneratedContent:
        """Full generation pipeline: build prompts → call Claude → validate → return."""
        system_prompt = self.build_system_prompt(brand_context, spec)
        user_prompt = self.build_user_prompt(content_props, brand_context, spec)

        # Determine model and temperature
        model = self._resolve_model(spec)
        temperature = self._resolve_temperature(spec)

        # Build tool schema from output_schema if available
        # output_schema_override allows subclasses to pass a per-request schema
        # without mutating self.output_schema (which is unsafe under concurrency)
        effective_schema = output_schema_override or self.output_schema
        tools = None
        tool_choice = None
        if effective_schema is not None:
            schema = effective_schema.model_json_schema()
            tool_name = f"generate_{self.generator_type}"
            tools = [
                {
                    "name": tool_name,
                    "description": f"Generate {self.generator_type.replace('_', ' ')} content",
                    "input_schema": schema,
                }
            ]
            tool_choice = {"type": "tool", "name": tool_name}

        # Call Claude
        result = await claude_client.generate(
            messages=[{"role": "user", "content": user_prompt}],
            system=system_prompt,
            model=model,
            temperature=temperature,
            max_tokens=self._resolve_max_tokens(spec),
            tools=tools,
            tool_choice=tool_choice,
        )

        # Parse and validate
        content = result.content
        warnings: list[str] = []

        # Validate against spec constraints
        content, validation_warnings = self.validate_output(content, spec)
        warnings.extend(validation_warnings)

        return GeneratedContent(
            content=content,
            usage={
                "input_tokens": result.usage.input_tokens,
                "output_tokens": result.usage.output_tokens,
                "cache_creation_input_tokens": result.usage.cache_creation_input_tokens,
                "cache_read_input_tokens": result.usage.cache_read_input_tokens,
            },
            model=result.model,
            warnings=warnings,
            metadata={
                "spec_id": spec.spec_id,
                "generator_type": self.generator_type,
            },
        )

    def _needs_social_proof(self) -> bool:
        """Override in subclasses that need social proof in prompts."""
        return self.generator_type in {
            "landing_page",
            "case_study",
            "document_slides",
            "lead_magnet",
        }

    def _resolve_model(self, spec: FormatSpec) -> str:
        """Resolve which Claude model to use."""
        if spec.pipeline and spec.pipeline.claude_model:
            return spec.pipeline.claude_model
        return self.default_model

    def _resolve_temperature(self, spec: FormatSpec) -> float:
        """Resolve generation temperature."""
        if spec.pipeline and spec.pipeline.claude_temperature is not None:
            temp = spec.pipeline.claude_temperature
            if isinstance(temp, (int, float)):
                return float(temp)
        return self.default_temperature

    def _resolve_max_tokens(self, spec: FormatSpec) -> int:
        """Resolve max output tokens."""
        if spec.pipeline and spec.pipeline.claude_max_tokens:
            return spec.pipeline.claude_max_tokens
        if spec.pipeline and spec.pipeline.max_output_tokens:
            return spec.pipeline.max_output_tokens
        return 4096

    def _format_brand_context(self, ctx: BrandContext) -> str:
        """Format brand context as a structured text block for system prompts."""
        lines = []
        if ctx.company_name:
            lines.append(f"COMPANY: {ctx.company_name}")
        if ctx.value_proposition:
            lines.append(f"VALUE PROPOSITION: {ctx.value_proposition}")
        if ctx.brand_voice:
            lines.append(f"BRAND VOICE: {ctx.brand_voice}")
        if ctx.brand_guidelines:
            bg = ctx.brand_guidelines
            for key in ("tone", "messaging_pillars", "dos", "donts", "key_messages"):
                val = getattr(bg, key, None)
                if val is None and isinstance(bg, BaseModel) and bg.model_extra:
                    val = bg.model_extra.get(key)
                if val:
                    if isinstance(val, list):
                        val = "; ".join(str(v) for v in val)
                    lines.append(f"{key.upper().replace('_', ' ')}: {val}")
        if ctx.competitor_differentiators:
            lines.append(
                "KEY DIFFERENTIATORS:\n- " + "\n- ".join(ctx.competitor_differentiators)
            )

        block = "\n".join(lines)
        return _truncate_block(block, "brand context")

    def _format_persona(self, ctx: BrandContext) -> str:
        """Format ICP/persona context for user prompts."""
        lines = []
        if ctx.target_persona:
            lines.append(ctx.target_persona)
        if ctx.icp_definition:
            icp = ctx.icp_definition
            for key in ("seniority", "buying_triggers", "objections"):
                val = getattr(icp, key, None)
                if val is None and isinstance(icp, BaseModel) and icp.model_extra:
                    val = icp.model_extra.get(key)
                if val:
                    if isinstance(val, list):
                        val = "; ".join(str(v) for v in val)
                    lines.append(f"{key.upper().replace('_', ' ')}: {val}")

        block = "\n".join(lines)
        return _truncate_block(block, "persona")

    def _format_social_proof(self, ctx: BrandContext) -> str:
        """Format case studies, testimonials, logos for content generation."""
        lines = []

        if ctx.case_studies:
            lines.append("CASE STUDIES:")
            for cs in ctx.case_studies[:3]:
                title = cs.title if hasattr(cs, "title") else str(cs)
                company = cs.company if hasattr(cs, "company") else ""
                result = cs.result if hasattr(cs, "result") else ""
                entry = f"- {title}"
                if company:
                    entry += f" ({company})"
                if result:
                    entry += f": {result}"
                lines.append(entry)

        if ctx.testimonials:
            lines.append("\nTESTIMONIALS:")
            for t in ctx.testimonials[:3]:
                quote = t.quote if hasattr(t, "quote") else str(t)
                author = t.author if hasattr(t, "author") else ""
                role = t.role if hasattr(t, "role") else ""
                if quote:
                    attribution = f" — {author}, {role}" if author else ""
                    lines.append(f'- "{quote}"{attribution}')

        if ctx.customer_logos:
            lines.append(
                f"\nCUSTOMER LOGOS: {len(ctx.customer_logos)} logos available"
            )

        block = "\n".join(lines)
        return _truncate_block(block, "social proof")


def _truncate_block(text: str, label: str, max_chars: int = 10_000) -> str:
    """Truncate a context block if it exceeds the character budget."""
    if len(text) <= max_chars:
        return text
    logger.warning(
        "Context block '%s' truncated: %d chars → %d chars",
        label,
        len(text),
        max_chars,
    )
    return text[:max_chars] + "\n[...truncated]"
