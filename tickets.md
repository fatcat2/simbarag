# Integration: Twilio API for WhatsApp Interface (Multi-User)

## Overview
Integrate Twilio's WhatsApp API to allow users to interact with Simba via WhatsApp. This requires multi-user support, linking WhatsApp numbers to existing or new user accounts.

## Tasks

### Phase 1: Infrastructure and Database Changes
- [x] **[TICKET-001]** Update `User` model to include `whatsapp_number`.
- [x] **[TICKET-002]** Generate and apply migrations for the database changes.

### Phase 2: Twilio Integration Blueprint
- [x] **[TICKET-003]** Create a new blueprint for Twilio/WhatsApp webhook.
- [x] **[TICKET-004]** Implement Twilio signature validation for security.
    - Decorator enabled on webhook. Set `TWILIO_SIGNATURE_VALIDATION=false` to disable in dev. Set `TWILIO_WEBHOOK_URL` if behind a reverse proxy.
- [x] **[TICKET-005]** Implement User identification from WhatsApp phone number.

### Phase 3: Core Messaging Logic
- [x] **[TICKET-006]** Integrate `consult_simba_oracle` with the WhatsApp blueprint.
- [x] **[TICKET-007]** Implement outgoing WhatsApp message responses.
- [x] **[TICKET-008]** Handle conversation context in WhatsApp.

