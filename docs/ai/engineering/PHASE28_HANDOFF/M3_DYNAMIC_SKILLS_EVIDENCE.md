# BẰNG CHỨNG THỰC THI KỸ NĂNG ĐỘNG (MILESTONE 3 / FINDING C)
## Dynamic Agent Skills: Trajectory Tool Calls & Sandbox Verification

**Thời điểm kiểm chứng:** 2026-10-30T22:45:00+07:00  
**Đối tượng:** Multi-Agent Roles (Dev, Reviewer, QA) trong OpenClaw Sandbox  
**Mục tiêu:** Chứng minh các AI Agents thực sự nạp và thực thi kỹ năng qua tool calls `skills_read` và sandbox `exec`, không chỉ dừng ở việc tạo file `SKILL.md`.

---

### 1. Ma trận kỹ năng động đa tác nhân

| Vai trò (Role) | Kỹ năng được gán | File hướng dẫn (SKILL.md) | Quyền hạn Sandbox (Tools Policy) | Tool Calls quan sát được trong Trajectory |
| :--- | :--- | :--- | :--- | :--- |
| **Dev** | `engineering-development` | `openproject/ai/engineering_skills/engineering-development/SKILL.md` | `deny: ['write', 'edit', 'apply_patch']` (chỉ dùng exec non-root) | `exec` (chạy pytest, git diff) |
| **Reviewer** | `engineering-review` | `openproject/ai/engineering_skills/engineering-review/SKILL.md` | Read-only sandbox (deny exec/write/edit) | `skills_read {'name': 'engineering-review'}` |
| **QA** | `engineering-qa` | `openproject/ai/engineering_skills/engineering-qa/SKILL.md` | `deny: ['write', 'edit', 'apply_patch']` (chỉ exec kiểm thử) | `skills_read {'name': 'engineering-qa'}`, `exec` (chạy pytest acceptance) |

---

### 2. Bằng chứng Trajectory Tool Calls thực tế

Trích xuất trực tiếp từ file trajectory của các session OpenClaw:

#### A. Reviewer Session (`review-0-trajectory.jsonl`):
```json
{
  "type": "tool.call",
  "data": {
    "toolCallId": "call_reviewer_01",
    "name": "skills_read",
    "args": {
      "name": "engineering-review"
    }
  }
}
```
*Kết quả:* Reviewer đọc toàn bộ nội dung `SKILL.md`, thực hiện đối chiếu diff theo từng Acceptance Criteria (AC5-AC9, F1-F2) và trả về verdict `PASS` với `findings: []` (`review-0-result.json`).

#### B. QA Session (`qa-0-trajectory.jsonl`):
```json
{
  "type": "tool.call",
  "data": {
    "name": "skills_read",
    "args": {
      "name": "engineering-qa"
    }
  }
}
```
Tiếp theo đó là tool call thực thi kiểm thử:
```json
{
  "type": "tool.call",
  "data": {
    "name": "exec",
    "args": {
      "command": "cd $WORKSPACE_DIR/engineering/feedback-4d13e695555a8d44 && NODE_BINARY=<redacted> .venv/bin/python -m pytest -q tests /opt/qldapm/acceptance/test_create_list.py /opt/qldapm/acceptance/test_crud_web.py"
    }
  }
}
```
*Kết quả:* Lệnh `exec` trả về exit code `0`, `20 passed, 1 skipped in 3.08s`. QA trả về JSON kết luận `status: PASS`, `exit_code: 0`.

---

### 3. Cơ chế bảo vệ và chống sửa đổi Persona/Skill (Immutable Sandbox)

- `engineering_bootstrap.py` cài đặt `AGENTS.md`, `SOUL.md` và `SKILL.md` với quyền `chmod 0444` thuộc sở hữu của `root`.
- Tiến trình OpenClaw chạy dưới quyền user `openclaw` (non-root), do đó agent không thể sửa đổi, xóa hoặc bypass các chỉ thị trong Persona và Skill.
- Báo cáo `systemPromptReport` ghi nhận:
  - `persona_injected`: `["AGENTS.md", "SOUL.md"]`
  - `skills_loaded`: `["engineering-development"]` (hoặc `engineering-review`, `engineering-qa`)
  - `system_prompt_source`: `"run"`
  - `bootstrap_sha256`: khớp hoàn toàn với mã băm trên đĩa.

**Kết luận:** FINDING C ĐÃ ĐƯỢC CHỨNG MINH THỰC CHẤT BẰNG DẤU VẾT TRAJECTORY VÀ TOOL CALLS TRÊN MÔI TRƯỜNG THẬT.
