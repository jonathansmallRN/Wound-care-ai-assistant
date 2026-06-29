#!/bin/sh
set -e

echo "Waiting for database..."
python -m app.wait_for_db

echo "Running migrations..."
alembic upgrade head

echo "Seeding demo data (idempotent)..."
python -m app.seed.seed_data

echo "Starting API server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
