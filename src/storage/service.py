from src.integrations.supabase_client import SupabaseClient
from src.shared.errors import StorageError

BUCKET = "artifacts"

# Map artifact types to file extensions
EXT_MAP = {
    "pdf": "pdf",
    "html_page": "html",
    "document_slides": "pdf",
    "audio": "mp3",
    "video": "mp4",
    "image": "png",
    "physical_mail": "pdf",
    "structured_text": "json",
}


class StorageService:
    def __init__(self, client: SupabaseClient):
        self._client = client
        self._bucket_ensured = False

    async def _ensure_bucket(self) -> None:
        if not self._bucket_ensured:
            await self._client.ensure_bucket(BUCKET, public=True)
            self._bucket_ensured = True

    async def upload_artifact(
        self,
        org_id: str,
        artifact_type: str,
        artifact_id: str,
        data: bytes,
        content_type: str = "application/octet-stream",
        ext: str | None = None,
    ) -> str:
        """Upload an artifact and return its public URL."""
        try:
            await self._ensure_bucket()
            file_ext = ext or EXT_MAP.get(artifact_type, "bin")
            path = f"{org_id}/{artifact_type}/{artifact_id}.{file_ext}"
            url = await self._client.upload(BUCKET, path, data, content_type)
            return url
        except Exception as e:
            raise StorageError(f"Failed to upload artifact: {e}") from e

    async def get_artifact_url(
        self,
        org_id: str,
        artifact_type: str,
        artifact_id: str,
        ext: str | None = None,
    ) -> str:
        file_ext = ext or EXT_MAP.get(artifact_type, "bin")
        path = f"{org_id}/{artifact_type}/{artifact_id}.{file_ext}"
        return await self._client.get_public_url(BUCKET, path)
