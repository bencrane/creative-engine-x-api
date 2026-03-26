import json

from src.brand.models import BrandContext


async def build_brand_context(org_id: str, pool) -> BrandContext:
    """Assemble a BrandContext from all brand_contexts rows for an org."""
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT context_type, context_data FROM brand_contexts WHERE organization_id = $1",
            org_id,
        )

    context_data: dict = {"organization_id": org_id}
    for row in rows:
        ct = row["context_type"]
        data = row["context_data"]
        if isinstance(data, str):
            data = json.loads(data)
        # Map context_type to BrandContext fields
        if ct == "brand_guidelines":
            context_data["brand_guidelines"] = data
        elif ct == "positioning":
            context_data.update(data)
        elif ct == "icp_definition":
            context_data["icp_definition"] = data
        elif ct == "case_studies":
            context_data["case_studies"] = data if isinstance(data, list) else [data]
        elif ct == "testimonials":
            context_data["testimonials"] = data if isinstance(data, list) else [data]
        elif ct == "identity":
            context_data.update(data)
        else:
            # Generic: merge into top-level
            context_data.update(data)

    return BrandContext(**context_data)


async def get_brand_context_row(org_id: str, context_type: str, pool) -> dict | None:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM brand_contexts WHERE organization_id = $1 AND context_type = $2",
            org_id,
            context_type,
        )
    if row is None:
        return None
    result = dict(row)
    if isinstance(result.get("context_data"), str):
        result["context_data"] = json.loads(result["context_data"])
    return result


async def upsert_brand_context(org_id: str, context_type: str, context_data: dict, pool) -> dict:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """INSERT INTO brand_contexts (organization_id, context_type, context_data)
               VALUES ($1, $2, $3::jsonb)
               ON CONFLICT (organization_id, context_type)
               DO UPDATE SET context_data = $3::jsonb, version = brand_contexts.version + 1, updated_at = now()
               RETURNING *""",
            org_id,
            context_type,
            json.dumps(context_data),
        )
    return dict(row)


async def delete_brand_context(org_id: str, context_type: str, pool) -> bool:
    async with pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM brand_contexts WHERE organization_id = $1 AND context_type = $2",
            org_id,
            context_type,
        )
    return result == "DELETE 1"
