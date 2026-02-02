# Stage 1: Build dependencies
FROM python:3.11-slim AS builder

WORKDIR /app

RUN pip install --no-cache-dir pip-tools

COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# Stage 2: Production image
FROM python:3.11-slim AS production

WORKDIR /app

# Create non-root user
RUN useradd --create-home appuser

# Copy wheels and install
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

# Copy application
COPY src/ ./src/

USER appuser

EXPOSE 8000

CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Stage 3: Development image
FROM production AS development

USER root
RUN pip install --no-cache-dir watchfiles
USER appuser

CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
