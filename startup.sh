#!/bin/bash

echo "Running database migrations..."
aerich upgrade

# Ensure Obsidian vault directory exists
mkdir -p /app/data/obsidian

# Start continuous Obsidian sync if enabled
if [ "${OBSIDIAN_CONTINUOUS_SYNC}" = "true" ]; then
    echo "Setting up Obsidian sync..."

    VAULT_PATH="${OBSIDIAN_VAULT_PATH:-/app/data/obsidian}"

    # Login
    ob login --email "${OBSIDIAN_EMAIL}" --password "${OBSIDIAN_PASSWORD}" && \
    # Setup sync for vault
    ob sync-setup \
        --vault "${OBSIDIAN_VAULT_ID}" \
        --path "${VAULT_PATH}" \
        --password "${OBSIDIAN_E2E_PASSWORD}" \
        --device-name "${OBSIDIAN_DEVICE_NAME:-simbarag}" && \
    # Start continuous sync in background
    echo "Starting Obsidian continuous sync..." && \
    ob sync --continuous --path "${VAULT_PATH}" &

    if [ $? -ne 0 ]; then
        echo "WARNING: Obsidian sync setup failed. Continuing without sync."
    fi
fi

echo "Starting application..."
python app.py
