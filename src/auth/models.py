from datetime import datetime

from pydantic import BaseModel


class Organization(BaseModel):
    id: str
    name: str
    slug: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class APIKeyRecord(BaseModel):
    id: str
    organization_id: str
    key_hash: str
    key_prefix: str
    name: str
    scopes: list[str] = []
    rate_limit_rpm: int = 60
    is_active: bool = True
    last_used_at: datetime | None = None
    created_at: datetime | None = None
    expires_at: datetime | None = None
