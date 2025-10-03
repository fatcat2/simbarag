FROM python:3.13-slim

WORKDIR /app

# Install system dependencies, Node.js, Yarn, and uv
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g yarn \
    && rm -rf /var/lib/apt/lists/* \
    && curl -LsSf https://astral.sh/uv/install.sh | sh

# Add uv to PATH
ENV PATH="/root/.local/bin:$PATH"

# Copy dependency files
COPY pyproject.toml ./

# Install Python dependencies using uv
RUN uv pip install --system -e .

# Copy frontend code and build
COPY raggr-frontend ./raggr-frontend
WORKDIR /app/raggr-frontend
RUN yarn install && yarn build

# Copy application code
WORKDIR /app
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