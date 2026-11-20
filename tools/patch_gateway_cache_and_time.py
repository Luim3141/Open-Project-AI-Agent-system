from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 1. Patch engineering_github_sync.py
sync_path = ROOT / 'openproject' / 'ai' / 'gateway' / 'engineering_github_sync.py'
sync_content = sync_path.read_text(encoding='utf-8')

old_sync_header = """_CACHED_TOKEN: Optional[str] = None
_SYNC_CACHE: Dict[str, str] = {}

PR_WP_MAP = {"""

new_sync_header = """_CACHED_TOKEN: Optional[str] = None
_SYNC_CACHE: Dict[str, str] = {}
_CACHED_PRS: List[Dict[str, Any]] = []
_CACHED_PRS_TIME: float = 0.0
_PRS_TTL: float = 60.0

PR_WP_MAP = {"""

old_fetch_def = """def fetch_pull_requests(
    repo: str = "Luim3141/mini-task-manager",
    token: Optional[str] = None,
) -> List[Dict[str, Any]]:
    \"\"\"Fetch all pull requests from GitHub REST API with stacked branch awareness.\"\"\"
    if token is None:
        token = get_github_token()"""

new_fetch_def = """def fetch_pull_requests(
    repo: str = "Luim3141/mini-task-manager",
    token: Optional[str] = None,
    force: bool = False,
) -> List[Dict[str, Any]]:
    \"\"\"Fetch all pull requests from GitHub REST API with stacked branch awareness.\"\"\"
    global _CACHED_PRS, _CACHED_PRS_TIME
    now = time.time()
    if not force and _CACHED_PRS and (now - _CACHED_PRS_TIME < _PRS_TTL):
        return _CACHED_PRS

    if token is None:
        token = get_github_token()"""

old_fetch_return = """    return prs"""

new_fetch_return = """    _CACHED_PRS = prs
    _CACHED_PRS_TIME = time.time()
    return prs"""

old_reconcile_call = """        prs = fetch_pull_requests(repo, token=token)"""
new_reconcile_call = """        prs = fetch_pull_requests(repo, token=token, force=True)"""

assert old_sync_header in sync_content, "sync_header not found"
assert old_fetch_def in sync_content, "fetch_def not found"
assert old_reconcile_call in sync_content, "reconcile_call not found"

sync_content = sync_content.replace(old_sync_header, new_sync_header, 1)
sync_content = sync_content.replace(old_fetch_def, new_fetch_def, 1)
# Replace the return prs inside fetch_pull_requests
idx = sync_content.find("return prs\n\n\ndef _get_cached_hash")
if idx == -1:
    idx = sync_content.find("return prs\r\n\r\n\r\ndef _get_cached_hash")
assert idx != -1, "return prs inside fetch_pull_requests not found"
sync_content = sync_content[:idx] + "_CACHED_PRS = prs\n    _CACHED_PRS_TIME = time.time()\n    return prs" + sync_content[idx + len("return prs"):]
sync_content = sync_content.replace(old_reconcile_call, new_reconcile_call, 1)

sync_path.write_text(sync_content, encoding='utf-8')
print("Successfully patched engineering_github_sync.py")

# 2. Patch engineering.py
eng_path = ROOT / 'openproject' / 'ai' / 'gateway' / 'engineering.py'
eng_content = eng_path.read_text(encoding='utf-8')

old_eng_select = 'rows = db.execute("SELECT q.id,q.state,q.payload,r.result,q.actor FROM ai_queue q JOIN ai_runs r ON r.id=q.id WHERE json_extract(q.payload,\'$.project_id\')=6 AND json_extract(q.payload,\'$.engine\')=\'openclaw\' ORDER BY q.created DESC LIMIT 10").fetchall()'
new_eng_select = 'rows = db.execute("SELECT q.id,q.state,q.payload,r.result,q.actor,q.created FROM ai_queue q JOIN ai_runs r ON r.id=q.id WHERE json_extract(q.payload,\'$.project_id\')=6 AND json_extract(q.payload,\'$.engine\')=\'openclaw\' ORDER BY q.created DESC LIMIT 10").fetchall()'

old_runs_append = "runs.append({'id':r['id'],'queue_state':r['state'],'unit':json.loads(r['payload'])['unit'],"
new_runs_append = "runs.append({'id':r['id'],'queue_state':r['state'],'created_at':r['created'],'unit':json.loads(r['payload'])['unit'],"

assert old_eng_select in eng_content, "old_eng_select not found"
assert old_runs_append in eng_content, "old_runs_append not found"

eng_content = eng_content.replace(old_eng_select, new_eng_select, 1)
eng_content = eng_content.replace(old_runs_append, new_runs_append, 1)

eng_path.write_text(eng_content, encoding='utf-8')
print("Successfully patched engineering.py")
