# Command Center — actual MAIN UI / source inventory

**PARTIAL**, không tính mọi nút là PASS chỉ vì được render. Captured 931 DOM controls, 240 unique control signatures; đầy đủ page/component label, endpoint, permission, expected effect, observed/blocked state trong [JSON](command-center-inventory.json). Scope project6, authenticated Owner18; các project/role khác không có authenticated browser session mới trong phase này.

| UI / component | Observed result | Evidence level |
|---|---|---|
| tab_mission | PASS | MAIN headless Chromium clicks |
| tab_pipeline | PASS | MAIN headless Chromium clicks |
| tab_workforce | PASS | MAIN headless Chromium clicks |
| tab_backlog | PASS | MAIN headless Chromium clicks |
| tab_execution | PASS | MAIN headless Chromium clicks |
| tab_github | PASS | MAIN headless Chromium clicks |
| tab_reports | PASS | MAIN headless Chromium clicks |
| tab_knowledge | PASS | MAIN headless Chromium clicks |
| tab_integrations | PASS | MAIN headless Chromium clicks |
| workforce_real_roles | PASS | MAIN headless Chromium clicks |
| workforce_run_inspector | PASS | MAIN headless Chromium clicks |
| reports_reader_raw_export | PASS | MAIN headless Chromium clicks |
| rag_actual_search_citations_and_quality_notice | PASS | MAIN headless Chromium clicks |
| phase4_actual_gemini_answer_citations_source_read_mobile | PASS | MAIN headless Chromium clicks |
| command_center_to_studio_evidence_and_history | PASS | MAIN headless Chromium clicks |

| Unique UI control / tool | Endpoint / effect | Status |
|---|---|---|
| tab-mission | Client tab switch; no mutation | PASS |
| tab-pipeline | Client tab switch; no mutation | PASS |
| tab-workforce | Client tab switch; no mutation | PASS |
| tab-backlog | Client tab switch; no mutation | PASS |
| tab-execution | Client tab switch; no mutation | PASS |
| tab-github | Client tab switch; no mutation | PASS |
| tab-reports | Client tab switch; no mutation | PASS |
| tab-knowledge | Client tab switch; no mutation | PASS |
| tab-integrations | Client tab switch; no mutation | PASS |
| engineering_run_once | /projects/ai-dev-demo/qldapm-ai/commands | BLOCKED BY AUTHORIZATION |
| engineering_control | /projects/ai-dev-demo/qldapm-ai/commands | BLOCKED BY AUTHORIZATION |
| engineering_control | /projects/ai-dev-demo/qldapm-ai/commands | BLOCKED BY AUTHORIZATION |
| engineering_github_sync | /projects/ai-dev-demo/qldapm-ai/commands | BLOCKED BY AUTHORIZATION |
| engineering_report_generate | /projects/ai-dev-demo/qldapm-ai/commands | BLOCKED BY AUTHORIZATION |
| engineering_notifications_dismiss | /projects/ai-dev-demo/qldapm-ai/commands | BLOCKED BY AUTHORIZATION |
| sprint_risks | /projects/ai-dev-demo/qldapm-ai/commands | NOT TESTED |
| bug_triage | /projects/ai-dev-demo/qldapm-ai/commands | NOT TESTED |
| engineering_resume | /projects/ai-dev-demo/qldapm-ai/commands | BLOCKED BY AUTHORIZATION |
| engineering_github_sync | /projects/ai-dev-demo/qldapm-ai/commands | BLOCKED BY AUTHORIZATION |
| knowledge_file_ingest | /projects/ai-dev-demo/qldapm-ai/commands | BLOCKED BY AUTHORIZATION |
| knowledge_file_ingest | /projects/ai-dev-demo/qldapm-ai/commands | BLOCKED BY AUTHORIZATION |
| knowledge_search | /projects/ai-dev-demo/qldapm-ai/commands | PASS |
| knowledge_search | /projects/ai-dev-demo/qldapm-ai/commands | PASS |
| knowledge_file_search | /projects/ai-dev-demo/qldapm-ai/commands | PASS |
| knowledge_file_search | /projects/ai-dev-demo/qldapm-ai/commands | PASS |
| knowledge_file_search | /projects/ai-dev-demo/qldapm-ai/commands | PASS |
| delegated_control | /projects/ai-dev-demo/qldapm-ai/commands | BLOCKED BY AUTHORIZATION |
| delegated_preview | /projects/ai-dev-demo/qldapm-ai/commands | BLOCKED BY AUTHORIZATION |
| delegated_preview | /projects/ai-dev-demo/qldapm-ai/commands | BLOCKED BY AUTHORIZATION |
| close-modal | Client JS/source handler; endpoint chưa chứng minh riêng | NOT TESTED |
| engineering_plan | /projects/ai-dev-demo/qldapm-ai/commands | BLOCKED BY AUTHORIZATION |
| engineering_plan | /projects/ai-dev-demo/qldapm-ai/commands | BLOCKED BY AUTHORIZATION |
| Đóng | Client JS/source handler; endpoint chưa chứng minh riêng | NOT TESTED |
| × | Client JS/source handler; endpoint chưa chứng minh riêng | NOT TESTED |
| engineering_report_schedule_update | /projects/ai-dev-demo/qldapm-ai/commands | BLOCKED BY AUTHORIZATION |
| engineering_report_schedule_update | /projects/ai-dev-demo/qldapm-ai/commands | BLOCKED BY AUTHORIZATION |

