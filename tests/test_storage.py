from unittest.mock import AsyncMock, patch

import pytest

from src.integrations.supabase_client import SupabaseClient
from src.shared.errors import StorageError
from src.storage.service import StorageService


class TestSupabaseClient:
    @patch("src.integrations.supabase_client.settings")
    def test_init(self, mock_settings):
        mock_settings.supabase_url = "https://example.supabase.co"
        mock_settings.supabase_service_role_key = "test-key"
        client = SupabaseClient(
            supabase_url="https://example.supabase.co",
            service_role_key="test-key",
        )
        assert client._url == "https://example.supabase.co"

    @patch("src.integrations.supabase_client.settings")
    async def test_get_public_url(self, mock_settings):
        mock_settings.supabase_url = "https://example.supabase.co"
        mock_settings.supabase_service_role_key = "test-key"
        client = SupabaseClient(
            supabase_url="https://example.supabase.co",
            service_role_key="test-key",
        )
        url = await client.get_public_url("artifacts", "org-1/pdf/art-1.pdf")
        assert url == "https://example.supabase.co/storage/v1/object/public/artifacts/org-1/pdf/art-1.pdf"
        await client.close()


class TestStorageService:
    async def test_upload_artifact_success(self):
        mock_client = AsyncMock(spec=SupabaseClient)
        mock_client.ensure_bucket = AsyncMock()
        mock_client.upload = AsyncMock(
            return_value="https://example.supabase.co/storage/v1/object/public/artifacts/org-1/pdf/art-1.pdf"
        )

        service = StorageService(mock_client)
        url = await service.upload_artifact(
            org_id="org-1",
            artifact_type="pdf",
            artifact_id="art-1",
            data=b"fake pdf content",
            content_type="application/pdf",
        )
        assert "org-1/pdf/art-1.pdf" in url
        mock_client.ensure_bucket.assert_awaited_once()
        mock_client.upload.assert_awaited_once()

    async def test_upload_artifact_uses_correct_extension(self):
        mock_client = AsyncMock(spec=SupabaseClient)
        mock_client.ensure_bucket = AsyncMock()
        mock_client.upload = AsyncMock(return_value="url")

        service = StorageService(mock_client)
        await service.upload_artifact(
            org_id="org-1",
            artifact_type="audio",
            artifact_id="art-2",
            data=b"audio data",
        )
        call_args = mock_client.upload.call_args
        assert call_args[0][1] == "org-1/audio/art-2.mp3"

    async def test_upload_artifact_raises_storage_error(self):
        mock_client = AsyncMock(spec=SupabaseClient)
        mock_client.ensure_bucket = AsyncMock(side_effect=Exception("Connection refused"))

        service = StorageService(mock_client)
        with pytest.raises(StorageError, match="Failed to upload"):
            await service.upload_artifact(
                org_id="org-1",
                artifact_type="pdf",
                artifact_id="art-1",
                data=b"data",
            )

    async def test_get_artifact_url(self):
        mock_client = AsyncMock(spec=SupabaseClient)
        mock_client.get_public_url = AsyncMock(
            return_value="https://example.supabase.co/storage/v1/object/public/artifacts/org-1/html_page/art-3.html"
        )

        service = StorageService(mock_client)
        url = await service.get_artifact_url("org-1", "html_page", "art-3")
        assert "html_page/art-3.html" in url

    async def test_bucket_only_ensured_once(self):
        mock_client = AsyncMock(spec=SupabaseClient)
        mock_client.ensure_bucket = AsyncMock()
        mock_client.upload = AsyncMock(return_value="url")

        service = StorageService(mock_client)
        await service.upload_artifact("org", "pdf", "a1", b"d")
        await service.upload_artifact("org", "pdf", "a2", b"d")

        # ensure_bucket should only be called once
        assert mock_client.ensure_bucket.await_count == 1
