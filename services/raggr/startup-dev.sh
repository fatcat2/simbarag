#!/bin/bash
set -e

echo "Initializing database directories..."
mkdir -p /app/chromadb /app/database

echo "Waiting for frontend to build..."
while [ ! -f /app/raggr-frontend/dist/index.html ]; do
    sleep 1
done
echo "Frontend built successfully!"

echo "Running database migrations..."
aerich upgrade

echo "Initializing visited.db with indexed_documents table..."
python3 -c "
import sqlite3
conn = sqlite3.connect('database/visited.db')
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS indexed_documents (id INTEGER PRIMARY KEY AUTOINCREMENT, paperless_id INTEGER)')
conn.commit()
conn.close()
print('Database initialized successfully')
"

echo "Starting reindex process..."
python main.py "" --reindex || echo "Reindex failed, continuing anyway..."

echo "Starting Flask application in debug mode..."
python app.py
