# SimbaRAG Documentation

Welcome to the SimbaRAG documentation! This guide will help you understand, develop, and deploy the SimbaRAG conversational AI system.

## Getting Started

New to SimbaRAG? Start here:

1. Read the main [README](../README.md) for project overview and architecture
2. Follow the [Development Guide](development.md) to set up your environment
3. Learn about [Authentication](authentication.md) setup with OIDC and LDAP

## Documentation Structure

### Core Guides

- **[Development Guide](development.md)** - Local development setup, project structure, and workflows
- **[Deployment Guide](deployment.md)** - Database migrations, deployment workflows, and troubleshooting
- **[Vector Store Guide](VECTORSTORE.md)** - Managing ChromaDB, indexing documents, and RAG operations
- **[Migrations Guide](MIGRATIONS.md)** - Database migration reference
- **[Authentication Guide](authentication.md)** - OIDC, Authelia, LLDAP configuration and user management

### Quick Reference

| Task | Documentation |
|------|---------------|
| Set up local dev environment | [Development Guide → Quick Start](development.md#quick-start) |
| Run database migrations | [Deployment Guide → Migration Workflow](deployment.md#migration-workflow) |
| Index documents | [Vector Store Guide → Management Commands](VECTORSTORE.md#management-commands) |
| Configure authentication | [Authentication Guide](authentication.md) |
| Run administrative scripts | [Development Guide → Scripts](development.md#scripts) |

## Common Tasks

### Development

```bash
# Start local development
docker compose -f docker-compose.dev.yml up -d
export DATABASE_URL="postgres://raggr:raggr_dev_password@localhost:5432/raggr"
export CHROMADB_PATH="./chromadb"
python app.py
```

### Database Migrations

```bash
# Generate migration
aerich migrate --name "your_change"

# Apply migrations
aerich upgrade

# View history
aerich history
```

### Vector Store Management

```bash
# Show statistics
python scripts/manage_vectorstore.py stats

# Index new documents
python scripts/manage_vectorstore.py index

# Reindex everything
python scripts/manage_vectorstore.py reindex
```

## Architecture Overview

SimbaRAG is built with:

- **Backend**: Quart (async Python), LangChain, Tortoise ORM
- **Frontend**: React 19, Rsbuild, Tailwind CSS
- **Database**: PostgreSQL (users, conversations)
- **Vector Store**: ChromaDB (document embeddings)
- **LLM**: Ollama (primary), OpenAI (fallback)
- **Auth**: Authelia (OIDC), LLDAP (user directory)

See the [README](../README.md#system-architecture) for detailed architecture diagram.

## Project Structure

```
simbarag/
├── app.py                  # Quart app entry point
├── main.py                 # RAG & LangChain agent
├── llm.py                  # LLM client
├── blueprints/             # API routes
├── config/                 # Configuration
├── utils/                  # Utilities
├── scripts/                # Admin scripts
├── raggr-frontend/         # React UI
├── migrations/             # Database migrations
├── docs/                   # This documentation
├── docker-compose.yml      # Production Docker setup
└── docker-compose.dev.yml  # Development Docker setup
```

## Key Concepts

### RAG (Retrieval-Augmented Generation)

SimbaRAG uses RAG to answer questions about Simba:

1. Documents are fetched from Paperless-NGX
2. Documents are chunked and embedded using OpenAI
3. Embeddings are stored in ChromaDB
4. User queries are embedded and matched against the store
5. Relevant chunks are passed to the LLM for context
6. LLM generates an answer using retrieved context

### LangChain Agent

The conversational agent has two tools:

- **simba_search**: Queries the vector store for Simba's documents
- **web_search**: Searches the web via Tavily API

The agent automatically selects tools based on the query.

### Authentication Flow

1. User initiates OIDC login via Authelia
2. Authelia authenticates against LLDAP
3. Backend receives OIDC tokens and issues JWT
4. Frontend stores JWT in localStorage
5. Subsequent requests use JWT for authorization

## Environment Variables

Key environment variables (see `.env.example` for complete list):

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | PostgreSQL connection |
| `CHROMADB_PATH` | Vector store location |
| `OLLAMA_URL` | Local LLM server |
| `OPENAI_API_KEY` | OpenAI for embeddings/fallback |
| `PAPERLESS_TOKEN` | Document source API |
| `OIDC_*` | Authentication configuration |
| `TAVILY_KEY` | Web search API |

## API Endpoints

### Authentication
- `GET /api/user/oidc/login` - Start OIDC flow
- `GET /api/user/oidc/callback` - OIDC callback
- `POST /api/user/refresh` - Refresh JWT

### Conversations
- `POST /api/conversation/` - Create conversation
- `GET /api/conversation/` - List conversations
- `POST /api/conversation/query` - Chat message

### RAG (Admin Only)
- `GET /api/rag/stats` - Vector store stats
- `POST /api/rag/index` - Index documents
- `POST /api/rag/reindex` - Reindex all

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Port already in use | Check if services are running: `lsof -ti:8080` |
| Database connection error | Ensure PostgreSQL is running: `docker compose ps` |
| ChromaDB errors | Clear and reindex: `python scripts/manage_vectorstore.py reindex` |
| Import errors | Check you're in `services/raggr/` directory |
| Frontend not building | `cd raggr-frontend && yarn install && yarn build` |

See individual guides for detailed troubleshooting.

## Contributing

1. Read the [Development Guide](development.md)
2. Set up your local environment
3. Make changes and test locally
4. Generate migrations if needed
5. Submit a pull request

## Additional Resources

- [LangChain Documentation](https://python.langchain.com/)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Quart Documentation](https://quart.palletsprojects.com/)
- [Tortoise ORM Documentation](https://tortoise.github.io/)
- [Authelia Documentation](https://www.authelia.com/)

## Need Help?

- Check the relevant guide in this documentation
- Review troubleshooting sections
- Check application logs: `docker compose logs -f`
- Inspect database: `docker compose exec postgres psql -U raggr`

---

**Documentation Version**: 1.0
**Last Updated**: January 2026
