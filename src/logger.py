# Commit: Добавлен глобальный LogRecordFactory для установки user_id='system' по умолчанию и устранения KeyError

import logging
import sys
import httpx
import http.client
import html

from .config import settings

# ── Новый код ──
_old_factory = logging.getLogRecordFactory()
def _record_factory(*args, **kwargs):
    record = _old_factory(*args, **kwargs)
    if not hasattr(record, "user_id"):
        record.user_id = "system"
    return record
logging.setLogRecordFactory(_record_factory)
# ──────────────

class IgnoreBadStatusLineFilter(logging.Filter):
    """Фильтр, игнорирующий ошибки BadStatusLine и сообщения с 'Invalid method encountered'."""
    def filter(self, record: logging.LogRecord) -> bool:
        exc = record.exc_info[1] if record.exc_info else None
        if exc and getattr(exc, "__class__", None).__name__ == "BadStatusLine":
            return False
        msg = record.getMessage()
        if "Invalid method encountered" in msg:
            return False
        return True

class TelegramHandler(logging.Handler):
    """ERROR+ логи отправляются в Telegram Bot API."""
    def __init__(self):
        super().__init__(level=logging.ERROR)
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.chat_id = settings.LOG_CHANNEL_ID

    def emit(self, record: logging.LogRecord) -> None:
        if not self.token or not self.chat_id:
            return

        if record.exc_info:
            etype = record.exc_info[0]
            if etype and issubclass(etype, (
                http.client.BadStatusLine,
                httpx.RemoteProtocolError,
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
                print(f"[Logger] Failed to send log chunk to Telegram: {e}", file=sys.stderr)

def configure_logging() -> None:
    """Настраивает:
      - INFO+ → консоль
      - ERROR+ → Telegram
    """
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    fmt = '%(asctime)s - %(levelname)s - [%(funcName)s/%(module)s] - [%(user_id)s] - %(message)s'
    formatter = logging.Formatter(fmt)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    root.addHandler(ch)

    th = TelegramHandler()
    th.setFormatter(formatter)
    th.addFilter(IgnoreBadStatusLineFilter())
    root.addHandler(th)

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.ERROR)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

configure_logging()
