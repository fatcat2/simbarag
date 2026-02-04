# Codebase Concerns

**Analysis Date:** 2026-02-04

## Tech Debt

**Duplicate system prompts in streaming and non-streaming endpoints:**
- Issue: Large system prompt (112 lines) duplicated verbatim in two endpoints
- Files: `/Users/ryanchen/Programs/raggr/blueprints/conversation/__init__.py` (lines 56-111 and 206-261)
- Impact: Changes to prompt must be made in two places, increasing maintenance burden and risk of inconsistency
- Fix approach: Extract system prompt to a constant or configuration file

**SQLite database for indexing tracking alongside PostgreSQL:**
- Issue: Uses SQLite (`database/visited.db`) to track indexed Paperless documents while main data is in PostgreSQL
- Files: `/Users/ryanchen/Programs/raggr/main.py` (lines 73, 212, 226), `/Users/ryanchen/Programs/raggr/scripts/index_immich.py` (line 33)
- Impact: Two database systems to manage, no transactions across databases, deployment complexity
- Fix approach: Migrate indexing tracking to PostgreSQL table using Tortoise ORM

**Broad exception catching throughout codebase:**
- Issue: 35+ instances of `except Exception as e` catching all exceptions indiscriminately
- Files: `/Users/ryanchen/Programs/raggr/blueprints/conversation/agents.py` (12 instances), `/Users/ryanchen/Programs/raggr/utils/ynab_service.py` (7 instances), `/Users/ryanchen/Programs/raggr/utils/mealie_service.py` (7 instances), `/Users/ryanchen/Programs/raggr/blueprints/conversation/__init__.py` (line 171), `/Users/ryanchen/Programs/raggr/blueprints/rag/__init__.py` (lines 26, 46)
- Impact: Masks programming errors, makes debugging difficult, catches system exceptions that shouldn't be caught
- Fix approach: Replace with specific exception types (ValueError, KeyError, HTTPException, etc.)

**Legacy main.py RAG logic not used by application:**
- Issue: `/Users/ryanchen/Programs/raggr/main.py` contains 275 lines of RAG logic including `consult_oracle()`, `classify_query()`, `consult_simba_oracle()` but app uses LangChain agents instead
- Files: `/Users/ryanchen/Programs/raggr/main.py`, `/Users/ryanchen/Programs/raggr/app.py` (imports `consult_simba_oracle` but endpoint is commented/unused)
- Impact: Dead code increases maintenance burden, confuses new developers about which code path is active
- Fix approach: Archive or remove unused code after verifying no production dependencies

**Environment variable typo in docker-compose:**
- Issue: Docker compose uses `TAVILIY_KEY` instead of `TAVILY_API_KEY`
- Files: `/Users/ryanchen/Programs/raggr/docker-compose.yml` (line 41), `/Users/ryanchen/Programs/raggr/docker-compose.dev.yml` (line 44)
- Impact: Tavily web search won't work in production Docker deployment
- Fix approach: Standardize on `TAVILY_API_KEY` throughout

**Hardcoded OpenAI model in conversation rename logic:**
- Issue: Uses `gpt-4o-mini` without environment variable configuration
- Files: `/Users/ryanchen/Programs/raggr/blueprints/conversation/logic.py` (line 72)
- Impact: Cannot switch models, will fail if OpenAI key not configured even when using local LLM
- Fix approach: Make model configurable via environment variable, use same fallback pattern as main agent

**Debug mode enabled in production app entry:**
- Issue: `debug=True` hardcoded in app.run()
- Files: `/Users/ryanchen/Programs/raggr/app.py` (line 165)
- Impact: Exposes stack traces and sensitive information if run directly (mitigated by Docker CMD using startup.sh)
- Fix approach: Use environment variable for debug flag

## Known Bugs

**Empty returns in PDF cleaner error handling:**
- Issue: Error handlers return None or empty lists without logging context
- Files: `/Users/ryanchen/Programs/raggr/utils/cleaner.py` (lines 58, 74, 81)
- Symptoms: Silent failures during PDF processing, no indication why document wasn't indexed
- Trigger: PDF processing errors (malformed PDFs, image conversion failures)
- Workaround: Check logs at DEBUG level, manually test PDF processing

**Console debug statements left in production code:**
- Issue: print() statements instead of logging in multiple locations
- Files: `/Users/ryanchen/Programs/raggr/blueprints/conversation/agents.py` (lines 109-113), `/Users/ryanchen/Programs/raggr/blueprints/conversation/logic.py` (line 20), `/Users/ryanchen/Programs/raggr/blueprints/conversation/__init__.py` (line 311), `/Users/ryanchen/Programs/raggr/raggr-frontend/src/components/ChatScreen.tsx` (lines 99-100, 132-133)
- Symptoms: Unstructured output mixed with proper logs, no log levels
- Fix approach: Replace with structured logging

**Conversation name timestamp method incorrect:**
- Issue: Uses `.timestamp` property instead of `.timestamp()` method
- Files: `/Users/ryanchen/Programs/raggr/blueprints/conversation/__init__.py` (line 330)
- Symptoms: Conversation name will be method reference string instead of timestamp
- Fix approach: Change to `datetime.datetime.now().timestamp()`

