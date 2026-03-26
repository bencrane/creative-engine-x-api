"""Tests for the Remotion Lambda provider (CEX-33)."""

from __future__ import annotations

import json
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.providers.remotion_provider import (
    DEFAULT_CODEC,
    DEFAULT_FRAMES_PER_LAMBDA,
    DEFAULT_PRIVACY,
    MAX_RETRIES,
    RemotionProvider,
    ProviderResult,
)
from src.shared.errors import ValidationError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FAKE_FUNCTION_NAME = "remotion-render-test-fn"
FAKE_SERVE_URL = "https://remotionlambda-test.s3.amazonaws.com/sites/creative-engine-x"
FAKE_REGION = "us-east-1"
FAKE_RENDER_ID = "abc123def456"
FAKE_BUCKET_NAME = "remotionlambda-test-bucket"


def _make_lambda_response(payload: dict, function_error: str | None = None) -> dict:
    response = {
        "StatusCode": 200,
        "Payload": BytesIO(json.dumps(payload).encode()),
    }
    if function_error:
        response["FunctionError"] = function_error
    return response


def _make_provider(lambda_client: MagicMock | None = None, **kwargs) -> RemotionProvider:
    defaults = {
        "function_name": FAKE_FUNCTION_NAME,
        "serve_url": FAKE_SERVE_URL,
        "region": FAKE_REGION,
        "lambda_client": lambda_client or _mock_lambda_client(),
    }
    defaults.update(kwargs)
    return RemotionProvider(**defaults)


def _mock_lambda_client(
    render_response: dict | None = None,
    progress_response: dict | None = None,
) -> MagicMock:
    mock = MagicMock()

    if render_response is None:
        render_response = {
            "renderId": FAKE_RENDER_ID,
            "bucketName": FAKE_BUCKET_NAME,
        }

    def invoke_side_effect(**kwargs):
        payload = json.loads(kwargs["Payload"])
        if payload.get("type") == "status":
            resp = progress_response or {
                "done": False,
                "overallProgress": 0.5,
                "outputFile": None,
                "fatalErrorEncountered": False,
                "errors": [],
            }
        else:
            resp = render_response
        return _make_lambda_response(resp)

    mock.invoke = MagicMock(side_effect=invoke_side_effect)
    return mock


# ---------------------------------------------------------------------------
# Tests: ProviderResult dataclass
# ---------------------------------------------------------------------------

class TestProviderResult:
    def test_basic_creation(self):
        result = ProviderResult(
            data={"render_id": "abc"},
            content_type="video/mp4",
            metadata={"codec": "h264"},
        )
        assert result.data["render_id"] == "abc"
        assert result.content_type == "video/mp4"
        assert result.metadata["codec"] == "h264"


# ---------------------------------------------------------------------------
# Tests: Input validation
# ---------------------------------------------------------------------------

class TestRemotionProviderValidation:
    async def test_rejects_missing_composition_id(self):
        provider = _make_provider()
        with pytest.raises(ValidationError, match="composition_id is required"):
            await provider.execute({"input_props": {}})

    async def test_rejects_empty_function_name(self):
        provider = _make_provider(function_name="")
        with pytest.raises(ValidationError, match="function name not configured"):
            await provider.execute({"composition_id": "test"})

    async def test_rejects_empty_serve_url(self):
        provider = _make_provider(serve_url="")
        with pytest.raises(ValidationError, match="serve URL not configured"):
            await provider.execute({"composition_id": "test"})


# ---------------------------------------------------------------------------
# Tests: Successful render trigger
# ---------------------------------------------------------------------------

