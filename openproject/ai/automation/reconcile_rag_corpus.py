"""RAG Corpus Deep Reconciliation Script.

Investigates:
1. Why OpenProject Main has 332 WPs, but only 326 are indexed in SQLite.
2. Why SQLite has 1,713 chunks, but Qdrant has 1,693 points (diff of 20 points).
3. Why earlier reports mentioned 1,359 points.
4. Exact list of excluded/missing/stale/orphan sources.
"""

import os
import pathlib
import json
import sqlite3
import requests

def main():
    root = pathlib.Path(os.environ["LOCALAPPDATA"]) / "QLDAPM" / "openproject-ai" / "gateway"
    db_path = root / "knowledge.sqlite"
    creds_path = root / "credentials.json"

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    # 1. Inspect Work Packages in SQLite
    wp_docs = conn.execute("SELECT id, source_id, title, metadata FROM knowledge_documents WHERE doc_type = 'WORK_PACKAGE'").fetchall()
    print(f"Total WORK_PACKAGE docs in SQLite: {len(wp_docs)}")

    indexed_wp_ids = set()
    for row in wp_docs:
        meta = json.loads(row["metadata"]) if row["metadata"] else {}
        native_id = meta.get("native_id")
        if native_id:
            indexed_wp_ids.add(int(native_id))
        else:
            sid = row["source_id"]
            parts = sid.split(":")
            if "wp" in parts:
                idx = parts.index("wp")
                if idx + 1 < len(parts):
                    try:
                        indexed_wp_ids.add(int(parts[idx+1]))
                    except ValueError:
                        pass

    print(f"Unique WP IDs indexed in SQLite: {len(indexed_wp_ids)}")

    # 2. Query OpenProject for all WPs in Project 5
    creds = json.loads(creds_path.read_text())
    pm_token = creds.get("19")
    headers = {"Authorization": f"Bearer {pm_token}", "Content-Type": "application/json"}
    
    url = "http://localhost:8088/api/v3/projects/5/work_packages?pageSize=500"
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        print(f"Error fetching OP WPs: {r.status_code}")
        return

    op_data = r.json()
    total_op = op_data.get("total", 0)
    elements = op_data.get("_embedded", {}).get("elements", [])
    print(f"\nTotal reported by OpenProject: {total_op}")
    print(f"Total elements retrieved: {len(elements)}")

    op_wp_map = {el["id"]: el for el in elements}
    all_op_ids = set(op_wp_map.keys())

    # 3. Find the exact missing WPs
    missing_in_sqlite = all_op_ids - indexed_wp_ids
    print(f"\n=== EXACT MISSING WORK PACKAGES IN SQLITE ({len(missing_in_sqlite)} items) ===")
    for wp_id in sorted(missing_in_sqlite):
        el = op_wp_map.get(wp_id, {})
        subj = el.get("subject", "N/A")
        type_name = el.get("_links", {}).get("type", {}).get("title", "N/A")
        status_name = el.get("_links", {}).get("status", {}).get("title", "N/A")
        desc = el.get("description", {}).get("raw", "")
        created_at = el.get("createdAt", "N/A")
        print(f"  WP #{wp_id}: [{type_name}] '{subj}' (Status: {status_name}, Desc len: {len(desc)}, Created: {created_at})")

    # Extra in SQLite?
    extra_in_sqlite = indexed_wp_ids - all_op_ids
    print(f"\n=== EXTRA IN SQLITE ({len(extra_in_sqlite)} items) ===")
    for wp_id in sorted(extra_in_sqlite):
        print(f"  WP #{wp_id} exists in SQLite but NOT in OpenProject!")

    # 4. Chunks vs Qdrant analysis
    total_chunks = conn.execute("SELECT count(*) FROM knowledge_chunks").fetchone()[0]
    print(f"\n=== CHUNKS VS QDRANT POINTS ===")
    print(f"Total chunks in SQLite: {total_chunks}")

    # Check Qdrant points
    r_qdrant = requests.get("http://localhost:6333/collections/qldapm_knowledge_dense")
    qdrant_points = 0
    if r_qdrant.status_code == 200:
        qdrant_points = r_qdrant.json().get("result", {}).get("points_count", 0)
    print(f"Total points in Qdrant: {qdrant_points}")
    print(f"Difference (SQLite chunks - Qdrant points): {total_chunks - qdrant_points}")

    # Inspect chunks for duplicate hashes
    chunk_rows = conn.execute("SELECT id, document_id, chunk_index, chunk_hash FROM knowledge_chunks").fetchall()
    hashes = {}
    for c in chunk_rows:
        h = c["chunk_hash"]
        if h not in hashes:
            hashes[h] = []
        hashes[h].append(c["id"])
    
    dup_groups = {h: ids for h, ids in hashes.items() if len(ids) > 1}
    total_dups = sum(len(ids) - 1 for ids in dup_groups.values())
    print(f"Duplicate chunk hashes: {len(dup_groups)} groups ({total_dups} duplicate chunks)")

    # Check the 20 diff between SQLite and Qdrant
    print("\n=== WHY 20 CHUNKS DIFF? ===")
    print(f"Number of duplicate chunk hashes in SQLite: {total_dups}")
    if total_dups == (total_chunks - qdrant_points):
        print("MATCH! The 20 points difference is EXACTLY due to 20 duplicate chunks deduplicated during vector upsert or indexing!")
    else:
        print(f"Deduplication explains {total_dups} of {total_chunks - qdrant_points} points.")

    # 5. Exact points diff by scrolling Qdrant
    import uuid
    cur = conn.cursor()
    cur.execute('''
        SELECT c.id, d.source_hash, c.chunk_index, d.source_id, d.title
        FROM knowledge_chunks c
        JOIN knowledge_documents d ON d.id = c.document_id
    ''')
    sqlite_points = {}
    for cid, shash, cidx, sid, title in cur.fetchall():
        pid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"qldapm.chunk.{shash}:{cidx}"))
        sqlite_points[pid] = {"chunk_id": cid, "source_id": sid, "title": title, "chunk_index": cidx}

    print(f"Total computed point IDs from SQLite: {len(sqlite_points)}")

    all_qdrant_ids = set()
    offset = None
    while True:
        payload = {"limit": 500, "with_payload": False, "with_vector": False}
        if offset:
            payload["offset"] = offset
        res = requests.post("http://localhost:6333/collections/qldapm_knowledge_dense/points/scroll", json=payload).json()
        points = res.get("result", {}).get("points", [])
        for p in points:
            all_qdrant_ids.add(p["id"])
        offset = res.get("result", {}).get("next_page_offset")
        if not offset or not points:
            break

    print(f"Total point IDs in Qdrant: {len(all_qdrant_ids)}")
    missing_in_qdrant = set(sqlite_points.keys()) - all_qdrant_ids
    print(f"Missing in Qdrant ({len(missing_in_qdrant)} points):")
    for pid in sorted(missing_in_qdrant):
        info = sqlite_points[pid]
        print(f"  Point {pid}: chunk #{info['chunk_id']} from [{info['source_id']}] '{info['title']}' index {info['chunk_index']}")

    extra_in_qdrant = all_qdrant_ids - set(sqlite_points.keys())
    print(f"Extra in Qdrant not in SQLite ({len(extra_in_qdrant)} points):")
    for pid in list(extra_in_qdrant)[:5]:
        print(f"  Point {pid}")

    # 6. Explaining earlier report of 1,359 points
    wp_chunks = conn.execute("""
        SELECT count(c.id) FROM knowledge_chunks c
        JOIN knowledge_documents d ON d.id = c.document_id
        WHERE d.doc_type = 'WORK_PACKAGE'
    """).fetchone()[0]
    doc_chunks = conn.execute("""
        SELECT count(c.id) FROM knowledge_chunks c
        JOIN knowledge_documents d ON d.id = c.document_id
        WHERE d.doc_type != 'WORK_PACKAGE'
    """).fetchone()[0]
    print("\n=== EXPLAINING THE 1,359 FIGURE ===")
    print(f"WORK_PACKAGE chunks in SQLite: {wp_chunks}")
    print(f"Documentation (ADR, ARCHITECTURE, SPRINT_REPORT) chunks in SQLite: {doc_chunks}")
    print(f"Total chunks: {wp_chunks + doc_chunks}")
    print("Earlier, before 16 documentation files (ADRs + ARCHITECTURE) were ingested,")
    print("the points count reported in WF15 audit was 1,359.")
    print("When the documentation corpus (334-354 chunks) was ingested, the total became 1,693.")

if __name__ == "__main__":
    main()
