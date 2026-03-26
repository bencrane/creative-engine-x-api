from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from src.auth.service import create_api_key, revoke_api_key
from src.db import get_pool

router = APIRouter(prefix="/auth", tags=["auth"])


class CreateAPIKeyRequest(BaseModel):
    name: str
    scopes: list[str] = []
    rate_limit_rpm: int = 60


class CreateAPIKeyResponse(BaseModel):
    raw_key: str
    key: dict


@router.post("/api-keys", response_model=CreateAPIKeyResponse)
async def create_key(body: CreateAPIKeyRequest, request: Request):
    pool = await get_pool()
    org_id = getattr(request.state, "organization_id", None)
    if not org_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    raw_key, record = await create_api_key(
        org_id=org_id,
        name=body.name,
        scopes=body.scopes,
        rate_limit_rpm=body.rate_limit_rpm,
        pool=pool,
    )
    return CreateAPIKeyResponse(raw_key=raw_key, key=record.model_dump())


@router.delete("/api-keys/{key_id}", status_code=204)
async def delete_key(key_id: str, request: Request):
    pool = await get_pool()
    org_id = getattr(request.state, "organization_id", None)
    if not org_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    await revoke_api_key(key_id=key_id, pool=pool)
