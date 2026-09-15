"""P6-26: Shopify credential management API routes."""

from __future__ import annotations

import uuid
from typing import Annotated, Any

import requests
import structlog
from aeo_shared.responses import success_response  # type: ignore[import-untyped]
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aeo_api.auth.rbac import CurrentRole, CurrentTenant
from aeo_api.db.models import get_db_session
from aeo_api.db.shopify_credential import ShopifyCredential

logger = structlog.get_logger()

router = APIRouter(prefix="/api/v1/shopify/credentials", tags=["shopify-credentials"])

DbSession = Annotated[AsyncSession, Depends(get_db_session)]


class CredentialCreateRequest(BaseModel):
    store_url: str
    access_token: str
    shop_name: str = ""


class CredentialMaskedResponse(BaseModel):
    id: uuid.UUID
    shop_name: str
    store_url_masked: str
    access_token_masked: str
    is_active: bool
    created_at: str
    updated_at: str


class CredentialTestRequest(BaseModel):
    credential_id: uuid.UUID | None = None
    store_url: str | None = None
    access_token: str | None = None


def _mask(value: str, visible: int = 4) -> str:
    if len(value) <= visible:
        return "****"
    return f"{value[:visible]}{'*' * (len(value) - visible)}"


def _require_owner_admin(role: str) -> None:
    if role not in ("owner", "admin"):
        raise HTTPException(status_code=403, detail="owner or admin role required")


@router.get("")
async def list_credentials(
    request: Request,
    tenant_id: CurrentTenant,
    role: CurrentRole,
    db: DbSession,
) -> dict[str, Any]:
    """List Shopify credentials for the current tenant (masked)."""
    _require_owner_admin(role)

    result = await db.execute(
        select(ShopifyCredential).where(
            ShopifyCredential.tenant_id == uuid.UUID(tenant_id),
        )
    )
    credentials = result.scalars().all()

    items = []
    for cred in credentials:
        from aeo_integrations.amazon.credentials import decrypt_credential  # type: ignore[import-untyped]

        items.append(
            CredentialMaskedResponse(
                id=cred.id,
                shop_name=cred.shop_name,
                store_url_masked=_mask(decrypt_credential(cred.store_url_encrypted)),
                access_token_masked=_mask(decrypt_credential(cred.access_token_encrypted)),
                is_active=cred.is_active,
                created_at=cred.created_at.isoformat() if cred.created_at else "",
                updated_at=cred.updated_at.isoformat() if cred.updated_at else "",
            ).model_dump()
        )

    data = {"credentials": items, "total": len(items)}
    return success_response(data, request.state.request_id).model_dump()  # type: ignore[no-any-return]


@router.post("")
async def create_credential(
    request: Request,
    body: CredentialCreateRequest,
    tenant_id: CurrentTenant,
    role: CurrentRole,
    db: DbSession,
) -> dict[str, Any]:
    """Create or update Shopify credentials (encrypted storage)."""
    _require_owner_admin(role)

    from aeo_integrations.amazon.credentials import encrypt_credential

    tid = uuid.UUID(tenant_id)

    result = await db.execute(
        select(ShopifyCredential).where(
            ShopifyCredential.tenant_id == tid,
            ShopifyCredential.is_active == True,  # noqa: E712
        )
    )
    existing = result.scalars().first()

    if existing:
        existing.store_url_encrypted = encrypt_credential(body.store_url)
        existing.access_token_encrypted = encrypt_credential(body.access_token)
        existing.shop_name = body.shop_name
        await db.flush()
        credential_id = existing.id
    else:
        credential = ShopifyCredential(
            tenant_id=tid,
            store_url_encrypted=encrypt_credential(body.store_url),
            access_token_encrypted=encrypt_credential(body.access_token),
            shop_name=body.shop_name,
        )
        db.add(credential)
        await db.flush()
        credential_id = credential.id

    await db.commit()

    data = {"id": str(credential_id), "status": "created"}
    return success_response(data, request.state.request_id).model_dump()  # type: ignore[no-any-return]


@router.post("/test")
async def test_connection(
    request: Request,
    body: CredentialTestRequest,
    tenant_id: CurrentTenant,
    role: CurrentRole,
    db: DbSession,
) -> dict[str, Any]:
    """Test Shopify Admin API connection with stored or provided credentials."""
    _require_owner_admin(role)

    store_url = body.store_url
    access_token = body.access_token

    if body.credential_id and not all([store_url, access_token]):
        result = await db.execute(
            select(ShopifyCredential).where(
                ShopifyCredential.id == body.credential_id,
                ShopifyCredential.tenant_id == uuid.UUID(tenant_id),
            )
        )
        cred = result.scalars().first()
        if not cred:
            raise HTTPException(status_code=404, detail="Credential not found")

        from aeo_integrations.amazon.credentials import decrypt_credential

        store_url = store_url or decrypt_credential(cred.store_url_encrypted)
        access_token = access_token or decrypt_credential(cred.access_token_encrypted)

    if not all([store_url, access_token]):
        raise HTTPException(status_code=400, detail="Incomplete credentials for connection test")

    assert store_url is not None
    assert access_token is not None

    try:
        normalized_url = store_url.rstrip("/")
        if not normalized_url.startswith("https://"):
            normalized_url = f"https://{normalized_url}"

        response = requests.get(
            f"{normalized_url}/admin/api/2024-01/shop.json",
            headers={"X-Shopify-Access-Token": access_token},
            timeout=10,
        )
        response.raise_for_status()
        shop_data = response.json().get("shop", {})

        data = {
            "success": True,
            "shop_name": shop_data.get("name", ""),
            "myshopify_domain": shop_data.get("myshopify_domain", ""),
        }
    except requests.exceptions.RequestException as exc:
        logger.warning("Shopify credential test failed", error=str(exc))
        data = {"success": False, "error": str(exc)}
    except Exception as exc:
        logger.warning("Shopify credential test failed", error=str(exc))
        data = {"success": False, "error": str(exc)}

    return success_response(data, request.state.request_id).model_dump()  # type: ignore[no-any-return]
