# HỒ SƠ PHÁP Y M3: KIỂM TOÁN PHỤC HỒI PHIÊN & DẤU VẾT THỰC THI (SESSION RECOVERY AUDIT)
> Thời điểm kiểm toán: `2026-10-30 20:29:35 UTC`  
> Nguồn dữ liệu: SQLite databases tại `/home/openclaw/.openclaw/agents/*/agent/openclaw-agent.sqlite`

---

## 1. THỐNG KÊ LỊCH SỬ PHIÊN VÀ DẤU VẾT THỰC THI

Dữ liệu thực tế được trích xuất từ 3 cơ sở dữ liệu SQLite của từng Agent:

| Agent Name | Database File | Sessions Recorded (`session_nodes`) | Trajectory Events (`trajectory_runtime_events`) | Transcript Events (`transcript_events`) | Memory Chunks Indexed |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **`dev`** | `~/.openclaw/agents/dev/...` | **15 sessions** | **313 events** | **377 events** | **144 chunks** |
| **`reviewer`** | `~/.openclaw/agents/reviewer/...` | **5 sessions** | **37 events** | **33 events** | **79 chunks** |
| **`qa`** | `~/.openclaw/agents/qa/...` | **4 sessions** | **44 events** | **48 events** | **8 chunks** |
| **TỔNG CỘNG** | - | **24 sessions** | **394 events** | **458 events** | **231 chunks** |

---

## 2. CƠ CHẾ BẢO TOÀN DỮ LIỆU & PHỤC HỒI KHI SỰ CỐ (RECOVERY MECHANISM)

1. **Transaction Integrity (Tính toàn vẹn giao dịch):**
   - Mọi lượt tương tác (`turn`) của Agent đều được OpenClaw ghi nhận nguyên tử (Atomic write) vào bảng `session_nodes` và `transcript_events`.
   - Nếu tiến trình bị tắt đột ngột (crash/kill), trạng thái phiên gần nhất vẫn được bảo lưu trọn vẹn trong SQLite.
2. **Deterministic Context Rehydration:**
   - Khi QLDAPM Gateway tái kết nối tới OpenClaw qua session ID đã lưu, OpenClaw đọc lại các memory chunks và transcript events từ SQLite, khôi phục ngữ cảnh chính xác mà không phải gọi lại LLM.
3. **Session Invariant:**
   - Không có phiên nào bị thất lạc (0 uncommitted transcripts).
   - Dấu vết kiểm toán (audit trails) sẵn sàng để truy vết pháp y bất kỳ lúc nào.
