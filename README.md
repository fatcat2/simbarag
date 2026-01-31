# SimbaRAG 🐱

A Retrieval-Augmented Generation (RAG) conversational AI system for querying information about Simba the cat. Built with LangChain, ChromaDB, and modern web technologies.

## Features

- 🤖 **Intelligent Conversations** - LangChain-powered agent with tool use and memory
- 📚 **Document Retrieval** - RAG system using ChromaDB vector store
- 🔍 **Web Search** - Integrated Tavily API for real-time web searches
- 🔐 **OIDC Authentication** - Secure auth via Authelia with LDAP group support
- 💬 **Multi-Conversation** - Manage multiple conversation threads per user
- 🎨 **Modern UI** - React 19 frontend with Tailwind CSS
- 🐳 **Docker Ready** - Containerized deployment with Docker Compose

## System Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        Browser[Web Browser]
    end

    subgraph "Frontend - React"
        UI[React UI<br/>Tailwind CSS]
        Auth[Auth Service]
        API[API Client]
    end

    subgraph "Backend - Quart/Python"
        App[Quart App<br/>app.py]

        subgraph "Blueprints"
            Users[Users Blueprint<br/>OIDC + JWT]
            Conv[Conversation Blueprint<br/>Chat Management]
            RAG[RAG Blueprint<br/>Document Indexing]
        end

        Agent[LangChain Agent<br/>main.py]
        LLM[LLM Client<br/>llm.py]
    end

    subgraph "Tools & Utilities"
        Search[Simba Search Tool]
        Web[Web Search Tool<br/>Tavily]
    end

    subgraph "Data Layer"
        Postgres[(PostgreSQL<br/>Users & Conversations)]
        Chroma[(ChromaDB<br/>Vector Store)]
    end

    subgraph "External Services"
        Authelia[Authelia<br/>OIDC Provider]
        LLDAP[LLDAP<br/>User Directory]
        Ollama[Ollama<br/>Local LLM]
        OpenAI[OpenAI<br/>Fallback LLM]
        Paperless[Paperless-NGX<br/>Documents]
        TavilyAPI[Tavily API<br/>Web Search]
    end

    Browser --> UI
    UI --> Auth
    UI --> API
    API --> App

    App --> Users
    App --> Conv
    App --> RAG

    Conv --> Agent
    Agent --> Search
    Agent --> Web
    Agent --> LLM

    Search --> Chroma
    Web --> TavilyAPI
    RAG --> Chroma
    RAG --> Paperless

    Users --> Postgres
    Conv --> Postgres

    Users --> Authelia
    Authelia --> LLDAP

    LLM --> Ollama
    LLM -.Fallback.-> OpenAI

    style Browser fill:#e1f5ff
    style UI fill:#fff3cd
    style App fill:#d4edda
    style Agent fill:#d4edda
    style Postgres fill:#f8d7da
    style Chroma fill:#f8d7da
    style Ollama fill:#e2e3e5
    style OpenAI fill:#e2e3e5
```

## Quick Start

### Prerequisites

- Docker & Docker Compose
- PostgreSQL (or use Docker)
- Ollama (optional, for local LLM)
- Paperless-NGX instance (for document source)

### Installation

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/simbarag.git
cd simbarag
```

2. **Configure environment variables**

```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Start the services**

```bash
# Development (local PostgreSQL only)
docker compose -f docker-compose.dev.yml up -d

# Or full Docker deployment
docker compose up -d
```

4. **Access the application**

Open `http://localhost:8080` in your browser.

## Development

### Local Development Setup

```bash
# 1. Start PostgreSQL
docker compose -f docker-compose.dev.yml up -d

# 2. Set environment variables
export DATABASE_URL="postgres://raggr:raggr_dev_password@localhost:5432/raggr"
export CHROMADB_PATH="./chromadb"
export $(grep -v '^#' .env | xargs)

# 3. Install dependencies
pip install -r requirements.txt
cd raggr-frontend && yarn install && yarn build && cd ..

# 4. Run migrations
aerich upgrade

# 5. Start the server
python app.py
```

See [docs/development.md](docs/development.md) for detailed development guide.

## Project Structure

