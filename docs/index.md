# SimbaRAG Documentation

SimbaRAG is a RAG-powered conversational AI system with enterprise authentication.

## Architecture

- **Backend**: Quart (async Python) with Tortoise ORM
- **Vector Store**: LangChain with configurable embeddings
- **Auth Stack**: LLDAP → Authelia → OAuth2/OIDC
- **Database**: PostgreSQL

## Sections

- [Authentication](authentication.md) - OIDC flow, user management, and RBAC planning
