"""P6-26: Shopify credential DB model with encrypted fields."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from aeo_api.db.base import Base


class ShopifyCredential(Base):
    """Encrypted Shopify Admin API credentials for a tenant."""

    __tablename__ = "shopify_credentials"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
    store_url_encrypted: Mapped[str] = mapped_column(String(512), nullable=False)
    access_token_encrypted: Mapped[str] = mapped_column(String(512), nullable=False)
    shop_name: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (Index("idx_shopify_credentials_tenant_active", "tenant_id", "is_active"),)
