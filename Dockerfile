# ── Stage 1: Build React SPA ──────────────────────────────────────────────────
FROM node:20-alpine AS frontend-build

WORKDIR /build
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ .
RUN npm run build

# ── Stage 2: Python backend ──────────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# System deps for PDF parsing + OCR + AWS CLI
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
    awscli \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY server/requirements.txt ./server/requirements.txt
RUN pip install --no-cache-dir -r server/requirements.txt

# Copy backend
COPY server/ ./server/

# Copy built frontend
COPY --from=frontend-build /build/dist ./static/

# Copy entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Create volume mount points
RUN mkdir -p /app/data /app/tenants_store

# Environment
ENV DATA_DIR=/app/data \
    QDRANT_URL=http://qdrant \
    QDRANT_PORT=6333 \
    TENANTS_DIR=/app/tenants_store \
    STATIC_DIR=/app/static \
    OLLAMA_BASE_URL=http://host.docker.internal:11434 \
    AWS_REGION=ap-northeast-2 \
    PYTHONUNBUFFERED=1

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
