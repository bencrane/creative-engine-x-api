import httpx

from src.config import settings


class SupabaseClient:
    """Thin wrapper around Supabase Storage REST API using httpx."""

    def __init__(
        self,
        supabase_url: str | None = None,
        service_role_key: str | None = None,
    ):
        self._url = (supabase_url or settings.supabase_url).rstrip("/")
        self._key = service_role_key or settings.supabase_service_role_key
        self._client = httpx.AsyncClient(
            base_url=f"{self._url}/storage/v1",
            headers={
                "Authorization": f"Bearer {self._key}",
                "apikey": self._key,
            },
            timeout=30.0,
        )

    async def ensure_bucket(self, bucket_id: str, public: bool = True) -> None:
        """Create bucket if it doesn't exist."""
        response = await self._client.get(f"/bucket/{bucket_id}")
        if response.status_code == 404 or response.status_code == 400:
            await self._client.post(
                "/bucket",
                json={"id": bucket_id, "name": bucket_id, "public": public},
            )

    async def upload(
        self,
        bucket_id: str,
        path: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload file and return the public URL."""
        response = await self._client.post(
            f"/object/{bucket_id}/{path}",
            content=data,
            headers={
                "Content-Type": content_type,
                "x-upsert": "true",
            },
        )
        response.raise_for_status()
        return f"{self._url}/storage/v1/object/public/{bucket_id}/{path}"

    async def get_public_url(self, bucket_id: str, path: str) -> str:
        return f"{self._url}/storage/v1/object/public/{bucket_id}/{path}"

    async def close(self) -> None:
        await self._client.aclose()
