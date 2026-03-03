#!/bin/bash

echo "Running database migrations..."
aerich upgrade

# Ensure Obsidian vault directory exists
mkdir -p /app/data/obsidian

# Start continuous Obsidian sync if enabled
if [ "${OBSIDIAN_CONTINUOUS_SYNC}" = "true" ]; then
    echo "Starting Obsidian continuous sync in background..."
    ob sync --continuous &
fi

echo "Starting reindex process in background..."
python main.py "" --reindex &

echo "Starting application..."
python app.py
