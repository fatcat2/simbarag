#!/bin/bash

echo "Running database migrations..."
aerich upgrade

# Ensure Obsidian vault directory exists
mkdir -p /app/data/obsidian

# Start continuous Obsidian sync if enabled
if [ "${OBSIDIAN_CONTINUOUS_SYNC}" = "true" ]; then
    if [ -z "${OBSIDIAN_EMAIL}" ] || [ -z "${OBSIDIAN_PASSWORD}" ] || [ -z "${OBSIDIAN_VAULT_ID}" ]; then
        echo "WARNING: OBSIDIAN_EMAIL, OBSIDIAN_PASSWORD, or OBSIDIAN_VAULT_ID not set. Skipping sync."
    else
        echo "Setting up Obsidian sync..."

        VAULT_PATH="${OBSIDIAN_VAULT_PATH:-/app/data/obsidian}"

        # Login and setup sync (foreground, must complete before sync starts)
        if ob login --email "${OBSIDIAN_EMAIL}" --password "${OBSIDIAN_PASSWORD}" && \
           ob sync-setup \
               --vault "${OBSIDIAN_VAULT_ID}" \
               --path "${VAULT_PATH}" \
               --password "${OBSIDIAN_E2E_PASSWORD}" \
               --device-name "${OBSIDIAN_DEVICE_NAME:-simbarag}"; then
            # Remove stale lock from previous container run
            rm -rf "${VAULT_PATH}/.obsidian/.sync.lock"
            # Start continuous sync in background
            echo "Starting Obsidian continuous sync..."
            ob sync --continuous --path "${VAULT_PATH}" &
        else
            echo "WARNING: Obsidian sync setup failed. Continuing without sync."
        fi
    fi
fi

echo "Starting application..."
python app.py
