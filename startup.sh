#!/bin/bash

echo "Starting reindex process..."
python main.py "" --reindex

echo "Starting Flask application..."
python app.py