## Security Considerations

**JWT secret key has weak default:**
- Risk: Default JWT_SECRET_KEY is "SECRET_KEY" if environment variable not set
- Files: `/Users/ryanchen/Programs/raggr/app.py` (line 39)
- Current mitigation: Documentation requires setting environment variable
- Recommendations: Fail fast on startup if JWT_SECRET_KEY is default value, generate random key on first run

**Hardcoded API key placeholder in llama-server configuration:**
- Risk: API key set to "not-needed" for local llama-server
- Files: `/Users/ryanchen/Programs/raggr/llm.py` (line 16), `/Users/ryanchen/Programs/raggr/blueprints/conversation/agents.py` (line 28)
- Current mitigation: Only used for local trusted network LLM servers
- Recommendations: Document that llama-server should be on trusted network only, consider basic authentication

**No rate limiting on streaming endpoints:**
- Risk: Users can spawn unlimited concurrent streaming requests
- Files: `/Users/ryanchen/Programs/raggr/blueprints/conversation/__init__.py` (line 29)
- Current mitigation: None
- Recommendations: Add per-user rate limiting, request queue, or connection limit

**Sensitive data in error messages:**
- Risk: Full exception details returned to client in tool error messages
- Files: `/Users/ryanchen/Programs/raggr/blueprints/conversation/agents.py` (lines 145, 219, 280, etc.)
- Current mitigation: Only exposed to authenticated users
- Recommendations: Sanitize error messages, return generic errors to client, log full details server-side

## Performance Bottlenecks

**Large conversation history loaded on every query:**
- Problem: Fetches all messages then slices to last 10 in memory
- Files: `/Users/ryanchen/Programs/raggr/blueprints/conversation/__init__.py` (lines 38, 47-50, 188, 197-200)
- Cause: No database-level limit on message fetch
- Improvement path: Add database query limit, use `.order_by('-created_at').limit(10)` at query level

**Sequential document indexing:**
- Problem: Documents indexed one at a time in loop
- Files: `/Users/ryanchen/Programs/raggr/main.py` (lines 67-96)
- Cause: No parallel processing or batching
- Improvement path: Use asyncio.gather() for concurrent PDF processing, batch ChromaDB inserts

**No caching for YNAB API calls:**
- Problem: Every query makes fresh API calls even for recently accessed data
- Files: `/Users/ryanchen/Programs/raggr/utils/ynab_service.py` (all methods)
- Cause: No caching layer
- Improvement path: Add Redis/in-memory cache with TTL for budget data, cache budget summaries for 5-15 minutes

**Frontend loads all conversations on mount:**
- Problem: Fetches all conversations without pagination
- Files: `/Users/ryanchen/Programs/raggr/raggr-frontend/src/components/ChatScreen.tsx` (lines 89-104)
- Cause: No pagination in API or frontend
- Improvement path: Add cursor-based pagination, lazy load older conversations

**ChromaDB persistence path creates I/O bottleneck:**
- Problem: All embedding queries/inserts hit disk-backed SQLite database
- Files: `/Users/ryanchen/Programs/raggr/main.py` (line 19)
- Cause: Uses PersistentClient without in-memory optimization
- Improvement path: Consider ChromaDB server mode for production, add memory-backed cache layer

## Fragile Areas

**LangChain agent tool calling depends on exact model support:**
- Files: `/Users/ryanchen/Programs/raggr/blueprints/conversation/agents.py` (line 733)
- Why fragile: Comment says "Llama 3.1 supports native function calling" but not all local models do
- Test coverage: No automated tests for tool calling
- Safe modification: Always test with target model before deploying, add fallback for models without tool support

**OIDC user provisioning auto-migrates local users:**
- Files: `/Users/ryanchen/Programs/raggr/blueprints/users/oidc_service.py` (lines 42-53)
- Why fragile: Automatically converts local auth users to OIDC based on email match, clears passwords
- Test coverage: No tests detected
- Safe modification: Add dry-run mode, require admin confirmation for migrations, back up user table first

**Streaming response parsing relies on specific line format:**
- Files: `/Users/ryanchen/Programs/raggr/raggr-frontend/src/api/conversationService.ts` (lines 95-135)
- Why fragile: Assumes SSE format with `data: ` prefix and JSON, buffer handling for incomplete lines
- Test coverage: No tests for edge cases (connection drops mid-stream, malformed JSON, large chunks)
- Safe modification: Add comprehensive error handling, test with slow connections and large responses

**Vector store query uses unvalidated metadata filters:**
- Files: `/Users/ryanchen/Programs/raggr/main.py` (lines 133-155)
- Why fragile: Metadata filters from QueryGenerator passed directly to ChromaDB without validation
- Test coverage: None detected
- Safe modification: Validate filter structure before query, whitelist allowed filter keys

