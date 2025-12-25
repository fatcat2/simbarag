#!/bin/bash
set -e

echo "Initializing directories..."
mkdir -p /app/chromadb

echo "Waiting for frontend to build..."
while [ ! -f /app/raggr-frontend/dist/index.html ]; do
    sleep 1
done
echo "Frontend built successfully!"

echo "Setting up database..."
# Give PostgreSQL a moment to be ready (healthcheck in docker-compose handles this)
sleep 3

if ls migrations/models/0_*.py 1> /dev/null 2>&1; then
    echo "Running database migrations..."
    aerich upgrade
else
    echo "No migrations found, initializing database..."
    aerich init-db
fi

echo "Starting reindex process..."
python main.py "" --reindex || echo "Reindex failed, continuing anyway..."

echo "Starting Flask application in debug mode..."
python app.py
