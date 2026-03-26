"""Jinja2 template engine wrapper.

CEX-27: Centralises Jinja2 Environment setup for HTML rendering.
Templates live in src/templates/.
"""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


def get_jinja2_env() -> Environment:
    """Return a configured Jinja2 Environment pointing at src/templates/."""
    return Environment(
        loader=FileSystemLoader(str(_TEMPLATES_DIR)),
        autoescape=False,
    )
