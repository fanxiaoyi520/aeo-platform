from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from aeo_shared.errors import ErrorCode
from aeo_shared.responses import error_response
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from aeo_api.config import get_settings, validate_production_settings
from aeo_api.db.redis import close_redis
from aeo_api.logging_setup import setup_logging
from aeo_api.middleware.rate_limit import RateLimitMiddleware
from aeo_api.middleware.request_id import ApiKeyMiddleware, RequestIdMiddleware
from aeo_api.routers import (
    agents,
    audit,
    health,
    intelligence,
    knowledge,
    metrics,
    risk,
    root,
    selection,
    tasks,
)

logger = structlog.get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    validate_production_settings(settings)
    setup_logging(debug=settings.app_debug)
    from aeo_llm.config import get_llm_settings

    llm = get_llm_settings()
    logger.info("starting", app=settings.app_name, env=settings.app_env, llm_model=llm.llm_model)
    yield
    await close_redis()
    logger.info("shutdown complete")


def create_app() -> FastAPI:
    app = FastAPI(
        title="AEO Platform API",
        version="0.1.0",
        description="Autonomous Ecommerce Operator API",
        lifespan=lifespan,
    )

    app.add_middleware(RateLimitMiddleware, limit_per_minute=settings.rate_limit_per_minute)
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(ApiKeyMiddleware, api_key=settings.auth_api_key)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.get_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(root.router)
    app.include_router(health.router)
    app.include_router(knowledge.router)
    app.include_router(metrics.router)
    app.include_router(audit.router)
    app.include_router(agents.router)
    app.include_router(risk.router)
    app.include_router(selection.router)
    app.include_router(intelligence.router)
    app.include_router(tasks.router)

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", "")
        body = error_response(ErrorCode.VALIDATION_ERROR, request_id, str(exc.errors()))
        return JSONResponse(status_code=422, content=body.model_dump())

    @app.exception_handler(StarletteHTTPException)
    async def http_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        request_id = getattr(request.state, "request_id", "")
        body = error_response(ErrorCode.VALIDATION_ERROR, request_id, str(exc.detail))
        return JSONResponse(status_code=exc.status_code, content=body.model_dump())

    @app.exception_handler(Exception)
    async def generic_handler(request: Request, exc: Exception) -> JSONResponse:
        request_id = getattr(request.state, "request_id", "")
        logger.exception("unhandled error", error=str(exc))
        body = error_response(ErrorCode.INTERNAL_ERROR, request_id)
        return JSONResponse(status_code=500, content=body.model_dump())

    return app


app = create_app()
