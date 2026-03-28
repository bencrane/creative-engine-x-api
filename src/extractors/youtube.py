"""YouTube transcript extractor.

Extracts plain-text transcripts from YouTube videos using the
youtube-transcript-api library.  Designed as a pre-processing step
for content generators that accept source_content.
"""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Sequence

from youtube_transcript_api import YouTubeTranscriptApi

logger = logging.getLogger(__name__)

# Maximum transcript length in characters (~32K chars ≈ ~8K tokens).
_MAX_TRANSCRIPT_CHARS = 32_000

# Preferred languages in priority order.
_DEFAULT_LANGUAGES = ("en", "en-US", "en-GB")


class YouTubeExtractionError(Exception):
    """Raised when transcript extraction fails."""


def extract_video_id(url: str) -> str:
    """Extract YouTube video ID from various URL formats.

    Supports:
        - https://www.youtube.com/watch?v=VIDEO_ID
        - https://youtu.be/VIDEO_ID
        - https://www.youtube.com/embed/VIDEO_ID
        - https://youtube.com/shorts/VIDEO_ID
    """
    patterns = [
        r"(?:youtube\.com/watch\?.*v=)([a-zA-Z0-9_-]{11})",
        r"(?:youtu\.be/)([a-zA-Z0-9_-]{11})",
        r"(?:youtube\.com/embed/)([a-zA-Z0-9_-]{11})",
        r"(?:youtube\.com/shorts/)([a-zA-Z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    raise YouTubeExtractionError(f"Could not extract video ID from URL: {url}")


async def extract_transcript(
    url: str,
    languages: Sequence[str] = _DEFAULT_LANGUAGES,
    max_chars: int = _MAX_TRANSCRIPT_CHARS,
) -> str:
    """Extract and return plain-text transcript from a YouTube video URL.

    Args:
        url: YouTube video URL (various formats supported).
        languages: Preferred transcript languages in priority order.
        max_chars: Maximum character length for the returned transcript.
                   Truncated at sentence boundary if exceeded.

    Returns:
        Plain-text transcript string.

    Raises:
        YouTubeExtractionError: If video ID cannot be parsed, transcript
            is unavailable, or no transcript exists in the requested languages.
    """
    video_id = extract_video_id(url)

    try:
        loop = asyncio.get_running_loop()
        transcript_list = await loop.run_in_executor(
            None,
            lambda: YouTubeTranscriptApi.get_transcript(
                video_id, languages=list(languages)
            ),
        )
    except Exception as e:
        raise YouTubeExtractionError(
            f"Failed to extract transcript for video '{video_id}': {e}"
        ) from e

    if not transcript_list:
        raise YouTubeExtractionError(
            f"Empty transcript returned for video '{video_id}'"
        )

    # Concatenate text segments into plain text.
    full_text = " ".join(
        segment.get("text", "").strip()
        for segment in transcript_list
        if segment.get("text", "").strip()
    )

    # Truncate if over budget, cutting at a sentence boundary.
    if len(full_text) > max_chars:
        truncated = full_text[:max_chars]
        last_period = truncated.rfind(". ")
        if last_period > max_chars * 0.5:
            truncated = truncated[: last_period + 1]
        full_text = truncated
        logger.warning(
            "Transcript for '%s' truncated to %d chars", video_id, len(full_text)
        )

    return full_text
