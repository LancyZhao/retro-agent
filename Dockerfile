FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app

COPY pyproject.toml README.md ./
COPY app ./app
COPY web ./web
COPY sample_data ./sample_data

RUN pip install --upgrade pip && pip install ".[web,redis]"

EXPOSE 8000
# Fully runnable with no secrets: falls back to the offline mock model.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