### Phase 4: Configuration and Deployment
- [x] **[TICKET-009]** Add Twilio credentials to environment variables.
    - Keys: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_WHATSAPP_NUMBER`.
- [ ] **[TICKET-010]** Document the Twilio webhook setup in `docs/whatsapp_integration.md`.
    - Include: Webhook URL format, Twilio Console setup instructions.

### Phase 5: Multi-user & Edge Cases
- [ ] **[TICKET-011]** Handle first-time users (auto-creation of accounts or invitation system).
- [ ] **[TICKET-012]** Handle media messages (optional/future: images, audio).
- [x] **[TICKET-013]** Rate limiting and error handling for Twilio requests.

## Implementation Details

### Twilio Webhook Payload (POST)
- `SmsMessageSid`, `NumMedia`, `Body`, `From`, `To`, `AccountSid`, etc.
- We primarily care about `Body` (user message) and `From` (user WhatsApp number).

### Workflow
1. Twilio receives a message -> POST to `/api/whatsapp/webhook`.
2. Validate signature.
3. Identify `User` by `From` number.
4. If not found, create a new `User` or return an error.
5. Get/create `Conversation` for this `User`.
6. Call `consult_simba_oracle` with the query and context.
7. Return response via TwiML `<Message>` tag.

---

# Integration: Obsidian Bidirectional Data Store

## Overview
Integrate Obsidian as a bidirectional data store using the [`obsidian-headless`](https://github.com/obsidianmd/obsidian-headless) npm package. SimbaRAG will be able to read/search Obsidian notes for RAG context and write new notes, research summaries, and tasks back to the vault via the LangChain agent.

## Tasks

### Phase 1: Infrastructure
- [ ] **[OBS-001]** Upgrade Node.js from 20 to 22 in `Dockerfile` (required by obsidian-headless).
- [ ] **[OBS-002]** Install `obsidian-headless` globally via npm in `Dockerfile`.
- [ ] **[OBS-003]** Add `obsidian_vault_data` volume and Obsidian env vars to `docker-compose.yml`.
- [ ] **[OBS-004]** Document Obsidian env vars in `.env.example` (`OBSIDIAN_AUTH_TOKEN`, `OBSIDIAN_VAULT_ID`, `OBSIDIAN_E2E_PASSWORD`, `OBSIDIAN_DEVICE_NAME`, `OBSIDIAN_CONTINUOUS_SYNC`).
- [ ] **[OBS-005]** Update `startup.sh` to conditionally run `ob sync --continuous` in background when `OBSIDIAN_CONTINUOUS_SYNC=true`.

### Phase 2: Core Service
- [ ] **[OBS-006]** Create `utils/obsidian_service.py` with `ObsidianService` class.
    - Vault setup via `ob sync-setup` (async subprocess)
    - One-time sync via `ob sync`
    - Sync status via `ob sync-status`
    - Walk vault directory for `.md` files (skip `.obsidian/`)
    - Parse Obsidian markdown: YAML frontmatter → metadata, wikilink conversion, embed stripping, tag extraction
    - Read specific note by relative path
    - Create new note with frontmatter (auto-adds `created_by: simbarag` + timestamp)
    - Create task note in configurable tasks folder

### Phase 3: RAG Indexing (Read)
- [ ] **[OBS-007]** Add `fetch_obsidian_documents()` to `blueprints/rag/logic.py` — uses `ObsidianService` to parse all vault `.md` files into LangChain `Document` objects with `source=obsidian` metadata.
- [ ] **[OBS-008]** Add `index_obsidian_documents()` to `blueprints/rag/logic.py` — deletes existing `source=obsidian` chunks, splits documents with shared `text_splitter`, embeds into shared `vector_store`.
- [ ] **[OBS-009]** Add `POST /api/rag/index-obsidian` endpoint (`@admin_required`) to `blueprints/rag/__init__.py`.

### Phase 4: Agent Tools (Read + Write)
- [ ] **[OBS-010]** Add `obsidian_search_notes` tool to `blueprints/conversation/agents.py` — semantic search via ChromaDB with `where={"source": "obsidian"}` filter.
- [ ] **[OBS-011]** Add `obsidian_read_note` tool to `blueprints/conversation/agents.py` — reads a specific note by relative path.
- [ ] **[OBS-012]** Add `obsidian_create_note` tool to `blueprints/conversation/agents.py` — creates a new markdown note in the vault (title, content, folder, tags).
- [ ] **[OBS-013]** Add `obsidian_create_task` tool to `blueprints/conversation/agents.py` — creates a task note with optional due date.
- [ ] **[OBS-014]** Register Obsidian tools conditionally (follow YNAB pattern: `obsidian_enabled` flag).
- [ ] **[OBS-015]** Update system prompt in `blueprints/conversation/__init__.py` with Obsidian tool usage instructions.

### Phase 5: Testing & Verification
- [ ] **[OBS-016]** Verify Docker image builds with Node.js 22 + obsidian-headless.
- [ ] **[OBS-017]** Test vault sync: setup → sync → verify files appear in `/app/data/obsidian`.
- [ ] **[OBS-018]** Test indexing: `POST /api/rag/index-obsidian` → verify chunks in ChromaDB with `source=obsidian`.
- [ ] **[OBS-019]** Test agent read tools: chat queries trigger `obsidian_search_notes` and `obsidian_read_note`.
- [ ] **[OBS-020]** Test agent write tools: chat creates notes/tasks → files appear in vault → sync pushes to Obsidian.

## Implementation Details

### Key Files
- `utils/obsidian_service.py` — new, core service (follows `utils/ynab_service.py` pattern)
- `blueprints/conversation/agents.py` — add tools (follows YNAB tool pattern at lines 101-279)
- `blueprints/conversation/__init__.py` — update system prompt (line ~94)
- `blueprints/rag/logic.py` — add indexing functions (reuse `vector_store`, `text_splitter`)
- `blueprints/rag/__init__.py` — add index endpoint

### Write-back Model
Files written to the vault directory are automatically synced to Obsidian Sync by the `ob sync --continuous` background process. No separate push step needed.

### Environment Variables
| Variable | Required | Description |
|----------|----------|-------------|
| `OBSIDIAN_AUTH_TOKEN` | Yes | Auth token for Obsidian Sync (non-interactive) |
| `OBSIDIAN_VAULT_ID` | Yes | Remote vault ID or name |
| `OBSIDIAN_E2E_PASSWORD` | If E2EE | End-to-end encryption password |
| `OBSIDIAN_DEVICE_NAME` | No | Client identifier (default: `simbarag-server`) |
| `OBSIDIAN_CONTINUOUS_SYNC` | No | Enable background sync (default: `false`) |

---

# Integration: WhatsApp to LangChain Agent Migration

## Overview
Migrate the WhatsApp blueprint from custom LLM logic to the LangChain agent-based system used by the conversation blueprint. This will provide Tavily web search, YNAB integration, and improved message handling capabilities.

## Tasks

### Phase 1: Import and Setup Changes
- [x] **[WA-001]** Remove dependency on `main.py`'s `consult_simba_oracle` import in `blueprints/whatsapp/__init__.py`.
- [x] **[WA-002]** Import `main_agent` from `blueprints.conversation.agents` in `blueprints/whatsapp/__init__.py`.
- [ ] **[WA-003]** Add import for `query_vector_store` from `blueprints.rag.logic` (if needed for simba_search tool).
- [x] **[WA-004]** Verify `main_agent` is already initialized as a global variable in `agents.py` (it is at line 295).

### Phase 2: Agent Invocation Adaptation
- [x] **[WA-005]** Replace `consult_simba_oracle()` call (lines 171-178) with LangChain agent invocation.
- [x] **[WA-006]** Add system prompt with Simba facts, medical conditions, and recent events from `blueprints/conversation/__init__.py` (lines 55-95).
- [x] **[WA-007]** Build messages payload with role-based conversation history (last 10 messages).
- [x] **[WA-008]** Handle agent response extraction: `response.get("messages", [])[-1].content`.
- [x] **[WA-009]** Keep existing error handling around agent invocation (try/except block).

### Phase 3: Configuration and Logging
- [x] **[WA-010]** Add YNAB availability logging (check `os.getenv("YNAB_ACCESS_TOKEN")` is not None) in webhook handler.
- [x] **[WA-011]** Ensure `main_agent` tools include `simba_search`, `web_search`, and optionally YNAB tools (already configured in `agents.py`).
- [x] **[WA-012]** Verify `simba_search` tool uses `query_vector_store()` which supports `where={"source": "paperless"}` filter (no change needed, works with existing ChromaDB collection).

### Phase 4: Testing Strategy
- [ ] **[WA-013]** Test Simba queries (e.g., "How much does Simba weigh?") — should use `simba_search` tool.
- [ ] **[WA-014]** Test general chat queries (e.g., "What's the weather?") — should use LLM directly, no tools.
- [ ] **[WA-015]** Test web search capability (e.g., "What's the latest cat health research?") — should use `web_search` tool with Tavily.
- [ ] **[WA-016]** Test YNAB integration if configured (e.g., "How much did I spend on food?") — should use appropriate YNAB tool.
- [ ] **[WA-017]** Test conversation context preservation (send multiple messages in sequence).
- [ ] **[WA-018]** Test rate limiting still works after migration.
- [ ] **[WA-019]** Test user creation and allowlist still function correctly.
- [ ] **[WA-020]** Test error handling for agent failures (returns "Sorry, I'm having trouble thinking right now. 😿").

### Phase 5: Cleanup and Documentation
- [ ] **[WA-021]** Optionally remove or deprecate deprecated `main.py` functions: `classify_query()`, `consult_oracle()`, `llm_chat()`, `consult_simba_oracle()` (keep for CLI tool usage).
- [ ] **[WA-022]** Update code comments in `main.py` to indicate WhatsApp no longer uses these functions.
- [ ] **[WA-023]** Document the agent-based approach in `docs/whatsapp_integration.md` (if file exists) or create new documentation.

## Implementation Details

### Current WhatsApp Flow
1. Twilio webhook → `blueprints/whatsapp/__init__.webhook()`
2. Call `consult_simba_oracle(input, transcript)` from `main.py`
3. `consult_simba_oracle()` uses custom `QueryGenerator` to classify query
4. Routes to `consult_oracle()` (ChromaDB) or `llm_chat()` (simple chat)
5. Returns text response

### Target WhatsApp Flow
1. Twilio webhook → `blueprints/whatsapp/__init__.webhook()`
2. Build LangChain messages payload with system prompt and conversation history
3. Invoke `main_agent.ainvoke({"messages": messages_payload})`
4. Agent decides when to use tools (simba_search, web_search, YNAB)
5. Returns text response from last message

### Key Differences
1. **No manual query classification** — Agent decides based on LLM reasoning
2. **Tavily web_search** now available for current information
3. **YNAB integration** available if configured
4. **System prompt consistency** with conversation blueprint
5. **Message format** — LangChain messages array vs transcript string

### Environment Variables
No new environment variables needed. Uses existing:
- `LLAMA_SERVER_URL` — for LLM model
- `TAVILY_API_KEY` — for web search
- `YNAB_ACCESS_TOKEN` — for budget integration (optional)

### Files Modified
- `blueprints/whatsapp/__init__.py` — Main webhook handler
