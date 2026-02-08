# Roadmap: SimbaRAG Email Integration

## Overview

Add IMAP email ingestion to SimbaRAG's existing document/finance/meal analytics capabilities. Admin users can configure email accounts, system syncs and embeds emails into ChromaDB on a schedule, automatically purges emails older than 30 days, and provides LangChain tools for inbox analytics through natural conversation.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Foundation** - Database models and IMAP utilities
- [ ] **Phase 2: Account Management** - Admin UI for configuring email accounts
- [ ] **Phase 3: Email Ingestion** - Sync engine, embeddings, retention cleanup
- [ ] **Phase 4: Query Tools** - LangChain tools for email analytics

## Phase Details

### Phase 1: Foundation
**Goal**: Core infrastructure for email ingestion is in place
**Depends on**: Nothing (first phase)
**Requirements**: None (foundational infrastructure)
**Success Criteria** (what must be TRUE):
  1. Database tables exist for email accounts, sync status, and email metadata
  2. IMAP connection utility can authenticate and list folders from test server
  3. Email body parser extracts text from both plain text and HTML formats
  4. Encryption utility securely stores and retrieves IMAP credentials
**Plans**: 2 plans

Plans:
- [x] 01-01-PLAN.md — Database models with encrypted credentials and migration
- [x] 01-02-PLAN.md — IMAP connection service and email body parser

### Phase 2: Account Management
**Goal**: Admin users can configure and manage IMAP email accounts
**Depends on**: Phase 1
**Requirements**: ACCT-01, ACCT-02, ACCT-03, ACCT-04, ACCT-05, ACCT-06, ACCT-07
**Success Criteria** (what must be TRUE):
  1. Admin can add new IMAP account with host, port, username, password, folder selection
  2. Admin can test IMAP connection and see success/failure before saving
  3. Admin can view list of configured accounts with masked credentials
  4. Admin can edit existing account configuration and delete accounts
  5. Only users in lldap_admin group can access email account endpoints
**Plans**: TBD

Plans:
- [ ] 02-01: TBD

### Phase 3: Email Ingestion
**Goal**: System automatically syncs emails, creates embeddings, and purges old content
**Depends on**: Phase 2
**Requirements**: SYNC-01, SYNC-02, SYNC-03, SYNC-04, SYNC-05, SYNC-06, SYNC-07, SYNC-08, SYNC-09, RETN-01, RETN-02, RETN-03, RETN-04, RETN-05
**Success Criteria** (what must be TRUE):
  1. System connects to configured IMAP accounts and fetches messages from selected folders
  2. System parses email metadata (subject, sender, date) and extracts body text from plain/HTML
  3. System generates embeddings and stores emails in ChromaDB with metadata
  4. System performs scheduled sync at configurable intervals (default hourly)
  5. System tracks last sync timestamp and performs incremental sync (only new emails)
  6. System automatically purges emails older than retention period (default 30 days)
  7. Admin can view sync logs showing success/failure, counts, and errors
**Plans**: TBD

Plans:
- [ ] 03-01: TBD

### Phase 4: Query Tools
**Goal**: Admin users can query email content through conversational interface
**Depends on**: Phase 3
**Requirements**: QUERY-01, QUERY-02, QUERY-03, QUERY-04, QUERY-05, QUERY-06
**Success Criteria** (what must be TRUE):
  1. LangChain agent has tool to search emails by content, sender, or date range
  2. Agent can identify most frequent senders in a timeframe
  3. Agent can analyze subject lines and identify common topics
  4. Agent can detect subscription/newsletter patterns (recurring senders, unsubscribe links)
  5. Agent can answer time-based queries ("emails this week", "emails in January")
  6. Only admin users can query email content via conversation interface
**Plans**: TBD

Plans:
- [ ] 04-01: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 2/2 | Complete | 2026-02-08 |
| 2. Account Management | 0/1 | Not started | - |
| 3. Email Ingestion | 0/1 | Not started | - |
| 4. Query Tools | 0/1 | Not started | - |
