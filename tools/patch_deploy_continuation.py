from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
file_path = ROOT / 'openproject' / 'ai' / 'automation' / 'engineering_deploy_continuation.py'
content = file_path.read_text(encoding='utf-8')

old_line = "count=int(run(['docker','exec','qldapm-ai-gateway-1','python','-c',\"import sqlite3;from contextlib import closing;\\nwith closing(sqlite3.connect('/state/gateway.sqlite')) as d:print(d.execute(\\\"SELECT count(*) FROM ai_queue WHERE state!='finished'\\\").fetchone()[0])\"]))"

# Connect from host or use chr(39)
new_line = "import sqlite3; count=int(sqlite3.connect(str(PRIVATE.parent/'gateway/gateway.sqlite')).execute(\"SELECT count(*) FROM ai_queue WHERE state!='finished'\").fetchone()[0])"

assert old_line in content, "old_line not found"
content = content.replace(old_line, new_line, 1)

file_path.write_text(content, encoding='utf-8')
print("Patched engineering_deploy_continuation.py successfully")
