"""Xử lý lỗi tập trung — mọi lỗi trả đúng format chuẩn
``{error_code, message, field_errors}`` (contracts/appraisal-api.md).

Đăng ký qua ``install_error_handlers(app)`` thay vì lặp lại ở từng endpoint.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class PaaError(Exception):
    """Lỗi nghiệp vụ có mã lỗi + HTTP status, trả theo format chuẩn."""

    def __init__(
        self,
        error_code: str,
        message: str,
        status_code: int = 400,
        field_errors: list[dict] | None = None,
    ) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.field_errors = field_errors or []


def _body(error_code: str, message: str, field_errors: list[dict] | None = None) -> dict:
    return {
        "error_code": error_code,
        "message": message,
        "field_errors": field_errors or [],
    }


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(PaaError)
    async def _paa_error(_: Request, exc: PaaError):
        return JSONResponse(
            status_code=exc.status_code,
            content=_body(exc.error_code, exc.message, exc.field_errors),
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, exc: RequestValidationError):
        field_errors = [
            {
                "field": ".".join(str(p) for p in err.get("loc", []) if p != "body"),
                "message": err.get("msg", ""),
                "type": err.get("type", ""),
            }
            for err in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content=_body(
                "validation_error",
                "Dữ liệu đầu vào không hợp lệ — không chấp nhận dữ liệu sai.",
                field_errors,
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(_: Request, exc: StarletteHTTPException):
        detail = exc.detail
        if isinstance(detail, dict) and "error_code" in detail:
            return JSONResponse(status_code=exc.status_code, content=detail)
        code = {404: "not_found", 409: "conflict"}.get(exc.status_code, "http_error")
        return JSONResponse(
            status_code=exc.status_code,
            content=_body(code, str(detail)),
        )

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content=_body("internal_error", f"Lỗi hệ thống: {exc}"),
        )
