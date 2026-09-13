"""P5-07: Tenant admin request/response schemas."""

from typing import Any

from pydantic import BaseModel, EmailStr, Field


class TenantResponse(BaseModel):
    id: str
    name: str
    slug: str
    plan: str
    is_active: bool
    settings: dict[str, Any] | None
    created_at: str
    updated_at: str


class TenantUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    settings: dict[str, Any] | None = None


class TenantMemberResponse(BaseModel):
    id: str
    email: str
    display_name: str | None
    role: str
    is_active: bool
    last_login_at: str | None
    created_at: str


class InviteMemberRequest(BaseModel):
    email: EmailStr
    display_name: str | None = Field(default=None, max_length=128)
    role: str = Field(default="member", pattern=r"^(owner|admin|member|viewer)$")


class UpdateMemberRoleRequest(BaseModel):
    role: str = Field(pattern=r"^(owner|admin|member|viewer)$")
