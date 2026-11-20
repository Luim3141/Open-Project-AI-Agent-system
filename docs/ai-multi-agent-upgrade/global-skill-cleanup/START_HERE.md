# Global Antigravity Cleanup — Hướng dẫn

1. Giải nén ZIP của ChatGPT vào `D:\AI project\QLDAPM chat\docs\ai-multi-agent-upgrade\global-skill-cleanup\`.
2. Đọc `REVIEW_REPORT_VI.md`; chỉ 77 global giữ lại, 1386 mục là **ứng viên xóa sau khi đối chiếu file thật**.
3. Mở Antigravity tại workspace QLDAPM, đọc/dán `PROMPT_FOR_GEMINI_DELETE_GLOBAL_SKILLS.md`.
4. Cho phép backup ra ổ D, xem dry-run, Gemini xóa vĩnh viễn những mục đã chứng thực trong whitelist; mọi mismatch phải skip.
5. Kiểm tra `results/<timestamp>/FINAL_CLEANUP_REPORT.md` rồi gửi ChatGPT kiểm tra.

**Không giải nén ZIP này vào `~/.gemini/config/skills/`**. Đây là bộ manifest, không phải các skill mới.
