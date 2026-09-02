FROM python:3.14-slim

WORKDIR /app

# Install system dependencies for Python packages
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       curl \
       git \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./backend/requirements.txt
COPY backend/dev-requirements.txt ./backend/dev-requirements.txt
RUN python -m pip install --upgrade pip setuptools wheel
RUN python -m pip install -r ./backend/requirements.txt

COPY backend ./backend
WORKDIR /app/backend

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
