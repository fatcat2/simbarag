# External Integrations

**Analysis Date:** 2026-02-04

## APIs & External Services

**Document Management:**
- Paperless-NGX - Document ingestion and retrieval
  - SDK/Client: Custom client in `utils/request.py` using `httpx`
  - Auth: `PAPERLESS_TOKEN` (bearer token)
  - Base URL: `BASE_URL` environment variable
  - Purpose: Fetch documents for indexing, download PDFs, retrieve document metadata and types

**LLM Services:**
- llama-server (primary) - Local LLM inference via OpenAI-compatible API
  - SDK/Client: `openai` Python package (v2.0.1+)
  - Connection: `LLAMA_SERVER_URL` (e.g., `http://192.168.1.213:8080/v1`)
  - Model: `LLAMA_MODEL_NAME` (e.g., `llama-3.1-8b-instruct`)
  - Implementation: `llm.py` creates OpenAI client with custom base_url
  - LangChain: `langchain-openai.ChatOpenAI` with custom base_url for agent framework

- OpenAI (fallback) - Cloud LLM service
  - SDK/Client: `openai` Python package
  - Auth: `OPENAI_API_KEY`
  - Models: `gpt-4o-mini` (embeddings and chat), `gpt-5-mini` (fallback for agents)
  - Implementation: Automatic fallback when `LLAMA_SERVER_URL` not configured
  - Used for: Chat completions, embeddings via ChromaDB embedding function

**Web Search:**
- Tavily - Web search API for real-time information retrieval
  - SDK/Client: `tavily-python` (v0.7.17+)
  - Auth: `TAVILY_API_KEY`
  - Implementation: `blueprints/conversation/agents.py` - `AsyncTavilyClient`
  - Used in: LangChain agent tool for web searches

**Budget Tracking:**
- YNAB (You Need A Budget) - Personal finance and budget management
  - SDK/Client: `ynab` Python package (v1.3.0+)
  - Auth: `YNAB_ACCESS_TOKEN` (Personal Access Token from YNAB settings)
  - Budget Selection: `YNAB_BUDGET_ID` (optional, auto-detects first budget if not set)
  - Implementation: `utils/ynab_service.py` - `YNABService` class
  - Features: Budget summary, transaction search, category spending, spending insights
  - API Endpoints: Budgets API, Transactions API, Months API, Categories API
  - Used in: LangChain agent tools for financial queries

**Meal Planning:**
- Mealie - Self-hosted meal planning and recipe management
  - SDK/Client: Custom async client using `httpx` in `utils/mealie_service.py`
  - Auth: `MEALIE_API_TOKEN` (Bearer token)
  - Base URL: `MEALIE_BASE_URL` (e.g., `http://192.168.1.5:9000`)
  - Implementation: `MealieService` class with async methods
  - Features: Shopping lists, meal plans, today's meals, recipe details, CRUD operations on meal plans
  - API Endpoints: `/api/households/shopping/*`, `/api/households/mealplans/*`, `/api/households/self/recipes/*`
  - Used in: LangChain agent tools for meal planning queries

**Photo Management (referenced but not actively used):**
- Immich - Photo library management
  - Connection: `IMMICH_URL`, `IMMICH_API_KEY`
  - Search: `SEARCH_QUERY`, `DOWNLOAD_DIR`
  - Note: Environment variables defined but service implementation not found in current code

## Data Storage

**Databases:**
- PostgreSQL 16
  - Connection: `DATABASE_URL` (format: `postgres://user:pass@host:port/db`)
  - Container: `postgres:16-alpine` image
  - Client: Tortoise ORM (async ORM with Pydantic models)
  - Models: User management, conversations, messages, OIDC state
  - Migrations: Aerich tool in `migrations/` directory
  - Volume: `postgres_data` persistent volume

**Vector Store:**
- ChromaDB
  - Type: Embedded vector database (PersistentClient)
  - Path: `CHROMADB_PATH` (Docker: `/app/data/chromadb`, local: `./data/chromadb`)
  - Collections: `simba_docs2` (main RAG documents), `feline_vet_lookup` (veterinary knowledge)
  - Embedding Function: OpenAI embeddings via `chromadb.utils.embedding_functions.openai_embedding_function`
  - Integration: LangChain via `langchain-chroma` for vector store queries
  - Volume: `chromadb_data` persistent volume

