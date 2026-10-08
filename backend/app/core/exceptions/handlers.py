from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.cors import cors_headers_for

from .errors import DomainError, NotFoundError


def register_exception_handlers(app: FastAPI):

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ):
        """FastAPI's default 422 body echoes the submitted values ("input").
        On auth routes that would send passwords back in the response, so
        there only type / location / message are returned. Every other route
        keeps FastAPI's standard behaviour."""

        if "/auth/" not in request.url.path:
            return await request_validation_exception_handler(request, exc)
        errors = [{k: v for k, v in err.items() if k not in ("input", "ctx", "url")} for err in exc.errors()]
        return JSONResponse(
            status_code=422,
            content={"detail": jsonable_encoder(errors)},
            headers=cors_headers_for(request.headers.get("origin")),
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request,
        exc: HTTPException,
    ):

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "message": exc.detail,
            },
            # Keep the exception's own headers (e.g. Retry-After on 429,
            # WWW-Authenticate on 401) alongside the CORS headers.
            headers={**(exc.headers or {}), **cors_headers_for(request.headers.get("origin"))},
        )

    @app.exception_handler(NotFoundError)
    async def not_found_handler(
        request: Request,
        exc: NotFoundError,
    ):

        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "message": exc.message,
            },
            headers=cors_headers_for(request.headers.get("origin")),
        )

    @app.exception_handler(DomainError)
    async def domain_error_handler(
        request: Request,
        exc: DomainError,
    ):

        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message": exc.message,
            },
            headers=cors_headers_for(request.headers.get("origin")),
        )

    @app.exception_handler(Exception)
    async def internal_exception_handler(
        request: Request,
        exc: Exception,
    ):

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Internal Server Error",
            },
            headers=cors_headers_for(request.headers.get("origin")),
        )
