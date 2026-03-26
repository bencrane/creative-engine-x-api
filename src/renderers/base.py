"""Renderer base protocol and artifact container.

CEX-24: Defines the RendererProtocol contract that all renderers implement,
and the RenderedArtifact dataclass for renderer output.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from src.brand.models import BrandContext
from src.generators.base import GeneratedContent
from src.specs.models import FormatSpec


@dataclass
class RenderedArtifact:
    """Container for rendered output with metadata."""

    data: bytes
    content_type: str
    filename: str
    metadata: dict | None = None


@runtime_checkable
class RendererProtocol(Protocol):
    """Protocol defining the renderer contract.

    All renderers must implement this interface.
    """

    async def render(
        self,
        content: GeneratedContent,
        spec: FormatSpec,
        brand_context: BrandContext,
    ) -> RenderedArtifact: ...
