"""FastAPI application factory."""

import json
import logging
import time
from collections.abc import Awaitable, Callable
from uuid import uuid4

from fastapi import FastAPI, Request, Response

from todo_api.config import get_settings
from todo_api.routers.todos import router as todos_router

LOGGER = logging.getLogger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(title=settings.app_name, version="1.0.0")

    @application.middleware("http")
    async def log_request(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = request.headers.get("X-Request-ID") or uuid4().hex
        started = time.perf_counter()
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        LOGGER.info(
            json.dumps(
                {
                    "event": "http_request_completed",
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "latency_ms": round((time.perf_counter() - started) * 1000, 2),
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return response

    @application.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    application.include_router(todos_router)
    return application


app = create_app()
