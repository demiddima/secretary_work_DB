# commit: заменена проверка BadStatusLine без зависимости от aiohttp
from .config import settings
import logging
import httpx

class IgnoreBadStatusLineFilter(logging.Filter):
    """
    Logging filter to ignore aiohttp BadStatusLine errors (TLS handshake on HTTP port)
    and messages containing 'Invalid method encountered', without requiring aiohttp.
    """
    def filter(self, record: logging.LogRecord) -> bool:
        # If exception is named BadStatusLine, ignore
        exc = record.exc_info[1] if record.exc_info else None
        if exc and exc.__class__.__name__ == "BadStatusLine":
            return False
        # If message text indicates invalid method, ignore
        msg = record.getMessage()
        if "Invalid method encountered" in msg:
            return False
        return True

class TelegramHandler(logging.Handler):
    """
    Logging handler that sends ERROR and above logs to a Telegram chat via Bot API.
    Uses Settings for credentials.
    """
    def __init__(self, level=logging.ERROR):
        super().__init__(level)
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.chat_id = settings.LOG_CHANNEL_ID

    def emit(self, record: logging.LogRecord) -> None:
        # Only send if credentials are set
        if not self.token or not self.chat_id:
            return
        try:
            msg = self.format(record)
            # send synchronously
            httpx.post(
                f"https://api.telegram.org/bot{self.token}/sendMessage",
                json={"chat_id": self.chat_id, "text": msg}
            )
        except Exception as e:
            # Print error to console if Telegram send fails
            print(f"[Logger] Failed to send log to Telegram: {e}")


def configure_logging() -> None:
    """
    Configures root logger:
      - Reads LOG_LEVEL from settings
      - Adds StreamHandler for console output
      - Adds TelegramHandler for ERROR+ logs, excluding BadStatusLine noise
    """
    log_level = settings.LOG_LEVEL.upper()
    root = logging.getLogger()
    root.setLevel(log_level)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(log_level)
    ch.setFormatter(formatter)
    root.addHandler(ch)

    # Telegram handler
    th = TelegramHandler()
    th.setLevel(logging.ERROR)
    th.setFormatter(formatter)
    # Добавляем фильтр, чтобы BadStatusLine не шёл в Telegram
    th.addFilter(IgnoreBadStatusLineFilter())
    root.addHandler(th)
    
    # Убираем детальные логи HTTPX и Aiogram
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("aiogram").setLevel(logging.WARNING)

# Initialize on import
configure_logging()
