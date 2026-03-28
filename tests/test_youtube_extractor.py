"""Tests for YouTube transcript extraction (src/extractors/youtube.py)."""

import pytest
from unittest.mock import patch

from src.extractors.youtube import (
    extract_video_id,
    extract_transcript,
    YouTubeExtractionError,
)


class TestExtractVideoId:
    def test_standard_url(self):
        assert extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_short_url(self):
        assert extract_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_embed_url(self):
        assert extract_video_id("https://www.youtube.com/embed/dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_shorts_url(self):
        assert extract_video_id("https://youtube.com/shorts/dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_url_with_extra_params(self):
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=120&list=PLtest"
        assert extract_video_id(url) == "dQw4w9WgXcQ"

    def test_invalid_url_raises(self):
        with pytest.raises(YouTubeExtractionError, match="Could not extract video ID"):
            extract_video_id("https://example.com/not-youtube")

    def test_empty_string_raises(self):
        with pytest.raises(YouTubeExtractionError):
            extract_video_id("")


class TestExtractTranscript:
    @pytest.mark.asyncio
    @patch("src.extractors.youtube.YouTubeTranscriptApi")
    async def test_successful_extraction(self, mock_api):
        mock_api.get_transcript.return_value = [
            {"text": "Hello world", "start": 0.0, "duration": 2.0},
            {"text": "This is a test", "start": 2.0, "duration": 3.0},
        ]
        result = await extract_transcript("https://youtu.be/dQw4w9WgXcQ")
        assert result == "Hello world This is a test"
        mock_api.get_transcript.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.extractors.youtube.YouTubeTranscriptApi")
    async def test_empty_transcript_raises(self, mock_api):
        mock_api.get_transcript.return_value = []
        with pytest.raises(YouTubeExtractionError, match="Empty transcript"):
            await extract_transcript("https://youtu.be/dQw4w9WgXcQ")

    @pytest.mark.asyncio
    @patch("src.extractors.youtube.YouTubeTranscriptApi")
    async def test_api_failure_raises(self, mock_api):
        mock_api.get_transcript.side_effect = Exception("No transcript available")
        with pytest.raises(YouTubeExtractionError, match="Failed to extract"):
            await extract_transcript("https://youtu.be/dQw4w9WgXcQ")

    @pytest.mark.asyncio
    @patch("src.extractors.youtube.YouTubeTranscriptApi")
    async def test_truncation_at_max_chars(self, mock_api):
        long_segment = "This is a sentence. " * 2000  # ~40K chars
        mock_api.get_transcript.return_value = [
            {"text": long_segment, "start": 0.0, "duration": 100.0},
        ]
        result = await extract_transcript(
            "https://youtu.be/dQw4w9WgXcQ", max_chars=1000
        )
        assert len(result) <= 1000
