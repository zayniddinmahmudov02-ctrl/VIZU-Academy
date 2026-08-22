from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.cors import cors_headers_for

from .errors import DomainError, NotFoundError


def register_exception_handlers(app: FastAPI):

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
            headers=cors_headers_for(request.headers.get("origin")),
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
