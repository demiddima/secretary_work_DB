from __future__ import annotations

import logging
import re
import time
from typing import Optional, Tuple

from fastapi import Request
from fastapi.responses import PlainTextResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.routing import Match


log = logging.getLogger("http.requests")


# --- анти-спам для логов (в памяти процесса) ---
_RATE: dict[str, dict[str, float | int]] = {}
_RATE_WINDOW_SEC = 60.0     # окно агрегации
_RATE_MAX_LOGS = 2          # сколько строк логировать на сигнатуру в окно


def _rate_allow(signature: str) -> Tuple[bool, int]:
    """
    Анти-спам: ограничивает число одинаковых логов (по сигнатуре) в минуту.
    Возвращает: (можно_логировать_сейчас, сколько_подавлено_в_прошлом_окне)
    """
    now = time.monotonic()
    st = _RATE.get(signature)

    if st is None or now >= float(st["reset_at"]):
        suppressed_prev = int(st["suppressed"]) if st else 0
        _RATE[signature] = {"reset_at": now + _RATE_WINDOW_SEC, "count": 1, "suppressed": 0}
        return True, suppressed_prev

    if int(st["count"]) < _RATE_MAX_LOGS:
        st["count"] = int(st["count"]) + 1
        return True, 0

    st["suppressed"] = int(st["suppressed"]) + 1
    return False, 0


def _extract_real_ip(request: Request) -> str:
    """
    Пытается корректно определить IP клиента:
    1) X-Forwarded-For (первый IP)
    2) X-Real-IP
    3) request.client.host
    """
    xff = request.headers.get("x-forwarded-for", "")
    if xff:
        first = xff.split(",")[0].strip()
        if first:
            return first

    rip = request.headers.get("x-real-ip", "").strip()
    if rip:
        return rip

    if request.client:
        return request.client.host

    return "-"


def _is_known_route(request: Request) -> bool:
    """
    Проверяет, известен ли маршрут приложению (включая path params).
    """
    scope = request.scope
    app = request.app

    # request.app.routes — есть и в FastAPI, и в Starlette
    for route in getattr(app, "routes", []):
        try:
            match, _ = route.matches(scope)
        except Exception:
            continue
        if match in (Match.FULL, Match.PARTIAL):
            return True
    return False


_WORDPRESS_RE = re.compile(
    r"(^/wp-|/wp-includes/|/wp-content/|/wp-admin/|xmlrpc\.php|wp-login\.php)",
    re.IGNORECASE,
)
_PHP_RE = re.compile(r"\.php($|[/?#])", re.IGNORECASE)


def _scan_signature(method: str, path: str, host: str) -> Optional[str]:
    """
    Возвращает сигнатуру скана/прокси-чека, если похоже на мусор.
    """
    m = method.upper()

    # Proxy-check (очень характерно)
    if m == "CONNECT":
        return "scan:proxy_connect"

    # Host не твой — часто proxy-check
    # Разрешим твои варианты: ludoch.site, *.twc1.net и прямой IP
    host_only = host.split(":")[0].strip().lower()
    if host_only and not (
        host_only == "ludoch.site"
        or host_only.endswith(".twc1.net")
        or host_only == "78.40.217.74"
    ):
        # Например: host='api.ipify.org'
        return "scan:foreign_host"

    # Двойной слэш в пути — тоже часто proxy-check
    if path.startswith("//"):
        return "scan:double_slash"

    # WordPress / PHP-webshell сканы
    if _WORDPRESS_RE.search(path):
        return "scan:wordpress"
    if _PHP_RE.search(path) or "/uploads/" in path or "/tmp/" in path or "/test/" in path:
        return "scan:php_probe"

    return None


class SuppressRootAccessLogMiddleware(BaseHTTPMiddleware):
    """
    Мгновенно отвечает на GET / (OK).
    Используй, если какие-то внешние мониторинги долбят корень.
    """
    async def dispatch(self, request: Request, call_next):
        if request.method == "GET" and request.url.path == "/":
            return PlainTextResponse("OK", status_code=200)
        return await call_next(request)


class RequestLogMiddleware(BaseHTTPMiddleware):
    """
    Логирует только то, что реально важно:
    - подозрительные сканы/прокси-чеки
    - ошибки (4xx/5xx)
    - неизвестные маршруты
    Всё остальное (нормальные 200 по твоим API) НЕ логирует, чтобы не было дублей.
    """
    async def dispatch(self, request: Request, call_next):
        start = time.monotonic()

        method = request.method
        path = request.url.path

        # Не логируем корень (и не трогаем его)
        if method == "GET" and path == "/":
            return await call_next(request)

        ua = request.headers.get("user-agent", "-")
        ct = request.headers.get("content-type", "-")
        host = request.headers.get("host", "-")
        xff = request.headers.get("x-forwarded-for", "-")
        rip_hdr = request.headers.get("x-real-ip", "-")
        real_ip = _extract_real_ip(request)

        sig = _scan_signature(method, path, host)

        # Если это явно прокси-чек — режем сразу, даже не отдаём в роутер
        if sig == "scan:proxy_connect":
            elapsed_ms = int((time.monotonic() - start) * 1000)
            allow, suppressed_prev = _rate_allow(sig)
            if suppressed_prev:
                log.info("[scan] %s (suppressed %d in last %ds)", sig, suppressed_prev, int(_RATE_WINDOW_SEC))
            if allow:
                log.info(
                    "[scan] %s %s -> 405 | ip=%s | xff=%r | rip=%r | host=%r | ua=%r | ct=%r | %dms",
                    method, path, real_ip, xff, rip_hdr, host, ua, ct, elapsed_ms
                )
            return PlainTextResponse("Method Not Allowed", status_code=405)

        # Обычная обработка
        resp: Response = await call_next(request)

        elapsed_ms = int((time.monotonic() - start) * 1000)

        known = _is_known_route(request)
        status = resp.status_code

        # Критерий: логируем только "интересное"
        interesting = False
        tag = "req"

        if sig:
            interesting = True
            tag = "scan"
        elif status >= 400:
            interesting = True
            tag = "err"
        elif not known:
            interesting = True
            tag = "unknown"
        # хочешь — можно включить медленные ответы:
        # elif elapsed_ms >= 800:
        #     interesting = True
        #     tag = "slow"

        if not interesting:
            return resp

        signature = sig or f"{tag}:{method}:{path}"

        allow, suppressed_prev = _rate_allow(signature)
        if suppressed_prev:
            log.info("[%s] %s (suppressed %d in last %ds)", tag, signature, suppressed_prev, int(_RATE_WINDOW_SEC))

        if allow:
            log.info(
                "[%s] %s %s -> %s | ip=%s | xff=%r | rip=%r | host=%r | ua=%r | ct=%r | %dms",
                tag,
                method,
                path,
                status,
                real_ip,
                xff,
                rip_hdr,
                host,
                ua,
                ct,
                elapsed_ms,
            )

        return resp
