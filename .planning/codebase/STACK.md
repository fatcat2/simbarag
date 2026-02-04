# Technology Stack

**Analysis Date:** 2026-02-04

## Languages

**Primary:**
- Python 3.13 - Backend application, RAG logic, API endpoints, utilities

**Secondary:**
- TypeScript 5.9.2 - Frontend React application with type safety
- JavaScript - Build tooling and configuration

## Runtime

**Environment:**
- Python 3.13-slim (Docker container)
- Node.js 20.x (for frontend builds)

**Package Manager:**
- uv - Python dependency management (Astral's fast installer)
- Yarn - Frontend package management
- Lockfiles: `uv.lock` and `raggr-frontend/yarn.lock` present

## Frameworks

**Core:**
- Quart 0.20.0 - Async Python web framework (Flask-like API with async support)
- React 19.1.1 - Frontend UI library
- Rsbuild 1.5.6 - Modern frontend build tool (Rspack-based)

**Testing:**
- Not explicitly configured in dependencies

**Build/Dev:**
- Rsbuild 1.5.6 - Frontend bundler with React plugin
- Black 25.9.0 - Python code formatter
- Biome 2.3.10 - Frontend linter and formatter (replaces ESLint/Prettier)
- Pre-commit 4.3.0 - Git hooks for code quality
- Docker Compose - Container orchestration (dev and prod configurations)

## Key Dependencies

**Critical:**
- `chromadb>=1.1.0` - Vector database for document embeddings and similarity search
- `openai>=2.0.1` - LLM client library (used for both OpenAI and llama-server via OpenAI-compatible API)
- `langchain>=1.2.0` - LLM application framework with agent and tool support
- `langchain-openai>=1.1.6` - LangChain integration for OpenAI/llama-server
- `langchain-chroma>=1.0.0` - LangChain integration for ChromaDB
- `tortoise-orm>=0.25.1` - Async ORM for PostgreSQL database operations
- `quart-jwt-extended>=0.1.0` - JWT authentication for Quart
- `authlib>=1.3.0` - OIDC/OAuth2 client library

**Infrastructure:**
- `httpx>=0.28.1` - Async HTTP client for API integrations
- `asyncpg>=0.30.0` - PostgreSQL async driver
- `aerich>=0.8.0` - Database migration tool for Tortoise ORM
- `pymupdf>=1.24.0` - PDF processing (fitz)
- `pillow>=10.0.0` - Image processing
- `pillow-heif>=1.1.1` - HEIF/HEIC image format support
- `bcrypt>=5.0.0` - Password hashing
- `python-dotenv>=1.0.0` - Environment variable management

**External Service Integrations:**
- `tavily-python>=0.7.17` - Web search API client
- `ynab>=1.3.0` - YNAB (budgeting app) API client
- `axios^1.12.2` - Frontend HTTP client
- `react-markdown^10.1.0` - Markdown rendering in React
- `marked^16.3.0` - Markdown parser

## Configuration

**Environment:**
- `.env` files for environment-specific configuration
- Required vars: `DATABASE_URL`, `JWT_SECRET_KEY`, `PAPERLESS_TOKEN`, `BASE_URL`
- Optional LLM: `LLAMA_SERVER_URL`, `LLAMA_MODEL_NAME` (primary) or `OPENAI_API_KEY` (fallback)
- Optional integrations: `YNAB_ACCESS_TOKEN`, `MEALIE_BASE_URL`, `MEALIE_API_TOKEN`, `TAVILY_API_KEY`
- OIDC auth: `OIDC_ISSUER`, `OIDC_CLIENT_ID`, `OIDC_CLIENT_SECRET`, `OIDC_REDIRECT_URI`
- ChromaDB: `CHROMADB_PATH` (defaults to `/app/data/chromadb` in Docker)

**Build:**
- `pyproject.toml` - Python project metadata and dependencies
- `rsbuild.config.ts` - Frontend build configuration
- `tsconfig.json` - TypeScript compiler configuration
- `Dockerfile` - Multi-stage build (Python + Node.js)
- `docker-compose.yml` - Production container setup
- `docker-compose.dev.yml` - Development with hot reload
- `aerich_config.py` - Database migration configuration
- `.pre-commit-config.yaml` - Git hooks for code quality

## Platform Requirements

**Development:**
- Python 3.13+
- Node.js 20.x
- PostgreSQL 16+ (via Docker or local)
- Docker and Docker Compose (recommended)

**Production:**
- Docker environment
- PostgreSQL 16-alpine container
- Persistent volumes for ChromaDB and PostgreSQL data
- Network access to external APIs (Paperless-NGX, YNAB, Mealie, Tavily, OpenAI, llama-server)

---

*Stack analysis: 2026-02-04*
