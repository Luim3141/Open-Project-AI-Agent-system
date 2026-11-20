<!-- CC_STABILIZATION_CURRENT_20261104 -->
# Control Center/Reports MAIN — functional repairs verified, performance open

Cập nhật 2026-11-04T16:22:32.919239+00:00 UTC (Asia/Bangkok,04/11/2026). **FUNCTIONAL_REPAIRS_VERIFIED — PERFORMANCE_GATE_OPEN**; chưa chứng nhận `AI_CONTROL_CENTER_DEMO_READY` hoặc FULL FUNCTIONAL PASS. Các block bên dưới là lịch sử.

MAIN: Gateway `sha256:698224aa0ddc88808ebab30b4705dfe7050b09db67b8ae3fc4a569d6a8447e1c`; Core `sha256:1a8f2528da78860faa69610568985471e26136d441a594f4f098c045ca181189`; n8n `sha256:05376355cd63186ba9b61c1e2a0f659105253cc1d37b36391a1771951c008269`. Images/source/pins được read-back; Gateway/Core healthy, n8n readiness200. Final PAUSED, queue0, workerALIVE, delegationOFF;21coding runs/531provider receipts giữ nguyên. Project5 scoped rows và global config/security tables bảo toàn; chỉ cho phép timestamp đăng nhập User thay đổi.

Native386/387/389/390/391/394 đã READY FOR RELEASE/v10 qua workflow thật và journal của principal25; không tự DONE.391/b7fd và394 vẫn SUCCEEDED, không replay. PR11MERGED/main, PR12OPEN; Demo artifact giữ nguyên. RAG algorithms đóng băng/FAILED; provider readiness riêng, không coi workerALIVE là inferenceREADY.

Report Reader đã sửa trên MAIN: CSP nonce, Turbo cache restore, timeout15s, không ghi đè response cũ; Daily6766ký tự/6sections/Raw Markdown, audit có facts/provenance thay vì trang trống. GitHub Sync hiển thị ACK→operation→COMPLETED — NO CHANGES/12checked/0changed mà không F5. Artifact caption ghi rõ metadata lịch sử; trạng thái merge hiện hành lấy từ bảng PR.

Gateway HTTP5samples: trước p50=9.8377s/samplep95(max)=18.9763s; sau p50=7.2148s/samplep95(max)=12.8446s. Mục tiêu initial usable<4s chưa đạt; warm UI paint<200ms chưa có phép đo riêng. Core observed GitHub Sync ACK1913.38ms là một mẫu, không phải p95. Gateway hiện1CPU/384MiB, có sample saturation~100% khi đo. Không tăng quota hay đổi nơi lưu DB để che giới hạn. Cần tiếp tục tối ưu/read-path load qualification trước chứng nhận Demo Ready.

Bằng chứng: [runtime](cc-stabilization/final-live-verification.json), [166 image regressions](cc-stabilization/image-regression-reports.json), [exact clone qualification](cc-stabilization/clone-qualification-caption.json), [browser](cc-stabilization/browser-uat.json), [Project5](cc-stabilization/native-integrity-after.json). Không đổi GitHub source/merge, Demo, RAG algorithms hoặc DR.

Chi tiết18câu trả lời: [FINAL_INTEGRATION_ACCEPTANCE.md](FINAL_INTEGRATION_ACCEPTANCE.md); checklist: [OWNER_MANUAL_UAT_GUIDE.md](OWNER_MANUAL_UAT_GUIDE.md).
<!-- END_CC_STABILIZATION_CURRENT_20261104 -->

# Reports, telemetry và UI contracts

Gateway `engineering_report_generate` tạo ON_DEMAND report `98237e37-b61b-403d-b8da-f2fe86179c6b`, `include_narrative=false`; `engineering_report_get` đọc lại HTTP 200, Project 6, actor 20. Snapshot có worker ALIVE, mode OFF, GitHub 7 PR/4 open; PR merged count bao gồm cả feature branch, cần đọc `merge_target` thay vì suy ra cả ba vào main. Evidence `post30218-20261101T1540Z/report-generate.json` và `report-readback.json`.

Lifecycle run #387 có 17 ACK và observation ở Gateway. `RUN_COMPLETED` và execution n8n là telemetry, không thay thế verdict review/QA và evidence PR. Static source UI có formatter `Asia/Ho_Chi_Minh` định dạng `dd/MM/yyyy HH:mm:ss`; report API/title thực tế vẫn dùng `yyyy-MM-dd HH:mm:ss`, cần phân biệt API và UI. Test report reader bằng Node VM PASS (text/object, empty/error và stale response); bốn test knowledge UI answer PASS. Chưa thực hiện bộ contract test UI toàn diện trong đợt này, chưa có Owner manual UAT. Không dùng Computer Use.

Stabilization: `include_narrative=true` trước đây bỏ qua AI im lặng do method không tồn tại. Gateway đã sửa qua `Gemini.structured` với chỉ aggregate metrics, một model call, 2 HTTP attempts và 1800 output tokens; trả `GENERATED` hoặc `UNAVAILABLE` rõ ràng, không lưu raw exception, và gắn nhãn AI chưa xác minh. Report thật `156c3aa7-e5ad-4390-b213-c6efd697301a` GENERATED, receipt LIVE_SUCCESS, detail read-back HTTP 200. Lần đầu dùng 512 tokens bị MAX_TOKENS và được giữ làm evidence. `stabilization-workflows/report-narrative-budget.json` và `report-narrative-readback.json` ghi kết quả. Năm test Ruby state contract và 10 report tests PASS; Owner UAT vẫn pending.
