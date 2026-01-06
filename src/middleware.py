from fastapi import Request
from starlette.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import PlainTextResponse
import logging


log = logging.getLogger("http.requests")

class SuppressRootAccessLogMiddleware(BaseHTTPMiddleware):
    """
    Отвечает на GET / мгновенно (OK) и без логов доступа,
    для всех остальных запросов отдаёт дальше.
    """
    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/":
            return PlainTextResponse("OK", status_code=200)
        return await call_next(request)

class RequestLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        ua = request.headers.get("user-agent", "-")
        ct = request.headers.get("content-type", "-")
        resp: Response = await call_next(request)
        log.info("%s %s -> %s | ua=%r | ct=%r", request.method, request.url.path, resp.status_code, ua, ct)
        return resp