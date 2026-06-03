FROM python:3.13-slim

WORKDIR /app

# Install system dependencies, Node.js, Yarn, and uv
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g yarn obsidian-headless @anthropic/gws \
    && rm -rf /var/lib/apt/lists/* \
    && curl -LsSf https://astral.sh/uv/install.sh | sh

# Add uv to PATH
ENV PATH="/root/.local/bin:$PATH"

# Copy dependency files
COPY pyproject.toml ./

# Install Python dependencies using uv
RUN uv pip install --system -e .

# Copy application code
COPY *.py ./
COPY blueprints ./blueprints
COPY migrations ./migrations
COPY utils ./utils
COPY config ./config
COPY scripts ./scripts
COPY startup.sh ./
RUN chmod +x startup.sh

# Copy frontend code and build
COPY raggr-frontend ./raggr-frontend
WORKDIR /app/raggr-frontend
RUN yarn install && yarn build
WORKDIR /app

# Create database directory
RUN mkdir -p /app/database

# Expose port
EXPOSE 8080

# Set environment variables
ENV PYTHONPATH=/app

# Run the startup script
CMD ["./startup.sh"]
