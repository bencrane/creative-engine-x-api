from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel

from src.brand.models import BrandContext
from src.brand.service import (
    build_brand_context,
    delete_brand_context,
    get_brand_context_row,
    upsert_brand_context,
)
from src.db import get_pool

router = APIRouter(prefix="/brand-contexts", tags=["brand"])


class UpsertBrandContextRequest(BaseModel):
    context_data: dict


@router.post("")
async def create_brand_context(body: UpsertBrandContextRequest, request: Request) -> Any:
    org_id = getattr(request.state, "organization_id", None)
    if not org_id:
        return {"error": "Not authenticated"}
    pool = await get_pool()
    row = await upsert_brand_context(org_id, "identity", body.context_data, pool)
    return {"status": "created", "id": str(row["id"])}


@router.get("/{org_id}")
async def get_brand_context(org_id: str) -> Any:
    pool = await get_pool()
    context = await build_brand_context(org_id, pool)
    return context.model_dump()


@router.put("/{org_id}/{context_type}")
async def update_brand_context(
    org_id: str, context_type: str, body: UpsertBrandContextRequest
) -> Any:
    pool = await get_pool()
    row = await upsert_brand_context(org_id, context_type, body.context_data, pool)
    return {"status": "updated", "id": str(row["id"]), "version": row["version"]}


@router.delete("/{org_id}/{context_type}")
async def remove_brand_context(org_id: str, context_type: str) -> Any:
    pool = await get_pool()
    deleted = await delete_brand_context(org_id, context_type, pool)
    if deleted:
        return {"status": "deleted"}
    return {"status": "not_found"}
