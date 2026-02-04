# Architecture

**Analysis Date:** 2026-02-04

## Pattern Overview

**Overall:** RAG (Retrieval-Augmented Generation) system with multi-agent conversational AI architecture

**Key Characteristics:**
- RAG pattern with vector database for document retrieval
- LangChain agent-based orchestration with tool calling
- Blueprint-based API organization (Quart framework)
- Asynchronous request handling throughout
- OIDC authentication with RBAC via LDAP groups
- Streaming SSE responses for real-time chat

## Layers

**API Layer (Quart Blueprints):**
- Purpose: HTTP request handling and route organization
- Location: `blueprints/*/`
- Contains: Blueprint definitions, route handlers, request/response serialization
- Depends on: Logic layer, models, JWT middleware
- Used by: Frontend (React SPA), external clients

**Logic Layer:**
- Purpose: Business logic and domain operations
- Location: `blueprints/*/logic.py`, `blueprints/*/agents.py`, `main.py`
- Contains: Conversation management, RAG indexing, agent orchestration, tool execution
- Depends on: Models, external services, LLM clients
- Used by: API layer

**Model Layer (Tortoise ORM):**
- Purpose: Database schema and data access
- Location: `blueprints/*/models.py`
- Contains: ORM model definitions, Pydantic serializers, database relationships
- Depends on: PostgreSQL database
- Used by: Logic layer, API layer

**Integration Layer:**
- Purpose: External service communication
- Location: `utils/`, `config/`
- Contains: Service clients (YNAB, Mealie, Paperless-NGX, OIDC)
- Depends on: External APIs
- Used by: Logic layer, tools

**Tool Layer (LangChain Tools):**
- Purpose: Agent-callable functions for extended capabilities
- Location: `blueprints/conversation/agents.py`
- Contains: `@tool` decorated functions for document search, web search, YNAB, Mealie
- Depends on: Integration layer, RAG logic
- Used by: LangChain agent

**Frontend (React SPA):**
- Purpose: User interface
- Location: `raggr-frontend/`
- Contains: React components, API service clients, authentication context
- Depends on: Backend API endpoints
- Used by: End users

## Data Flow

**Chat Query Flow:**

1. User submits query in frontend (`raggr-frontend/src/components/ChatScreen.tsx`)
2. Frontend calls `/api/conversation/query` with SSE streaming (`raggr-frontend/src/api/conversationService.ts`)
3. API endpoint validates JWT, fetches user and conversation (`blueprints/conversation/__init__.py`)
4. User message saved to database via Tortoise ORM (`blueprints/conversation/models.py`)
5. Recent conversation history (last 10 messages) loaded and formatted
6. LangChain agent invoked with messages payload (`blueprints/conversation/agents.py`)
7. Agent decides which tools to call based on query (simba_search, ynab_*, mealie_*, web_search)
8. Tools execute: RAG query (`blueprints/rag/logic.py`), API calls (`utils/*.py`)
9. LLM generates response using tool results
10. Response streamed back via SSE events (status updates, content chunks)
11. Complete response saved to database
12. Frontend renders streaming response in real-time

**RAG Document Flow:**

1. Admin triggers indexing via `/api/rag/index` or `/api/rag/reindex`
2. RAG logic fetches documents from Paperless-NGX (`blueprints/rag/fetchers.py`)
3. Documents chunked using LangChain text splitter (1000 chars, 200 overlap)
4. Embeddings generated using OpenAI embedding model (text-embedding-3-small)
5. Vectors stored in ChromaDB persistent collection (`chroma_db/`)
6. Query time: embeddings generated for query, similarity search retrieves top 2 docs
7. Documents serialized and passed to LLM as context

**State Management:**
- Conversation state: PostgreSQL via Tortoise ORM
- Vector embeddings: ChromaDB persistent storage
- User sessions: JWT tokens in frontend localStorage
- Authentication: OIDC state in-memory (production should use Redis)

## Key Abstractions

