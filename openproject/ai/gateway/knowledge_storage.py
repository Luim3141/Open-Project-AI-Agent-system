"""Isolated Persistent Storage Manager for QLDAPM Local Second Brain.
Strictly segregated from OpenProject business tables.
Provides zero-dependency persistent SQLite storage with FTS5,
with seamless detection of PostgreSQL 'qldapm_knowledge' schema.
"""
from contextlib import contextmanager
from dataclasses import dataclass, field
import json
import logging
import os
from pathlib import Path
import sqlite3
import time
from typing import Any, Dict, Generator, List, Optional
from .knowledge_classifier import KnowledgeDocType, KnowledgeDocument
from .permissions import AI_SYSTEM_OWNER
from .engineering_fencing import ensure_current

logger = logging.getLogger("qldapm.knowledge_storage")

SCHEMA_NAME = "qldapm_knowledge"

@dataclass
class KnowledgeStorageConfig:
    schema_name: str = SCHEMA_NAME
    database_url: Optional[str] = None
    db_path: Optional[str] = None
    enable_pgvector: bool = True
    is_mock: bool = False

@dataclass
class MigrationResult:
    success: bool
    schema: str
    tables_created: List[str]
    vector_enabled: bool
    fts_enabled: bool
    error: Optional[str] = None

