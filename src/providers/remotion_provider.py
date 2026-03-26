"""Remotion Lambda provider adapter.

CEX-33: Wraps AWS Lambda invocation of Remotion's renderMediaOnLambda
for video rendering. Uses boto3 to invoke the deployed Remotion Lambda
function directly.
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass

import boto3

from src.config import settings
from src.shared.errors import ValidationError

logger = logging.getLogger(__name__)

DEFAULT_CODEC = "h264"
DEFAULT_PRIVACY = "no-acl"
DEFAULT_FRAMES_PER_LAMBDA = 20
MAX_RETRIES = 3
INITIAL_BACKOFF = 1.0


@dataclass
class ProviderResult:
    """Result from a Remotion Lambda render trigger."""

    data: dict
    content_type: str
    metadata: dict


class RemotionProvider:
    """Remotion Lambda provider implementing the provider pattern.

    Invokes the deployed Remotion Lambda function via boto3 to trigger
    video rendering. Returns a render ID for progress polling.
    """

    def __init__(
        self,
        function_name: str | None = None,
        serve_url: str | None = None,
        region: str | None = None,
        aws_access_key_id: str | None = None,
        aws_secret_access_key: str | None = None,
        lambda_client: object | None = None,
    ):
        self._function_name = function_name or settings.remotion_function_name
        self._serve_url = serve_url or settings.remotion_serve_url
        self._region = region or settings.aws_region or "us-east-1"
        self._lambda_client = lambda_client or boto3.client(
            "lambda",
            region_name=self._region,
            aws_access_key_id=aws_access_key_id or settings.aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key or settings.aws_secret_access_key,
        )

    async def execute(self, input_data: dict, config: dict | None = None) -> ProviderResult:
        """Trigger a Remotion Lambda render.

        Args:
            input_data: Must contain 'composition_id', 'input_props'.
                Optional: 'codec', 'duration_frames', 'out_name'.
            config: Optional overrides for frames_per_lambda, privacy.

        Returns:
            ProviderResult with render_id, bucket_name in data dict.

        Raises:
            ValidationError: If required fields are missing.
        """
        config = config or {}

        composition_id = input_data.get("composition_id")
        if not composition_id:
            raise ValidationError("composition_id is required")

        input_props = input_data.get("input_props", {})
        codec = input_data.get("codec", DEFAULT_CODEC)
        out_name = input_data.get("out_name")

        if not self._function_name:
            raise ValidationError("Remotion function name not configured")
        if not self._serve_url:
            raise ValidationError("Remotion serve URL not configured")

        # Build Lambda payload matching renderMediaOnLambda parameters
        payload: dict = {
            "type": "start",
            "serveUrl": self._serve_url,
            "composition": composition_id,
            "codec": codec,
            "inputProps": input_props,
            "framesPerLambda": config.get("frames_per_lambda", DEFAULT_FRAMES_PER_LAMBDA),
            "privacy": config.get("privacy", DEFAULT_PRIVACY),
            "logLevel": "info",
            "outName": out_name or None,
            "imageFormat": "jpeg",
            "maxRetries": 1,
            "region": self._region,
            "functionName": self._function_name,
        }

        # Invoke Lambda
        response = await self._invoke_lambda(payload)

        render_id = response.get("renderId", "")
        bucket_name = response.get("bucketName", "")

        return ProviderResult(
            data={
                "render_id": render_id,
                "bucket_name": bucket_name,
                "function_name": self._function_name,
                "region": self._region,
            },
            content_type="video/mp4",
            metadata={
                "composition_id": composition_id,
                "codec": codec,
                "render_id": render_id,
                "bucket_name": bucket_name,
            },
        )

    async def get_render_progress(
        self,
        render_id: str,
        bucket_name: str,
    ) -> dict:
        """Poll render progress from Remotion Lambda.

        Args:
            render_id: The render ID from execute().
            bucket_name: The S3 bucket from execute().

        Returns:
            Progress dict with keys: done, overallProgress, outputFile,
            fatalErrorEncountered, errors.
        """
        payload = {
            "type": "status",
            "renderId": render_id,
            "bucketName": bucket_name,
            "region": self._region,
            "functionName": self._function_name,
        }

        response = await self._invoke_lambda(payload)

        return {
            "done": response.get("done", False),
            "overallProgress": response.get("overallProgress", 0),
            "outputFile": response.get("outputFile"),
            "outputSizeInBytes": response.get("outputSizeInBytes", 0),
            "fatalErrorEncountered": response.get("fatalErrorEncountered", False),
            "errors": response.get("errors", []),
            "timeToFinish": response.get("timeToFinish"),
            "costs": response.get("costs"),
        }

    async def _invoke_lambda(self, payload: dict) -> dict:
        """Invoke the Remotion Lambda function with retry."""
        last_exception: Exception | None = None

        for attempt in range(MAX_RETRIES):
            try:
                response = await asyncio.to_thread(
                    self._lambda_client.invoke,
                    FunctionName=self._function_name,
                    Payload=json.dumps(payload).encode(),
                    InvocationType="RequestResponse",
                )
                response_payload = json.loads(response["Payload"].read())

                if response.get("FunctionError"):
                    error_msg = response_payload.get("errorMessage", "Unknown Lambda error")
                    raise RuntimeError(f"Remotion Lambda error: {error_msg}")

                return response_payload

            except RuntimeError:
                raise
            except Exception as exc:
                last_exception = exc
                if attempt < MAX_RETRIES - 1:
                    backoff = INITIAL_BACKOFF * (2**attempt)
                    logger.warning(
                        "Remotion Lambda invocation failed (attempt %d/%d), retrying in %.1fs: %s",
                        attempt + 1,
                        MAX_RETRIES,
                        backoff,
                        str(exc),
                    )
                    await asyncio.sleep(backoff)
                    continue
                raise

        raise RuntimeError(
            f"Remotion Lambda invocation failed after {MAX_RETRIES} retries: {last_exception}"
        )
