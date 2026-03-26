import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.brand.models import BrandContext, BrandGuidelines, ICPDefinition, CaseStudy, Testimonial
from src.brand.service import build_brand_context, upsert_brand_context, delete_brand_context


class TestBrandModels:
    def test_brand_context_defaults(self):
        ctx = BrandContext()
        assert ctx.company_name == ""
        assert ctx.case_studies == []
        assert ctx.brand_guidelines is None

    def test_brand_context_with_data(self):
        ctx = BrandContext(
            company_name="Acme",
            industry="SaaS",
            brand_voice="Professional",
            brand_guidelines=BrandGuidelines(primary_color="#000000"),
            icp_definition=ICPDefinition(title="VP Marketing"),
            case_studies=[CaseStudy(title="Success Story")],
            testimonials=[Testimonial(quote="Great product!", author="Jane")],
        )
        assert ctx.company_name == "Acme"
        assert ctx.brand_guidelines.primary_color == "#000000"
        assert len(ctx.case_studies) == 1

    def test_brand_context_extra_fields(self):
        ctx = BrandContext(company_name="Acme", custom_field="extra")
        assert ctx.custom_field == "extra"


class TestBuildBrandContext:
    async def test_builds_from_db_rows(self):
        rows = [
            {"context_type": "identity", "context_data": json.dumps({"company_name": "Acme", "industry": "SaaS"})},
            {"context_type": "brand_guidelines", "context_data": json.dumps({"primary_color": "#FF0000"})},
            {"context_type": "positioning", "context_data": json.dumps({"value_proposition": "Best in class"})},
        ]
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=rows)
        mock_pool = MagicMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)

        ctx = await build_brand_context("org-1", mock_pool)
        assert ctx.organization_id == "org-1"
        assert ctx.company_name == "Acme"
        assert ctx.brand_guidelines.primary_color == "#FF0000"
        assert ctx.value_proposition == "Best in class"

    async def test_builds_empty_when_no_rows(self):
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[])
        mock_pool = MagicMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)

        ctx = await build_brand_context("org-1", mock_pool)
        assert ctx.organization_id == "org-1"
        assert ctx.company_name == ""


class TestUpsertBrandContext:
    async def test_upsert_returns_row(self):
        mock_row = {
            "id": "ctx-1",
            "organization_id": "org-1",
            "context_type": "identity",
            "context_data": '{"company_name": "Acme"}',
            "version": 1,
        }
        mock_conn = AsyncMock()
        mock_conn.fetchrow = AsyncMock(return_value=mock_row)
        mock_pool = MagicMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)

        result = await upsert_brand_context("org-1", "identity", {"company_name": "Acme"}, mock_pool)
        assert result["id"] == "ctx-1"
        assert result["version"] == 1


class TestDeleteBrandContext:
    async def test_delete_returns_true(self):
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value="DELETE 1")
        mock_pool = MagicMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)

        result = await delete_brand_context("org-1", "identity", mock_pool)
        assert result is True

    async def test_delete_returns_false_when_not_found(self):
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value="DELETE 0")
        mock_pool = MagicMock()
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)

        result = await delete_brand_context("org-1", "identity", mock_pool)
        assert result is False
