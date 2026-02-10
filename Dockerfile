# ============================================================
# Stage 1: Build frontend (Next.js standalone)
# ============================================================
FROM node:22-alpine AS frontend-builder

WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --ignore-scripts

COPY frontend/ .

# Empty string = use relative URLs (proxied via Next.js rewrites)
ENV NEXT_PUBLIC_API_URL=""
RUN npm run build

# ============================================================
# Stage 2: Build backend (Python venv via uv)
# ============================================================
FROM python:3.13-slim AS backend-builder

RUN apt-get update && \
    apt-get install -y --no-install-recommends binutils && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /build/backend

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY backend/ .

# Clean and strip venv IN the builder stage (before COPY to final)
RUN find .venv -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; \
    find .venv -type d -name tests -exec rm -rf {} + 2>/dev/null; \
    find .venv -type d -name test -exec rm -rf {} + 2>/dev/null; \
    find .venv -name '*.pyc' -delete 2>/dev/null; \
    find .venv -name '*.pyo' -delete 2>/dev/null; \
    find .venv -name '*.so' -exec strip --strip-unneeded {} \; 2>/dev/null; \
    find .venv -name '*.so.*' -exec strip --strip-unneeded {} \; 2>/dev/null; \
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; \
    true

# ============================================================
# Stage 3: Prepare minimal Node.js runtime
# ============================================================
FROM node:22-slim AS node-runtime

# Strip node binary
RUN strip /usr/local/bin/node 2>/dev/null; true

# ============================================================
# Stage 4: Final runtime image
# ============================================================
FROM python:3.13-slim AS final

# Copy stripped node binary (~40MB after strip)
COPY --from=node-runtime /usr/local/bin/node /usr/local/bin/node

# Install only supervisord
RUN apt-get update && \
    apt-get install -y --no-install-recommends supervisor && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy cleaned backend venv + source
COPY --from=backend-builder /build/backend/.venv /app/backend/.venv
COPY --from=backend-builder /build/backend/src /app/backend/src
COPY --from=backend-builder /build/backend/migrations /app/backend/migrations
COPY --from=backend-builder /build/backend/alembic.ini /app/backend/alembic.ini
COPY --from=backend-builder /build/backend/pyproject.toml /app/backend/pyproject.toml
COPY --from=backend-builder /build/backend/scripts /app/backend/scripts

# Copy frontend standalone output
COPY --from=frontend-builder /build/frontend/.next/standalone /app/frontend
COPY --from=frontend-builder /build/frontend/.next/static /app/frontend/.next/static
COPY --from=frontend-builder /build/frontend/public /app/frontend/public

# Copy docker config
COPY docker/supervisord.conf /app/docker/supervisord.conf
COPY docker/entrypoint.sh /app/docker/entrypoint.sh
RUN chmod +x /app/docker/entrypoint.sh

# Create data directory for ChromaDB
RUN mkdir -p /app/data/chroma_db

EXPOSE 3000 8000

ENTRYPOINT ["/app/docker/entrypoint.sh"]
