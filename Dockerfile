# syntax=docker/dockerfile:1.6

# NOTE:
# - Cette image sert à piloter Docker/Compose du host via /var/run/docker.sock
# - Elle installe docker CLI + docker compose plugin depuis le repo officiel Docker
# - Compatible Debian/Ubuntu (détection via /etc/os-release)

FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# --- System deps: certs + curl + gpg + docker cli + compose plugin ---
# On évite docker.io (Debian) et on préfère docker-ce-cli (repo officiel Docker)
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        gnupg \
        lsb-release; \
    rm -rf /var/lib/apt/lists/*

# --- Add Docker official apt repo (Debian/Ubuntu) ---
RUN set -eux; \
    install -m 0755 -d /etc/apt/keyrings; \
    curl -fsSL https://download.docker.com/linux/$(. /etc/os-release && echo "$ID")/gpg \
      | gpg --dearmor -o /etc/apt/keyrings/docker.gpg; \
    chmod a+r /etc/apt/keyrings/docker.gpg; \
    . /etc/os-release; \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/${ID} ${VERSION_CODENAME} stable" \
      > /etc/apt/sources.list.d/docker.list; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        docker-ce-cli \
        docker-compose-plugin; \
    rm -rf /var/lib/apt/lists/*; \
    docker --version; \
    docker compose version

# --- (Optionnel) utilitaires confort ---
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        tini \
        tzdata; \
    rm -rf /var/lib/apt/lists/*

# --- Python deps (si tu as requirements.txt) ---
# COPY requirements.txt /app/requirements.txt
# RUN pip install --no-cache-dir -r /app/requirements.txt

# --- App code ---
# COPY src/ /app/src/
# COPY pyproject.toml /app/pyproject.toml
# COPY ... etc

# Exemple: lancement via module
# (À adapter selon ton projet)
ENTRYPOINT ["/usr/bin/tini","--"]
CMD ["python","-m","azursmartmix_control.main"]
