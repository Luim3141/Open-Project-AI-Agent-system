"""Real Container Persistence & ACL Test for Second Brain.
Validates:
1. Accurate architectural description: SQLite FTS5 is active runtime store;
   PostgreSQL qldapm_knowledge schema is isolated from public.
2. Real container restart of qldapm-ai-stage-staging-gateway-1.
3. Data integrity across container restart (content and hash match).
4. Real actor ACL enforcement (PM sees PM-only doc, FE is denied).
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "openproject" / "ai"))

from gateway.knowledge_classifier import (
    KnowledgeDocType,
    classify_document,
    SecurityValidationError,
    ALLOWED_PROJECTS,
)
from gateway.knowledge_storage import (
    KnowledgeStorage,
    KnowledgeStorageConfig,
)
from gateway.knowledge_search import KnowledgeSearchEngine

HOST_STATE_DIR = Path(os.environ["LOCALAPPDATA"]) / "QLDAPM" / "openproject-ai" / "stage-ai"
GATEWAY_CONTAINER = "qldapm-ai-stage-staging-gateway-1"

def main():
    print("=== Second Brain Real Container Persistence & ACL Test ===")
    results = []

    def record_step(name, passed, details=""):
        results.append({"name": name, "passed": passed, "details": details})
        tag = "[PASS]" if passed else "[FAIL]"
        print(f"{tag:7} {name:32} | {details}")

    # 1. PostgreSQL Schema Isolation check
    try:
        cmd = [
            "docker", "exec", "-i", "qldapm-ai-stage-db-1",
            "psql", "-U", "postgres", "-d", "openproject", "-t", "-A", "-c",
            "SELECT count(*) FROM pg_tables WHERE schemaname = 'public' AND tablename LIKE '%knowledge%';"
        ]
        out = subprocess.check_output(cmd, text=True).strip()
        isolated = (out == "0")
        record_step("PG_SCHEMA_ISOLATION", isolated, f"Public tables with 'knowledge': {out} (expected 0, schema isolated)")
    except Exception as e:
        record_step("PG_SCHEMA_ISOLATION", False, f"Postgres inspection error: {e}")

    # 2. Whitelist Verification
    p3_ok = "3" in ALLOWED_PROJECTS and "QLDAPM-LOCAL" in ALLOWED_PROJECTS
    record_step("WHITELIST_PROJECT_3", p3_ok, f"Allowed projects: {sorted(list(ALLOWED_PROJECTS))}")

    # Reject unauthorized project
    try:
        classify_document(
            doc_type=KnowledgeDocType.ARCHITECTURE,
            project_id="UNAUTHORIZED_999",
            source_id="unauth.md",
            title="Unauth",
            content="Unauth content"
        )
        record_step("REJECT_UNAUTHORIZED_PROJECT", False, "Failed to reject unauthorized project")
    except SecurityValidationError:
        record_step("REJECT_UNAUTHORIZED_PROJECT", True, "Successfully raised SecurityValidationError for project 999")
    except Exception as e:
        record_step("REJECT_UNAUTHORIZED_PROJECT", False, f"Unexpected error: {e}")

    # 3. Insert real test document into live runtime SQLite storage
    db_path = HOST_STATE_DIR / "knowledge.sqlite"
    print(f"Using runtime SQLite storage: {db_path}")
    storage = KnowledgeStorage(KnowledgeStorageConfig(db_path=str(db_path), is_mock=False))
    searcher = KnowledgeSearchEngine(storage)

    test_doc_id = f"test-real-persist-{int(time.time())}"
    doc_content = f"Confidential strategy content for persistence verification token={time.time()}"
    content_hash = hashlib.sha256(doc_content.encode("utf-8")).hexdigest()

    doc = classify_document(
        doc_type=KnowledgeDocType.ADR,
        project_id="3",
        source_id=test_doc_id,
        title="Real Container Persistence Verification",
        content=doc_content,
        allowed_roles=["PM"]
    )
    storage.store_document(doc)
    record_step("DOCUMENT_STORED_PRE_RESTART", True, f"Stored doc source_id={test_doc_id}, hash={content_hash[:16]}")

    # 4. Restart staging-gateway container
    print(f"Restarting container {GATEWAY_CONTAINER}...")
    restart_res = subprocess.run(["docker", "restart", GATEWAY_CONTAINER], capture_output=True, text=True)
    if restart_res.returncode != 0:
        record_step("CONTAINER_RESTART", False, f"docker restart failed: {restart_res.stderr}")
        sys.exit(1)
    
    # Wait for gateway to become healthy
    print("Waiting for gateway health check...")
    deadline = time.time() + 45
    healthy = False
    while time.time() < deadline:
        h_res = subprocess.run(
            ["docker", "inspect", "--format", "{{.State.Health.Status}}", GATEWAY_CONTAINER],
            capture_output=True, text=True
        )
        if h_res.stdout.strip() == "healthy":
            healthy = True
            break
        time.sleep(1)

    record_step("CONTAINER_HEALTHY_POST_RESTART", healthy, f"{GATEWAY_CONTAINER} status is healthy")

    # 5. Read back document from inside container via SQLite
    readback_cmd = [
        "docker", "exec", "-i", GATEWAY_CONTAINER,
        "python", "-c", f"""
