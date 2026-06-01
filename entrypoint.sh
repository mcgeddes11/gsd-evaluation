#!/bin/bash
set -e

echo "Running database migrations..."
#python3 - << 'EOF'
#import os, sys, sqlite3
#url = os.environ.get('DATABASE_URL','')
#path = url.replace('sqlite:////', '/')
#if not os.path.exists(path):
#    sys.exit(0)
#conn = sqlite3.connect(path)
#tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
#conn.close()
#if tables and 'alembic_version' not in tables:
#    print("Database exists without migration history - will stamp at head")
#    sys.exist(2)
#sys.exit(0)
#EOF
#
#STAMP_RESULT=$?
#if [ "$STAMP_RESULT" -eq 2 ]; then
#    echo "Stamping database at head..."
#    (cd migrations && alembic stamp head)
#fi
(cd migrations && alembic upgrade head)

echo "Starting gunicorn..."
exec gunicorn wsgi:app \
    --bind 0.0.0.0:5000 \
    --workers 2 \
    --timeout 60 \
    --access-logfile - \
    --error-logfile -
