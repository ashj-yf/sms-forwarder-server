import uuid
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import cast

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import router as v1_router
from app.core.exceptions import AppError, ErrorCode
from app.core.logger import configure_logging
from app.utils.responses import error_response

configure_logging()
app = FastAPI(title="SmsForwarder Server")


@app.middleware("http")
async def request_id_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[object]]
) -> Response:
    request.state.request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    response = cast(Response, await call_next(request))
    response.headers["X-Request-ID"] = request.state.request_id
    return response


@app.exception_handler(AppError)
def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    status_code = int(exc.code) if int(exc.code) >= 400 else 400
    headers = {}
    if exc.code == ErrorCode.RATE_LIMITED:
        headers["Retry-After"] = str(exc.details.get("retry_after", 60))
    return JSONResponse(
        error_response(request, int(exc.code), exc.message, exc.details),
        status_code,
        headers,
    )


@app.exception_handler(Exception)
def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    del exc
    return JSONResponse(
        error_response(request, int(ErrorCode.INTERNAL_ERROR), "internal error"),
        500,
    )


app.include_router(v1_router, prefix="/api/v1")

frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=frontend_dist / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa_fallback(path: str) -> FileResponse:
        del path
        return FileResponse(frontend_dist / "index.html")
