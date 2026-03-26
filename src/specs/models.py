from typing import Any

from pydantic import BaseModel, ConfigDict


class Pipeline(BaseModel):
    generator: str | None = None
    renderer: str | None = None
    provider: str | None = None
    claude_model: str | None = None
    claude_temperature: float | str | None = None
    model_config = ConfigDict(extra="allow")


class Delivery(BaseModel):
    mode: str  # sync | async
    output_format: str
    storage: str | None = None
    model_config = ConfigDict(extra="allow")


class FormatSpec(BaseModel):
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
    model_config = ConfigDict(extra="allow")