**Document chunking without validation:**
- Files: `/Users/ryanchen/Programs/raggr/utils/chunker.py` referenced in `/Users/ryanchen/Programs/raggr/main.py` (line 69)
- Why fragile: No validation of chunk size, overlap, or content before embedding
- Test coverage: None detected
- Safe modification: Add max chunk length validation, handle empty documents gracefully

## Scaling Limits

**Single PostgreSQL connection per request:**
- Current capacity: Depends on PostgreSQL max_connections (default ~100)
- Limit: Connection exhaustion under high concurrent load
- Scaling path: Implement connection pooling with Tortoise ORM pool settings, increase PostgreSQL max_connections

**ChromaDB local persistence not horizontally scalable:**
- Current capacity: Single-node file-based storage
- Limit: Cannot distribute across multiple app instances, I/O bound on single disk
- Scaling path: Migrate to ChromaDB server mode with shared storage or dedicated vector DB (Qdrant, Pinecone, Weaviate)

**Server-sent events keep connections open:**
- Current capacity: Limited by web server worker count and file descriptor limits
- Limit: Each streaming query holds connection open for full duration (10-60+ seconds)
- Scaling path: Use message queue (Redis Streams, RabbitMQ) for response streaming, implement connection pooling

**No horizontal scaling for background indexing:**
- Current capacity: Single process indexes documents sequentially
- Limit: Cannot parallelize across multiple workers/containers
- Scaling path: Implement task queue (Celery, RQ) for distributed indexing, use message broker to coordinate

**Frontend state management in React useState:**
- Current capacity: Works for single user, no persistence
- Limit: State lost on refresh, no offline support, memory growth with long conversations
- Scaling path: Migrate to Redux/Zustand with persistence, implement virtual scrolling for long conversations

## Dependencies at Risk

**ynab Python package is community-maintained:**
- Risk: Unofficial YNAB API wrapper, last update may lag behind API changes
- Impact: YNAB features break if API changes
- Migration plan: Monitor YNAB API changelog, consider switching to direct httpx/aiohttp requests for control

**LangChain rapid version changes:**
- Risk: Frequent breaking changes between minor versions in LangChain ecosystem
- Impact: Upgrades require code changes, agent patterns deprecated
- Migration plan: Pin specific versions in pyproject.toml, test thoroughly before upgrading

**Quart framework less mature than Flask:**
- Risk: Smaller community, fewer third-party extensions, async bugs less documented
- Impact: Harder to find solutions for edge cases
- Migration plan: Consider FastAPI as alternative (better async support, more active), or Flask with async support

## Missing Critical Features

**No observability/monitoring:**
- Problem: No structured logging, metrics, or tracing
- Blocks: Understanding production issues, performance debugging, user behavior analysis
- Priority: High

**No backup strategy for ChromaDB vector store:**
- Problem: Vector embeddings not backed up, expensive to regenerate
- Blocks: Disaster recovery, migrating instances
- Priority: High

**No API versioning:**
- Problem: Breaking API changes will break existing clients
- Blocks: Frontend/backend independent deployment
- Priority: Medium

**No health check endpoints:**
- Problem: Container orchestration cannot verify service health
- Blocks: Proper Kubernetes deployment, load balancer integration
- Priority: Medium

**No user quotas or resource limits:**
- Problem: Users can consume unlimited API calls, storage, compute
- Blocks: Cost control, fair resource allocation
- Priority: Medium

## Test Coverage Gaps

**No tests for LangChain agent tools:**
- What's not tested: All 15 tools in `/Users/ryanchen/Programs/raggr/blueprints/conversation/agents.py`
- Files: No test files detected for agents module
- Risk: Tool failures not caught until production, parameter handling bugs
- Priority: High

**No tests for streaming SSE implementation:**
- What's not tested: Server-sent events parsing, partial message handling, error recovery
- Files: `/Users/ryanchen/Programs/raggr/blueprints/conversation/__init__.py` (streaming endpoints), `/Users/ryanchen/Programs/raggr/raggr-frontend/src/api/conversationService.ts`
- Risk: Connection drops, malformed responses cause undefined behavior
- Priority: High

**No tests for OIDC authentication flow:**
- What's not tested: User provisioning, group claims parsing, token validation
- Files: `/Users/ryanchen/Programs/raggr/blueprints/users/oidc_service.py`, `/Users/ryanchen/Programs/raggr/blueprints/users/__init__.py`
- Risk: Auth bypass, user migration bugs, group permission issues
- Priority: High

**No integration tests for RAG pipeline:**
- What's not tested: End-to-end document indexing, query, and response generation
- Files: `/Users/ryanchen/Programs/raggr/blueprints/rag/logic.py`, `/Users/ryanchen/Programs/raggr/main.py`
- Risk: Embedding model changes, ChromaDB version changes break retrieval
- Priority: Medium

**No tests for external service integrations:**
- What's not tested: YNAB API error handling, Mealie API error handling, Tavily search failures
- Files: `/Users/ryanchen/Programs/raggr/utils/ynab_service.py`, `/Users/ryanchen/Programs/raggr/utils/mealie_service.py`
- Risk: API changes break features silently, rate limits not handled
- Priority: Medium

---

*Concerns audit: 2026-02-04*
