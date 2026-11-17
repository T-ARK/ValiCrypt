# ValiCrypt Multi-Stage Production Dockerfile
# Stage 1: Frontend Build
FROM node:22-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci || npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Production Backend Runtime
FROM python:3.11-slim AS runtime

# Install system dependencies including FFmpeg and FFprobe
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root application user
RUN groupadd -g 1000 appgroup && \
    useradd -u 1000 -g appgroup -s /bin/bash -m appuser

WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/app ./backend/app
COPY backend/cli ./backend/cli
COPY backend/pyproject.toml ./backend/
COPY bin ./bin
RUN chmod +x ./bin/*

# Copy built frontend assets to backend's expected directory
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Ensure permissions for non-root user
RUN mkdir -p /tmp/mediavault /app/mediavault.db && \
    chown -R appuser:appgroup /app /tmp/mediavault

USER appuser

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/backend
ENV PATH="/app/bin:${PATH}"
ENV FFMPEG_PATH=/usr/bin/ffmpeg
ENV FFPROBE_PATH=/usr/bin/ffprobe
ENV PORT=8000
ENV HOST=0.0.0.0

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

CMD ["sh", "-c", "python3 -m uvicorn app.main:app --app-dir /app/backend --host 0.0.0.0 --port ${PORT:-8000}"]
