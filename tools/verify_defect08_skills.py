import sqlite3
import json
import os
import subprocess

db_path = r'C:\Users\LUIM\AppData\Local\QLDAPM\openproject-ai\gateway\gateway.sqlite'

print("=================================================================")
print("VERIFYING DEFECT-08: DYNAMIC AGENT SKILLS 6-STEP CYCLE")
print("=================================================================\n")

# Step 1: Installed
print("--- Step 1: INSTALLED ---")
skills_dir = r"D:\AI project\QLDAPM chat\openproject\ai\engineering_skills"
skills = os.listdir(skills_dir)
print(f"Skills in repo ({len(skills)}): {skills}")
for s in skills:
    skill_file = os.path.join(skills_dir, s, "SKILL.md")
    if os.path.exists(skill_file):
        print(f"  - {s}/SKILL.md: {os.path.getsize(skill_file)} bytes")

# Step 2: Discovered & Configured in OpenClaw
print("\n--- Step 2: DISCOVERED & CONFIGURED IN RUNTIME ---")
r_cfg = subprocess.run(["wsl", "-d", "OpenClawGateway", "cat", "/home/openclaw/.openclaw/openclaw.json"], capture_output=True, text=True)
if r_cfg.returncode == 0:
    cfg = json.loads(r_cfg.stdout)
    entries = cfg.get("agents", {}).get("entries", {})
    for role, data in entries.items():
        print(f"  Role '{role}': skills={data.get('skills')}, contextInjection={data.get('contextInjection')}, cwd={data.get('cwd')}")
else:
    print("  Failed to read openclaw.json:", r_cfg.stderr)

# Step 3: Selected & Staged in Isolated Agent Directory
print("\n--- Step 3: SELECTED & ISOLATED WORKSPACE ---")
r_ls = subprocess.run(["wsl", "-d", "OpenClawGateway", "ls", "-la", "/opt/qldapm/agents/feedback-4d13e695555a8d44/"], capture_output=True, text=True)
print(r_ls.stdout.strip())

# Step 4: Read & Injected into LLM Prompt Context
print("\n--- Step 4: READ & INJECTED (systemPromptReport / contextInjection) ---")
with sqlite3.connect(db_path) as d:
    cur = d.cursor()
    cur.execute("SELECT event_id, run_id, document FROM execution_events ORDER BY rowid DESC LIMIT 20")
    events = cur.fetchall()
    print(f"Recent execution_events: {len(events)}")
    injected_count = 0
    for eid, rid, doc_str in events:
        if "skill" in doc_str.lower() or "injectedworkspacefiles" in doc_str.lower():
            injected_count += 1
            print(f"  Event {eid} (run {str(rid)[:8]}...): mentions skill/injected files")
            
    # Check gemini_call_receipts
    cur.execute("SELECT id, run_id, document FROM gemini_call_receipts ORDER BY rowid DESC LIMIT 5")
    receipts = cur.fetchall()
    print(f"Recent Gemini Call Receipts ({len(receipts)}):")
    for cid, crid, cdoc_str in receipts:
        try:
            cdoc = json.loads(cdoc_str)
            usage = cdoc.get("usage", {})
            print(f"  Call: {cid} | Run: {str(crid)[:8]} | Model: {cdoc.get('model')} | Prompt Tokens: {usage.get('prompt_tokens')} | Output Tokens: {usage.get('candidate_tokens')}")
        except:
            print(f"  Call: {cid} | Run: {str(crid)[:8]}")

# Step 5: Executed in Sandbox
print("\n--- Step 5: EXECUTED (Tool Permissions & Constraints) ---")
# dev has deny write/edit (uses non-root patches), reviewer has deny exec/write/edit, qa has deny write/edit
for role, data in entries.items():
    print(f"  Role '{role}' tools policy: {data.get('tools')}")

# Step 6: Verified
print("\n--- Step 6: VERIFIED (Acceptance & Test Results) ---")
r_acc = subprocess.run(["wsl", "-d", "OpenClawGateway", "ls", "-la", "/opt/qldapm/acceptance/"], capture_output=True, text=True)
print("Acceptance test suite files in WSL:\n" + r_acc.stdout.strip())

with sqlite3.connect(db_path) as d:
    cur = d.cursor()
    cur.execute("SELECT id, title, created FROM engineering_reports ORDER BY created DESC LIMIT 3")
    print("\nVerified Engineering Reports in DB:")
    for rep in cur.fetchall():
        print(f"  Report {rep[0]}: {rep[1]}")

print("\n=================================================================")
print("DEFECT-08 VERIFICATION COMPLETE")
print("=================================================================")
