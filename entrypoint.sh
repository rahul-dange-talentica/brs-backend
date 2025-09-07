#!/bin/bash
set -e

echo "Starting BRS Backend Application..."

# Wait for database to be ready
echo "Waiting for database to be ready..."
for i in {1..30}; do
    if python -c "
import os
import psycopg2
import re

# Manual parsing to handle special characters in password
database_url = os.environ['DATABASE_URL']
match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', database_url)

if match:
    username = match.group(1)
    password = match.group(2)
    host = match.group(3)
    port = int(match.group(4))
    database = match.group(5)
    
    conn = psycopg2.connect(
        host=host,
        port=port,
        user=username,
        password=password,
        database=database
    )
    conn.close()
else:
    raise Exception('Could not parse DATABASE_URL')
" 2>/dev/null; then
        echo "Database is ready!"
        break
    fi
    echo "Database not ready, waiting... ($i/30)"
    sleep 2
done

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Seed initial data
echo "Seeding initial data..."
python seed_data.py

# Start the application
echo "Starting uvicorn server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
