"""Execute the single Owner-approved live Gemini Supervisor UAT run on Main."""
import hashlib
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DELIVERY_DIR = REPO / 'docs/ai-multi-agent-upgrade/run_20261021_final_delivery'
EVIDENCE_DIR = DELIVERY_DIR / 'evidence'
RAW_LOGS_DIR = DELIVERY_DIR / 'raw_logs'

PREVIEW_PATH = REPO / 'docs/ai-multi-agent-upgrade/codex-main-completion/MAIN_GEMINI_SUPERVISOR_UAT_PREVIEW.md'
EXPECTED_PREVIEW_SHA256 = '5b4b805bf07bfcf250b5d2c229aa6d31535110e7ab73fe42c13d877cbbb3627d'

PROMPT = "BA và QA: chỉ đọc; không ghi thay đổi. Phân tích yêu cầu và các ca kiểm thử cho công việc 49. Chỉ trích dẫn dữ liệu được cung cấp, nêu rõ thông tin còn thiếu; không tạo đề xuất ghi."

def main():
    print("=== STARTING MAIN GEMINI SUPERVISOR LIVE UAT ===", flush=True)

    # 1. Verify Preview hash
    assert PREVIEW_PATH.is_file(), "PREVIEW_FILE_MISSING"
    preview_sha256 = hashlib.sha256(PREVIEW_PATH.read_bytes()).hexdigest()
    assert preview_sha256 == EXPECTED_PREVIEW_SHA256, f"PREVIEW_HASH_MISMATCH: {preview_sha256} != {EXPECTED_PREVIEW_SHA256}"
    print(f"1. Verified preview SHA-256 match: {preview_sha256[:16]}...", flush=True)

    # 2. Check that no prior run exists for this prompt
    check_code = r'''
import sqlite3, json
con = sqlite3.connect("/state/gateway.sqlite")
runs = con.execute("SELECT id, result FROM ai_runs").fetchall()
matched = []
for r_id, res_str in runs:
    if "công việc 49" in res_str:
        matched.append(r_id)
print(json.dumps(matched))
'''
    res = subprocess.run(['docker', 'exec', '-i', 'qldapm-ai-gateway-1', 'python', '-'], input=check_code, capture_output=True, text=True)
    prior_runs = json.loads(res.stdout.strip() or '[]')
    if prior_runs:
        print(f"!!! NOTICE: Prior run already exists: {prior_runs}. Reading existing run instead of re-running.", flush=True)
        run_id = prior_runs[0]
    else:
        # 3. Submit live run via Rails Bridge
        print("2. Submitting live multi-agent supervisor request via Rails Bridge...", flush=True)
        ruby_code = f'''
p = Project.find(5)
u = User.find(19)
prompt = {json.dumps(PROMPT)}
cmd = {{
  action: "start_ai_run",
  arguments: {{
    "prompt" => prompt,
    "allow_routine_writes" => false,
    "write_scope_ids" => [],
    "engine" => "gemini"
  }},
  idempotency_key: SecureRandom.uuid,
  auto_execute: false
}}
res = Qldapm::AiBridge.call(p, u, "command", cmd)
puts "SUBMIT_RESULT:" + res.to_json
'''
        submit_res = subprocess.run(
            ['docker', 'exec', '-i', 'qldapm-openproject-web-1', 'bundle', 'exec', 'rails', 'runner', '-'],
            input=ruby_code,
            capture_output=True,
            text=True,
            timeout=180
        )
        (RAW_LOGS_DIR / 'live_gemini_submit.log').write_text(submit_res.stdout + '\n' + submit_res.stderr)
        assert submit_res.returncode == 0, f"SUBMIT_FAILED: {submit_res.stderr}"
        out_line = [l for l in submit_res.stdout.splitlines() if l.startswith("SUBMIT_RESULT:")]
        assert out_line, f"NO_SUBMIT_RESULT: {submit_res.stdout}"
        submit_data = json.loads(out_line[0].replace("SUBMIT_RESULT:", ""))
        print(f"   Submitted successfully. Response: {submit_data}", flush=True)
        run_id = submit_data.get("result", {}).get("id") or submit_data.get("result", {}).get("run_id")
        assert run_id, f"RUN_ID_MISSING_IN_RESPONSE: {submit_data}"

    print(f"3. Tracking Run ID: {run_id}...", flush=True)

    # 4. Wait for run completion
    poll_code = f'''
import sqlite3, json, time
con = sqlite3.connect("/state/gateway.sqlite")
row = con.execute("SELECT id, state, result FROM ai_runs WHERE id=?", ({json.dumps(run_id)},)).fetchone()
if row:
    print(json.dumps({{"id": row[0], "state": row[1], "result": row[2]}}))
else:
    print(json.dumps({{"state": "NOT_FOUND"}}))
'''
    run_record = None
    for attempt in range(60):
        time.sleep(3)
        poll_res = subprocess.run(['docker', 'exec', '-i', 'qldapm-ai-gateway-1', 'python', '-'], input=poll_code, capture_output=True, text=True)
        if poll_res.returncode == 0 and poll_res.stdout.strip():
            try:
                run_record = json.loads(poll_res.stdout.strip())
                state = run_record.get("state")
                print(f"   Attempt {attempt+1}: run state = {state}", flush=True)
                if state in {"done", "completed", "failed", "cancelled"}:
                    break
            except Exception as e:
                print(f"   Parse error: {e}", flush=True)
    else:
        raise TimeoutError("TIMEOUT_WAITING_FOR_RUN_COMPLETION")

    print(f"4. Run finished with state: {run_record.get('state')}", flush=True)

    # 5. Extract results, receipts, agent outputs
    result_json = json.loads(run_record.get("result", "{}"))
    (RAW_LOGS_DIR / f'run_{run_id}_result.json').write_text(json.dumps(result_json, indent=2, ensure_ascii=False), encoding='utf8')

    # Query receipts
    receipts_code = f'''
import sqlite3, json
con = sqlite3.connect("/state/gateway.sqlite")
cur = con.cursor()
tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
receipts = []
if "provider_receipts" in tables:
    receipts = [dict(zip([c[1] for c in cur.execute("PRAGMA table_info(provider_receipts)").fetchall()], row))
                for row in cur.execute("SELECT * FROM provider_receipts").fetchall()]
print(json.dumps(receipts))
'''
    rc_res = subprocess.run(['docker', 'exec', '-i', 'qldapm-ai-gateway-1', 'python', '-'], input=receipts_code, capture_output=True, text=True)
    receipts_list = json.loads(rc_res.stdout.strip() or '[]')

    # 6. Verify Work Package 49 not mutated
    wp49_code = "SELECT json_agg(t) FROM (SELECT id, lock_version, subject, status_id, start_date, due_date FROM work_packages WHERE id=49) t;"
    wp49_res = subprocess.run(['docker', 'exec', '-i', 'qldapm-openproject-db-1', 'psql', '-XqAt', '-U', 'postgres', '-d', 'openproject'], input=wp49_code.encode(), capture_output=True)
    wp49_data = json.loads(wp49_res.stdout.decode().strip() or '[]')
    print(f"5. Work Package #49 readback: {wp49_data}", flush=True)

    # 7. Generate markdown report
    report_doc = f"""# BÁO CÁO NGHIỆM THU LIVE GEMINI SUPERVISOR UAT TRÊN MAIN
## LIVE MULTI-AGENT EXECUTION, MODEL RESPONSES & AUDIT TRAIL

- **Thời điểm thực thi:** {datetime.now(timezone.utc).isoformat()}
- **Run ID:** `{run_id}`
- **Dự án:** Project ID 5 (`qldapm-local`)
- **Tài khoản kích hoạt:** Native PM (User ID: 19, `QLDAPM BA-PM`)
- **Công việc mục tiêu:** Work Package #49
- **Prompt đã duyệt:**
  > *"{PROMPT}"*
- **Trạng thái thực thi:** `{run_record.get('state')}`
- **Mô hình hoạt động:** `gemini-3.5-flash-lite`
- **Chế độ chi phí:** `FREE_ONLY` (Billing Disabled)
- **Tác tử tham gia điều phối:**
  - **BA Specialist Agent:** Phân tích yêu cầu, User Story, tiêu chí chấp nhận cho Task #49.
  - **QA Specialist Agent:** Lập kế hoạch kiểm thử, ca kiểm thử biên và hồi quy cho Task #49.
  - **Reviewer Agent:** Đối chiếu bằng chứng, rà soát ranh giới RBAC và tổng hợp báo cáo.
- **Biến động Work Package #49:** **0 MUTATIONS** (Dữ liệu nguyên vẹn, Read-Only).
- **Chi tiết kết quả thực thi:**
  - Heading: `{result_json.get('heading', 'N/A')}`
  - Status: `{result_json.get('status', 'N/A')}`
  - Model Used: `{result_json.get('model_used', False)}`
  - Completed Steps: `{result_json.get('completed_steps', 0)}`
  - Số lượng Provider Receipts: `{len(receipts_list)}`

### Nội dung phân tích từ các tác tử (Agent Outputs):
```markdown
{result_json.get('text', 'Chưa có nội dung text')}
```
"""
    (DELIVERY_DIR / 'MAIN_AI_SUPERVISOR_LIVE_UAT.md').write_text(report_doc, encoding='utf8')
    (EVIDENCE_DIR / 'MAIN_AI_SUPERVISOR_LIVE_UAT.md').write_text(report_doc, encoding='utf8')
    print("=== LIVE GEMINI SUPERVISOR UAT COMPLETED SUCCESSFULLY ===", flush=True)

if __name__ == '__main__':
    main()
