FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml ./

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Copy application code
COPY *.py ./

# Create ChromaDB directory
RUN mkdir -p /app/chromadb

# Expose port
EXPOSE 8080

# Set environment variables
ENV PYTHONPATH=/app
ENV CHROMADB_PATH=/app/chromadb

# Run the Flask application
CMD ["python", "app.py"]