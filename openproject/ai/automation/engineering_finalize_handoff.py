"""Build the final Vietnamese handoff from verified artifacts, without inference."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import zipfile
import xml.etree.ElementTree as ET

from automation.engineering_checkpoint import refresh
from automation.engineering_worker import ROOT,DEMO,operator

DOCS=ROOT/'docs/ai/engineering'


def read(name):return json.loads((DOCS/name).read_text(encoding='utf-8'))
def write(name,text):(DOCS/name).write_text(text.strip()+'\n',encoding='utf-8')


def finalize():
    if (DOCS/'PHASE2_CONTINUATION_REQUEST.md').exists():
        raise ValueError('BASELINE_FINALIZER_SUPERSEDED_USE_CONTINUATION_HANDOFF')
    qualification=read('FINAL_QUALIFICATION.json');deployment=read('deployment.json');demo=read('demo-service.json')
    if qualification['status']!='PASS':raise ValueError('FINAL_QUALIFICATION_REQUIRED')
    live=operator('status')
    if live['mode']!='OFF' or any(r['queue_state']!='finished' or r['result']['status']!='succeeded' for r in live['runs']):raise ValueError('COMPLETED_OFF_REQUIRED')
    results=[r['result'] for r in live['runs']]
    full=next(r for r in results if r['head_sha']==demo['head_sha'])
    suites=list(ET.parse(full['test_evidence']['artifact']).getroot().iter('testsuite'))
    tests=sum(int(s.get('tests',0)) for s in suites)
    if tests!=17 or any(int(s.get('failures',0))+int(s.get('errors',0)) for s in suites):raise ValueError('APPLICATION_TESTS_NOT_PASS')
    old_journal=DOCS/'IMPLEMENTATION_JOURNAL_ARCHIVE_PRE_FINAL.md'
    if not old_journal.exists():shutil.copy2(DOCS/'IMPLEMENTATION_JOURNAL.md',old_journal)
    write('MANUAL_UAT_CHECKLIST.md',r'''
# Kiểm thử thủ công sau Phase 2

Triển khai/backend đã kiểm chứng bằng code và terminal. Theo yêu cầu, không dùng computer use. Bạn xác nhận phần giao diện và trải nghiệm; chưa coi human acceptance là hoàn tất.

## Mini Task Manager

Mở **http://127.0.0.1:18791**. Source ở `D:\AI project\QLDAPM-demo\mini-task-manager`, branch `codex/mini-task-manager-ready`, commit `29ff0ec1e531d917ce96737d768c8e16dad895c5`.

1. Tạo task, tải lại trang và kiểm tra task còn tồn tại.
2. Sửa tiêu đề; đổi lần lượt `todo`, `in_progress`, `done`.
3. Tìm kiếm tiêu đề, thử chuỗi có `%` và `_`; kết hợp bộ lọc trạng thái.
4. Xóa đúng task thử của bạn và kiểm tra danh sách cập nhật.
5. Thử tiêu đề trống, Tab/Enter, màn hình hẹp; kiểm tra label và thông báo lỗi dễ hiểu.

## QLDAPM Engineering

Mở **http://127.0.0.1:18088/projects/ai-dev-demo/qldapm-ai**, đăng nhập tài khoản PM Project 6 đã xác minh (`user 20`).

1. Kiểm tra OFF, hai run đã hoàn tất, commit/PR, kết quả QA, reviewer và usage.
2. Chọn #379/unit đã hoàn tất rồi RUN ONCE: phải trả cùng run/artifact, không tạo thêm task hoặc gọi model lại.
3. PAUSE phải hiện PAUSED; OFF đưa về OFF. Với unit đang chờ chưa claim, RUN ONCE tiếp tục đúng unit cũ. Với unit đã chạy và dừng giữa chừng, cần đối soát checkpoint trước khi tiếp tục.
4. Kiểm tra Native Tasks #380/#381 và progress của #379; kiểm tra PR #1 và #2.

PR #2 đặt trên branch của PR #1. Chưa merge PR; #379 chờ review/UAT và chưa tự chuyển Done. Các bản ghi sửa lỗi/failed attempts được giữ trong `runs/`.

## Khi tiện kiểm tra lại Windows logon

Task `QLDAPMEngineeringDelivery` đã được start thật và xác minh Running/idle không gọi model. Chưa reboot/logon Windows để kiểm thử trigger thực tế. Sau một lần đăng nhập Windows khi tiện, kiểm tra Docker, app18791 và task delivery. Không cần đóng phiên Codex để thử; runtime dùng OpenClaw/Gemini và host adapter.
''')
    write('OPERATIONS_RUNBOOK.md',r'''
# Vận hành và phục hồi Phase 2

Workspace `D:\AI project\QLDAPM chat`. Đọc `deployment.json`, `FINAL_QUALIFICATION.json` và `IMPLEMENTATION_STATE.json` trước thao tác. Không replay publication: PR #1/#2 và Native #380/#381 đã tồn tại.

## Runtime và địa chỉ

- OpenProject: `http://127.0.0.1:18088`.
- QLDAPM Gateway: `http://127.0.0.1:18089`.
- n8n: `http://127.0.0.1:5679`, giữ nguyên16workflow active/published.
- OpenClaw: một WSL2 distro `OpenClawGateway`, loopback18789; root provider gate18890.
- Mini Task Manager: `http://127.0.0.1:18791`, user service `qldapm-mini-task-manager.service`.
- Data demo: `/home/openclaw/engineering/demo-data/tasks.sqlite`; giữ nguyên khi restart/update.

## Kiểm tra / start

```powershell
Set-Location -LiteralPath 'D:\AI project\QLDAPM chat'
wsl --list --verbose
docker ps
wsl -d OpenClawGateway -u openclaw --cd /home/openclaw --exec /usr/bin/dbus-launch true
wsl -d OpenClawGateway -u openclaw --cd /home/openclaw --exec /usr/local/bin/openclaw --version
wsl -d OpenClawGateway -u openclaw --cd /home/openclaw --exec /usr/local/bin/openclaw gateway health --json
Get-ScheduledTask -TaskName QLDAPMEngineeringDelivery
Start-ScheduledTask -TaskName QLDAPMEngineeringDelivery
```

Task dùng current interactive user, hidden PowerShell, logon trigger, cho phép chạy bằng pin, IgnoreNew. Wrapper chỉ boot đúng distro và poll queue; không tự admit công việc. Log private: `%LOCALAPPDATA%/QLDAPM/openproject-ai/operator/engineering-delivery.log`. Đã start thật/kiểm tra idle; Windows reboot/logon trigger chưa thử.

```powershell
$env:PYTHONPATH='openproject/ai'
& 'openproject/ai/.venv/Scripts/python.exe' -B -c "from automation.engineering_worker import operator; print(operator('status'))"
& 'openproject/ai/.venv/Scripts/python.exe' -B -c "from automation.engineering_worker import operator; print(operator('control',mode='PAUSED'))"
& 'openproject/ai/.venv/Scripts/python.exe' -B -c "from automation.engineering_worker import operator; print(operator('control',mode='OFF'))"
```

PAUSE giữ job chưa claim. RUN ONCE tiếp tục cùng job chưa thực thi sau kiểm tra source mới. OFF có thể hủy job chưa claim; RUN ONCE chỉ tái kích hoạt khi chứng minh `served=0`. Job đã chạy/unknown không tự replay. In-flight PAUSE/OFF dừng tại checkpoint; nếu worker mất, lease kết thúc và mode về OFF, giữ outcome để đối soát.

## Lỗi cài Node ban đầu

Installer đã dùng Node24.19.0, CLI yêu cầu `>=24.22.1 <25 || >=26.12.1`, npm exit1. Installer tự `wsl --unregister OpenClawGateway` lúc rollback; vì vậy không còn distro cũ để sửa tại chỗ. Log gốc giữ tại `%APPDATA%/OpenClawTray/Logs/Setup/` (run `f93f29404270`).

Đã tạo lại đúng một Ubuntu24.04 WSL2 bằng `wsl --install --distribution Ubuntu-24.04 --name OpenClawGateway --location ... --no-launch --web-download`; cài private Node24.22.2 sau kiểm SHA256 chính thức, prefix `/home/openclaw/.openclaw/tools/node-v24.22.2`, npm11.19.1 và `openclaw@2026.10.8 --allow-scripts=openclaw --no-fund --no-audit`. Wrapper `/usr/local/bin/openclaw` đặt PATH vào prefix này. Windows Node25.8.2 không đổi.

Không chạy installer Windows lại để quay về Node cũ. Không unregister distro hoặc global WSL shutdown. Chỉ mount repo demo; Windows drive automount/interop bị tắt. Source thực thi dùng ext4 linked worktrees để tránh lỗi staged-file publish trên drvfs; các smoke artifacts cũ được giữ.

## Gemini / quota / receipts

Model đã chạy thật: `google/gemini-3.5-flash-lite`, không fallback. Real key root-only `/root/.qldapm-openclaw/google-key`0600; OpenClaw chỉ có local gate token. Không in key/.env/config auth. Gate OFF mặc định; shared QLDAPM quota được reserve trước allowance/deadline hữu hạn; retry tính trong allowance. Giữ13RPM/450RPD/225000TPM policy hiện hữu; bounded wait75s, không tăng quota hoặc đổi paid tier.

Nếu OpenClaw báo sign-in nhưng transport hết `remaining`, có thể là gate allowance hết; không tự rotate key. Xem dispatch/result/transport/trajectory trong `runs/<run>/attempt-N`. Unknown: OFF gate/fence own Gateway, export/reconcile trước tiếp tục. `openclaw gateway stop --force` là lệnh dừng service đã kiểm chứng. Không gọi lại thao tác Native/GitHub có outcome unknown.

Metadata IDs nay gồm session UUID + step + sequence. Script `engineering_reconcile_usage.py` đã chạy một lần để khôi phục56request thực từ transport, lưu before archive và SHA; không chạy lại tự động. Counter quota không bị sửa. Tokens là provider-reported; có usage thiếu ở lỗi503, không là chứng từ billing. Không kiểm tra Google billing console live.

## Tests / source

```powershell
$env:PYTHONPATH='openproject/ai;openproject/ai/tests'
& 'openproject/ai/.venv/Scripts/python.exe' -B -m unittest tests.test_engineering tests.test_agent_queue tests.test_ai_queue tests.test_agent_registry tests.test_openclaw_provider_gate tests.test_native_incremental_sync tests.test_execution_monitor tests.test_knowledge_sync -q
```

External acceptance ở `/opt/qldapm/acceptance/`, root-owned; chạy bằng user openclaw, không chạy application code bằng root. Demo release theo commit ở `/home/openclaw/engineering/releases/29ff0ec1e531d917ce96737d768c8e16dad895c5`. `engineering_demo.py` đã install/test; không rerun installer khi port18791 đang dùng. Restart app qua systemd user, giữ datafile.

## Rollback

Prior images/private backup ở `deployment.json`. Chặn admission, đối soát active run trước rollback. Restore image/config bằng compose cho riêng Gateway/Core web; không tự restore business DB. Các additive metadata tables có thể giữ. Không xóa Docker volumes, source untracked, VHDX hoặc demo data.

**SQLite live bind mount do Linux sở hữu. Không mở bằng Windows sqlite3.** Bước backup từng giữ Windows connection gây disk I/O; đã đóng đúng process và Linux quick_check=ok. Không xóa WAL/SHM/restore DB để sửa. Backup helper đã chuyển vào Linux và explicit closing.

Handoff: cập nhật state/journal/evidence rồi chạy `engineering_checkpoint.py`. Snapshot code không chứa credentials; sáu hồ sơ handoff hiện hành vẫn ở thư mục này.
''')
    write('E2E_EVIDENCE.md',f'''
# Bằng chứng Phase 2 — backend hoàn tất, chờ UAT người dùng

Kết quả được đối soát bằng code/terminal; không dùng computer use sau yêu cầu của người dùng. Các lần thất bại và rework được giữ, không gọi chúng là PASS.

| Hạng mục | Bằng chứng | Kết quả |
|---|---|---|
| OpenClaw/Node | Node24.22.2 + CLI2026.10.8, smoke actual exec red1/green0 | PASS |
| Project6 scope | Fresh PM20; Project5 vẫn BA20; scope/nonce/role-revocation tests | PASS |
| Queue/control | Atomic claim, semantic dedup, pause/cancel-before-claim, lost-worker OFF | PASS |
| Unit đầu | run5c43e11d-43b7-48b9-a4f8-b5a5e28dbf03; commit726f9738; PR1; Native380 | PASS sau artifact reconciliation; Dev terminal budget error giữ nguyên |
| CRUD/Web | run54edcb3a-51c4-4bd0-b7e8-ea797ab51ccb; commit{full['head_sha']}; PR2; Native381 | PASS |
| Reviewer/QA | Sessions độc lập, exact diff hash; thực thi pytest | PASS |
| App acceptance | {tests}tests, bao gồm AC1-9; working tree và clean exported release | PASS |
| RAG | Existing SQLite/FTS5/Qdrant/BGE-M3; actual retrieval379/380 và379/381 | PASS |
| n8n | WF04 HTTP200/20events Project6; execution2701success;16active/published | PASS |
| Local app | HTML200; create/edit/status/restart persistence/delete đúng fixture | PASS |
| Source/runtime | SHA256 Gateway/Core và provider gate khớp source; Windows Node25.8.2 giữ nguyên | PASS |
| Idle | ModeOFF, gateinactive, requests56→56 khi delivery poll | PASS |
| UI/reboot | Người dùng tự kiểm thử | PENDING |

Đã chạy86targeted regression tests PASS; sau điều chỉnh claim-OFF cuối chạy15engineering checks PASS. Rails Ruby/ERB compile và JavaScript lấy từ HTTP app `node --check` PASS. Có warning deprecation httpx/Starlette; không đổi dependency ngoài phạm vi khi tests đang đạt.

Nguồn: `FINAL_QUALIFICATION.json`, `deployment.json`, `demo-service.json`, `WF04-live.json`, `n8n-preservation.json`, `provider-receipts-session-fix.json`, `runs/*/result.json`, JUnit/log/trajectory.56request được khôi phục từ transport theo session, có before archive; quota và business counters không đổi. Không suy phí Google thực tế từ số cost0/usage SDK.

PR2 đặt trên branch PR1; chưa merge. #379 chưa tự Done. First unit có các failed attempts rồi explicit artifact reconciliation; second unit có15PASS/2FAIL,16PASS/1FAIL và cuối17PASS. Đây là rework thật với evidence, không bỏ test hoặc giả lập agent.
''')
    write('GEMINI_CONTINUE_PROMPT.md',r'''
# Gemini tiếp quản QLDAPM MAIN Phase 2

Bạn là Senior Software Engineer tiếp quản từ Codex. Workspace `D:\AI project\QLDAPM chat`. Đọc HANDOFF_GEMINI_LATEST.md, IMPLEMENTATION_STATE.json, IMPLEMENTATION_JOURNAL.md, OPERATIONS_RUNBOOK.md, E2E_EVIDENCE.md, FINAL_QUALIFICATION.json và PHASE2_REQUEST.md. Kiểm tra Git/runtime trước thay đổi; không nghiên cứu lại Phase1, không xóa source/untracked hoặc reset DB.

Backend Phase2 đã triển khai/kiểm chứng; chờ người dùng UAT giao diện. **Người dùng yêu cầu không dùng computer use; ưu tiên code/terminal, giao checklist để người dùng tự test.** Tiếp tục theo next_exact_action và feedback thực tế, không khởi chạy lại hai unit đã hoàn tất.

Kiến trúc: existing QLDAPM Supervisor/Gateway sở hữu admission/queue/state; OpenClaw/Gemini API thực thi Dev/Reviewer/QA. PM/BA dùng local registry deterministic, model_used=false. Không Paperclip server/Codex CLI/OpenAI/9Router runtime. Giữ n8n16 và SecondBrain SQLite/FTS5/Qdrant/Ollama BGE-M3.

Project5 qldapm-local được bảo vệ. Scope demo là Project6 ai-dev-demo/#379, actorPM20 được xác minh qua Native; không đổi mapping BA20 của Project5. Hai unit allowlist ở gateway/engineering_units.py; mở rộng WP/unit khác cần contract/authorization rõ ràng, không tháo guard.

Full demo commit29ff0ec1e531d917ce96737d768c8e16dad895c5, Windows branchcodex/mini-task-manager-ready, PR2 đặt trên branchPR1. Native380/381 và RAG đã có; không replay publication. First unit có terminal model-budget failures đã được giữ và explicit artifact reconciliation; đọc runs/ nếu điều tra. Metadata receipts đã sửa session namespace và reconcile56actualrequests; không rerun script phục hồi lịch sử.

App http://127.0.0.1:18791, data `/home/openclaw/engineering/demo-data/tasks.sqlite`. Delivery taskQLDAPMEngineeringDelivery đang chạy hidden/current user, không phụ thuộc phiên Codex. Đã test start/idle, chưa reboot/logon thật. Không keys trong prompt/log/source; real Gemini key root-only. Không paid fallback; khi quota/key lỗi giữ checkpoint/OFF.

Source hiện hành và deployment hashes xem state/manifest. QLDAPM MAIN có source untracked có từ trước; chưa commit/push MAIN trong Phase2. Snapshot code là bản phục hồi, sáu handoff files hiện hành nằm ngoài snapshot. Mỗi milestone lưu source/evidence, cập nhật state/journal, chạy engineering_checkpoint.py. Giữ nguyên lịch sử và phân biệt automated PASS với human acceptance.
''')
    write('IMPLEMENTATION_JOURNAL.md',r'''
# Nhật ký triển khai Phase 2

Nhật ký gốc chi tiết trước tổng kết được giữ tại `IMPLEMENTATION_JOURNAL_ARCHIVE_PRE_FINAL.md`; artifacts và failed attempts trong `runs/` là nguồn đối soát. Bản này trình bày tiến trình bằng tiếng Việt.

1. Checkpoint0: đọc request/architecture, kiểm tra Git/container/WSL, tạo đủ sáu hồ sơ trước thay đổi. Project5 được bảo vệ; Project6/#379/repo demo được cấp quyền.
2. Checkpoint1: journal installer chứng minh Node24.19.0 không đạt engines; retry thất bại, installer tự unregister distro lúc rollback. Không giả định còn distro/VHDX cũ.
3. Checkpoint2: tạo đúng một Ubuntu24.04 WSL2 OpenClawGateway; private Node24.22.2 kiểm SHA256, CLI2026.10.8. Không thay Node Windows. Disable drive automount/interop, chỉ mount demo; systemd user/linger; không global WSL shutdown.
4. Checkpoint3: hai smoke trước thất bại (503/timeout và staged-publish drvfs). Giữ dev/smoke files. Chuyển linked worktree ext4; smoke3 thực sự exec red1/green0, host rerun/hash PASS. Fresh Native xác minh PM20 Project6.
5. Checkpoint4–5: thêm scope/queue/bridge opt-in và gate root-owned, không mở generic business writes.33 rồi78targeted testsPASS, OFF probe CLI bị gate từ chối, cài venv WSL. Một manual token probe bị automatic approval review chặn; dùng CLI/unit tests thay thế, không che giấu.
6. Checkpoint6: deploy patch trên exact qualified base. Windows SQLite backup connection bị giữ gây disk I/O; dừng đúng process, Linux quick_check=ok; không xóa sidecars/restore DB. Sửa helper backup bên Linux/explicit close. Phát hiện compose private override giữ Core image cũ, sửa riêng web và readback.
7. Checkpoint7–8: integrated unit đầu dừng theo allowance, rồi gặp503. Đối soát terminal, giữ artifacts, không replay unknown. RAG vướng URL GitHub do sanitizer cũ; chỉ Project6 chuyển opaque Native references, classifier/Project5 giữ nguyên. Tăng bounded allowance, shared quota không tăng; đăng ký delivery logon task.
8. Checkpoint9: Dev đã tạo code/test thật nhưng hết allowance trước summary; independent7testsPASS. Explicit artifact continuation dựa exact failed-result/diff/test hashes, không giả Dev CLI hoàn tất. Reviewer/QA độc lập PASS; commit726f9738/PR1, Native380 và parent progress; RAG2records; OFF.
9. Checkpoint10–11,30/10/2026: theo yêu cầu chỉ code/terminal, không computer use. Thêm unitCRUD/Web phụ thuộc head đã verify, UI evidence/selector và WF04 owned-run scope. Actual acceptance bắt hai lỗi literal wildcard/label dù reviewer ban đầuPASS. Rework bị localRPM trước inference; bounded wait25→75s, không tăng quota. Live WF04 HTTP200/20events đúngProject6, execution2701success;16workflow active/published. Temporary test token được thu hồi.
10. Checkpoint12: rework đầu sửa wildcard, còn16/17 vì label JS không gắn với form. Focused rework sửa đúng label/aria và verification command; cuối17/17, Reviewer/QA độc lập PASS; commit29ff0ec1/PR2, Native381, RAG379/381, OFF. Windows source branchready, dev/ cũ giữ nguyên.
11. Kiểm chứng release: export đúng Git commit ra versioned release, user service18791. Terminal create/edit/status/restart persistence/delete đúng fixturePASS; clean release17testsPASS; served JS syntaxPASS. Không chạy app code bằng root, không reset data.
12. Rà cuối: phát hiện UUID receipt chỉ theo step/index ghi đè attempts; thêm session UUID, lưu before archive, atomically phục hồi56actualrequests từ transport; không đổi quota/business counters.86targeted testsPASS; final claim-OFF tweak có15engineering checksPASS. PAUSE giữ queued, RUN ONCE chỉ tái kích hoạt neverclaimed; executed/unknown cần đối soát. Source/runtime hashes, Project5 fresh BA20/config, n8n16, OFF/gateinactive và hidden delivery idle56→56 đềuPASS.
13. Hồ sơ cuối: snapshot code/manifest, recovery/runbook và checklist UAT. Chưa merge PR hoặc đánh dấu #379Done; chưa human UI acceptance hoặc Windows reboot/logon trigger test. Một shell command cập nhật tài liệu bị automatic approval review chặn; chuyển sang file patch và helper hồ sơ, không bỏ yêu cầu handoff.
''')
    # Preserve the historical architecture document and update only its Phase2 preface.
    architecture=ROOT/'architecture.md';text=architecture.read_text(encoding='utf-8')
    marker='## Final stabilization'
    if marker not in text:raise ValueError('ARCHITECTURE_HISTORY_MARKER_REQUIRED')
    prefix='''## Phase 2 — đã triển khai backend, chờ UAT người dùng (30/10/2026)

Authority: docs/ai/engineering/HANDOFF_GEMINI_LATEST.md, IMPLEMENTATION_STATE.json, FINAL_QUALIFICATION.json và deployment.json. Source/runtime SHA256 khớp; không coi health hoặc automated PASS là human acceptance.

QLDAPM Supervisor/Gateway giữ admission, scope, atomic claim, lifecycle và completion trên existing Store/AgentTask/AgentRun. Host delivery adapter chỉ thực thi contract đã claim, serialized Dev→Reviewer→QA/rework→publication. Không Supervisor/Paperclip server thứ hai. Runtime dùng OpenClaw/Gemini API, không Codex CLI/OpenAI/9Router. PM/BA local registry deterministic (model_used=false); selected local skill adaptations version1.0.0.

Project6 opt-in exact ai-dev-demo/#379, PM20 được revalidate Native. Hai unit: create-list-persistence-v1 và crud-search-web-v1, unit2 phụ thuộc verified head unit1. Generic business tools/confirm không được mở rộng; Project5 config/BA20/gates giữ nguyên. REST WF04 suy project từ owned stored run, sau đó kiểm lại membership; n8n16active/published không sửa workflow.

OpenClaw nằm trong một WSL2 Ubuntu24.04 distro, Node24.22.2/CLI2026.10.8, một loopback Gateway18789. Chỉ mount demo, disable Windows interop/automount. Ext4 linked worktrees tránh staged publish lỗi trên drvfs. Heartbeat/cron/fallback tắt. Root transport gate18890 giữ real key0600, client chỉ có local token; allowance/deadline/shared quota bao gồm retry. Receipt namespace gồm session/step/sequence, lịch sử rework đã reconcile từ transport với before archive.

OFF/RUN ONCE/PAUSE bền vững. PAUSE giữ queued; explicit RUN ONCE tái kích hoạt cùng neverclaimed unit sau source check. Executed/unknown không tự replay. Worker mất/lease finished sẽ về OFF; in-flight pause giữ checkpoint để đối soát. Delivery chạy hidden/current Windows user qua QLDAPMEngineeringDelivery, đã start/idle verify, chưa reboot/logon thật.

Reviewer session độc lập/read-only; QA và host chạy pytest thật trên exact diff/commit. Root-owned external acceptance không nằm trong writable repo; app luôn non-root. Publisher dùng trusted bare repo + Git bundle, tránh Windows Git config/hooks do agent sửa. PR1/PR2 open (PR2 stack trên PR1), Native380/381 và RAG readback; #379 chờ review/UAT.

SecondBrain vẫn là SQLite/FTS5/Qdrant/Ollama BGE-M3, không thêm embedding DB/model. Native URLs Project6 thành opaque aliases trước classifier, không crawl hoặc làm yếu Project5. Incremental scanner/outbox reuse và actor/project ACL revalidation.

Mini Task Manager đủ CRUD/status/search/filter/SQLite/web;17testsPASS, clean release và terminal persistence qua restartPASS. User service loopback18791 phục vụ versioned release commit29ff0ec1, data riêng demo-data/tasks.sqlite. Windows source checkout cùng commit, giữ dev/smoke cũ. Không auto merge/deploy MAIN bằng quyền agent; triển khai MAIN do host operator đã được người dùng cấp quyền.

Rollback image/config theo private snapshot, không tự restore business DB hoặc xóa volumes. SQLite live do Linux sở hữu; backup phải bên Linux với explicit close. Source MAIN chưa commit/push trong Phase2; code snapshot và manifest giữ thay đổi untracked. UI/human acceptance theo checklist do người dùng tự test, không computer use.

'''
    architecture.write_text(prefix+text[text.index(marker):],encoding='utf-8')
    files=[ROOT/'architecture.md',DOCS/'PHASE2_REQUEST.md',DOCS/'OPERATIONS_RUNBOOK.md',DOCS/'MANUAL_UAT_CHECKLIST.md']
    for name in qualification['gateway_source_sha256']:files.append(ROOT/'openproject/ai/gateway'/name)
    for name in qualification['core_source_sha256']:files.append(ROOT/'openproject/ai/core/overlay'/name)
    files+=list((ROOT/'openproject/ai/engineering_skills').rglob('SKILL.md'))
    files+=list((ROOT/'openproject/ai/automation').glob('engineering_*.py'))
    files+=[ROOT/'openproject/ai/automation'/name for name in ['openclaw_provider_gate.py','Start-EngineeringDelivery.ps1','EngineeringGateway.Dockerfile','EngineeringCore.Dockerfile']]
    files+=[ROOT/'openproject/ai/tests'/name for name in ['test_engineering.py','test_ai_queue.py','test_openclaw_provider_gate.py']]
    files.append(DOCS/'runs/54edcb3a-51c4-4bd0-b7e8-ea797ab51ccb/attempt-2/publish.bundle')
    files=sorted(set(files));manifest=[]
    secret=re.compile(rb'(?:AIza[0-9A-Za-z_-]{35}|ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{60,})')
    for path in files:
        content=path.read_bytes()
        if secret.search(content):raise ValueError('POSSIBLE_SECRET_SNAPSHOT_HOLD')
        manifest.append({'path':path.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(content).hexdigest(),'bytes':len(content)})
    snapshot=DOCS/'PHASE2_SOURCE_20261030.zip'
    if snapshot.exists():raise ValueError('SNAPSHOT_ALREADY_EXISTS_DO_NOT_OVERWRITE')
    write('SOURCE_MANIFEST.json',json.dumps({'scope':'code + stable runbook/UAT/request + demo Git bundle; mutable six handoff files remain current on disk','files':manifest},ensure_ascii=False,indent=2))
    with zipfile.ZipFile(snapshot,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for path in files:z.write(path,path.relative_to(ROOT).as_posix())
        z.write(DOCS/'SOURCE_MANIFEST.json','docs/ai/engineering/SOURCE_MANIFEST.json')
    write('SOURCE_SNAPSHOT.json',json.dumps({'path':str(snapshot),'sha256':hashlib.sha256(snapshot.read_bytes()).hexdigest(),'files':len(files),'credentials_included':False},indent=2))
    state=read('IMPLEMENTATION_STATE.json')
    state.update(current_stage='IMPLEMENTED_READY_FOR_USER_UAT',status='READY_FOR_USER_UAT',last_verified_checkpoint='FINAL',
        active_run_ids=[],active_openclaw_run_id=None,in_progress=[],blocked=[],
        remaining=['Người dùng tự kiểm thử UI theo MANUAL_UAT_CHECKLIST.md','Review/merge PR1 rồi PR2 khi được người dùng chấp thuận','Windows logon/reboot trigger test khi tiện; chưa thực hiện'],
        next_exact_action='Người dùng UAT app18791 và QLDAPM Project6/#379. Nếu có lỗi, ghi actual/expected rồi sửa theo evidence; không replay hai unit/publication đã hoàn tất.',
        deployment_state=[deployment,{'demo':demo,'delivery_task':'Running; manual start/idle verified; logon/reboot NOT RUN'}],
        completed=['A: baseline/checkpoint trước thay đổi','B: Node/OpenClaw/Gemini actual file+exec verified','C-F: Project6 scope, registry/profiles/skills, durable queue/controls, bounded real execution','G: existing SecondBrain actual ingestion/retrieval379/380/381','H: n8n16preserved, WF04 live20events/execution2701success','I: two commits/PRs/Native children readback','J: full CRUD/status/search/SQLite/web,17tests and deployed restart persistencePASS','Final:86targeted tests +15final engineering checks, Ruby/ERB/served JS compile, source parity/control/idle/preservationPASS'],
        test_evidence=['FINAL_QUALIFICATION.json','E2E_EVIDENCE.md','demo-service.json','demo-static-checks.json','WF04-live.json','n8n-preservation.json','provider-receipts-session-fix.json','runs/*/result.json + JUnit/log/trajectory'],
        changed_files=[m['path'] for m in manifest],code_snapshot=read('SOURCE_SNAPSHOT.json'),
        ui_uat='PENDING_USER; code/terminal only per explicit request; no computer use',
        startup_delivery='QLDAPMEngineeringDelivery Running, hidden/current user; manual start/idlePASS; actual logon/rebootNOTRUN')
    state['repositories']['qldapm'].update(branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT).decode().strip(),
        head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip(),phase2_source_uncommitted=True,code_snapshot_preserved=True)
    state['repositories']['demo'].update(branch='codex/mini-task-manager-ready',head=full['head_sha'],dirty=True,untracked_preserved=['dev/'])
    state['openproject'].update(last_verified_version=operator('source')['lock_version'],native_children=[380,381],business_done=False)
    state['openclaw'].update(execution_workspace='/home/openclaw/engineering/crud-search-web-v1',gateway_status='HEALTH_AND_ACTUAL_EXEC_VERIFIED',provider_gate='OFF; root-owned real key; session-scoped receipts; no fallback')
    write('IMPLEMENTATION_STATE.json',json.dumps(state,ensure_ascii=False,indent=2));refresh()
    print(json.dumps({'status':state['status'],'snapshot':str(snapshot),'files':len(files),'application_tests':tests}))


if __name__=='__main__':finalize()
