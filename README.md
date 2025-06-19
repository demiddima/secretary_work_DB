# db_service

`db_service` — независимый модуль для работы с базой данных сообщества Ludoman.

## Установка

1. Склонируйте репозиторий:
   ```bash
   git clone https://your.repo/url/db_service.git
   cd db_service
   ```
2. Создайте виртуальное окружение и установите зависимости:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. Скопируйте `.env.example` в `.env` и укажите ваши параметры подключения.

## Использование

```python
from src.database import init_db, AsyncSessionLocal
from src.crud import upsert_chat, create_user

async def main():
    await init_db()
    async with AsyncSessionLocal() as session:
        await upsert_chat(session, 12345, "Test Chat", "group")
        await create_user(session, 67890, username="john_doe", full_name="John Doe")
```
Затуп на серваке
