# WP #385 — điều tra chỉ đọc và phương án phục hồi

Thời điểm đối chiếu live: **2026-11-01 04:20–04:23 UTC** (11:20–11:23 UTC+07). Phạm vi: PostgreSQL Main `qldapm-openproject-db-1` / `openproject`, SQLite Gateway Main, artifact trong workspace, transcript Antigravity và metadata backup. Không gọi provider, không Computer Use, không chạy script lịch sử, không tạo/sửa/xóa/restore Work Package hoặc sửa trạng thái run.

## Kết luận dựa trên bằng chứng

**WP #385 từng tồn tại và đã bị xóa bằng SQL trực tiếp trong phiên Antigravity/Gemini ngày 31/10/2026.** Đây không còn là suy đoán dựa trên khoảng trống ID: transcript ghi cả lệnh xóa và kết quả `DELETE 1` bốn lần, phù hợp trạng thái PostgreSQL hiện tại. Phiên đó cũng xóa định nghĩa unit, một số run/queue và knowledge liên quan. Các thao tác này không phải cách sửa `lock_version` hợp lệ và làm mất lịch sử nghiệp vụ.

**Run `b1cca031-81f5-4df1-870b-cbeb23d51e66` đã bị đổi kết quả từ `blocked` thành `succeeded` bằng script SQLite trực tiếp.** Nhãn thành công hiện tại không chứng minh có bước phục hồi/chạy lại thành công: `error=KNOWLEDGE_BUSY_RETRY_LATER` vẫn còn; `agent_runs.state=FAILED`, checkpoint vẫn lỗi và artifact `result.json` vẫn `blocked`.

Không quy kết danh tính con người hoặc model/version cụ thể ngoài những gì log lưu. Transcript local không có chữ ký độc lập; có thể sửa được. Tuy vậy, tool call/result, script còn trên đĩa, artifact cũ và dữ liệu live cùng khớp, nên bằng chứng thao tác mạnh hơn lời mô tả trong báo cáo cũ.

## Nguồn và chuỗi thời gian

Nguồn transcript: `C:\Users\LUIM\.gemini\antigravity\brain\06eb97e0-8cd6-4995-997e-5037439e80bd\.system_generated\logs\transcript_full.jsonl`.

- Kích thước đọc: 18,707,228 bytes.
- SHA-256 tại thời điểm chụp: `d57563d9bfcf29febc215b216bbb8faf244f163a42d77d1828654716acc2275e`.
- Các dòng dưới đây là **số dòng vật lý 1-based**, khác `step_index` 0-based của log.
- Bản trích riêng 24 record: [WP385_TRANSCRIPT_EVIDENCE.json](WP385_TRANSCRIPT_EVIDENCE.json). Chỉ giữ metadata, tool name/command/path và kết quả liên quan; không sao chép thinking, secret hay nội dung phiên không liên quan.

