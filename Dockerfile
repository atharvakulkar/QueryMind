# ============================================================
# QueryMind — Multi-stage Dockerfile
# ============================================================
# Stage 1: Build the Vite / React frontend
# Stage 2: Python runtime (FastAPI + Uvicorn) serving API + static UI
# ============================================================

# ---------- Stage 1: Frontend build ----------
FROM node:20-alpine AS frontend-build

WORKDIR /build

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --ignore-scripts

COPY frontend/ ./
RUN npm run build

# ---------- Stage 2: Python runtime ----------
FROM python:3.11-slim AS runtime

# Prevent Python from writing .pyc files and enable unbuffered stdout
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system deps (for asyncpg)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY core/ core/
COPY database/ database/
COPY backend/ backend/
COPY mcp_server/ mcp_server/
COPY pytest.ini .

# Copy compiled frontend assets from Stage 1
COPY --from=frontend-build /build/dist/ /app/frontend/dist/

# Expose default port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run with Uvicorn
CMD ["uvicorn", "backend.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