class TestRemotionProviderSuccess:
    async def test_returns_provider_result_with_render_id(self):
        provider = _make_provider()
        result = await provider.execute({
            "composition_id": "meta-ad-1x1",
            "input_props": {"scenes": [], "brand": {}, "cta_text": "CTA"},
        })

        assert isinstance(result, ProviderResult)
        assert result.data["render_id"] == FAKE_RENDER_ID
        assert result.data["bucket_name"] == FAKE_BUCKET_NAME
        assert result.content_type == "video/mp4"

    async def test_metadata_includes_composition_and_codec(self):
        provider = _make_provider()
        result = await provider.execute({
            "composition_id": "tiktok-ad",
            "input_props": {},
        })

        assert result.metadata["composition_id"] == "tiktok-ad"
        assert result.metadata["codec"] == DEFAULT_CODEC
        assert result.metadata["render_id"] == FAKE_RENDER_ID

    async def test_custom_codec(self):
        mock_client = _mock_lambda_client()
        provider = _make_provider(lambda_client=mock_client)

        await provider.execute({
            "composition_id": "meta-ad-1x1",
            "input_props": {},
            "codec": "h265",
        })

        call_args = mock_client.invoke.call_args
        payload = json.loads(call_args.kwargs["Payload"])
        assert payload["codec"] == "h265"

    async def test_custom_out_name(self):
        mock_client = _mock_lambda_client()
        provider = _make_provider(lambda_client=mock_client)

        await provider.execute({
            "composition_id": "meta-ad-1x1",
            "input_props": {},
            "out_name": "custom-output.mp4",
        })

        call_args = mock_client.invoke.call_args
        payload = json.loads(call_args.kwargs["Payload"])
        assert payload["outName"] == "custom-output.mp4"


# ---------------------------------------------------------------------------
# Tests: Lambda invocation
# ---------------------------------------------------------------------------

class TestRemotionProviderLambdaCall:
    async def test_invokes_correct_function(self):
        mock_client = _mock_lambda_client()
        provider = _make_provider(lambda_client=mock_client)

        await provider.execute({
            "composition_id": "meta-ad-1x1",
            "input_props": {},
        })

        call_kwargs = mock_client.invoke.call_args.kwargs
        assert call_kwargs["FunctionName"] == FAKE_FUNCTION_NAME
        assert call_kwargs["InvocationType"] == "RequestResponse"

    async def test_payload_includes_serve_url(self):
        mock_client = _mock_lambda_client()
        provider = _make_provider(lambda_client=mock_client)

        await provider.execute({
            "composition_id": "meta-ad-1x1",
            "input_props": {"key": "value"},
        })

        payload = json.loads(mock_client.invoke.call_args.kwargs["Payload"])
        assert payload["serveUrl"] == FAKE_SERVE_URL
        assert payload["inputProps"] == {"key": "value"}
        assert payload["framesPerLambda"] == DEFAULT_FRAMES_PER_LAMBDA
        assert payload["privacy"] == DEFAULT_PRIVACY

    async def test_config_overrides_frames_per_lambda(self):
        mock_client = _mock_lambda_client()
        provider = _make_provider(lambda_client=mock_client)

        await provider.execute(
            {"composition_id": "meta-ad-1x1", "input_props": {}},
            config={"frames_per_lambda": 40},
        )

        payload = json.loads(mock_client.invoke.call_args.kwargs["Payload"])
        assert payload["framesPerLambda"] == 40


# ---------------------------------------------------------------------------
# Tests: Lambda error handling
# ---------------------------------------------------------------------------

