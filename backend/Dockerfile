FROM python:3.14-slim

WORKDIR /app

# Install system dependencies for Python packages
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       libgl1 \
       libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./backend/requirements.txt
RUN python -m pip install --upgrade pip setuptools wheel
RUN python -m pip install -r ./backend/requirements.txt

RUN groupadd --system --gid 10001 pocketcoach \
    && useradd --system --uid 10001 --gid pocketcoach --home-dir /app pocketcoach
COPY --chown=pocketcoach:pocketcoach backend ./backend
WORKDIR /app/backend

EXPOSE 8080
USER 10001:10001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--proxy-headers", "--forwarded-allow-ips=*"]
