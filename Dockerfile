# Builder stage: build wheels for dependencies
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies for MySQL
RUN apt-get update \
    && apt-get install -y build-essential libmariadb-dev-compat libmariadb-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy project metadata and build wheels
COPY pyproject.toml requirements.txt ./
RUN pip wheel --no-cache-dir --wheel-dir=/wheels -r requirements.txt

# Final stage: runtime image
FROM python:3.11-slim

WORKDIR /app

# Install wheels as root
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/*.whl

# Create non-root user and switch
RUN addgroup --system app && adduser --system --ingroup app app
USER app

# Copy application code
COPY --chown=app:app . .

# Expose service port
EXPOSE 8000

# Healthcheck for container orchestration
HEALTHCHECK --interval=30s --timeout=5s \
  CMD curl -f http://localhost:8000/health || exit 1

# Entrypoint
ENTRYPOINT ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]
