import sqlite3

db_path = r"C:\Users\LUIM\AppData\Local\QLDAPM\openproject-ai\gateway\knowledge.sqlite"
conn = sqlite3.connect(db_path)
c = conn.cursor()

print("=== ALL 376 DOCUMENTS IN KNOWLEDGE_DOCUMENTS ===")

c.execute("SELECT count(*) FROM knowledge_documents")
print("Total rows:", c.fetchone()[0])

# Group by doc_type
c.execute("SELECT doc_type, count(*) FROM knowledge_documents GROUP BY doc_type")
print("\nBy doc_type:", c.fetchall())

# Let's categorize every document by source_id prefix
c.execute("SELECT id, doc_type, source_id, title FROM knowledge_documents")
rows = c.fetchall()

categories = {}
actor_docs = []
file_docs = []
sprint_docs = []
op_wp_docs = []
other_docs = []

for row in rows:
    sid = row[2]
    dtype = row[1]
    if sid.startswith("actor:"):
        actor_docs.append(row)
    elif sid.startswith("file:"):
        file_docs.append(row)
    elif sid.startswith("op:sprint:"):
        sprint_docs.append(row)
    elif sid.startswith("op:wp:"):
        op_wp_docs.append(row)
    else:
        other_docs.append(row)

print(f"\nCategorization by source_id:")
print(f"1. 'op:wp:*': {len(op_wp_docs)}")
print(f"2. 'actor:*': {len(actor_docs)}")
print(f"3. 'file:*': {len(file_docs)}")
print(f"4. 'op:sprint:*': {len(sprint_docs)}")
print(f"5. Other: {len(other_docs)}")
print(f"TOTAL: {len(op_wp_docs) + len(actor_docs) + len(file_docs) + len(sprint_docs) + len(other_docs)}")

print(f"\nActor documents ({len(actor_docs)}):")
for a in actor_docs:
    print(f"  {a[2]} | {a[1]} | {a[3]}")

print(f"\nFile documents ({len(file_docs)}):")
for f in file_docs:
    print(f"  {f[2]} | {f[1]} | {f[3]}")

print(f"\nSprint documents ({len(sprint_docs)}):")
for s in sprint_docs:
    print(f"  {s[2]} | {s[1]} | {s[3]}")

# Check unique WP IDs across op:wp: and actor:
wp_ids_op = set()
for r in op_wp_docs:
    # op:wp:<id>
    wp_ids_op.add(int(r[2].split(":")[2]))

print(f"\nDistinct WP IDs in op:wp:*: {len(wp_ids_op)} (min: {min(wp_ids_op)}, max: {max(wp_ids_op)})")

# Check if any actor doc references WP not in op:wp:*
actor_wp_ids = set()
for r in actor_docs:
    parts = r[2].split(":")
    # actor:<actor_id>:wp:<wp_id>
    actor_wp_ids.add(int(parts[3]))
print(f"Distinct WP IDs in actor:*: {actor_wp_ids}")

# Check doc_type breakdown within op:wp:*
op_wp_types = {}
for r in op_wp_docs:
    dtype = r[1]
    op_wp_types[dtype] = op_wp_types.get(dtype, 0) + 1
print(f"\ndoc_type breakdown of op:wp:* documents: {op_wp_types}")

# Check doc_type breakdown of file:* documents
file_types = {}
for r in file_docs:
    dtype = r[1]
    file_types[dtype] = file_types.get(dtype, 0) + 1
print(f"doc_type breakdown of file:* documents: {file_types}")

conn.close()