**Conversation:**
- Purpose: Represents a chat thread with message history
- Examples: `blueprints/conversation/models.py`
- Pattern: Aggregate root with message collection, foreign key to User

**ConversationMessage:**
- Purpose: Individual message in conversation (user or assistant)
- Examples: `blueprints/conversation/models.py`
- Pattern: Entity with enum speaker type, foreign key to Conversation

**User:**
- Purpose: Authenticated user with OIDC or local credentials
- Examples: `blueprints/users/models.py`
- Pattern: Entity with bcrypt password hashing, LDAP group membership, admin check method

**LangChain Agent:**
- Purpose: Orchestrates LLM calls with tool selection
- Examples: `blueprints/conversation/agents.py` (main_agent)
- Pattern: ReAct agent pattern with function calling via OpenAI-compatible API

**Tool Functions:**
- Purpose: Discrete capabilities callable by the agent
- Examples: `simba_search`, `ynab_budget_summary`, `mealie_shopping_list` in `blueprints/conversation/agents.py`
- Pattern: Decorated functions with docstrings that become tool descriptions

**LLMClient:**
- Purpose: Abstraction over LLM providers with fallback
- Examples: `llm.py`, `blueprints/conversation/agents.py`
- Pattern: Primary llama-server with OpenAI fallback, OpenAI-compatible interface

**Service Clients:**
- Purpose: External API integration wrappers
- Examples: `utils/ynab_service.py`, `utils/mealie_service.py`, `utils/request.py`
- Pattern: Class-based clients with async methods, relative date parsing

## Entry Points

**Web Application:**
- Location: `app.py`
- Triggers: `python app.py` or Docker container startup
- Responsibilities: Initialize Quart app, register blueprints, configure Tortoise ORM, serve React frontend

**CLI Indexing:**
- Location: `main.py` (when run as script)
- Triggers: `python main.py --reindex` or `--query <text>`
- Responsibilities: Document indexing, direct RAG queries without API

**Database Migrations:**
- Location: `aerich_config.py`
- Triggers: `aerich migrate`, `aerich upgrade`
- Responsibilities: Schema migration generation and application

**Admin Scripts:**
- Location: `scripts/add_user.py`, `scripts/user_message_stats.py`, `scripts/manage_vectorstore.py`
- Triggers: Manual execution
- Responsibilities: User management, analytics, vector store inspection

**React Frontend:**
- Location: `raggr-frontend/src/index.tsx`
- Triggers: Bundle served at `/` by backend
- Responsibilities: Initialize React app, authentication context, routing

## Error Handling

**Strategy:** Try-catch with logging at service boundaries, HTTP status codes for client errors

**Patterns:**
- API routes: Return JSON error responses with appropriate HTTP status codes (400, 401, 403, 500)
- Example: `blueprints/rag/__init__.py` line 26-27
- Async operations: Try-except blocks with logger.error for traceability
- Example: `blueprints/conversation/agents.py` line 142-145 (YNAB tool error handling)
- JWT validation: Decorator-based authentication with 401 response on failure
- Example: `@jwt_refresh_token_required` in all protected routes
- Frontend: Error callbacks in streaming service, redirect to login on session expiry
- Example: `raggr-frontend/src/components/ChatScreen.tsx` line 234-237
- Agent tool failures: Return error string to agent for recovery or user messaging
- Example: `blueprints/conversation/agents.py` line 384-385

## Cross-Cutting Concerns

**Logging:** Python logging module with INFO level, structured with logger names by module (utils.ynab_service, blueprints.conversation.agents)

**Validation:** Pydantic models for serialization, Tortoise ORM field constraints, JWT token validation via quart-jwt-extended

**Authentication:** OIDC (Authelia) with PKCE flow → JWT tokens → RBAC via LDAP groups. Decorators: `@jwt_refresh_token_required` for auth, `@admin_required` for admin-only endpoints (`blueprints/users/decorators.py`)

---

*Architecture analysis: 2026-02-04*
