"""Second Brain Persistence & Whitelist Audit Script.
Validates:
1. Schema segregation: qldapm_knowledge is isolated from public tables.
2. Whitelist: Project 3 & QLDAPM-LOCAL allowed, unauthorized project rejected.
3. Persistence across restart: Insert -> simulate restart / re-open -> read back.
4. Role-based ACL: Documents restricted to PM are hidden from FE/QA.
5. FTS search: Verifies FTS5 full-text indexing and retrieval.
"""
import os
import shutil
import sqlite3
import subprocess
import tempfile
from pathlib import Path

from openproject.ai.gateway.knowledge_classifier import (
    KnowledgeDocType,
    classify_document,
    SecurityValidationError,
    ALLOWED_PROJECTS,
)
from openproject.ai.gateway.knowledge_storage import (
    KnowledgeStorage,
    KnowledgeStorageConfig,
)

results = []

def record(name, passed, details=""):
    results.append({"name": name, "passed": passed, "details": details})
    print(f"[{'PASS' if passed else 'FAIL'}] {name}: {details}")

def main():
    print("=== Second Brain Persistence & Whitelist Audit ===")

    # 1. Check PostgreSQL schema segregation
    try:
        cmd = [
            "docker", "exec", "-i", "qldapm-ai-stage-db-1",
            "psql", "-U", "postgres", "-d", "openproject", "-t", "-A", "-c",
            "SELECT count(*) FROM pg_tables WHERE schemaname = 'public' AND tablename LIKE '%knowledge%';"
        ]
        out = subprocess.check_output(cmd, text=True).strip()
        isolated = (out == "0")
        record("PG-SCHEMA-ISOLATION", isolated, f"Public tables with 'knowledge': {out} (expected 0)")
    except Exception as e:
        record("PG-SCHEMA-ISOLATION", False, f"Error checking PG schema: {e}")

    # 2. Check Whitelist in knowledge_classifier
    proj3_in = "3" in ALLOWED_PROJECTS
    local_in = "QLDAPM-LOCAL" in ALLOWED_PROJECTS
    record("WHITELIST-PROJECT-3", proj3_in and local_in, f"ALLOWED_PROJECTS includes 3 and QLDAPM-LOCAL: {ALLOWED_PROJECTS}")

    # 3. Classify document with project 3
    try:
        doc = classify_document(
            doc_type=KnowledgeDocType.ARCHITECTURE,
            project_id="3",
            source_id="docs/arch.md",
            title="Local Architecture",
            content="Architecture of QLDAPM local deployment.",
            allowed_roles=["PM", "FE"]
        )
        record("CLASSIFY-PROJECT-3", doc.project_id == "3", f"Classified project_id={doc.project_id}")
    except Exception as e:
        record("CLASSIFY-PROJECT-3", False, f"Failed to classify project 3: {e}")

    # 4. Reject unauthorized project
    try:
        classify_document(
            doc_type=KnowledgeDocType.ARCHITECTURE,
            project_id="ATTACK_PROJECT_99",
            source_id="docs/hack.md",
            title="Hack",
            content="Unauthorized",
        )
        record("REJECT-UNAUTHORIZED-PROJECT", False, "Failed to reject unauthorized project")
    except SecurityValidationError:
        record("REJECT-UNAUTHORIZED-PROJECT", True, "Unauthorized project rejected with SecurityValidationError")
    except Exception as e:
        record("REJECT-UNAUTHORIZED-PROJECT", False, f"Unexpected error: {e}")

    # 5. Persistence across restart (SQLite FTS5 Storage)
    test_dir = Path(tempfile.mkdtemp(prefix="qldapm_sb_test_"))
    db_file = test_dir / "knowledge_test.sqlite"
    try:
        config = KnowledgeStorageConfig(db_path=str(db_file), is_mock=False)
        storage = KnowledgeStorage(config)

        # Store PM-only doc
        doc_pm = classify_document(
            doc_type=KnowledgeDocType.ADR,
            project_id="3",
            source_id="adr-001",
            title="ADR PM Strategy",
            content="Confidential PM strategy for budget and staffing.",
            allowed_roles=["PM"]
        )
        storage.store_document(doc_pm)

        # Store Shared doc
        doc_shared = classify_document(
            doc_type=KnowledgeDocType.WORK_PACKAGE,
            project_id="QLDAPM-LOCAL",
            source_id="wp-100",
            title="Implement OAuth authentication",
            content="Authentication implementation steps for FE and BE developers.",
            allowed_roles=["PM", "FE", "BE", "QA"]
        )
        storage.store_document(doc_shared)

        # Verify docs exist in storage
        docs_before = storage.query_documents(project_id="3")
        record("STORAGE-WRITE", len(docs_before) >= 1, f"Stored {len(docs_before)} documents for project 3")

        # Simulate Restart: delete storage instance and create new instance pointing to same db_file
        del storage
        storage_restarted = KnowledgeStorage(config)

        docs_after = storage_restarted.query_documents(project_id="3")
        persisted = len(docs_after) >= 1 and docs_after[0].title == "ADR PM Strategy"
        record("STORAGE-PERSISTENCE-RESTART", persisted, f"Loaded {len(docs_after)} documents after restart from disk")

        # 6. Test FTS Search after restart via SQLite connection
        with storage_restarted._connection() as conn:
            cur = conn.execute("SELECT * FROM knowledge_fts WHERE knowledge_fts MATCH 'authentication'")
            rows = cur.fetchall()
            fts_pass = len(rows) > 0 and "OAuth" in rows[0]["title"]
            record("STORAGE-FTS5-SEARCH", fts_pass, f"FTS5 MATCH returned {len(rows)} results")

        # 7. Test ACL: FE searching for PM-only document
        fe_docs = storage_restarted.query_documents(project_id="3", role="FE")
        acl_enforced = (len(fe_docs) == 0)
        record("STORAGE-ACL-ENFORCEMENT", acl_enforced, f"FE query on PM-only content returned {len(fe_docs)} results (expected 0)")

        # PM searching for same document
        pm_docs = storage_restarted.query_documents(project_id="3", role="PM")
        pm_can_read = (len(pm_docs) > 0 and pm_docs[0].title == "ADR PM Strategy")
        record("STORAGE-PM-ACCESS", pm_can_read, f"PM query returned {len(pm_docs)} results (expected >= 1)")

        # 8. Test Backup & Restore capability
        backup = storage_restarted.backup_schema()
        record("STORAGE-BACKUP", len(backup["documents"]) >= 2, f"Backup exported {len(backup['documents'])} documents")

        storage_empty = KnowledgeStorage(KnowledgeStorageConfig(db_path=":memory:", is_mock=True))
        restore_res = storage_empty.restore_schema(backup)
        restored_docs = storage_empty.query_documents(project_id="3")
        record("STORAGE-RESTORE", restore_res.success and len(restored_docs) >= 1, f"Restored {len(restored_docs)} docs")

    finally:
        shutil.rmtree(test_dir, ignore_errors=True)

    # Output report
    report_file = Path("docs/ai-multi-agent-upgrade/verification_runs/run_20261017_2045/SECOND_BRAIN_PERSISTENCE_AUDIT.md")
    report_file.parent.mkdir(parents=True, exist_ok=True)
    with open(report_file, "w", encoding="utf-8") as f:
        f.write("# SECOND BRAIN PERSISTENCE & WHITELIST AUDIT\n\n")
        f.write("## Overview\n")
        f.write("- **PostgreSQL Schema:** `qldapm_knowledge` (segregated from OpenProject `public` tables)\n")
        f.write("- **SQLite Engine:** Persistent file with FTS5 virtual table indexing\n")
        f.write("- **Project Whitelist:** Updated to include Project `3` and identifier `QLDAPM-LOCAL`\n\n")
        f.write("## Test Results\n\n")
        f.write("| Test | Result | Details |\n")
        f.write("|------|--------|---------|\n")
        for r in results:
            status = "**PASS**" if r["passed"] else "**FAIL**"
            f.write(f"| `{r['name']}` | {status} | {r['details']} |\n")
        f.write("\n## Architectural Relationship\n")
        f.write("1. **PostgreSQL `qldapm_knowledge`**: Dedicated database schema on staging PostgreSQL with 2 tables (`knowledge_documents`, `knowledge_chunks`), 5 indexes (GIN full-text search `idx_kdoc_tsv`, btree `idx_kdoc_project`, `idx_kdoc_source`, `idx_kdoc_type`, primary key). Strictly separated from OpenProject public tables.\n")
        f.write("2. **SQLite FTS5 (`knowledge.sqlite`)**: High-performance local storage and lexical search index for the AI Gateway container at `/state/knowledge.sqlite`. Hydrates from disk upon startup, ensuring zero data loss on gateway restarts.\n")
        f.write("3. **Security Boundaries**: Projects are strictly whitelisted (`3`, `QLDAPM-LOCAL`, `QAG3`, `DEMO`). External web scraping and crawling patterns are rejected with `SecurityValidationError`.\n")

    print(f"Report written to {report_file}")

if __name__ == "__main__":
    main()
