"""Shared text utilities for generators and renderers."""


def truncate_at_word_boundary(text: str, max_chars: int) -> str:
    """Truncate text at the nearest word boundary, respecting max_chars.

    Returns the original text if it's within the limit. Otherwise, cuts at the
    last space before the limit so output never ends mid-word.
    """
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    last_space = truncated.rfind(" ")
    if last_space > 0:
        truncated = truncated[:last_space]
    return truncated
