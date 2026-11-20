"""Ingest Real Allowlisted Documentation Corpus into Qdrant & SQLite Knowledge Base.
Scope: Authoritative architecture, ADRs, agent specs, workflows, and user stories.
Zero mocks, strict hardware bounds (batch size 2, 1 worker, 1024 dims).
"""
import json
import logging
import os
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from openproject.ai.gateway.knowledge_storage import KnowledgeStorage, KnowledgeStorageConfig, SCHEMA_NAME
from openproject.ai.gateway.knowledge_ingestion import KnowledgeIngester
from openproject.ai.gateway.vector_client import VectorClient, COLLECTION_NAME
from openproject.ai.gateway.local_loaders import load_local_file

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("qldapm.corpus_ingest")

ALLOWLISTED_DOCS = [
    # Business Requirements & User Stories
    "user-story-web-quan-ly-du-an-rut-gon.docx",
    # Architectural Decision Records (ADRs)
    "docs/adr/0001-local-five-user-multi-agent.md",
    "docs/adr/0002-n8n-community-local-owner.md",
    "docs/adr/0003-orchestration-typed-state-machine.md",
    "docs/adr/0004-user-capacity-scale-20.md",
    # Agent & Domain Guidelines
    "docs/agents/domain.md",
    "docs/agents/issue-tracker.md",
    "docs/agents/triage-labels.md",
    # Architecture & Engine Specifications
    "docs/ai/01_FINAL_ARCHITECTURE.md",
    "docs/ai/06_NATIVE_API_ENGINE.md",
    "docs/ai/07_N8N_MAIN_AUTOMATION.md",
    "docs/ai-multi-agent-upgrade/ARCHITECTURE_TARGET.md",
    "docs/ai-multi-agent-upgrade/FIVE_USER_SCOPE.md",
    "docs/ai-multi-agent-upgrade/FREE_TIER_POLICY.md",
    # Operational Workflows & Policies
    "jira-management.md",
    "jira-workflows.md",
]


def ingest_corpus():
    root_state = Path("C:/Users/LUIM/AppData/Local/QLDAPM/openproject-ai/gateway")
    db_path = str(root_state / "knowledge.sqlite")

    vector_client = VectorClient(
        ollama_url="http://127.0.0.1:11434",
        qdrant_url="http://127.0.0.1:6333",
        collection_name=COLLECTION_NAME,
        batch_size=2,
    )
    if not vector_client.is_available():
        raise RuntimeError("VectorClient services (Ollama / Qdrant) not available!")

    vector_client.ensure_collection()

    storage = KnowledgeStorage(KnowledgeStorageConfig(
        schema_name=SCHEMA_NAME,
        db_path=db_path,
        is_mock=False,
    ))
    storage.migrate_schema()

    ingester = KnowledgeIngester(
        storage=storage,
        vector_client=vector_client,
        chunk_size=600,
        chunk_overlap=100,
    )

    t0 = time.time()
    results = []

    for rel_path in ALLOWLISTED_DOCS:
        p = Path(rel_path)
        if not p.exists():
            logger.warning(f"File not found: {rel_path}, skipping.")
            continue

        try:
            doc = load_local_file(p, project_id="5")
            res = ingester.ingest(doc)
            results.append({
                "file": rel_path,
                "title": doc.title,
                "doc_type": doc.doc_type.value,
                "status": res.status.value,
                "chunks": res.chunks_count,
                "vector_indexed": res.vector_indexed,
            })
            logger.info(f"Ingested {rel_path} -> Status: {res.status.value}, Chunks: {res.chunks_count}, Vector: {res.vector_indexed}")
        except Exception as e:
            logger.error(f"Error ingesting {rel_path}: {e}")
            results.append({"file": rel_path, "status": "FAILED", "error": str(e)})

    total_time = round(time.time() - t0, 2)
    logger.info(f"Corpus ingestion completed in {total_time}s across {len(results)} documents.")
    return results


if __name__ == "__main__":
    ingest_corpus()
