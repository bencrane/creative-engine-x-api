"""HTML renderer for landing pages.

CEX-27: Renders landing page HTML using Jinja2 templates and brand context.
Supports 4 templates: lead_magnet_download, case_study, webinar, demo_request.
"""

from __future__ import annotations

import logging

from src.brand.models import BrandContext
from src.config import settings
from src.generators.base import GeneratedContent
from src.providers.jinja2_provider import get_jinja2_env
from src.renderers.base import RenderedArtifact
from src.specs.models import FormatSpec

logger = logging.getLogger(__name__)

VALID_TEMPLATES = {
    "lead_magnet_download",
    "case_study",
    "webinar",
    "demo_request",
}


class HTMLRenderer:
    """Render landing page HTML from Jinja2 templates with branding.

    Implements RendererProtocol. Expects content.content to have:
    - template: str (one of the 4 template names)
    - slug: str
    - Plus template-specific fields (headline, subhead, form_fields, etc.)
    """

    async def render(
        self,
        content: GeneratedContent,
        spec: FormatSpec,
        brand_context: BrandContext,
    ) -> RenderedArtifact:
        data = content.content
        if isinstance(data, dict):
            template_name = data.get("template", "lead_magnet_download")
            slug = data.get("slug", "")
            template_vars = dict(data)
        else:
            template_name = getattr(data, "template", "lead_magnet_download")
            slug = getattr(data, "slug", "")
            template_vars = data.__dict__.copy() if hasattr(data, "__dict__") else {}

        if template_name not in VALID_TEMPLATES:
            template_name = "lead_magnet_download"

        # Build branding dict for template
        bg = brand_context.brand_guidelines
        branding = {
            "primary_color": bg.primary_color if bg else "#00e87b",
            "secondary_color": bg.secondary_color if bg else "#09090b",
            "font_family": bg.font_family if bg else "Inter, sans-serif",
            "company_name": brand_context.company_name or "",
            "logo_url": bg.logo_url if bg else "",
        }

        # Build tracking dict for template
        tracking = {
            "rudderstack_write_key": settings.rudderstack_write_key or "",
            "rudderstack_data_plane_url": settings.rudderstack_data_plane_url or "",
        }

        # Render template
        env = get_jinja2_env()
        template = env.get_template(f"{template_name}.html")
        html = template.render(
            slug=slug,
            branding=branding,
            tracking=tracking,
            **{k: v for k, v in template_vars.items() if k not in ("template", "slug", "branding", "tracking")},
        )

        html_bytes = html.encode("utf-8")

        return RenderedArtifact(
            data=html_bytes,
            content_type="text/html",
            filename=f"{slug or template_name}.html",
            metadata={
                "template": template_name,
                "renderer": "html",
            },
        )
