from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import PlainTextResponse


class SuppressRootAccessLogMiddleware(BaseHTTPMiddleware):
    """
    Отвечает на GET / мгновенно (OK) и без логов доступа,
    для всех остальных запросов отдаёт дальше.
    """
    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/":
            return PlainTextResponse("OK", status_code=200)
        return await call_next(request)

