#!/bin/bash

echo "Running database migrations..."
aerich upgrade

echo "Starting reindex process..."
python main.py "" --reindex

echo "Starting Flask application..."
python app.py