class TestRemotionProviderErrors:
    async def test_raises_on_function_error(self):
        mock_client = MagicMock()
        mock_client.invoke = MagicMock(return_value=_make_lambda_response(
            {"errorMessage": "Out of memory"},
            function_error="Unhandled",
        ))
        provider = _make_provider(lambda_client=mock_client)

        with pytest.raises(RuntimeError, match="Out of memory"):
            await provider.execute({
                "composition_id": "meta-ad-1x1",
                "input_props": {},
            })

    async def test_retries_on_transient_error(self):
        mock_client = MagicMock()
        call_count = 0

        def invoke_side_effect(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionError("Connection reset")
            return _make_lambda_response({
                "renderId": FAKE_RENDER_ID,
                "bucketName": FAKE_BUCKET_NAME,
            })

        mock_client.invoke = MagicMock(side_effect=invoke_side_effect)
        provider = _make_provider(lambda_client=mock_client)

        with patch("src.providers.remotion_provider.asyncio.sleep", new_callable=AsyncMock):
            result = await provider.execute({
                "composition_id": "meta-ad-1x1",
                "input_props": {},
            })

        assert result.data["render_id"] == FAKE_RENDER_ID
        assert call_count == 2


# ---------------------------------------------------------------------------
# Tests: get_render_progress
# ---------------------------------------------------------------------------

class TestRemotionProviderProgress:
    async def test_returns_progress_dict(self):
        progress_response = {
            "done": False,
            "overallProgress": 0.75,
            "outputFile": None,
            "outputSizeInBytes": 0,
            "fatalErrorEncountered": False,
            "errors": [],
            "timeToFinish": None,
            "costs": {"accruedSoFar": 0.01},
        }
        mock_client = _mock_lambda_client(progress_response=progress_response)
        provider = _make_provider(lambda_client=mock_client)

        result = await provider.get_render_progress(FAKE_RENDER_ID, FAKE_BUCKET_NAME)

        assert result["done"] is False
        assert result["overallProgress"] == 0.75
        assert result["outputFile"] is None

    async def test_returns_completed_progress(self):
        progress_response = {
            "done": True,
            "overallProgress": 1.0,
            "outputFile": "https://s3.amazonaws.com/bucket/renders/abc/out.mp4",
            "outputSizeInBytes": 5000000,
            "fatalErrorEncountered": False,
            "errors": [],
            "timeToFinish": 12500,
            "costs": {"accruedSoFar": 0.05},
        }
        mock_client = _mock_lambda_client(progress_response=progress_response)
        provider = _make_provider(lambda_client=mock_client)

        result = await provider.get_render_progress(FAKE_RENDER_ID, FAKE_BUCKET_NAME)

        assert result["done"] is True
        assert result["overallProgress"] == 1.0
        assert "s3.amazonaws.com" in result["outputFile"]
        assert result["timeToFinish"] == 12500

    async def test_returns_error_progress(self):
        progress_response = {
            "done": False,
            "overallProgress": 0.3,
            "outputFile": None,
            "fatalErrorEncountered": True,
            "errors": [{"message": "Render failed", "chunk": 2}],
        }
        mock_client = _mock_lambda_client(progress_response=progress_response)
        provider = _make_provider(lambda_client=mock_client)

        result = await provider.get_render_progress(FAKE_RENDER_ID, FAKE_BUCKET_NAME)

        assert result["fatalErrorEncountered"] is True
        assert len(result["errors"]) == 1

    async def test_progress_sends_status_type(self):
        mock_client = _mock_lambda_client()
        provider = _make_provider(lambda_client=mock_client)

        await provider.get_render_progress(FAKE_RENDER_ID, FAKE_BUCKET_NAME)

        payload = json.loads(mock_client.invoke.call_args.kwargs["Payload"])
        assert payload["type"] == "status"
        assert payload["renderId"] == FAKE_RENDER_ID
        assert payload["bucketName"] == FAKE_BUCKET_NAME


# ---------------------------------------------------------------------------
# Tests: Constructor
# ---------------------------------------------------------------------------

class TestRemotionProviderConstructor:
    def test_uses_explicit_params(self):
        mock_client = MagicMock()
        provider = RemotionProvider(
            function_name="my-fn",
            serve_url="https://example.com",
            region="eu-west-1",
            lambda_client=mock_client,
        )
        assert provider._function_name == "my-fn"
        assert provider._serve_url == "https://example.com"
        assert provider._region == "eu-west-1"

    def test_falls_back_to_settings(self):
        with patch("src.providers.remotion_provider.settings") as mock_settings, \
             patch("src.providers.remotion_provider.boto3") as mock_boto:
            mock_settings.remotion_function_name = "settings-fn"
            mock_settings.remotion_serve_url = "https://settings-url"
            mock_settings.aws_region = "ap-southeast-1"
            mock_settings.aws_access_key_id = "key"
            mock_settings.aws_secret_access_key = "secret"
            mock_boto.client.return_value = MagicMock()

            provider = RemotionProvider()
            assert provider._function_name == "settings-fn"
            assert provider._serve_url == "https://settings-url"
            assert provider._region == "ap-southeast-1"
