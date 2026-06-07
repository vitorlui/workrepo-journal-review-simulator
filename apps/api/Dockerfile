# Shared Python image for the API and the worker (build context = repo root).
FROM python:3.12-slim

# System libraries: weasyprint (best-effort PDF, D10) + fonts.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 libpangoft2-1.0-0 libpangocairo-1.0-0 \
    libcairo2 libgdk-pixbuf-2.0-0 libffi-dev fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY apps/api/requirements.txt /app/apps/api/requirements.txt
RUN pip install --no-cache-dir -r /app/apps/api/requirements.txt

# Core library + configuration + entrypoints (worker is the shared core, C6).
COPY worker /app/worker
COPY config /app/config
COPY db /app/db
COPY scripts /app/scripts
COPY apps/api /app/apps/api

ENV PYTHONPATH=/app:/app/apps/api
ENV DATA_DIR=/app/data
ENV PYTHONUNBUFFERED=1

EXPOSE 8000
WORKDIR /app/apps/api
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
