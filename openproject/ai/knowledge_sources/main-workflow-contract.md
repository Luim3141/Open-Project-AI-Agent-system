# Main local knowledge ingestion contract

Revision: 2026-10-28. Source key and existing permitted roles are retained.

Main WF01 supports two explicit sources: an authorized Native Work Package ID, or a server-registered local `source_key`. A source key never means a filesystem path. Native ingestion retains its original authorization and version checks.

The local file registry binds the Main project, an allowlisted root, one file, its SHA256 and permitted business roles. PM and AI System Owner can request indexing. Search and indexed readback require a fresh authenticated identity and the current server role, project and checksum policy. A changed file is refused until the operator verifies and updates its pinned checksum; indexing a new revision requires a new request UUID.

WF01 file operations are `ingest`, `reindex`, `search` and `read`. Ingestion parses bounded text, DOCX or text-layer PDF, persists document/chunk metadata in SQLite, embeds through local Ollama BGE-M3, then verifies Qdrant points. A failed vector commit is reported as pending, and the same ingestion key may safely repair it. Native Work Packages are never mutated by these operations.

Search uses the existing hybrid retrieval engine restricted to the current registered document ID. Citations contain the logical source key, document identity and original file SHA256. Readback checks these identities again; stale citations and unregistered or unmatched points do not become evidence. Client file paths, raw content, actor/project claims and deletion requests cannot authorize source access.

Supported formats at this boundary: UTF-8 TXT, Markdown, CSV, JSON, bounded DOCX and text-layer PDF. PDF parsing runs in a bounded child process (15 seconds, 64 pages, 256 KiB input and text output; Linux memory/CPU limits). Encrypted, malformed, oversized or image-only pages fail the whole ingestion; OCR and arbitrary uploads are not implemented here. Unverified user feedback cannot change the registry or promote content. This document is operational project documentation, not a QA test execution attestation.

Retrieval reference: `QLDAPM_LOCAL_KNOWLEDGE_CONTRACT_20261028`.
