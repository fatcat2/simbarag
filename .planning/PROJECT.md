# SimbaRAG Email Integration

## What This Is

A personal RAG (Retrieval-Augmented Generation) conversational AI system that answers questions about your life through document search, budget tracking, meal planning, and now email inbox analytics. It ingests documents from Paperless-NGX, YNAB transactions, Mealie recipes, and (new) IMAP email to provide intelligent, context-aware responses.

## Core Value

Personal information retrieval through natural conversation - ask about any aspect of your documented life (papers, finances, meals, emails) and get accurate, context-aware answers drawn from your own data sources.

## Requirements

### Validated

- ✓ OIDC authentication via Authelia with PKCE flow — existing
- ✓ RBAC using LDAP groups (lldap_admin for admin privileges) — existing
- ✓ Multi-user conversations with persistent message history — existing
- ✓ RAG document search from Paperless-NGX documents — existing
- ✓ Multi-agent LangChain orchestration with tool calling — existing
- ✓ YNAB budget integration (budget summary, transactions, spending insights) — existing
- ✓ Mealie meal planning integration (shopping lists, meal plans, recipes) — existing
- ✓ Tavily web search for real-time information — existing
- ✓ Streaming SSE chat responses for real-time feedback — existing
- ✓ Vector embeddings in ChromaDB for similarity search — existing
- ✓ JWT session management with refresh tokens — existing
- ✓ Local LLM support via llama-server with OpenAI fallback — existing

### Active

- [ ] IMAP email ingestion for inbox analytics
- [ ] Multi-account email support (multiple IMAP connections)
- [ ] Admin-only email access (configuration and queries)
- [ ] Scheduled email sync (configurable interval)
- [ ] Auto-purge emails older than 30 days from vector index
- [ ] Index email metadata: subject, body text, sender information
- [ ] Read-only email analysis (no modification/deletion of emails)
- [ ] Email-aware LangChain tools (who's emailing, what subjects, subscription patterns)

### Out of Scope

- Email actions (mark read/unread, delete, archive) — read-only analytics only
- SMTP sending capabilities — inbox ingestion only
- Email attachment indexing — too complex for v1, focus on text content
- Real-time email sync — scheduled sync sufficient, reduces server load
- POP3 support — IMAP provides better state management
- Non-admin email access — privacy-sensitive feature, admin-only

## Context

**Existing Architecture:**
- Python/Quart async backend with React frontend
- Tortoise ORM with PostgreSQL for relational data
- ChromaDB for vector embeddings (persistent storage)
- Blueprint-based API organization with `/api/rag`, `/api/conversation`, `/api/user`
- LangChain agent with `@tool` decorated functions for extended capabilities
- Existing integrations: Paperless-NGX (documents), YNAB (finance), Mealie (meals), Tavily (web)

**Email Use Cases:**
- "What emails did I get this week?"
- "Who has been emailing me most frequently?"
- "Show me subscription emails I should unsubscribe from"
- "What topics am I being emailed about?"
- Inbox pattern recognition and analytics through natural language

**Privacy Considerations:**
- Email is highly personal - admin-only access prevents exposure to other users
- 30-day retention window limits data exposure and storage growth
- Self-hosted deployment keeps email content on user's infrastructure

## Constraints

- **Tech Stack**: Python/Quart backend — must use existing framework and patterns
- **Storage**: ChromaDB vector store — email embeddings live alongside documents
- **Authentication**: LDAP group-based RBAC — email features gated to `lldap_admin` group
- **Deployment**: Docker Compose self-hosted — no cloud email storage or processing
- **Retention**: 30-day sliding window — automatic purge of older emails from index
- **Performance**: Scheduled sync only — avoid real-time polling overhead on mail servers

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| IMAP only (no SMTP) | User wants inbox analytics, not sending capabilities | — Pending |
| Admin-only access | Email is privacy-sensitive, limit to trusted admins | — Pending |
| 30-day retention | Balance utility with privacy/storage concerns | — Pending |
| Scheduled sync | Reduces server load vs real-time polling | — Pending |
| No attachment indexing | Complexity vs value, focus on text content first | — Pending |
| ChromaDB for emails | Reuse existing vector store, no new infrastructure | — Pending |

---
*Last updated: 2026-02-04 after initialization*
