# Commit: Добавлены фильтры IgnoreNotHandledUpdatesFilter и IgnoreStaticPathsFilter, а также глобальный RecordFactory для user_id

import logging
import sys
import html
import http.client
import httpx
import aiohttp.http_exceptions
from aiohttp.http_exceptions import HttpProcessingError, BadHttpMessage, BadStatusLine as AioBadStatusLine

from .config import settings

# ── Глобальный LogRecordFactory: дефолтный user_id="system" ──
_old_factory = logging.getLogRecordFactory()


def _record_factory(*args, **kwargs):
    record = _old_factory(*args, **kwargs)
    if not hasattr(record, "user_id"):
        record.user_id = "system"
    return record


logging.setLogRecordFactory(_record_factory)
# ────────────────────────────────────────────────────────────────

class IgnoreBadStatusLineFilter(logging.Filter):
    """Игнорирует шумные HTTP-исключения и сопутствующие сообщения."""
    def filter(self, record: logging.LogRecord) -> bool:
        if record.exc_info:
            exc_type = record.exc_info[0]
            if exc_type and issubclass(exc_type, (
                http.client.BadStatusLine,
                httpx.RemoteProtocolError,
                HttpProcessingError,
                BadHttpMessage,
                AioBadStatusLine
            )):
                return False
        msg = record.getMessage()
        if any(sub in msg for sub in ("Invalid method encountered", "TLSV1_ALERT")):
            return False
        return True


class IgnoreNotHandledUpdatesFilter(logging.Filter):
    """Игнорирует логи вида 'Update id=… is not handled.'."""
    def filter(self, record: logging.LogRecord) -> bool:
        return "is not handled." not in record.getMessage()


class IgnoreStaticPathsFilter(logging.Filter):
    """Игнорирует записи access-лога для указанных URL-путей."""
    def __init__(self, ignore_paths: list[str]):
        super().__init__()
        self.ignore_paths = ignore_paths

    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        return not any(path in msg for path in self.ignore_paths)


class TelegramHandler(logging.Handler):
    """Отправляет ERROR+ логи в Telegram через Bot API."""
    def __init__(self):
        super().__init__(level=logging.ERROR)
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.chat_id = settings.LOG_CHANNEL_ID

    def emit(self, record: logging.LogRecord) -> None:
        if not self.token or not self.chat_id:
            return
        # повторная фильтрация BadStatusLine
        if record.exc_info:
            etype = record.exc_info[0]
            if etype and issubclass(etype, (
                http.client.BadStatusLine,
                httpx.RemoteProtocolError,
                HttpProcessingError
            )):
                return

        text = self.format(record)
        escaped = html.escape(text)
        max_len = 4096 - len("<pre></pre>")
        for start in range(0, len(escaped), max_len):
            segment = escaped[start:start+max_len]
            payload = f"<pre>{segment}</pre>"
            try:
                resp = httpx.post(
                    f"https://api.telegram.org/bot{self.token}/sendMessage",
                    json={"chat_id": self.chat_id, "text": payload, "parse_mode": "HTML"},
                    timeout=5.0
                )
                if resp.status_code != 200:
                    print(f"[Logger] Telegram API error {resp.status_code}: {resp.text}", file=sys.stderr)
            except Exception as e:
                print(f"[Logger] Не удалось отправить лог в Telegram: {e}", file=sys.stderr)


def configure_logging() -> None:
    
    root = logging.getLogger()
    # чистим старые хендлеры при повторном вызове
    for h in list(root.handlers):
        root.removeHandler(h)
    root.setLevel(logging.INFO)

    fmt = '%(asctime)s - %(levelname)s - [%(funcName)s/%(module)s] - [%(user_id)s] - %(message)s'
    formatter = logging.Formatter(fmt)

    # Консольный хендлер
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    ch.addFilter(IgnoreNotHandledUpdatesFilter())
    root.addHandler(ch)

    # Telegram-хендлер
    th = TelegramHandler()
    th.setLevel(logging.ERROR)
    th.setFormatter(formatter)
    th.addFilter(IgnoreBadStatusLineFilter())
    th.addFilter(IgnoreNotHandledUpdatesFilter())
    root.addHandler(th)

    # Подавление шумных логов сторонних библиотек
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.ERROR)

    # Логи доступа uvicorn (INFO+), игнорируем статику
    access_logger = logging.getLogger("uvicorn.access")
    access_logger.setLevel(logging.INFO)
    static_paths = ["/favicon.ico", "/robots.txt", "/sitemap.xml", "/config.json"]
    access_logger.addFilter(IgnoreStaticPathsFilter(static_paths))


# Инициализация логирования при импорте
configure_logging()
