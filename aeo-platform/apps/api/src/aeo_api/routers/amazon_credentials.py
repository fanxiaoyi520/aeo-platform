"""P6-21: Amazon credential management API routes."""

from __future__ import annotations

import uuid
from typing import Annotated, Any

import structlog
from aeo_shared.responses import success_response
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aeo_api.auth.rbac import CurrentRole, CurrentTenant
from aeo_api.db.amazon_credential import AmazonCredential
from aeo_api.db.models import get_db_session

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/amazon/credentials", tags=["amazon-credentials"])

DbSession = Annotated[AsyncSession, Depends(get_db_session)]


class CredentialCreateRequest(BaseModel):
    client_id: str
    client_secret: str
    refresh_token: str
    marketplace_id: str = "ATVPDKIKX0DER"
    region: str = "us-east-1"


class CredentialMaskedResponse(BaseModel):
    id: uuid.UUID
    marketplace_id: str
    region: str
    client_id_masked: str
    refresh_token_masked: str
    is_active: bool
    created_at: str
    updated_at: str


class CredentialTestRequest(BaseModel):
    credential_id: uuid.UUID | None = None
    client_id: str | None = None
    client_secret: str | None = None
    refresh_token: str | None = None


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
    """List Amazon credentials for the current tenant (masked)."""
    _require_owner_admin(role)

    result = await db.execute(
        select(AmazonCredential).where(
            AmazonCredential.tenant_id == uuid.UUID(tenant_id),
        )
    )
    credentials = result.scalars().all()

    items = []
    for cred in credentials:
        from aeo_integrations.amazon.credentials import decrypt_credential

        items.append(
            CredentialMaskedResponse(
                id=cred.id,
                marketplace_id=cred.marketplace_id,
                region=cred.region,
                client_id_masked=_mask(decrypt_credential(cred.client_id_encrypted)),
                refresh_token_masked=_mask(decrypt_credential(cred.refresh_token_encrypted)),
                is_active=cred.is_active,
                created_at=cred.created_at.isoformat() if cred.created_at else "",
                updated_at=cred.updated_at.isoformat() if cred.updated_at else "",
            ).model_dump()
        )

    data = {"credentials": items, "total": len(items)}
    return success_response(data, request.state.request_id).model_dump()


@router.post("")
async def create_credential(
    request: Request,
    body: CredentialCreateRequest,
    tenant_id: CurrentTenant,
    role: CurrentRole,
    db: DbSession,
) -> dict[str, Any]:
    """Create or update Amazon credentials (encrypted storage)."""
    _require_owner_admin(role)

    from aeo_integrations.amazon.credentials import encrypt_credential

    tid = uuid.UUID(tenant_id)

    result = await db.execute(
        select(AmazonCredential).where(
            AmazonCredential.tenant_id == tid,
            AmazonCredential.is_active == True,  # noqa: E712
        )
    )
    existing = result.scalars().first()

    if existing:
        existing.client_id_encrypted = encrypt_credential(body.client_id)
        existing.client_secret_encrypted = encrypt_credential(body.client_secret)
        existing.refresh_token_encrypted = encrypt_credential(body.refresh_token)
        existing.marketplace_id = body.marketplace_id
        existing.region = body.region
        await db.flush()
        credential_id = existing.id
    else:
        credential = AmazonCredential(
            tenant_id=tid,
            client_id_encrypted=encrypt_credential(body.client_id),
            client_secret_encrypted=encrypt_credential(body.client_secret),
            refresh_token_encrypted=encrypt_credential(body.refresh_token),
            marketplace_id=body.marketplace_id,
            region=body.region,
        )
        db.add(credential)
        await db.flush()
        credential_id = credential.id

    await db.commit()

    data = {"id": str(credential_id), "status": "created"}
    return success_response(data, request.state.request_id).model_dump()


@router.post("/test")
async def test_connection(
    request: Request,
    body: CredentialTestRequest,
    tenant_id: CurrentTenant,
    role: CurrentRole,
    db: DbSession,
) -> dict[str, Any]:
    """Test Amazon SP-API connection with stored or provided credentials."""
    _require_owner_admin(role)

    client_id = body.client_id
    client_secret = body.client_secret
    refresh_token = body.refresh_token

    if body.credential_id and not all([client_id, client_secret, refresh_token]):
        result = await db.execute(
            select(AmazonCredential).where(
                AmazonCredential.id == body.credential_id,
                AmazonCredential.tenant_id == uuid.UUID(tenant_id),
            )
        )
        cred = result.scalars().first()
        if not cred:
            raise HTTPException(status_code=404, detail="Credential not found")

        from aeo_integrations.amazon.credentials import decrypt_credential

        client_id = client_id or decrypt_credential(cred.client_id_encrypted)
        client_secret = client_secret or decrypt_credential(cred.client_secret_encrypted)
        refresh_token = refresh_token or decrypt_credential(cred.refresh_token_encrypted)

    if not all([client_id, client_secret, refresh_token]):
        raise HTTPException(status_code=400, detail="Incomplete credentials for connection test")

    try:
        from aeo_integrations.amazon.auth import AmazonCredentialError, clear_token_cache
        from sp_api.auth import AccessTokenClient  # type: ignore[import-untyped]

        credentials = {
            "lwa_app_id": client_id,
            "lwa_client_secret": client_secret,
        }
        auth_client = AccessTokenClient(
            refresh_token=refresh_token,
            credentials=credentials,
        )
        response = auth_client.get_auth()
        clear_token_cache()

        data = {
            "success": True,
            "token_type": response.token_type,
            "expires_in": response.expires_in,
        }
    except AmazonCredentialError as exc:
        data = {"success": False, "error": str(exc)}
    except Exception as exc:
        logger.warning("Amazon credential test failed", error=str(exc))
        data = {"success": False, "error": str(exc)}

    return success_response(data, request.state.request_id).model_dump()
