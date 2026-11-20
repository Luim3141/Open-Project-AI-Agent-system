"""Refresh the Gemini handoff from recorded evidence; never infer runtime success."""
import datetime
import json
from pathlib import Path


def refresh(root=None):
    root=Path(root or Path(__file__).resolve().parents[3]/'docs/ai/engineering')
    state_path=root/'IMPLEMENTATION_STATE.json'
    state=json.loads(state_path.read_text(encoding='utf-8'))
    state['updated_at']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).isoformat()
    state_path.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    body=['# QLDAPM MAIN Phase2 — Gemini handoff mới nhất',
        f"Cập nhật: {state['updated_at']}; checkpoint {state['last_verified_checkpoint']}; stage {state['current_stage']}; {state['status']}.",
        'Kiến trúc: existing QLDAPM Supervisor/Gateway + OpenClaw/Gemini API. Giữ OpenProject/n8n16/SecondBrain/BGE-M3. Project5 được bảo vệ. Project6/WP379 và repo demo được cấp engineering writes; không Codex/OpenAI runtime hoặc paid fallback.',
        'Source/config/triển khai phải phân biệt candidate và serving. Không reset/clean dữ liệu hoặc source untracked. Không chạy legacy Staging fixtures/runner.',
        '## Git / source',json.dumps(state['repositories'],ensure_ascii=False,indent=2),
        '## Runtime đã ghi nhận',json.dumps(state['openclaw'],ensure_ascii=False,indent=2),
        '## Project/WP đã xác minh',json.dumps(state['openproject'],ensure_ascii=False,indent=2)]
    for title,key in [('Hoàn tất','completed'),('Đang làm','in_progress'),('Blockers','blocked'),('Còn lại','remaining'),
                      ('Files thay đổi (giữ các untracked cũ)','changed_files'),('Test evidence (không suy PASS)','test_evidence'),
                      ('Deployment / rollback','deployment_state'),('Current deployment manifest','deployment_current'),
                      ('Feature completeness','feature_matrix'),('Three-repository implementation','repository_integration'),
                      ('Source snapshot hiện hành','code_snapshot'),('Deferred — chỉ khi được yêu cầu','deferred'),
                      ('Active run IDs — reconcile trước retry','active_run_ids')]:
        body+=['## '+title,json.dumps(state.get(key,[]),ensure_ascii=False,indent=2)]
    body+=['## Exact next action',state['next_exact_action'],
        '## Tiếp quản',
        'Đọc PHASE2_REQUEST.md, IMPLEMENTATION_JOURNAL.md, E2E_EVIDENCE.md và OPERATIONS_RUNBOOK.md. Kiểm tra Git/runtime thực tế trước tiếp tục; không nghiên cứu lại Phase1. File chưa commit vẫn là công việc cần giữ. Dùng GEMINI_CONTINUE_PROMPT.md để chuyển phiên. Cập nhật state/journal/evidence rồi chạy helper này sau mỗi milestone.',
        "Commands: `git status --short`; `git -C 'D:\\AI project\\QLDAPM-demo\\mini-task-manager' status --short --branch`; `wsl --list --verbose`; `docker ps`; xem runbook cho OpenClaw. Không replay run unknown hoặc approval đã consume."]
    (root/'HANDOFF_GEMINI_LATEST.md').write_text('\n\n'.join(body)+'\n',encoding='utf-8')
    return state['updated_at']


if __name__=='__main__':print(refresh())
