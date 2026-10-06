"""diet_server — FastAPI 后端入口。"""

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

from logging_setup import setup_logging

LOG_FILE = setup_logging()
logger = logging.getLogger("diet_server")

# healthcheck 每 30 秒一次，降到 DEBUG 免得刷屏
QUIET_PATHS = {"/api/health"}


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("服务启动完成，日志写入 %s", LOG_FILE.resolve())
    yield
    logger.info("服务已关闭")


app = FastAPI(title="diet_server", version="0.1.0", lifespan=lifespan)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    client = request.client.host if request.client else "-"

    try:
        response = await call_next(request)
    except Exception:
        cost_ms = (time.perf_counter() - start) * 1000
        # exception() 会带上完整堆栈，方便排查
        logger.exception(
            "%s %s 请求异常 (%.1fms) client=%s", request.method, request.url.path, cost_ms, client
        )
        raise

    cost_ms = (time.perf_counter() - start) * 1000
    emit = logger.debug if request.url.path in QUIET_PATHS else logger.info
    emit(
        "%s %s -> %d (%.1fms) client=%s",
        request.method,
        request.url.path,
        response.status_code,
        cost_ms,
        client,
    )
    return response


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "diet_server", "docs": "/docs"}


@app.get("/api/hello")
def hello() -> dict[str, str]:
    return {"message": "Hello, World!"}


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": app.title, "version": app.version}
