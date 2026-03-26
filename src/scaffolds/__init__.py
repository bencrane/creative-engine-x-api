"""
Scaffold constraint registry for all Lob mailer formats.

Loads machine-readable JSON constraint files and provides lookup,
filtering, and LLM prompt generation for every supported format+size.
"""

import json
from pathlib import Path
from typing import Any

_SCAFFOLDS_DIR = Path(__file__).parent
_registry: dict[str, dict[str, Any]] = {}


def _load_all() -> None:
    """Load all scaffold JSON files from disk into the registry."""
    if _registry:
        return
    for path in sorted(_SCAFFOLDS_DIR.glob("*.json")):
        data = json.loads(path.read_text())
        _registry[data["slug"]] = data


def all_scaffolds() -> dict[str, dict[str, Any]]:
    """Return the full registry keyed by slug."""
    _load_all()
    return dict(_registry)


def get_by_slug(slug: str) -> dict[str, Any] | None:
    """Look up a single scaffold by its slug (e.g. 'postcard-4x6')."""
    _load_all()
    return _registry.get(slug)


def get_by_format(fmt: str) -> list[dict[str, Any]]:
    """Return all scaffolds matching a format type (e.g. 'postcard', 'selfmailer', 'letter')."""
    _load_all()
    return [s for s in _registry.values() if s["format"] == fmt]


def get_by_plan(plan: str) -> list[dict[str, Any]]:
    """Return all scaffolds available for a plan level ('any' or 'enterprise')."""
    _load_all()
    if plan == "enterprise":
        return list(_registry.values())
    return [s for s in _registry.values() if s["plan"] == "any"]


def list_slugs() -> list[str]:
    """Return all available scaffold slugs."""
    _load_all()
    return sorted(_registry.keys())


def list_formats() -> list[str]:
    """Return all unique format types."""
    _load_all()
    return sorted({s["format"] for s in _registry.values()})


def get_llm_prompt(slug: str, surface_id: str) -> str | None:
    """
    Get the pre-written LLM constraint prompt for a specific scaffold surface.

    Args:
        slug: The scaffold slug (e.g. 'postcard-4x6')
        surface_id: The surface ID (e.g. 'front', 'back', 'outside', 'inside', 'page1', 'pageN')

    Returns:
        The LLM prompt string, or None if not found.
    """
    scaffold = get_by_slug(slug)
    if not scaffold:
        return None
    for surface in scaffold.get("surfaces", []):
        if surface["id"] == surface_id:
            return surface.get("llmPrompt")
    return None


def get_all_llm_prompts(slug: str) -> dict[str, str]:
    """
    Get all LLM constraint prompts for a scaffold, keyed by surface ID.

    Returns:
        Dict mapping surface_id -> llmPrompt (e.g. {'front': '...', 'back': '...'})
    """
    scaffold = get_by_slug(slug)
    if not scaffold:
        return {}
    return {
        surface["id"]: surface["llmPrompt"]
        for surface in scaffold.get("surfaces", [])
        if "llmPrompt" in surface
    }


def get_zones(slug: str, surface_id: str) -> list[dict[str, Any]]:
    """
    Get all zone constraints for a specific surface.

    Returns:
        List of zone dicts with position, size, rule, etc.
    """
    scaffold = get_by_slug(slug)
    if not scaffold:
        return []
    for surface in scaffold.get("surfaces", []):
        if surface["id"] == surface_id:
            return surface.get("zones", [])
    return []


def get_dimensions(slug: str) -> dict[str, Any] | None:
    """Get the dimensions dict for a scaffold (trim, file, bleed info)."""
    scaffold = get_by_slug(slug)
    if not scaffold:
        return None
    return {
        "dimensions": scaffold["dimensions"],
        "bleedModel": scaffold["bleedModel"],
        "safeZone": scaffold.get("safeZone"),
    }


def summary() -> list[dict[str, str]]:
    """Return a compact summary of all scaffolds for listing/selection UIs."""
    _load_all()
    return [
        {
            "slug": s["slug"],
            "displayName": s["displayName"],
            "format": s["format"],
            "plan": s["plan"],
            "surfaces": [surf["id"] for surf in s.get("surfaces", [])],
        }
        for s in _registry.values()
    ]
