FROM python:3.11-slim

# Устанавливаем системные зависимости и драйверы для MySQL
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      build-essential \
      default-libmysqlclient-dev \
      libssl-dev \
      libffi-dev \
      python3-dev \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем файлы зависимостей и устанавливаем
COPY requirements.txt pyproject.toml ./
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Копируем всё приложение, включая alembic/
COPY . .

# Создаём непользовательский аккаунт для безопасности
RUN addgroup --system app && adduser --system --ingroup app app
USER app

EXPOSE 8000

# Прогон миграций и запуск сервиса
ENTRYPOINT ["sh", "-c", "\
    alembic upgrade head && \
    uvicorn src.api:app --host 0.0.0.0 --port 8000 \
"]
