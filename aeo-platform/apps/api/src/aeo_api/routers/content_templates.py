"""Content templates API — MV2-06: multi-platform template library exposure."""

from __future__ import annotations

from typing import Any

from aeo_shared.content_templates import get_content_template_library
from aeo_shared.responses import success_response
from fastapi import APIRouter, Request

router = APIRouter(prefix="/api/v1/content-templates", tags=["content-templates"])


def _ok(request: Request, data: dict[str, Any]) -> dict[str, Any]:
    return success_response(data, request.state.request_id).model_dump()


@router.get("")
async def list_content_templates(
    request: Request,
    content_type: str | None = None,
    platform: str | None = None,
) -> dict[str, Any]:
    """Return content templates with optional filtering by content_type and platform."""
    lib = get_content_template_library()
    templates = lib.filter_by(content_type=content_type, platform=platform)
    payload = {
        "templates": [t.to_dict() for t in templates],
        "summary": {
            "total": len(templates),
            "content_types": lib.list_content_types(),
            "platforms": lib.list_platforms(),
        },
    }
    return _ok(request, payload)
