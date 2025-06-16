FROM python:3.11-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
         build-essential \
         default-libmysqlclient-dev \
         libssl-dev \
         libffi-dev \
         python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose port for health check
EXPOSE 8080

CMD ["python", "-u", "main.py"]
