#!/bin/sh
set -e

echo "==> Running database migrations..."
cd /app/backend
/app/backend/.venv/bin/alembic upgrade head

if [ "$SEED_DATABASE" = "true" ]; then
  echo "==> Seeding database..."
  /app/backend/.venv/bin/python scripts/seed_database.py
fi

if [ "$SEED_VECTORDB" = "true" ]; then
  echo "==> Seeding ChromaDB..."
  /app/backend/.venv/bin/python scripts/seed_vectordb.py
fi

echo "==> Starting services..."
exec /usr/bin/supervisord -c /app/docker/supervisord.conf
