FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps for docker SDK (TLS/certs) + health
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl \
  && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml /app/pyproject.toml

RUN pip install --upgrade pip \
 && pip install .

COPY src/ /app/src/

ENV PYTHONPATH=/app/src

# Expose UI (NiceGUI) port
EXPOSE 8088

CMD ["python", "-m", "azursmartmix_control.main"]