RAG: search/answer choice → actual Rails POST → Gateway selected quotes → rendered blockquotes/citations → pinned file read. [Actual Gemini answer DOM/quotes](browser-uat.json); [visible file-only extract](main-file-extract-visible.png) và [visible pinned read](main-file-read-visible.png) được kiểm không dùng Gemini. Native citations cũng được render trong search. File citations là logical source+checksum; không giả public URL mở được trên điện thoại. Ingest vẫn giới hạn registry/pin, chưa reindex trong phase này.

Mission, Pipeline, Workforce, Backlog, Execution, GitHub, Reports, Knowledge và Integrations đã mở thật. Workforce roles BA/PM/Dev/Reviewer/QA, run inspector/receipts, Reports rendered/raw/export, Studio3nodes398/artifacts/PR15, search393-empty, Back/reload398 đã kiểm. Native business READY FOR RELEASE tách engineering COMPLETED, không coi run COMPLETE là Owner acceptance.

Responsive390px: [visible MAIN bar](main-mobile.json) width284/scroll284, [screenshot](main-rag-mobile-visible.png). Browser harness đầu đo clientWidth trên inline form=0, nên số0x0 trong browser-uat không phải proof mobile; đã dùng visible search-bar bounding box để kiểm lại. [Isolated red→green CSS](mobile-form-red.json) chỉ là fixture thật CSS/Chromium, tách MAIN evidence.

Search và pinned-file read gặp503/network error không khóa UNKNOWN_WRITE; chỉ write transport-unknown mới giữ replay lock. Pinned-file read không xóa search citations hoặc clear pending/unknown của write khác. [File read outage RED→GREEN](file-read-outage-green.log), abort/counter/clear/newquery/stale ordering và CSRF JSON POST/deny/unknown verified bằng actual inline JS VM; không giả là đã ép outage trên MAIN.15UIgroups chạy trước final scopedfile-read fix; file-onlyextract/read được kiểm riêng sau fix, không gọi inference lại để làm mới screenshots. Trong UI navigation burst có429 rồi200 (network trace), rate limit vẫn giữ nguyên. Không chạy p95 campaign.

Task create/edit/approve/run/resume/AUTO/GitHub sync, report generation/schedule, notification dismiss, ingest và delegated actions **BLOCKED BY AUTHORIZATION** hoặc source-only; không phát sinh demoTask mới. Project selector/change-role, mọi repeated historical run/report/link, logout/session-expiry/recovery toàn UI: **NOT TESTED mới**; contracts không thay authenticated UAT.
