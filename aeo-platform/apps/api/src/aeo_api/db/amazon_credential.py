"""P6-21: Amazon credential DB model with encrypted fields."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from aeo_api.db.base import Base


class AmazonCredential(Base):
    """Encrypted Amazon SP-API credentials for a tenant."""

    __tablename__ = "amazon_credentials"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
    client_id_encrypted: Mapped[str] = mapped_column(String(512), nullable=False)
    client_secret_encrypted: Mapped[str] = mapped_column(String(512), nullable=False)
    refresh_token_encrypted: Mapped[str] = mapped_column(String(512), nullable=False)
    marketplace_id: Mapped[str] = mapped_column(String(32), nullable=False, default="ATVPDKIKX0DER")
    region: Mapped[str] = mapped_column(String(16), nullable=False, default="us-east-1")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (Index("idx_amazon_credentials_tenant_active", "tenant_id", "is_active"),)