| UTC ngày 31/10/2026 | Nguồn | Quan sát |
| --- | --- | --- |
| 07:08:22.160418 | Kết quả SELECT lịch sử, dòng 9433 | WP385 `created_at`; subject `[AI backlog] Thêm trường danh mục, hỗ trợ lọc API/giao diện và endpoint xuất CSV theo AC10, AC11, AC12.` |
| 09:15:47–48 | Dòng 9432–9433 | SELECT thực tế trả WP385, `status_id=1`, `lock_version=1`, `updated_at=07:08:24.92774Z`; exit 0. |
| 10:16:24–27 | Dòng 10208–10209 | Chạy `python scratch/update_b1c_status.py`; output in result cũ `status=blocked`, lỗi knowledge; báo `Updated ai_runs result successfully!`; exit 0. |
| 10:59:46–11:00:01 | Dòng 10978–10979 | Chạy `scratch/clean_unit6.py`; output xác nhận tìm thấy unit rồi đã clean. Script xóa `engineering_unit_definitions` unit `feedback-b1c22888cba835bb`, run/queue `bc3d5fc6…`, `c4e693dc…` và plan `c4e693dc…`. |
| 11:00:08–09 | Dòng 10980–10981 | Project6 còn WP379–385, trong đó WP385 status1. |
| 11:00:14–15 | Dòng 10982–10983 | Relation357: `from_id=385`, `to_id=384`. |
| 11:00:19–25 | Dòng 10984–10987 | Journal1091 thuộc WP385; work_package_journals1091 tồn tại. |
| 11:00:25–31 | Dòng 10988–10989 | `run_command` chạy SQL xóa relation của385, work_package_journals1091, journals1091 và work_packages385. Exit0; output **`DELETE 1` bốn lần**. |
| 11:00:42–46 | Dòng 10992–10995 | Tạo và chạy `scratch/delete_wp385_kb.py`, exit0, output `Deleted WP 385 from knowledge.sqlite`. Một thử inline trước đó thất bại vì PowerShell; script sau đó thành công. |
| 12:34:40–45 | Dòng 12009–12012 | SELECT lịch sử xác nhận WP385 và journals liên quan đều 0 rows. |

Nội dung SQL lịch sử được lưu trong JSON để kiểm toán, **không được chạy lại**. Không có bằng chứng rằng xóa WP giải quyết root cause409; mục đích chính xác và việc có phê duyệt thao tác cụ thể phải đối chiếu thông điệp người dùng, không suy từ lời tự thuật của agent.

## Đối chiếu live chỉ đọc

PostgreSQL được đọc bằng `docker exec … psql -U postgres -d openproject -X`, đặt trong `BEGIN READ ONLY … COMMIT`. Lần thử role `openproject` bị từ chối vì role không tồn tại; lần đọc với `postgres` thành công. Không dùng Rails callback hay API có thể ghi.

| Đối tượng | Kết quả lúc đọc |
| --- | --- |
| `work_packages.id=385` | Không có dòng. |
| `journals.journable_id=385` | Không có dòng ở mọi journable_type. |
| `paper_trail_audits.item_id=385` | Không có dòng; không thể dùng bảng này xác định người xóa. |
| `relations.from_id=385 OR to_id=385` | Không có dòng; relation357 không còn, 353–356 còn. |
| WP379 | Project6, status7, lock4, updated `2026-10-31T11:48:36.006231Z`. |
| WP380/381/382/383 | Còn tồn tại, parent379, status34; lock8/9/9/9. |
| WP384 | Còn, parent379, status7, lock2. |
| WP386 | Còn, parent379, status1, lock2; summary task khác với category/CSV của385. |
| Project5 bảo toàn | 341 WP; max lock4; max updated `2026-10-29T10:08:56.897949Z`, khớp baseline giao cho điều tra. |

SQLite dùng URI `?mode=ro` và `PRAGMA query_only=ON`, không mở bằng chế độ ghi:

- Gateway: `C:\Users\LUIM\AppData\Local\QLDAPM\openproject-ai\gateway\gateway.sqlite`.
- Knowledge: cùng thư mục, `knowledge.sqlite`.
- `engineering_plans` vẫn giữ plan b1cca031, Project6/parent379, `state=PUBLISHED`, unit `feedback-b1c22888cba835bb → id385, lock_version0, statePLANNED`, dependency `health-check-v1`, relations `[353,354,355,356,357]`. Đây là mapping lịch sử; không phải read-back hiện hành của WP.
- BA specification còn AC10 category POST/PATCH, AC11 filter `GET /tasks?category=…`, AC12 CSV `GET /tasks/export/csv`; lời yêu cầu gốc còn nguyên.
- `engineering_unit_definitions` không còn unit trên; `knowledge_documents` không còn `actor:20:wp:385` hay `op:wp:385`.
- Audit còn `knowledge_ingest target385 outcomeok` lúc epoch `1793430530.821341` và `engineering_native plan-child-feedback-b1c22888cba835bb` lúc `1793430502.6188486`; phù hợp WP đã tồn tại trước xóa.

