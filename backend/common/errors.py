"""Application-level error types and a single exception handler."""
from fastapi import Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    status_code = 400

    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


class NotFoundError(AppError):
    status_code = 404


class ForbiddenError(AppError):
    status_code = 403


class UnauthorizedError(AppError):
    status_code = 401


class ConflictError(AppError):
    status_code = 409


def register_exception_handlers(app):
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
