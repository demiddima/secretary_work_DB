# Builder stage
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y build-essential libmysqlclient-dev && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml requirements.txt ./
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# Final stage
FROM python:3.11-slim

# Create non-root user
RUN addgroup --system app && adduser --system --ingroup app app

USER app
WORKDIR /app

COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/*.whl

COPY --chown=app:app . .

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s CMD curl -f http://localhost:8000/health || exit 1

ENTRYPOINT ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]
