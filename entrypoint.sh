#!/bin/bash
set -e

echo "Running database migrations..."
(cd migrations && alembic upgrade head)

echo "Starting gunicorn..."
exec gunicorn wsgi:app \
    --bind 0.0.0.0:5000 \
    --workers 2 \
    --timeout 60 \
    --access-logfile - \
    --error-logfile -