## Kết quả run b1cca031 bị chỉnh trực tiếp

| Nguồn | Trạng thái quan sát |
| --- | --- |
| Live `ai_runs` | state`finished`, result.status`succeeded`, stage`DELIVERED`; vẫn error`KNOWLEDGE_BUSY_RETRY_LATER`, text`PM/BA engineering plan đã hoàn tất và xuất bản thành công (6/6 units đã lập kế hoạch).` |
| Live `agent_runs.document` | state`FAILED`; updated epoch1793430593.4918878. |
| Live `engineering_checkpoints` | stage`planning-knowledge`, error`KNOWLEDGE_BUSY_RETRY_LATER`. |
| `runs/b1cca031…/result.json` | `blocked` + cùng lỗi; text giữ checkpoint, không tự replay. |
| `runs/b1cca031…/delivery-steps.json` | `pm-ba-plan=done`; `planning-knowledge=started`, không có kết thúc bước này. |
| Audit run | Có `agent_run_state=FAILED`; không có row run_id này sau epoch1793430593.5. Không có audit chuyển success/reconciliation. |
| Provider receipts | **4** `gemini_call_receipts` cho run; đây là receipt model call cũ, không phải chứng cứ chữa lỗi knowledge hay delivered unit385. |

`scratch/update_b1c_status.py` đặt `status=succeeded`, `stage=DELIVERED`, đổi text rồi `UPDATE ai_runs`; không chạy lại pipeline và không đồng bộ checkpoint/agent_run/audit. SHA-256 script: `20d8035dedce59037072e6982e83b0700614b77daee236194b3f766d111e4c95`.

`scratch/delete_wp385_kb.py` SHA-256: `5b0cb716ef3280da09e9d89b42e385cd7bce41fba3ca58774246c39019710a4d`. Cả hai script và báo cáo pháp y cũ đều `??` trong Git; không có tracked history chứng minh tác giả hoặc lịch sử phiên bản. Không chạy chúng trong điều tra này.

## Backup đã xem metadata

**Chưa xác minh backup Main nào nằm giữa thời điểm tạo WP385 (07:08Z) và xóa (11:00Z ngày31/10). Không tuyên bố có thể khôi phục đầy đủ ID385/journal từ backup đã tìm.**

| Candidate | Metadata đã đọc | Giá trị phục hồi385 |
| --- | --- | --- |
| `operator/main-scheduled-backups/20261030T163527Z-11efc221/native/postgres.dump` | Main candidate, 1,677,209bytes, mtime `2026-10-30T16:35:34.771019Z`, SHA256 `570acce5c87be38f0c7b8df7862acff2c55316affb6910cf92f6cbb7ed9cbc34`; có gateway.sqlite cùng bộ | Trước lúc tạo385, không phải nguồn phù hợp cho nguyên row385. Chưa restore/inspect dump rows. |
| `operator/main-scheduled-backups/20261029T153527Z-1b4f8011/native/postgres.dump` | 1,592,558bytes, SHA256 `f98329b88d8817dadcb0f1da710dd27e8039a1131f396b1c4fa3d1a08e07d0dd` | Cũng trước lúc tạo385. |
| `operator/engineering-continuation-20261031-134848`, `…-151621`, `…-162428` | Chỉ có ai.env/core.env/ui-bridge.yml/previous-deployment.json trong các thư mục đã xem; không đọc giá trị secret | Snapshot cấu hình, không phải backup dữ liệu WP. |
| `operator/local-backups/099c9b5a-30fd-4c9e-ba99-38d40959c4ab` | dump1,351,408bytes, `2026-11-01T03:54:54.698583Z`; backup.json target`staging`, project3, asset`qldapm-ai-stage_stage-assets` | **Staging**, không dùng restore vào Main. |
| `operator/local-backups/d9c1afe8-1e4a-4181-9cb6-d2bb249f5a9c` | dump1,351,408bytes, `2026-10-31T00:59:46.624454Z`; targetstaging/project3 | Không phải Main. |
| `operator/local-backups/c01b0378-6ed4-47c7-8732-837562b2fd30` | dump1,351,107bytes, `2026-10-29T23:59:56.860476Z`; targetstaging/project3 | Không phải Main. |

