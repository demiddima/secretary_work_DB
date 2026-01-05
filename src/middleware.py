from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import PlainTextResponse
import re
import json
from typing import Any
import logging

# Настроим логирование
logger = logging.getLogger("uvicorn.error")
logging.basicConfig(level=logging.INFO)

class SuppressRootAccessLogMiddleware(BaseHTTPMiddleware):
    """
    Отвечает на GET / мгновенно (OK) и без логов доступа,
    для всех остальных запросов отдаёт дальше.
    """
    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/":
            return PlainTextResponse("OK", status_code=200)
        return await call_next(request)
    

class CleanRequestDataMiddleware(BaseHTTPMiddleware):
    """
    Middleware, которое обрабатывает тело запроса и очищает данные от Telegram-ссылок и HTML-разметки.
    """
    async def dispatch(self, request: Request, call_next):
        # Получаем тело запроса
        body = await request.body()

        # Преобразуем байты в строку
        body_str = body.decode("utf-8")

        # Логируем тело запроса
        logger.info(f"Received request body: {body_str}")

        # Если тело не пустое, очищаем данные
        if body_str:
            try:
                # Логируем перед очисткой
                logger.info("Cleaning data...")

                # Удаляем конкретные ссылки и HTML-разметку
                cleaned_body_str = self.clean_telegram_link(body_str)

                # Логируем очищенные данные
                logger.info(f"Cleaned body: {cleaned_body_str}")

                # Переопределяем тело запроса с очищенными данными
                request._body = cleaned_body_str.encode("utf-8")

                # Преобразуем очищенную строку в объект JSON, если это необходимо
                body_data = json.loads(cleaned_body_str)
                logger.info(f"Parsed JSON body: {body_data}")

            except Exception as e:
                # Логируем ошибку
                logger.error(f"Error cleaning request data: {e}")

        # Передаем запрос дальше в приложение
        response = await call_next(request)
        return response

    def clean_data_from_links(self, data: Any) -> Any:
        """
        Универсальный обработчик, очищающий данные от Telegram-ссылок и HTML-разметки.
        Работает с любыми полями, переданными в запросах.
        """
        if isinstance(data, str):  # Если значение — строка
            logger.info(f"Cleaning string: {data}")
            return self.clean_telegram_link(data)  # Очищаем ссылку
        elif isinstance(data, dict):  # Если это словарь (например, данные пользователя)
            logger.info("Cleaning dictionary data...")
            return {key: self.clean_data_from_links(value) for key, value in data.items()}
        elif isinstance(data, list):  # Если это список
            logger.info("Cleaning list data...")
            return [self.clean_data_from_links(item) for item in data]
        else:
            return data  # Если это не строка и не коллекция, возвращаем как есть

    def clean_telegram_link(self, input_string: str) -> str:
        """
        Удаляет конкретные строки: href="tg://resolve?domain=admi_ludochat"> и </a> из данных.
        Домен может быть любым.
        """
        # Логируем, что очищаем
        logger.info(f"Cleaning string: {input_string}")
        
        # Заменяем строки href="tg://resolve?domain=<domain_value"> и </a> на пустоту
        input_string = re.sub(r'href="tg://resolve\?domain=([a-zA-Z0-9_]+)">\1', r'\1', input_string)
        input_string = input_string.replace('</a>', '')

        # Логируем результат
        logger.info(f"Cleaned string: {input_string}")
        
        return input_string  # Возвращаем очищенную строку