**File Storage:**
- Local filesystem only
  - PDF downloads: Temporary files for processing
  - Image conversion: Temporary files from PDF to image conversion
  - Database tracking: `database/visited.db` SQLite for tracking indexed documents

**Caching:**
- None - No explicit caching layer configured

## Authentication & Identity

**Auth Provider:**
- Authelia (OIDC) - Self-hosted authentication and authorization server
  - Implementation: Custom OIDC client in `config/oidc_config.py`
  - Discovery: `.well-known/openid-configuration` endpoint (configurable via `OIDC_USE_DISCOVERY`)
  - Environment Variables:
    - `OIDC_ISSUER` (e.g., `https://auth.example.com`)
    - `OIDC_CLIENT_ID` (e.g., `simbarag`)
    - `OIDC_CLIENT_SECRET`
    - `OIDC_REDIRECT_URI` (default: `http://localhost:8080/`)
  - Manual endpoint override: `OIDC_AUTHORIZATION_ENDPOINT`, `OIDC_TOKEN_ENDPOINT`, `OIDC_USERINFO_ENDPOINT`, `OIDC_JWKS_URI`
  - Token Verification: JWT verification using `authlib.jose.jwt` with JWKS
  - LDAP Integration: LLDAP groups for RBAC (checks `lldap_admin` group for admin permissions)

**Session Management:**
- JWT tokens via `quart-jwt-extended`
  - Secret: `JWT_SECRET_KEY` environment variable
  - Storage: Frontend localStorage
  - Decorators: `@jwt_refresh_token_required` for protected endpoints, `@admin_required` for admin routes

## Monitoring & Observability

**Error Tracking:**
- None - No external error tracking service configured

**Logs:**
- Standard Python logging to stdout/stderr
  - Format: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`
  - Level: INFO (configurable via logging module)
  - Special loggers: `utils.ynab_service`, `utils.mealie_service`, `blueprints.conversation.agents` set to INFO level
  - Docker: Logs accessible via `docker compose logs`

**Metrics:**
- None - No metrics collection configured

## CI/CD & Deployment

**Hosting:**
- Docker Compose - Self-hosted container deployment
  - Production: `docker-compose.yml`
  - Development: `docker-compose.dev.yml` with volume mounts for hot reload
  - Image: `torrtle/simbarag:latest` (custom build)

**CI Pipeline:**
- None - No automated CI/CD configured
  - Manual builds: `docker compose build raggr`
  - Manual deploys: `docker compose up -d`

**Container Registry:**
- Docker Hub (inferred from image name `torrtle/simbarag:latest`)

## Environment Configuration

**Required env vars:**
- `DATABASE_URL` - PostgreSQL connection string
- `JWT_SECRET_KEY` - JWT token signing key
- `PAPERLESS_TOKEN` - Paperless-NGX API token
- `BASE_URL` - Paperless-NGX instance URL

**LLM configuration (choose one):**
- `LLAMA_SERVER_URL` + `LLAMA_MODEL_NAME` - Local llama-server (primary)
- `OPENAI_API_KEY` - OpenAI API (fallback)

**Optional integrations:**
- `YNAB_ACCESS_TOKEN`, `YNAB_BUDGET_ID` - YNAB budget integration
- `MEALIE_BASE_URL`, `MEALIE_API_TOKEN` - Mealie meal planning
- `TAVILY_API_KEY` - Web search capability
- `IMMICH_URL`, `IMMICH_API_KEY`, `SEARCH_QUERY`, `DOWNLOAD_DIR` - Immich photos

**OIDC authentication:**
- `OIDC_ISSUER`, `OIDC_CLIENT_ID`, `OIDC_CLIENT_SECRET`, `OIDC_REDIRECT_URI`
- `OIDC_USE_DISCOVERY` - Enable/disable OIDC discovery (default: true)

**Secrets location:**
- `.env` file in project root (not committed to git)
- Docker Compose reads from `.env` file automatically
- Example file: `.env.example` with placeholder values

## Webhooks & Callbacks

**Incoming:**
- `/api/user/oidc/callback` - OIDC authorization code callback from Authelia
  - Method: GET with `code` and `state` query parameters
  - Flow: Authorization code → token exchange → user info → JWT creation

**Outgoing:**
- None - No webhook subscriptions to external services

---

*Integration audit: 2026-02-04*
