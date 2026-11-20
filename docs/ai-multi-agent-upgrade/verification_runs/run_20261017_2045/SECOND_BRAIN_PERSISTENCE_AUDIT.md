# SECOND BRAIN PERSISTENCE & WHITELIST AUDIT

## Overview
- **PostgreSQL Schema:** `qldapm_knowledge` (segregated from OpenProject `public` tables)
- **SQLite Engine:** Persistent file with FTS5 virtual table indexing
- **Project Whitelist:** Updated to include Project `3` and identifier `QLDAPM-LOCAL`

## Test Results

| Test | Result | Details |
|------|--------|---------|
| `PG-SCHEMA-ISOLATION` | **PASS** | Public tables with 'knowledge': 0 (expected 0) |
| `WHITELIST-PROJECT-3` | **PASS** | ALLOWED_PROJECTS includes 3 and QLDAPM-LOCAL: {'QLDAPM-LOCAL', 'QAG3', 'DEMO-PROJECT', 'QLDAPM', '3', 'DEMO'} |
| `CLASSIFY-PROJECT-3` | **PASS** | Classified project_id=3 |
| `REJECT-UNAUTHORIZED-PROJECT` | **PASS** | Unauthorized project rejected with SecurityValidationError |
| `STORAGE-WRITE` | **PASS** | Stored 1 documents for project 3 |
| `STORAGE-PERSISTENCE-RESTART` | **PASS** | Loaded 1 documents after restart from disk |
| `STORAGE-FTS5-SEARCH` | **PASS** | FTS5 MATCH returned 1 results |
| `STORAGE-ACL-ENFORCEMENT` | **PASS** | FE query on PM-only content returned 0 results (expected 0) |
| `STORAGE-PM-ACCESS` | **PASS** | PM query returned 1 results (expected >= 1) |
| `STORAGE-BACKUP` | **PASS** | Backup exported 2 documents |
| `STORAGE-RESTORE` | **PASS** | Restored 1 docs |

## Architectural Relationship
1. **PostgreSQL `qldapm_knowledge`**: Dedicated database schema on staging PostgreSQL with 2 tables (`knowledge_documents`, `knowledge_chunks`), 5 indexes (GIN full-text search `idx_kdoc_tsv`, btree `idx_kdoc_project`, `idx_kdoc_source`, `idx_kdoc_type`, primary key). Strictly separated from OpenProject public tables.
2. **SQLite FTS5 (`knowledge.sqlite`)**: High-performance local storage and lexical search index for the AI Gateway container at `/state/knowledge.sqlite`. Hydrates from disk upon startup, ensuring zero data loss on gateway restarts.
3. **Security Boundaries**: Projects are strictly whitelisted (`3`, `QLDAPM-LOCAL`, `QAG3`, `DEMO`). External web scraping and crawling patterns are rejected with `SecurityValidationError`.
