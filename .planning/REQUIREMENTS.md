# Requirements: SimbaRAG Email Integration

**Defined:** 2026-02-04
**Core Value:** Personal information retrieval through natural conversation - ask about any aspect of your documented life (papers, finances, meals, emails) and get accurate, context-aware answers.

## v1 Requirements

### Email Account Management

- [ ] **ACCT-01**: Admin can add new IMAP account with host, port, username, password, and folder selection
- [ ] **ACCT-02**: Admin can test IMAP connection before saving configuration
- [ ] **ACCT-03**: Admin can view list of configured email accounts
- [ ] **ACCT-04**: Admin can edit existing email account configuration
- [ ] **ACCT-05**: Admin can delete email account (removes config and associated emails from index)
- [ ] **ACCT-06**: Email account credentials are stored securely (encrypted in database)
- [ ] **ACCT-07**: Only users in lldap_admin group can access email account management

### Email Ingestion & Sync

- [ ] **SYNC-01**: System connects to IMAP server and fetches messages from configured folders
- [ ] **SYNC-02**: System parses email metadata (subject, sender name, sender address, date received)
- [ ] **SYNC-03**: System extracts email body text from both plain text and HTML formats
- [ ] **SYNC-04**: System generates embeddings for email content and stores in ChromaDB
- [ ] **SYNC-05**: System performs scheduled sync at configurable intervals (default: hourly)
- [ ] **SYNC-06**: System tracks last sync timestamp for each email account
- [ ] **SYNC-07**: System performs incremental sync (only fetches emails since last sync)
- [ ] **SYNC-08**: System logs sync status (success/failure, email count, errors) for monitoring
- [ ] **SYNC-09**: Sync operates in background without blocking web requests

### Email Retention & Cleanup

- [ ] **RETN-01**: System automatically purges emails older than configured retention period from vector index
- [ ] **RETN-02**: Admin can configure retention period per account (default: 30 days)
- [ ] **RETN-03**: System runs scheduled cleanup job to remove expired emails
- [ ] **RETN-04**: System logs cleanup actions (emails purged, timestamps) for audit trail
- [ ] **RETN-05**: System preserves original emails on IMAP server (does not delete from server)

### Email Query & Analytics

- [ ] **QUERY-01**: LangChain agent has tool to search emails by content, sender, or date range
- [ ] **QUERY-02**: Agent can identify who has emailed the user most frequently in a given timeframe
- [ ] **QUERY-03**: Agent can analyze subject lines and identify common topics
- [ ] **QUERY-04**: Agent can detect subscription/newsletter patterns (recurring senders, unsubscribe links)
- [ ] **QUERY-05**: Agent can answer time-based queries ("emails this week", "emails in January")
- [ ] **QUERY-06**: Only admin users can query email content via conversation interface

## v2 Requirements

### Advanced Analytics

- **ANLYT-01**: Email attachment metadata indexing (filenames, types, sizes)
- **ANLYT-02**: Thread/conversation grouping for related emails
- **ANLYT-03**: Email sentiment analysis (positive/negative/neutral)
- **ANLYT-04**: VIP sender designation and filtering

### Enhanced Sync

- **SYNC-10**: Real-time push notifications via IMAP IDLE
- **SYNC-11**: Selective folder sync (include/exclude patterns)
- **SYNC-12**: Sync progress indicators in UI

### Email Actions

- **ACTION-01**: Mark emails as read/unread through agent commands
- **ACTION-02**: Delete emails from server through agent commands
- **ACTION-03**: Move emails to folders through agent commands

## Out of Scope

| Feature | Reason |
|---------|--------|
| SMTP email sending | User wants read-only inbox analytics, not composition |
| Email attachment content extraction | High complexity, focus on text content for v1 |
| POP3 support | IMAP provides better state management and sync capabilities |
| Non-admin email access | Privacy-sensitive feature, restrict to trusted administrators |
| Email filtering rules | Out of scope for analytics use case |
| Calendar integration | Different domain, not related to inbox analytics |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| ACCT-01 | Phase 2 | Pending |
| ACCT-02 | Phase 2 | Pending |
| ACCT-03 | Phase 2 | Pending |
| ACCT-04 | Phase 2 | Pending |
| ACCT-05 | Phase 2 | Pending |
| ACCT-06 | Phase 2 | Pending |
| ACCT-07 | Phase 2 | Pending |
| SYNC-01 | Phase 3 | Pending |
| SYNC-02 | Phase 3 | Pending |
| SYNC-03 | Phase 3 | Pending |
| SYNC-04 | Phase 3 | Pending |
| SYNC-05 | Phase 3 | Pending |
| SYNC-06 | Phase 3 | Pending |
| SYNC-07 | Phase 3 | Pending |
| SYNC-08 | Phase 3 | Pending |
| SYNC-09 | Phase 3 | Pending |
| RETN-01 | Phase 3 | Pending |
| RETN-02 | Phase 3 | Pending |
| RETN-03 | Phase 3 | Pending |
| RETN-04 | Phase 3 | Pending |
| RETN-05 | Phase 3 | Pending |
| QUERY-01 | Phase 4 | Pending |
| QUERY-02 | Phase 4 | Pending |
| QUERY-03 | Phase 4 | Pending |
| QUERY-04 | Phase 4 | Pending |
| QUERY-05 | Phase 4 | Pending |
| QUERY-06 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 25 total
- Mapped to phases: 25
- Unmapped: 0

---
*Requirements defined: 2026-02-04*
*Last updated: 2026-02-07 after roadmap creation*
