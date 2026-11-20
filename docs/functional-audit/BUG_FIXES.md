# Bug fixes — đã triển khai MAIN

| Lỗi / mức | Repro và root cause | Sửa tối thiểu | Xác minh |
|---|---|---|---|
| F1 P1: false DONE #398 | Owner msg30 gọi “đã làm xong (DONE)” dù AWAITING_OWNER; output LLM chưa ràng buộc business acceptance | engine.py ground kết luận DONE bằng matching live Native business DONE + FULLY_COMPLETED + không source conflicts; lưu câu đã ground vào memory | Baseline immutable 4/5 tests fail; green62; Owner32 nói chưa DONE; telegram-live-postfix.json |
| F2: version27 bị gọi27steps | LLM đọc checkpoint revision như số bước; thiếu typed count/semantics | tools.context_result thêm completed_step_count/version_semantics, giữ khi truncation; system instructions | Actual11steps; Owner34 giải thích đúng revision27/11steps; checkpoint contracts |
| F3 P1: global read loop | GeminiTG-R06 lặp5rounds; registry chỉ có task/current-agent reads, TG-R07 suy noBlocked không state filter | 3 Empty strict tools get_active_agents/get_blocked_tasks/get_pending_approvals → Observer hiện hành, không backend mới | Owner35→functioncall→Gateway→feedback→36 PASS, resolved3.5lite, budget18/20 |
| F3b: global DTO mất root project và quá lớn | MAIN pending3rows443357B bị context truncate; project ở nested system | Explicit authorized project_id + compact task/stage state; giữ source bounds/freshness/conflicts, detail artifacts dùng detail tools | Test fixture omitted project + huge artifacts RED→GREEN; final pending8660B, untruncated; semantic13/13 |
| F4: read errors bị mask503 | Actual report503 quan sát, sau đó cùng report200. Ruby RED chứng minh upstream409/429 bị remap503; chưa biết upstream code của lượt503 đầu | Core private bridge_error_status dùng chung, giữ400..599/Retry-After/requestID cho observer/command/report/execution/history | Report9status cases, execution/history18cases, busy controller; MAIN report render/raw/export PASS. Không claim lượt503 đầu chắc là429 |
| F5: malformed execution offset503 | MAIN offset=bad503, offset negative422 | Integer(exception:false), reject invalid/negative422 trước Gateway | RED log; Ruby no-Gateway-call assertion; final MAIN bad/-1→422,0→200 |

Product files chỉ4: Core qldapm_ai_controller.rb và Telegram engine.py/tools.py/system_instructions.py. Không đổi Gateway, n8n, orchestrator, dependencies, keys, model, caps hoặc acceptance gates. Tests cũ được chỉnh theo current contract: malformed QA422, canonical resume eligibility, extracted Knowledge partial, WF11 legacy readonly input. Không hạ điều kiện production để làm tests xanh.

RAG UI: một lượt không xuất hiện kết quả; probe sau query200~10.55s/direct200~11.09s và full rerun14/14PASS. Chưa xác định root cause của lượt fail; không tune timeout/threshold hoặc xóa evidence để nhận FULL PASS.
