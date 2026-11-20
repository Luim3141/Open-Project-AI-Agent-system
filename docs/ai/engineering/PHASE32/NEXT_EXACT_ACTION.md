# HƯỚNG DẪN HÀNH ĐỘNG CHÍNH XÁC KẾ TIẾP (NEXT EXACT ACTION) — PHASE 3.2
## SỔ TAY HƯỚNG DẪN DÀNH CHO CHỦ DỰ ÁN & KỸ SƯ TIẾP QUẢN TRỰC TIẾP (HUMAN UAT WALKTHROUGH)

**Trạng thái hệ thống:** Đã sẵn sàng 100% cho trải nghiệm trực tiếp trên trình duyệt.  
**Địa chỉ truy cập chính thức:** [`http://127.0.0.1:18088/projects/ai-dev-demo/qldapm-ai?ui=modern`](http://127.0.0.1:18088/projects/ai-dev-demo/qldapm-ai?ui=modern)  
**Tài khoản đăng nhập:** `op-owner` (hoặc tài khoản Administrator có quyền trong Project 6).  

---

### BƯỚC 1: TRẢI NGHIỆM TÍNH NĂNG GIAO VIỆC MỚI CHO AI (+PM/BA)
1. Mở trình duyệt, truy cập đường dẫn Command Center ở trên.
2. Tại thanh công cụ Header (góc trên bên phải), bấm vào nút **`+ Giao việc mới cho AI`** (màu xanh dương đậm).
3. Hộp thoại **"Giao việc mới cho AI · Phân tích Yêu cầu & Lập Kế hoạch"** sẽ mở lên.
4. Nhập một yêu cầu tính năng thực tế bằng tiếng Việt, ví dụ:
   > *"Bổ sung tính năng phân loại công việc theo danh mục (category) và xuất danh sách ra file CSV. Cần kiểm tra quyền người dùng trước khi xuất và có unit test đi kèm."*
5. Nhấn **"Gửi tới PM/BA Agent"**.
6. Quan sát thông báo Toast xuất hiện xác nhận yêu cầu đã được tiếp nhận. Chuyển sang **Tab Backlog** để thấy Kế hoạch phân tích của PM & BA.

---

### BƯỚC 2: KIỂM TRA SƠ ĐỒ ĐIỀU PHỐI VÀ TELEMETRY (EXECUTION INSPECTOR)
1. Nhấp chuột vào **Tab 4 (Execution Center)** trên thanh điều hướng bên trái.
2. Tìm cột **Run ID** hoặc cột **Hành động**.
3. Bấm vào bất kỳ mã **Run ID** tương tác nào (ví dụ: `b1cca031...`).
4. Cửa sổ **"Chi tiết Thực thi & Giám sát Tác nhân"** sẽ mở lên:
   - **Tab Sơ đồ Tương tác DAG:** Xem sơ đồ luồng Tác nhân (Supervisor → Dev → Reviewer → QA).
   - **Tab Dòng sự kiện (Timeline):** Xem bảng ghi thời gian thực từng sự kiện và sequence.
   - **Tab Mã nguồn & Diff:** Xem mã nguồn diff đã sinh.
   - **Tab Bằng chứng QA & Test:** Xem kết quả kiểm thử Pytest.
   - **Tab Raw Telemetry:** Xem cấu trúc JSON kỹ thuật thô.
5. Nhấn phím `Escape` hoặc nút `×` để đóng cửa sổ.

---

### BƯỚC 3: ĐỐI SOÁT CHUỖI STACKED PRS TRÊN GITHUB
1. Nhấp chuột vào **Tab 5 (GitHub)**.
2. Quan sát bảng 5 Pull Requests đã được liên kết chính xác với các Work Packages tương ứng (#380 đến #384).
3. Kiểm tra các huy hiệu đích merge:
   - PR #1 mang huy hiệu **`MAIN`** (nhắm vào nhánh chính).
   - PR #2 đến #5 mang huy hiệu **`FEATURE_BRANCH`** (xếp tầng trên nhánh trước).
4. Bấm nút **"Đồng bộ GitHub ngay"** trên đầu bảng. Thông báo Toast sẽ xác nhận việc đối soát trực tiếp với GitHub REST API thành công trong tích tắc.

---

### BƯỚC 4: ĐỌC VÀ SAO CHÉP TOÀN VĂN BÁO CÁO TIẾN ĐỘ
1. Nhấp chuột vào **Tab 6 (Reports)**.
2. Tìm thẻ báo cáo bất kỳ và bấm nút **"Xem toàn văn"** (`.qcc-read-report-btn`).
3. Cửa sổ **"Đọc Báo cáo Toàn văn"** sẽ mở lên, trình bày đầy đủ nhận định của AI, các chỉ số hoàn thành, tỷ lệ pass test và khuyến nghị kỹ thuật.
4. Bấm nút **"Sao chép Markdown"** ở góc phải tiêu đề modal để copy toàn bộ nội dung vào bộ nhớ tạm.
5. Thử bấm nút **"Snapshot Tức Thời (+AI)"** tại Header để sinh thêm một bản báo cáo mới ngay tại thời điểm hiện tại.

---

### BƯỚC 5: KIỂM TRA TÍNH MINH BẠCH CỦA CHẾ ĐỘ AUTO VÀ RUN ONCE
1. Tại Header, bấm vào nút **`BẬT AUTO`**.
2. Hệ thống sẽ hiển thị Toast thông báo trung thực:
   > *"Tất cả 5/5 Backlog units hiện tại đã hoàn tất giao hàng. Chế độ AUTO tự động ngắt an toàn (OFF) để bảo vệ hệ thống. Nhấn 'Giao việc mới cho AI' để lập kế hoạch cho tính năng tiếp theo."*
3. Hành vi này chứng minh hệ thống vận hành có nguyên tắc, tự bảo vệ chống lãng phí tài nguyên và không chạy lặp vô tận khi công việc đã hoàn tất.
