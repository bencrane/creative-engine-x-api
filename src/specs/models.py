from typing import Any

from pydantic import BaseModel, ConfigDict


class Pipeline(BaseModel):
    model_config = ConfigDict(extra="forbid")

    generator: str | None = None
    renderer: str | None = None
    provider: str | None = None
    claude_model: str | None = None
    claude_temperature: float | str | None = None
    claude_max_tokens: int | None = None
    claude_output_structure: Any = None
    generation_flow: Any = None
    generation_strategy: Any = None
    max_output_tokens: int | None = None
    prompt_caching: Any = None
    steps: Any = None
    structured_output_pattern: Any = None


class Delivery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: str  # sync | async
    output_format: str
    storage: str | None = None
    asset_type_enum: str | None = None
    auth: Any = None
    bucket: str | None = None
    fulfillment: Any = None
    path_pattern: str | None = None
    path_template: str | None = None
    public_url: Any = None
    slug_returned: bool | None = None
    surface_tag: str | None = None
    webhook_on_complete: bool | None = None


class FormatSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    spec_id: str
    artifact_type: str
    surface: str
    version: str
    description: str = ""
    subtype: str | None = None
    constraints: Any = None
    subtypes: dict | None = None
    pipeline: Pipeline | None = None
    delivery: Delivery | None = None
    content_props_schema: dict | None = None
    output_schema: dict | None = None
    acceptance_criteria: Any = None
    brand_context: Any = None
    brief_field_definitions: Any = None
    duration_configs: Any = None
    elevenlabs_provider: Any = None
    example_request: Any = None
    example_response: Any = None
    hosting: Any = None
    platform_formats: Any = None
    platform_guidance: Any = None
    quality_bar: Any = None
    remotion_compositions: Any = None
    renderer: Any = None
    script_segment_schema: Any = None
