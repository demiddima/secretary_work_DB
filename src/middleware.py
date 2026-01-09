import logging
import re
from fastapi import Request
from fastapi.responses import PlainTextResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.routing import Match

log = logging.getLogger("http.requests")


# --- Быстрые фильтры мусора (сканеры/боты) ---

# Методы, которые тебе почти наверняка не нужны в API.
_BLOCK_METHODS = {"PROPFIND", "TRACE", "TRACK", "CONNECT"}

# Паттерны путей, которые почти всегда являются сканом/эксплойтом.
# Можно дополнять по логам.
_BLOCK_PATH_RE = re.compile(
    r"(?i)("
    r"wp-|wordpress|wp-includes|wp-content|wp-admin|xmlrpc\.php|"
    r"\.php($|/)|"
    r"\.env($|/)|\.git($|/)|"
    r"cgi-bin|"
    r"owa/|autodiscover|"
    r"actuator|"
    r"/sdk/|^/sdk|"
    r"/\.well-known/|"
    r"phpmyadmin|"
    r"server-status"
    r")"
)

# User-Agent, которые часто встречаются у сканеров.
# (не обязателен, но помогает)
_BLOCK_UA_RE = re.compile(r"(?i)(zgrab|masscan|nmap|sqlmap|acunetix)")


def _is_known_route(request: Request) -> bool:
    """
    Возвращает True, если запрос (path+method) совпал с одним из зарегистрированных роутов приложения.
    """
    scope = request.scope
    app = request.app
    for route in getattr(app.router, "routes", []):
        match, _ = route.matches(scope)
        if match == Match.FULL:
            return True
    return False


def _should_drop_silently(request: Request) -> bool:
    """
    True => считаем запрос мусором и режем без логирования.
    """
    method = request.method.upper()
    path = request.url.path or "/"
    ua = (request.headers.get("user-agent") or "").strip()

    # 1) странные методы (WebDAV/пробники/прокси)
    if method in _BLOCK_METHODS:
        return True

    # 2) явные эксплойт-пути
    if _BLOCK_PATH_RE.search(path):
        return True

    # 3) подозрительный UA (опционально)
    if ua and _BLOCK_UA_RE.search(ua):
        return True

    # 4) двойные слэши часто у мусора типа //api.ipify.org/
    if "//" in path:
        return True

    return False


class SuppressRootAccessLogMiddleware(BaseHTTPMiddleware):
    """
    1) GET / -> мгновенно "OK" (без лишней нагрузки)
    2) Мусор/скан -> 404 без логов
    3) Неизвестные роуты -> 404 без логов
    """
    async def dispatch(self, request: Request, call_next):
        path = request.url.path or "/"

        # Корневой "healthcheck" — часто дергают роботы/балансер/ты сам.
        if request.method.upper() == "GET" and path == "/":
            return PlainTextResponse("OK", status_code=200)

        # Сканеры режем сразу и тихо.
        if _should_drop_silently(request):
            return PlainTextResponse("Not Found", status_code=404)

        # Любой неизвестный роут — тоже тихо режем (это главный "пылесос" логов).
        if not _is_known_route(request):
            return PlainTextResponse("Not Found", status_code=404)

        return await call_next(request)


class RequestLogMiddleware(BaseHTTPMiddleware):
    """
    Логирует только ПРОБЛЕМЫ по вашим реальным эндпоинтам:
    - 4xx/5xx (401/422/500 и т.п.)
    Успешные 2xx не логируются, чтобы не дублировать логи хендлеров.
    """
    async def dispatch(self, request: Request, call_next):
        ua = request.headers.get("user-agent", "-")
        ct = request.headers.get("content-type", "-")
        host = request.headers.get("host", "-")
        xff = request.headers.get("x-forwarded-for", "-")
        real_ip = request.headers.get("x-real-ip", "-")

        client_ip = request.client.host if request.client else "-"

        resp: Response = await call_next(request)

        # Логируем только ошибки
        if resp.status_code >= 400:
            log.info(
                "%s %s -> %s | ip=%s | xff=%r | rip=%r | host=%r | ua=%r | ct=%r",
                request.method,
                request.url.path,
                resp.status_code,
                client_ip,
                xff,
                real_ip,
                host,
                ua,
                ct,
            )

        return resp