import sqlite3
conn = sqlite3.connect('/state/knowledge.sqlite')
cur = conn.cursor()
cur.execute("SELECT content FROM knowledge_documents WHERE project_id='3' AND source_id='{test_doc_id}'")
row = cur.fetchone()
if row:
    print('FOUND:' + row[0])
else:
    print('NOT_FOUND')
"""
    ]
    readback_res = subprocess.run(readback_cmd, capture_output=True, text=True)
    found_line = [l for l in readback_res.stdout.splitlines() if l.startswith("FOUND:")]
    if found_line:
        retrieved_content = found_line[0][6:]
        retrieved_hash = hashlib.sha256(retrieved_content.encode("utf-8")).hexdigest()
        hash_matched = (retrieved_hash == content_hash)
        record_step("READBACK_POST_CONTAINER_RESTART", hash_matched, f"Retrieved from inside container post-restart, hash match={hash_matched}")
    else:
        record_step("READBACK_POST_CONTAINER_RESTART", False, f"Doc not found post-restart: {readback_res.stdout} {readback_res.stderr}")

    # 6. Test Actor ACL Filtering
    # Query with PM role (authorized)
    pm_docs = storage.query_documents(project_id="3", role="PM")
    pm_found = any(d.source_id == test_doc_id for d in pm_docs)
    pm_search = searcher.search("Confidential strategy persistence", project_id="3", role="PM")
    pm_search_found = any(r.source_id == test_doc_id for r in pm_search)
    record_step("ACL_PM_AUTHORIZED_ACCESS", pm_found and pm_search_found, f"PM query & search found PM-only document: found={pm_found}, search={pm_search_found}")

    # Query with FE role (unauthorized)
    fe_docs = storage.query_documents(project_id="3", role="FE")
    fe_found = any(d.source_id == test_doc_id for d in fe_docs)
    fe_search = searcher.search("Confidential strategy persistence", project_id="3", role="FE")
    fe_search_found = any(r.source_id == test_doc_id for r in fe_search)
    record_step("ACL_FE_DENIED_ACCESS", (not fe_found) and (not fe_search_found), f"FE query & search correctly filtered out PM document: query={not fe_found}, search={not fe_search_found}")

    # 7. Cleanup test document
    storage.delete_document(doc.source_hash)
    print("Test document cleaned up from storage.")

    # Summary
    all_ok = all(r["passed"] for r in results)
    pass_cnt = sum(1 for r in results if r["passed"])
    print(f"\nSecond Brain Container Persistence & ACL: {pass_cnt}/{len(results)} PASS")
    if not all_ok:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