class KnowledgeStorage:
    def __init__(self, config: Optional[KnowledgeStorageConfig] = None):
        self.config = config or KnowledgeStorageConfig()
        self.schema_name = self.config.schema_name
        self.pgvector_available = False  # SQLite is the runtime store; no PostgreSQL/vector backend is connected.
        self.fts_available = True
        self._mock_tables: Dict[str, Dict[str, Any]] = {}
        self._vector_cleanup = {}
        
        # Determine persistence target
        if self.config.is_mock:
            self.db_path = ":memory:"
        else:
            self.db_path = self.config.db_path or os.environ.get("QLDAPM_KNOWLEDGE_DB")
            if not self.db_path:
                runtime = os.environ.get("QLDAPM_AI_RUNTIME") or os.environ.get("LOCALAPPDATA")
                if runtime and "LOCALAPPDATA" in os.environ and runtime == os.environ.get("LOCALAPPDATA"):
                    base = Path(runtime) / "QLDAPM/openproject-ai/stage-ai"
                elif runtime:
                    base = Path(runtime)
                else:
                    base = Path(".")
                base.mkdir(parents=True, exist_ok=True)
                self.db_path = str(base / "knowledge.sqlite")

        # Initialize SQLite database and load existing documents
        self._init_sqlite()

    @contextmanager
    def _connection(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row
            conn.execute('PRAGMA foreign_keys=ON')
            conn.execute('PRAGMA busy_timeout=5000')
            conn.execute('PRAGMA journal_mode=WAL')
            yield conn
        finally:
            conn.close()

    def _ensure_tables(self, conn: sqlite3.Connection):
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS knowledge_documents (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                doc_type TEXT NOT NULL,
                source_id TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                allowed_roles TEXT NOT NULL,
                metadata TEXT NOT NULL,
                source_hash TEXT NOT NULL UNIQUE,
                created_at REAL,
                updated_at REAL
            );
            CREATE TABLE IF NOT EXISTS knowledge_chunks (
                id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                chunk_text TEXT NOT NULL,
                chunk_hash TEXT NOT NULL,
                created_at REAL,
                FOREIGN KEY(document_id) REFERENCES knowledge_documents(id) ON DELETE CASCADE
            );
            CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(
                source_hash UNINDEXED,
                title,
                content,
                tokenize='unicode61'
            );
            CREATE INDEX IF NOT EXISTS idx_kdoc_project ON knowledge_documents(project_id);
            CREATE INDEX IF NOT EXISTS idx_kdoc_type ON knowledge_documents(doc_type);
            CREATE TABLE IF NOT EXISTS knowledge_vector_cleanup (
                project_id TEXT NOT NULL,
                doc_type TEXT NOT NULL,
                source_id TEXT NOT NULL,
                points TEXT NOT NULL,
                PRIMARY KEY(project_id,doc_type,source_id)
            );
        """)

    def pending_vector_cleanup(self, scope):
        if self.db_path == ':memory:':return self._vector_cleanup.get(tuple(scope),[])
        with self._connection() as db:
            row=db.execute('SELECT points FROM knowledge_vector_cleanup WHERE project_id=? AND doc_type=? AND source_id=?',scope).fetchone()
        return json.loads(row[0]) if row else []

    def save_vector_cleanup(self, scope, points):
        ensure_current()
        if self.db_path == ':memory:':
            self._vector_cleanup[tuple(scope)]=points
            return
        with self._connection() as db:
            if points:
                db.execute('INSERT INTO knowledge_vector_cleanup VALUES(?,?,?,?) ON CONFLICT(project_id,doc_type,source_id) DO UPDATE SET points=excluded.points',(*scope,json.dumps(points)))
            else:db.execute('DELETE FROM knowledge_vector_cleanup WHERE project_id=? AND doc_type=? AND source_id=?',scope)
            ensure_current();db.commit()

    def _init_sqlite(self):
        """Initialize persistent SQLite schema and load existing documents."""
        tbl_doc = f"{self.schema_name}.knowledge_documents"
        tbl_chk = f"{self.schema_name}.knowledge_chunks"
        self._mock_tables[tbl_doc] = {}
        self._mock_tables[tbl_chk] = {}

        if self.db_path == ":memory:" and self.config.is_mock:
            return

        try:
            with self._connection() as conn:
                self._ensure_tables(conn)
                # Hydrate in-memory cache from persistent SQLite
                cursor = conn.execute("SELECT * FROM knowledge_documents")
                for row in cursor.fetchall():
                    doc_dict = {
                        "id": row["id"],
                        "project_id": row["project_id"],
                        "doc_type": row["doc_type"],
                        "source_id": row["source_id"],
                        "title": row["title"],
                        "content": row["content"],
                        "allowed_roles": json.loads(row["allowed_roles"]),
                        "metadata": json.loads(row["metadata"]),
                        "source_hash": row["source_hash"],
                    }
                    self._mock_tables[tbl_doc][row["source_hash"]] = doc_dict

                # Also chunks
                cursor_chk = conn.execute("SELECT * FROM knowledge_chunks")
                for row in cursor_chk.fetchall():
                    self._mock_tables[tbl_chk][row["id"]] = dict(row)
        except Exception as e:
            raise ValueError('KNOWLEDGE_STORE_UNAVAILABLE') from None

    def _reload(self):
        if self.db_path == ':memory:':
            return
        with self._connection() as db:
            if not db.execute("SELECT 1 FROM sqlite_master WHERE name='knowledge_documents'").fetchone():
                self._mock_tables[f'{self.schema_name}.knowledge_documents'] = {}
                self._mock_tables[f'{self.schema_name}.knowledge_chunks'] = {}
                return
            db.execute('BEGIN')
            rows = db.execute('SELECT * FROM knowledge_documents').fetchall()
            chunks = db.execute('SELECT * FROM knowledge_chunks').fetchall()
        self._mock_tables[f'{self.schema_name}.knowledge_documents'] = {
            r['source_hash']: {**dict(r), 'allowed_roles': json.loads(r['allowed_roles']), 'metadata': json.loads(r['metadata'])} for r in rows}
        self._mock_tables[f'{self.schema_name}.knowledge_chunks'] = {r['id']:dict(r) for r in chunks}

    def has_vector_support(self) -> bool:
        return self.pgvector_available

    def has_fts_support(self) -> bool:
        return self.fts_available

    def get_tables(self) -> List[str]:
        return list(self._mock_tables.keys())

    def migrate_schema(self) -> MigrationResult:
        """Create isolated schema and tables. Never touches OpenProject public tables."""
        created = [
            f"{self.schema_name}.knowledge_documents",
            f"{self.schema_name}.knowledge_chunks",
        ]
        for tbl in created:
            if tbl not in self._mock_tables:
                self._mock_tables[tbl] = {}

        if self.db_path != ":memory:":
            try:
                with self._connection() as conn:
                    self._ensure_tables(conn)
                    conn.commit()
            except Exception as e:
                logger.error(f"Migration error: {e}")
                return MigrationResult(
                    success=False,
                    schema=self.schema_name,
                    tables_created=[],
                    vector_enabled=self.pgvector_available,
                    fts_enabled=self.fts_available,
                    error=str(e),
                )

        return MigrationResult(
            success=True,
            schema=self.schema_name,
            tables_created=created,
            vector_enabled=self.pgvector_available,
            fts_enabled=self.fts_available,
        )

    def rollback_schema(self) -> MigrationResult:
        """Drop isolated schema. Leaves public schema completely untouched."""
        if self.db_path == ':memory:':
            pending=any(self._vector_cleanup.values())
        else:
            with self._connection() as db:pending=db.execute('SELECT 1 FROM knowledge_vector_cleanup LIMIT 1').fetchone() is not None
        if pending:raise ValueError('KNOWLEDGE_PENDING_VECTOR_CLEANUP_ROLLBACK_DENIED')
        self._mock_tables.clear()
        self._vector_cleanup.clear()
        if self.db_path != ":memory:":
            try:
                with self._connection() as conn:
                    conn.executescript("""
                        DROP TABLE IF EXISTS knowledge_fts;
                        DROP TABLE IF EXISTS knowledge_chunks;
                        DROP TABLE IF EXISTS knowledge_documents;
                        DROP TABLE IF EXISTS knowledge_vector_cleanup;
                    """)
                    conn.commit()
            except Exception as e:
                logger.error(f"Rollback error: {e}")
                return MigrationResult(
                    success=False,
                    schema=self.schema_name,
                    tables_created=[],
                    vector_enabled=self.pgvector_available,
                    fts_enabled=self.fts_available,
                    error=str(e),
                )
        return MigrationResult(
            success=True,
            schema=self.schema_name,
            tables_created=[],
            vector_enabled=self.pgvector_available,
            fts_enabled=self.fts_available,
        )

    def store_document(self, doc: KnowledgeDocument, chunks=None) -> bool:
        ensure_current()
        tbl = f"{self.schema_name}.knowledge_documents"
        if tbl not in self._mock_tables:
            self._mock_tables[tbl] = {}

        doc_dict = {
            "id": doc.source_hash,
            "project_id": doc.project_id,
            "doc_type": doc.doc_type.value,
            "source_id": doc.source_id,
            "title": doc.title,
            "content": doc.content,
            "allowed_roles": list(doc.allowed_roles),
            "metadata": dict(doc.metadata),
            "source_hash": doc.source_hash,
        }
        # Persist to SQLite
        if self.db_path != ":memory:":
            try:
                with self._connection() as conn:
                    self._ensure_tables(conn)
                    now = time.time()
                    conn.execute('BEGIN IMMEDIATE')
                    previous = conn.execute('SELECT metadata FROM knowledge_documents WHERE project_id=? AND doc_type=? AND source_id=?',
                        (doc.project_id,doc.doc_type.value,doc.source_id)).fetchall()
                    if any(json.loads(row[0]).get('lock_version',-1)>doc.metadata.get('lock_version',-1) for row in previous):
                        raise ValueError('KNOWLEDGE_STALE_REVISION')
                    old = conn.execute('SELECT source_hash FROM knowledge_documents WHERE project_id=? AND doc_type=? AND source_id=? AND source_hash!=?',
                        (doc.project_id,doc.doc_type.value,doc.source_id,doc.source_hash)).fetchall()
                    for row in old:
                        conn.execute('DELETE FROM knowledge_chunks WHERE document_id=?',(row[0],))
                        conn.execute('DELETE FROM knowledge_fts WHERE source_hash=?',(row[0],))
                        conn.execute('DELETE FROM knowledge_documents WHERE source_hash=?',(row[0],))
                    conn.execute("""
                        INSERT INTO knowledge_documents (
                            id, project_id, doc_type, source_id, title, content,
                            allowed_roles, metadata, source_hash, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(source_hash) DO UPDATE SET
                            title=excluded.title,
                            content=excluded.content,
                            allowed_roles=excluded.allowed_roles,
                            metadata=excluded.metadata,
                            updated_at=excluded.updated_at
                    """, (
                        doc.source_hash, doc.project_id, doc.doc_type.value, doc.source_id,
                        doc.title, doc.content, json.dumps(list(doc.allowed_roles)),
                        json.dumps(dict(doc.metadata)), doc.source_hash, now, now
                    ))
                    # Update FTS index
                    conn.execute("DELETE FROM knowledge_fts WHERE source_hash=?", (doc.source_hash,))
                    from .knowledge_search import _tokenize
                    conn.execute("INSERT INTO knowledge_fts (source_hash, title, content) VALUES (?, ?, ?)",
                                 (doc.source_hash, ' '.join(_tokenize(doc.title)), ' '.join(_tokenize(doc.content))))
                    from .knowledge_ingestion import chunk_text
                    conn.execute('DELETE FROM knowledge_chunks WHERE document_id=?',(doc.source_hash,))
                    for chunk in chunks if chunks is not None else chunk_text(doc.content):
                        conn.execute('INSERT INTO knowledge_chunks VALUES(?,?,?,?,?,?)',
                            (doc.source_hash+':'+str(chunk['chunk_index']),doc.source_hash,chunk['chunk_index'],chunk['chunk_text'],chunk['chunk_hash'],now))
                    ensure_current();conn.commit()
            except Exception as e:
                return False
        self._mock_tables[tbl][doc.source_hash] = doc_dict
        if self.db_path == ':memory:':
            from .knowledge_ingestion import chunk_text
            table=self._mock_tables.setdefault(f'{self.schema_name}.knowledge_chunks',{})
            for key in [key for key,row in table.items() if row['document_id']==doc.source_hash]:del table[key]
            for chunk in chunks if chunks is not None else chunk_text(doc.content):
                key=doc.source_hash+':'+str(chunk['chunk_index'])
                table[key]={'id':key,'document_id':doc.source_hash,**chunk}
        return True

    def delete_document(self, source_hash: str) -> bool:
        ensure_current()
        tbl = f"{self.schema_name}.knowledge_documents"
        deleted = False
        if self.db_path != ":memory:":
            try:
                with self._connection() as conn:
                    conn.execute('DELETE FROM knowledge_chunks WHERE document_id=?',(source_hash,))
                    cur = conn.execute("DELETE FROM knowledge_documents WHERE source_hash=?", (source_hash,))
                    conn.execute("DELETE FROM knowledge_fts WHERE source_hash=?", (source_hash,))
                    ensure_current();conn.commit()
                    if cur.rowcount > 0:
                        deleted = True
            except Exception:
                raise ValueError('KNOWLEDGE_DELETE_FAILED') from None
        if source_hash in self._mock_tables.get(tbl,{}):
            del self._mock_tables[tbl][source_hash]
            deleted = True
        chunks=self._mock_tables.get(f'{self.schema_name}.knowledge_chunks',{})
        for key in [key for key,row in chunks.items() if row['document_id']==source_hash]:del chunks[key]
        return deleted

    def count_documents(self) -> int:
        self._reload()
        tbl = f"{self.schema_name}.knowledge_documents"
        return len(self._mock_tables.get(tbl, {}))

    def query_documents(
        self,
        project_id: str,
        role: Optional[str] = None,
        doc_type: Optional[KnowledgeDocType] = None,
    ) -> List[KnowledgeDocument]:
        self._reload()
        tbl = f"{self.schema_name}.knowledge_documents"
        rows = self._mock_tables.get(tbl, {}).values()
        results: List[KnowledgeDocument] = []

        for r in rows:
            if r["project_id"] != project_id:
                continue
            if role and role != AI_SYSTEM_OWNER and role not in r["allowed_roles"]:
                continue
            if doc_type and r["doc_type"] != doc_type.value:
                continue

            results.append(
                KnowledgeDocument(
                    doc_type=KnowledgeDocType(r["doc_type"]),
                    project_id=r["project_id"],
                    source_id=r["source_id"],
                    title=r["title"],
                    content=r["content"],
                    source_hash=r["source_hash"],
                    allowed_roles=r["allowed_roles"],
                    metadata=r["metadata"],
                )
            )
        return results

    def backup_schema(self) -> Dict[str, Any]:
        """Export isolated backup of qldapm_knowledge schema data."""
        self._reload()
        tbl_doc = f"{self.schema_name}.knowledge_documents"
        tbl_chk = f"{self.schema_name}.knowledge_chunks"
        return {
            "schema": self.schema_name,
            "documents": list(self._mock_tables.get(tbl_doc, {}).values()),
            "chunks": list(self._mock_tables.get(tbl_chk, {}).values()),
        }

    def backup_file(self, destination):
        """SQLite online backup includes committed WAL; caller supplies a new private artifact path."""
        if self.db_path == ':memory:':
            raise ValueError('PERSISTENT_KNOWLEDGE_STORE_REQUIRED')
        path = Path(destination)
        with path.open('xb'):
            pass
        with self._connection() as source:
            target=sqlite3.connect(path)
            try:
                source.backup(target)
                if target.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                    raise ValueError('KNOWLEDGE_BACKUP_CORRUPT')
            finally:
                target.close()
        return path

    def restore_schema(self, backup_data):
        """Restore into an empty isolated store; verify all input before the first write."""
        if backup_data.get('schema') != self.schema_name or self.count_documents():
            raise ValueError('KNOWLEDGE_RESTORE_REQUIRES_EMPTY_MATCHING_STORE')
        documents=[]
        for row in backup_data.get('documents',[]):
            documents.append(KnowledgeDocument(doc_type=KnowledgeDocType(row['doc_type']),
                project_id=row['project_id'],source_id=row['source_id'],title=row['title'],content=row['content'],
                source_hash=row['source_hash'],allowed_roles=row['allowed_roles'],metadata=row['metadata']))
        if self.db_path == ':memory:':
            for doc in documents:
                if not self.store_document(doc):
                    raise ValueError('KNOWLEDGE_RESTORE_FAILED')
        else:
            import tempfile
            with tempfile.TemporaryDirectory(prefix='qldapm-restore-') as folder:
                temporary=KnowledgeStorage(KnowledgeStorageConfig(db_path=str(Path(folder)/'knowledge.sqlite')))
                for doc in documents:
                    if not temporary.store_document(doc):
                        raise ValueError('KNOWLEDGE_RESTORE_FAILED')
                with temporary._connection() as source, self._connection() as target:
                    source.backup(target)
            self._reload()
        return MigrationResult(True,self.schema_name,self.get_tables(),False,True)
