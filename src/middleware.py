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
    """
    Логирует ТОЛЬКО полезное (чтобы не было дубля с бизнес-логами):

    Пишем в лог, если:
      - 404/405 (маршрут/метод не существует),
      - любой 4xx/5xx,
      - (опционально) "медленный" запрос (по порогу slow_ms).

    Успешные 2xx по существующим роутам не логируем.
    """

    def __init__(self, app, *, slow_ms: int = 700, log_ok: bool = False):
        super().__init__(app)
        self.slow_ms = int(slow_ms)
        self.log_ok = bool(log_ok)  # если захочешь включить логирование 2xx вручную

    async def dispatch(self, request: Request, call_next):
        start = time.monotonic()

        ua = request.headers.get("user-agent", "-")
        ct = request.headers.get("content-type", "-")
        host = request.headers.get("host", "-")
        xff = request.headers.get("x-forwarded-for", "-")
        xri = request.headers.get("x-real-ip", "-")

        client_ip = request.client.host if request.client else "-"

        # “реальный” ip: сначала X-Real-IP, потом первый из XFF, иначе client_ip
        if xri and xri != "-":
            rip = xri
        elif xff and xff != "-":
            rip = xff.split(",")[0].strip()
        else:
            rip = client_ip

        try:
            resp: Response = await call_next(request)
        except Exception:
            dur_ms = int((time.monotonic() - start) * 1000)
            log.exception(
                "%s %s -> EXC | ip=%s | xff=%r | rip=%r | host=%r | ua=%r | ct=%r | %sms",
                request.method,
                request.url.path,
                client_ip,
                xff,
                rip,
                host,
                ua,
                ct,
                dur_ms,
            )
            raise

        dur_ms = int((time.monotonic() - start) * 1000)
        status = resp.status_code

        # Если роут не сматчился, FastAPI/Starlette обычно не ставят endpoint в scope
        endpoint = request.scope.get("endpoint")
        route_missing = endpoint is None

        is_404_405 = status in (404, 405)
        is_error = status >= 400
        is_slow = dur_ms >= self.slow_ms
        is_ok = 200 <= status < 300

        # Основная логика: логируем только "аномалии"
        should_log = (
            is_404_405
            or is_error
            or is_slow
            or (self.log_ok and is_ok)
            or (route_missing and not is_ok)  # на всякий случай
        )

        if should_log:
            log.info(
                "%s %s -> %s | ip=%s | xff=%r | rip=%r | host=%r | ua=%r | ct=%r | %sms",
                request.method,
                request.url.path,
                status,
                client_ip,
                xff,
                rip,
                host,
                ua,
                ct,
                dur_ms,
            )

        return resp