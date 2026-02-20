FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# --- System deps: docker CLI + compose plugin + minimal runtime ---
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl \
    docker.io docker-compose-plugin \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY pyproject.toml /app/pyproject.toml
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir .

# App code
COPY src/ /app/src/

# Entrypoint
CMD ["python", "-m", "azursmartmix_control.main"]
