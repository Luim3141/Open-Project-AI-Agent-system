"""Batch Ingestion Runner for QLDAPM Main Knowledge Base.
Ingests:
1. Critical local project requirements (user story docx).
2. Live OpenProject Work Packages and Epics from Project 5.
3. Live OpenProject Sprints.
"""
import json
import logging
from pathlib import Path

from openproject.ai.gateway.knowledge_storage import KnowledgeStorage, KnowledgeStorageConfig, SCHEMA_NAME
from openproject.ai.gateway.knowledge_ingestion import KnowledgeIngester
from openproject.ai.gateway.vector_client import VectorClient, COLLECTION_NAME
from openproject.ai.gateway.local_loaders import load_local_file
from openproject.ai.gateway.openproject_loader import load_openproject_work_packages, load_openproject_sprints
from openproject.ai.gateway.native import Native

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("qldapm.run_ingest")


def main():
    root_state = Path("C:/Users/LUIM/AppData/Local/QLDAPM/openproject-ai/gateway")
    db_path = str(root_state / "knowledge.sqlite")
    creds_path = root_state / "credentials.json"
    config_path = root_state / "config.json"

    creds = json.loads(creds_path.read_text(encoding="utf-8"))
    config = json.loads(config_path.read_text(encoding="utf-8"))

    # Initialize VectorClient
    vector_client = VectorClient(
        ollama_url="http://127.0.0.1:11434",
        qdrant_url="http://127.0.0.1:6333",
        collection_name=COLLECTION_NAME,
        batch_size=2,
    )
    vector_client.ensure_collection()

    # Initialize Storage
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

    logger.info("--- Step 1: Ingesting Local Specification DOCX ---")
    docx_path = Path("user-story-web-quan-ly-du-an-rut-gon.docx")
    if docx_path.exists():
        doc = load_local_file(docx_path, project_id="5")
        res = ingester.ingest(doc)
        logger.info(f"DOCX Ingest: {res.status} | Chunks: {res.chunks_count} | Vector: {res.vector_indexed}")

    logger.info("--- Step 2: Ingesting Live OpenProject Main Work Packages ---")
    # Connect Native API as PM (User 19)
    # Inside docker it's web:8080, on Windows host it's localhost:8088
    pm_token = creds.get("19")
    native = Native("http://localhost:8088", pm_token, 5)

    docs = load_openproject_work_packages(native, project_id="5")
    logger.info(f"Found {len(docs)} work packages in Project 5")

    # Ingest in small batches with progress logging
    created, updated, skipped = 0, 0, 0
    for i, wp_doc in enumerate(docs):
        r = ingester.ingest(wp_doc)
        if r.status.value == "CREATED":
            created += 1
        elif r.status.value == "UPDATED":
            updated += 1
        else:
            skipped += 1
        if (i + 1) % 25 == 0 or (i + 1) == len(docs):
            logger.info(f"Progress: {i + 1}/{len(docs)} | Created: {created}, Updated: {updated}, Skipped: {skipped}")

    logger.info("--- Step 3: Ingesting Live OpenProject Sprints ---")
    sprint_docs = load_openproject_sprints(native, project_id="5")
    for sp_doc in sprint_docs:
        r = ingester.ingest(sp_doc)
        logger.info(f"Sprint Ingest {sp_doc.title}: {r.status} (Vector: {r.vector_indexed})")

    logger.info("--- Ingestion Complete ---")
    logger.info(f"Total documents in SQLite: {storage.count_documents()}")


if __name__ == "__main__":
    main()
