# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SimbaRAG is a RAG (Retrieval-Augmented Generation) conversational AI system for querying information about Simba (a cat). It ingests documents from Paperless-NGX, stores embeddings in PostgreSQL via pgvector, and uses LLMs (Ollama or OpenAI) to answer questions.

## Commands

### Development

```bash
# Start environment
docker compose up --build

# View logs
docker compose logs -f raggr
```

### Database Migrations (Aerich/Tortoise ORM)

```bash
# Generate migration (must run in Docker with DB access)
docker compose exec raggr aerich migrate --name describe_change

# Apply migrations (auto-runs on startup, manual if needed)
docker compose exec raggr aerich upgrade

# View migration history
docker compose exec raggr aerich history
```

### Frontend

```bash
cd raggr-frontend
yarn install
yarn build      # Production build
yarn dev        # Dev server (rarely needed, backend serves frontend)
```

### Production

```bash
docker compose build raggr
docker compose up -d
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Docker Compose                          │
├─────────────────────────────────────────────────────────────┤
│  raggr (port 8080)              │  postgres (port 5432)    │
│  ├── Quart backend              │  PostgreSQL 16 + pgvector│
│  └── React frontend (served)    │                          │
└─────────────────────────────────────────────────────────────┘
```

**Backend** (root directory):
- `app.py` - Quart application entry, serves API and static frontend
- `main.py` - RAG logic, document indexing, LLM interaction, LangChain agent
- `llm.py` - LLM client with Ollama primary, OpenAI fallback
- `aerich_config.py` - Database migration configuration
- `blueprints/` - API routes organized as Quart blueprints
  - `users/` - OIDC auth, JWT tokens, RBAC with LDAP groups
  - `conversation/` - Chat conversations and message history
  - `rag/` - Document indexing endpoints (admin-only)
- `config/` - Configuration modules
  - `oidc_config.py` - OIDC authentication configuration
- `utils/` - Reusable utilities
  - `chunker.py` - Document chunking for embeddings
  - `cleaner.py` - PDF cleaning and summarization
  - `image_process.py` - Image description with LLM
  - `request.py` - Paperless-NGX API client
- `scripts/` - Administrative and utility scripts
  - `add_user.py` - Create users manually
  - `user_message_stats.py` - User message statistics
  - `manage_vectorstore.py` - Vector store management CLI
  - `inspect_vector_store.py` - Inspect ChromaDB contents
  - `query.py` - Query generation utilities
- `migrations/` - Database migration files

**Frontend** (`raggr-frontend/`):
- React 19 with Rsbuild bundler
- Tailwind CSS for styling
- Built to `dist/`, served by backend at `/`

**Auth Flow**: LLDAP → Authelia (OIDC) → Backend JWT → Frontend localStorage

## Testing

Always run `make test` before pushing code to ensure all tests pass.

```bash
make test       # Run tests
make test-cov   # Run tests with coverage
```

## Key Patterns

- All endpoints are async (`async def`)
- Use `@jwt_refresh_token_required` for authenticated endpoints
- Use `@admin_required` for admin-only endpoints (checks `lldap_admin` group)
- Tortoise ORM models in `blueprints/*/models.py`
- Frontend API services in `raggr-frontend/src/api/`

## Environment Variables

See `.env.example`. Key ones:
- `DATABASE_URL` - PostgreSQL connection
- `OIDC_*` - Authelia OIDC configuration
- `OLLAMA_URL` - Local LLM server
- `OPENAI_API_KEY` - Fallback LLM
- `PAPERLESS_TOKEN` / `BASE_URL` - Document source
