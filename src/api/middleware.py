import time
import uuid
from collections.abc import Awaitable, Callable
import os

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from src.core.logging import logger

ALLOWED_CORS_ORIGINS = [
    "http://localhost:4173",
    "http://127.0.0.1:4173",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://smart-retail-shelf-monitor.vercel.app",
]

configured_frontend_url = os.getenv("FRONTEND_URL", "").strip().rstrip("/")
if configured_frontend_url and configured_frontend_url not in ALLOWED_CORS_ORIGINS:
    ALLOWED_CORS_ORIGINS.append(configured_frontend_url)


def register_middleware(app: FastAPI) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.middleware("http")(request_logging_middleware)


async def request_logging_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    correlation_id = str(uuid.uuid4())
    start = time.perf_counter()

    response = await call_next(request)
    latency = (time.perf_counter() - start) * 1000

    response.headers["X-Correlation-ID"] = correlation_id

    logger.info(
        "[%s] %s %.2f ms",
        request.method,
        request.url.path,
        latency,
    )

    return response