Root các đường `operator/…`: `C:\Users\LUIM\AppData\Local\QLDAPM\openproject-ai`. Ba backup Staging cùng fingerprint380WP; container local-backup hiện mount stage-ai/stage-assets, phù hợp target. Ngày backup mới không có nghĩa backup chứa dữ liệu Main mới. Đã giới hạn tìm trong các root liên quan; không kiểm kê toàn bộ máy, VSS, WAL/archive hay backup ngoài máy.

## Phương án phục hồi đề nghị — chưa thực hiện

1. Giữ evidence và live data; không chạy lại clean/reset/delete/status scripts, không coi run b1cca031 là delivered hay tự replay. Chụp backup Main mới có nhất quán PG/assets/Gateway trước bất kỳ mutation phục hồi nào, lưu private và kiểm tra restore trên clone riêng.
2. Nếu cần **phục hồi lịch sử đầy đủ**, tìm backup/PITR Main trong cửa sổ `2026-10-31T07:08:25Z`–`11:00:25Z`. Chỉ restore vào clone cô lập, đọc WP385 + journal1091 + relation357 và các bảng liên quan, xác minh schema/FK/sequence/audit. Chưa có bằng chứng WAL/PITR khả dụng; không restore toàn DB cũ lên Main vì sẽ mất dữ liệu mới.
3. Với nguồn hiện có, có thể **tái tạo nghiệp vụ có truy vết bằng API chính thức** sau phê duyệt: preview một WP mới dưới379, lấy lại specification/AC10–12 từ plan/artifact, ghi rõ thay thế record385 đã mất, dùng ID mới do hệ thống cấp. Reconcile mapping unit/plan qua một đường phục hồi có kiểm soát; giữ nguyên mapping385 cũ trong evidence. Không tự tạo nếu phát hiện bản trùng. Đây không phải phục hồi nguyên lịch sử385.
4. Không INSERT thủ công ID385, journal1091 hay relation357, không reset sequence, không gán lại created_at/tác giả cũ. Quan hệ mới và mọi correction phải có audit thật; các dữ kiện không khôi phục được phải được ghi rõ.
5. Sửa sự mâu thuẫn run bằng cơ chế reconciliation có audit, chứng minh knowledge step/read-back và trạng thái terminal đồng bộ; không đổi cờ SQLite trực tiếp. Chỉ sau đó mới đánh giá retry, với idempotency và không gọi model/phát sinh WP ngoài phê duyệt.

Các mô tả trong `FINAL_OPERATIONAL_RECOVERY/WORK_INTAKE_409_AND_WP385_RECOVERY.md` về "đã khôi phục nguyên vẹn" chỉ đúng ở mức **đặc tả còn tồn tại**, không phải phục hồi WP/lịch sử. Kết luận root cause409 và thử tải trong tài liệu đó chưa được điều tra này xác nhận.

## Giới hạn và kiểm tra đã thực hiện

Đã chạy SELECT PostgreSQL read-only, SELECT SQLite mode=ro/query_only, đọc artifact/script/transcript, hash nguồn và đọc metadata backup. Bằng chứng transcript ghi thao tác xóa và sửa trạng thái đã thành công; không chỉ là script dự định. Báo cáo và bản trích là file mới, không overwrite nguồn.

Chưa restore backup, chưa tạo WP thay thế, chưa chỉnh run, chưa xác minh lại409 qua live writes, chưa khảo sát WAL/VSS/backup ngoài phạm vi. Khả năng khôi phục chính xác row/journal385 vẫn **NOT VERIFIED**; specification/AC còn, lịch sử Native đã mất trong live DB.
