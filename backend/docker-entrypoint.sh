#!/bin/sh
set -e

echo "Executing Alembic database migrations..."
alembic upgrade head

echo "Starting FastAPI backend server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
