# Development Guide

This guide explains how to run SimbaRAG in development mode.

## Quick Start

### Option 1: Local Development (Recommended)

Run PostgreSQL in Docker and the application locally for faster iteration:

```bash
# 1. Start PostgreSQL
docker compose -f docker-compose.dev.yml up -d

# 2. Set environment variables
export DATABASE_URL="postgres://raggr:raggr_dev_password@localhost:5432/raggr"
export CHROMADB_PATH="./chromadb"
export $(grep -v '^#' .env | xargs)  # Load other vars from .env

# 3. Install dependencies (first time)
pip install -r requirements.txt
cd raggr-frontend && yarn install && yarn build && cd ..

# 4. Run migrations
aerich upgrade

# 5. Start the server
python app.py
```

The application will be available at `http://localhost:8080`.

### Option 2: Full Docker Development

Run everything in Docker with hot reload (slower, but matches production):

```bash
# Uncomment the raggr service in docker-compose.dev.yml first!

# Start all services
docker compose -f docker-compose.dev.yml up --build

# View logs
docker compose -f docker-compose.dev.yml logs -f raggr
```

## Project Structure

```
raggr/
├── app.py                    # Quart application entry point
├── main.py                   # RAG logic and LangChain agent
├── llm.py                    # LLM client (Ollama + OpenAI fallback)
├── aerich_config.py          # Database migration configuration
│
├── blueprints/               # API route blueprints
│   ├── users/               # Authentication (OIDC, JWT, RBAC)
│   ├── conversation/        # Chat conversations and messages
│   └── rag/                 # Document indexing (admin only)
│
├── config/                   # Configuration modules
│   └── oidc_config.py       # OIDC authentication settings
│
├── utils/                    # Reusable utilities
│   ├── chunker.py           # Document chunking for embeddings
│   ├── cleaner.py           # PDF cleaning and summarization
│   ├── image_process.py     # Image description with LLM
│   └── request.py           # Paperless-NGX API client
│
├── scripts/                  # Administrative scripts
│   ├── add_user.py          # Create users manually
│   ├── user_message_stats.py # User message statistics
│   ├── manage_vectorstore.py # Vector store management
│   ├── inspect_vector_store.py # Inspect ChromaDB contents
│   └── query.py             # Query generation utilities
│
├── raggr-frontend/          # React frontend
│   └── src/                # Frontend source code
│
├── migrations/              # Database migrations
└── docs/                    # Documentation
```

## Making Changes

### Backend Changes

**Local development:**
1. Edit Python files
2. Save
3. Restart `python app.py` (or use a tool like `watchdog` for auto-reload)

**Docker development:**
1. Edit Python files
2. Files are synced via Docker watch mode
3. Container automatically restarts

### Frontend Changes

```bash
cd raggr-frontend

# Development mode with hot reload
yarn dev

# Production build (for testing)
yarn build
```

The backend serves built files from `raggr-frontend/dist/`.

### Database Model Changes

When you modify Tortoise ORM models:

```bash
# Generate migration
aerich migrate --name "describe_your_change"

# Apply migration
aerich upgrade

# View history
aerich history
```

See [deployment.md](deployment.md) for detailed migration workflows.

### Adding Dependencies

**Backend:**
```bash
# Add to requirements.txt or use uv
pip install package-name
pip freeze > requirements.txt
```

**Frontend:**
```bash
cd raggr-frontend
yarn add package-name
```

## Useful Commands

### Database

```bash
# Connect to PostgreSQL
docker compose -f docker-compose.dev.yml exec postgres psql -U raggr -d raggr

# Reset database
docker compose -f docker-compose.dev.yml down -v
docker compose -f docker-compose.dev.yml up -d
aerich init-db
```

### Vector Store

```bash
# Show statistics
python scripts/manage_vectorstore.py stats

# Index new documents from Paperless
python scripts/manage_vectorstore.py index

# Clear and reindex everything
python scripts/manage_vectorstore.py reindex
```

See [vectorstore.md](vectorstore.md) for details.

### Scripts

```bash
# Add a new user
python scripts/add_user.py

# View message statistics
python scripts/user_message_stats.py

# Inspect vector store contents
python scripts/inspect_vector_store.py
```

## Environment Variables

Copy `.env.example` to `.env` and configure:

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection | `postgres://user:pass@localhost:5432/db` |
| `CHROMADB_PATH` | ChromaDB storage path | `./chromadb` |
| `OLLAMA_URL` | Ollama server URL | `http://localhost:11434` |
| `OPENAI_API_KEY` | OpenAI API key (fallback LLM) | `sk-...` |
| `PAPERLESS_TOKEN` | Paperless-NGX API token | `...` |
| `BASE_URL` | Paperless-NGX URL | `https://paperless.example.com` |
| `OIDC_ISSUER` | OIDC provider URL | `https://auth.example.com` |
| `OIDC_CLIENT_ID` | OIDC client ID | `simbarag` |
| `OIDC_CLIENT_SECRET` | OIDC client secret | `...` |
| `JWT_SECRET_KEY` | JWT signing key | `random-secret` |
| `TAVILY_KEY` | Tavily web search API key | `tvly-...` |

## Troubleshooting

### Port Already in Use

```bash
# Find and kill process on port 8080
lsof -ti:8080 | xargs kill -9

# Or change the port in app.py
```

### Database Connection Errors

```bash
# Check if PostgreSQL is running
docker compose -f docker-compose.dev.yml ps postgres

# View PostgreSQL logs
docker compose -f docker-compose.dev.yml logs postgres
```

### Frontend Not Building

```bash
cd raggr-frontend
rm -rf node_modules dist
yarn install
yarn build
```

### ChromaDB Errors

```bash
# Clear and recreate ChromaDB
rm -rf chromadb/
python scripts/manage_vectorstore.py reindex
```

### Import Errors After Reorganization

Ensure you're in the project root directory when running scripts, or use:

```bash
# Add project root to Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python scripts/your_script.py
```

## Hot Tips

- Use `python -m pdb app.py` for debugging
- Enable Quart debug mode in `app.py`: `app.run(debug=True)`
- Check API logs: They appear in the terminal running `python app.py`
- Frontend logs: Open browser DevTools console
- Use `docker compose -f docker-compose.dev.yml down -v` for a clean slate
