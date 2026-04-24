#!/bin/bash
set -e

echo "Rebuilding frontend..."
cd /app/raggr-frontend
yarn build
cd /app

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

echo "Starting Flask application in debug mode..."
python app.py
