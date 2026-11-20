# Triage labels

Năm nhãn mặc định của Matt Pocock được lưu trong custom field single-select `Triage`, tách biệt hoàn toàn với workflow/status nghiệp vụ.

| Canonical role | Giá trị Triage | Ý nghĩa |
|---|---|---|
| needs-triage | needs-triage | Cần phân loại/đánh giá |
| needs-info | needs-info | Cần thêm thông tin |
| ready-for-agent | ready-for-agent | Đặc tả đủ để agent xử lý |
| ready-for-human | ready-for-human | Cần người thực hiện |
| wontfix | wontfix | Không xử lý, lưu lý do |

Resolve custom field ID/options qua schema API thực trước khi ghi. `wontfix` không tự CANCELLED, các nhãn ready không tự phê duyệt, triển khai hoặc chuyển status. Không áp nhãn này sang Jira trừ khi được yêu cầu riêng.