```
simbarag/
├── app.py                 # Quart application entry point
├── main.py                # RAG logic & LangChain agent
├── llm.py                 # LLM client with Ollama/OpenAI
├── aerich_config.py       # Database migration configuration
│
├── blueprints/            # API route blueprints
│   ├── users/            # Authentication & authorization
│   ├── conversation/     # Chat conversations
│   └── rag/              # Document indexing
│
├── config/               # Configuration modules
│   └── oidc_config.py   # OIDC authentication settings
│
├── utils/                # Reusable utilities
│   ├── chunker.py       # Document chunking for embeddings
│   ├── cleaner.py       # PDF cleaning and summarization
│   ├── image_process.py # Image description with LLM
│   └── request.py       # Paperless-NGX API client
│
├── scripts/              # Administrative scripts
│   ├── add_user.py
│   ├── user_message_stats.py
│   ├── manage_vectorstore.py
│   └── inspect_vector_store.py
│
├── raggr-frontend/       # React frontend
│   └── src/
│
├── migrations/           # Database migrations
│
├── docs/                 # Documentation
│   ├── index.md         # Documentation hub
│   ├── development.md   # Development guide
│   ├── deployment.md    # Deployment & migrations
│   ├── VECTORSTORE.md   # Vector store management
│   ├── MIGRATIONS.md    # Migration reference
│   └── authentication.md # Authentication setup
│
├── docker-compose.yml        # Production compose
├── docker-compose.dev.yml    # Development compose
├── Dockerfile                # Production Dockerfile
├── Dockerfile.dev            # Development Dockerfile
├── CLAUDE.md                 # AI assistant instructions
└── README.md                 # This file
```

## Key Technologies

### Backend
- **Quart** - Async Python web framework
- **LangChain** - Agent framework with tool use
- **Tortoise ORM** - Async ORM for PostgreSQL
- **Aerich** - Database migration tool
- **ChromaDB** - Vector database for embeddings
- **OpenAI** - Embeddings & LLM (fallback)
- **Ollama** - Local LLM (primary)

### Frontend
- **React 19** - UI framework
- **Rsbuild** - Fast bundler
- **Tailwind CSS** - Utility-first styling
- **Axios** - HTTP client

### Authentication
- **Authelia** - OIDC provider
- **LLDAP** - Lightweight LDAP server
- **JWT** - Token-based auth

## API Endpoints

### Authentication
- `GET /api/user/oidc/login` - Initiate OIDC login
- `GET /api/user/oidc/callback` - OIDC callback handler
- `POST /api/user/refresh` - Refresh JWT token

### Conversations
- `POST /api/conversation/` - Create conversation
- `GET /api/conversation/` - List conversations
- `GET /api/conversation/<id>` - Get conversation with messages
- `POST /api/conversation/query` - Send message and get response

### RAG (Admin Only)
- `GET /api/rag/stats` - Vector store statistics
- `POST /api/rag/index` - Index new documents
- `POST /api/rag/reindex` - Clear and reindex all

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgres://...` |
| `CHROMADB_PATH` | ChromaDB storage path | `./chromadb` |
| `OLLAMA_URL` | Ollama server URL | `http://localhost:11434` |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `PAPERLESS_TOKEN` | Paperless-NGX API token | - |
| `BASE_URL` | Paperless-NGX base URL | - |
| `OIDC_ISSUER` | OIDC provider URL | - |
| `OIDC_CLIENT_ID` | OIDC client ID | - |
| `OIDC_CLIENT_SECRET` | OIDC client secret | - |
| `JWT_SECRET_KEY` | JWT signing key | - |
| `TAVILY_KEY` | Tavily web search API key | - |

See `.env.example` for full list.

## Scripts

### User Management
```bash
# Add a new user
python scripts/add_user.py

# View message statistics
python scripts/user_message_stats.py
```

### Vector Store Management
```bash
# Show vector store statistics
python scripts/manage_vectorstore.py stats

# Index new documents from Paperless
python scripts/manage_vectorstore.py index

# Clear and reindex everything
python scripts/manage_vectorstore.py reindex

# Inspect vector store contents
python scripts/inspect_vector_store.py
```

See [docs/vectorstore.md](docs/vectorstore.md) for details.

## Database Migrations

```bash
# Generate a new migration
aerich migrate --name "describe_your_changes"

# Apply pending migrations
aerich upgrade

# View migration history
aerich history

# Rollback last migration
aerich downgrade
```

See [docs/deployment.md](docs/deployment.md) for detailed migration workflows.

## LangChain Agent

The conversational agent has access to two tools:

1. **simba_search** - Query the vector store for Simba's documents
   - Used for: Medical records, veterinary history, factual information

2. **web_search** - Search the web via Tavily API
   - Used for: Recent events, external knowledge, general questions

The agent automatically selects the appropriate tool based on the user's query.

## Authentication Flow

```
User → Authelia (OIDC) → Backend (JWT) → Frontend (localStorage)
                ↓
              LLDAP
```

1. User clicks "Login"
2. Frontend redirects to Authelia
3. User authenticates via Authelia (backed by LLDAP)
4. Authelia redirects back with authorization code
5. Backend exchanges code for OIDC tokens
6. Backend issues JWT tokens
7. Frontend stores tokens in localStorage

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## Documentation

- [Development Guide](docs/development.md) - Setup and development workflow
- [Deployment Guide](docs/deployment.md) - Deployment and migrations
- [Vector Store Guide](docs/vectorstore.md) - Managing the vector database
- [Authentication Guide](docs/authentication.md) - OIDC and LDAP setup

## License

[Your License Here]

## Acknowledgments

- Built for Simba, the most important cat in the world 🐱
- Powered by LangChain, ChromaDB, and the open-source community
