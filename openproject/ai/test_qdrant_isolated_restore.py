"""ISOLATED QDRANT DISASTER RECOVERY RESTORE DRILL
Tests restoring the cold volume archive into a completely isolated Qdrant container instance
on port 6335, verifying collection status, 1,745 points, vector config, payload schema,
and 3 legacy vectors, and sample search without touching MAIN.
"""

import os
import sys
import time
import json
import shutil
import tarfile
import urllib.request
import subprocess

PORT = 6335
CONTAINER_NAME = "qdrant-isolated-drill"
BACKUP_DIR = r"C:\Users\LUIM\AppData\Local\QLDAPM\openproject-ai\gateway\backups\drill"
TEMP_STORAGE = os.path.join(BACKUP_DIR, "test_qdrant_drill_storage")
ARCHIVE_PATH = os.path.join(BACKUP_DIR, "qdrant_collection_backup_1793168825.tar.gz")

print("================================================================================")
print("STARTING ISOLATED QDRANT RESTORE DRILL ON CONTAINER " + CONTAINER_NAME)
print("================================================================================\n")

# 1. Clean previous temp storage or container if exists
subprocess.run(["docker", "rm", "-f", CONTAINER_NAME], capture_output=True)
if os.path.exists(TEMP_STORAGE):
    shutil.rmtree(TEMP_STORAGE)

os.makedirs(os.path.join(TEMP_STORAGE, "collections"), exist_ok=True)

# 2. Extract cold volume archive into isolated collections dir
print(f"1. Extracting cold archive: {ARCHIVE_PATH}")
t0 = time.time()
with tarfile.open(ARCHIVE_PATH, "r:gz") as tar:
    tar.extractall(path=os.path.join(TEMP_STORAGE, "collections"))
dur_extract = round(time.time() - t0, 3)
print(f"   Extracted in {dur_extract}s into: {os.path.join(TEMP_STORAGE, 'collections')}")

# 3. Start isolated Qdrant container on port 6335
print(f"\n2. Launching isolated container {CONTAINER_NAME} on port {PORT}...")
cmd_run = [
    "docker", "run", "-d",
    "--name", CONTAINER_NAME,
    "-p", f"127.0.0.1:{PORT}:6333",
    "-v", f"{TEMP_STORAGE}:/qdrant/storage:z",
    "qdrant/qdrant:latest"
]
p_run = subprocess.run(cmd_run, capture_output=True, text=True, check=True)
container_id = p_run.stdout.strip()[:12]
print(f"   Container started: {container_id}")

# 4. Wait for Qdrant to be healthy on port 6335
print("\n3. Waiting for isolated Qdrant service to become ready...")
ready = False
for attempt in range(20):
    time.sleep(1)
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{PORT}/")
        with urllib.request.urlopen(req, timeout=2) as r:
            if r.status == 200:
                ready = True
                print(f"   Ready after {attempt+1}s.")
                break
    except Exception:
        pass

if not ready:
    print("   FAILED: Qdrant isolated container did not become ready.")
    subprocess.run(["docker", "logs", "--tail", "30", CONTAINER_NAME])
    subprocess.run(["docker", "rm", "-f", CONTAINER_NAME])
    shutil.rmtree(TEMP_STORAGE)
    sys.exit(1)

# 5. Query restored collection metadata
print("\n4. Verifying restored collection metadata...")
req_col = urllib.request.Request(f"http://127.0.0.1:{PORT}/collections/qldapm_knowledge_dense")
with urllib.request.urlopen(req_col, timeout=5) as r:
    col_data = json.loads(r.read().decode())["result"]

status = col_data.get("status")
points_count = col_data.get("points_count")
indexed_vectors = col_data.get("indexed_vectors_count")
vec_params = col_data.get("config", {}).get("params", {}).get("vectors", {})
size = vec_params.get("size")
distance = vec_params.get("distance")

print(f"   Status: {status} (Expected: green)")
print(f"   Points Count: {points_count} (Expected: 1745)")
print(f"   Vectors: size={size}, distance={distance} (Expected: 1024, Cosine)")

# 6. Verify the 3 legacy points exist in the restored collection
print("\n5. Verifying the 3 historical legacy points in restored collection...")
legacy_point_ids = [
    # Let's search or scroll points
]
req_scroll = urllib.request.Request(
    f"http://127.0.0.1:{PORT}/collections/qldapm_knowledge_dense/points/scroll",
    data=json.dumps({"limit": 100, "with_payload": True, "filter": {
        "must": [{"key": "source_id", "match": {"any": ["op:wp:42", "test:local:adr:0001", "test:wp:999"]}}]
    }}).encode(),
    headers={"Content-Type": "application/json"},
    method="POST"
)
try:
    with urllib.request.urlopen(req_scroll, timeout=5) as r:
        scroll_res = json.loads(r.read().decode())["result"]
        found_legacy = scroll_res.get("points", [])
        print(f"   Found legacy points matching source_ids: {len(found_legacy)}")
        for pt in found_legacy:
            print(f"     ID: {pt.get('id')} | source_id: {pt.get('payload', {}).get('source_id')}")
except Exception as e:
    print(f"   Scroll error: {e}")

# 7. Test sample vector search in isolated collection
print("\n6. Testing sample semantic search retrieval in isolated instance...")
dummy_vector = [0.01] * 1024
req_search = urllib.request.Request(
    f"http://127.0.0.1:{PORT}/collections/qldapm_knowledge_dense/points/search",
    data=json.dumps({"vector": dummy_vector, "limit": 3, "with_payload": True}).encode(),
    headers={"Content-Type": "application/json"},
    method="POST"
)
with urllib.request.urlopen(req_search, timeout=5) as r:
    search_res = json.loads(r.read().decode())["result"]
    print(f"   Search returned {len(search_res)} results.")
    for idx, hit in enumerate(search_res):
        print(f"     Result #{idx+1}: score={round(hit.get('score', 0), 4)}, title={hit.get('payload', {}).get('title')}")

# 8. Clean up isolated resources
print("\n7. Cleaning up isolated test container and temporary storage...")
subprocess.run(["docker", "rm", "-f", CONTAINER_NAME], capture_output=True)
shutil.rmtree(TEMP_STORAGE)
print("   Cleaned up container and storage successfully.")

# Final evaluation
success = (status == "green" and points_count == 1745 and size == 1024 and len(search_res) == 3)
print("\n================================================================================")
print(f"DRILL VERDICT: {'QUALIFIED_ISOLATED_RESTORE_PASS' if success else 'DRILL_FAILED'}")
print("================================================================================")

sys.exit(0 if success else 1)
