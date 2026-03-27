"""Pipeline class registry — maps (artifact_type, surface) to generator/renderer classes.

The YAML spec files reference generators and renderers by inconsistent names (class paths,
short names, library names). This registry provides a reliable mapping from the spec's
routing key to the actual Python classes that implement the pipeline.
"""

from src.generators.ad_copy import AdCopyGenerator
from src.generators.audio_script import AudioScriptGenerator
from src.generators.case_study import CaseStudyGenerator
from src.generators.document_slides import DocumentSlidesGenerator
from src.generators.image_brief import ImageBriefGenerator
from src.generators.landing_page import LandingPageGenerator
from src.generators.lead_magnet import LeadMagnetGenerator
from src.generators.physical_mail import PhysicalMailGenerator
from src.generators.video_script import VideoScriptGenerator

from src.renderers.audio_renderer import AudioRenderer
from src.renderers.html_renderer import HTMLRenderer
from src.renderers.pdf_renderer import PDFRenderer
from src.renderers.slide_renderer import SlideRenderer
from src.renderers.video_renderer import VideoRenderer

# Maps (artifact_type, surface) → generator class
# The generator class is instantiated per-request.
GENERATOR_REGISTRY: dict[tuple[str, str], type] = {
    # structured_text generators (sync, no rendering)
    ("structured_text", "linkedin"): AdCopyGenerator,
    ("structured_text", "meta"): AdCopyGenerator,
    ("structured_text", "google"): AdCopyGenerator,
    ("structured_text", "generic"): ImageBriefGenerator,  # default for generic; subtype resolves below

    # pdf
    ("pdf", "generic"): LeadMagnetGenerator,

    # html_page
    ("html_page", "web"): LandingPageGenerator,

    # document_slides
    ("document_slides", "linkedin"): DocumentSlidesGenerator,

    # audio
    ("audio", "voice_channel"): AudioScriptGenerator,

    # video
    ("video", "generic"): VideoScriptGenerator,
    ("video", "meta"): VideoScriptGenerator,
    ("video", "tiktok"): VideoScriptGenerator,

    # physical_mail
    ("physical_mail", "direct_mail"): PhysicalMailGenerator,
}

# Subtype-level overrides for (artifact_type, surface, subtype)
GENERATOR_SUBTYPE_OVERRIDES: dict[tuple[str, str, str], type] = {
    ("structured_text", "generic", "video_script"): VideoScriptGenerator,
    ("structured_text", "generic", "image_brief"): ImageBriefGenerator,
    ("html_page", "web", "case_study"): CaseStudyGenerator,
}

# Maps (artifact_type, surface) → renderer class (or None for JSON-only)
RENDERER_REGISTRY: dict[tuple[str, str], type | None] = {
    # structured_text — no rendering, JSON output
    ("structured_text", "linkedin"): None,
    ("structured_text", "meta"): None,
    ("structured_text", "google"): None,
    ("structured_text", "generic"): None,

    # pdf
    ("pdf", "generic"): PDFRenderer,

    # html_page
    ("html_page", "web"): HTMLRenderer,

    # document_slides
    ("document_slides", "linkedin"): SlideRenderer,

    # audio
    ("audio", "voice_channel"): AudioRenderer,

    # video
    ("video", "generic"): VideoRenderer,
    ("video", "meta"): VideoRenderer,
    ("video", "tiktok"): VideoRenderer,

    # physical_mail — HTML output via Jinja2 (no PDF step; consumer submits to Lob)
    ("physical_mail", "direct_mail"): None,
}


def resolve_generator(artifact_type: str, surface: str, subtype: str | None = None) -> type:
    """Resolve a generator class for the given routing key."""
    if subtype:
        override = GENERATOR_SUBTYPE_OVERRIDES.get((artifact_type, surface, subtype))
        if override:
            return override
    cls = GENERATOR_REGISTRY.get((artifact_type, surface))
    if cls is None:
        raise ValueError(f"No generator registered for ({artifact_type}, {surface})")
    return cls


def resolve_renderer(artifact_type: str, surface: str) -> type | None:
    """Resolve a renderer class for the given routing key, or None for JSON-only."""
    return RENDERER_REGISTRY.get((artifact_type, surface))
