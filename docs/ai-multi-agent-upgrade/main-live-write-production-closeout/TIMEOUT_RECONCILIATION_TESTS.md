# Timeout, reconciliation and lifecycle tests

| Case | Expected / actual | Phương pháp | Kết quả |
|---|---|---|---|
| CREATE5/30/55/75s | Một POST; response còn trong90s được nhận | Native.call + Mock HTTP stream, virtual clock; không phải thời gian Native thật | PASS |
| CREATE95s | Deadline UNKNOWN, không POST lần2 | Virtual clock / NativeError | PASS |
| Commit rồi mất HTTP | Marker/author/fields duy nhất được đối soát, không CREATE lại | Unit và actual isolated Native clone fixture369 | PASS |
| Worker bị kill trước progress | Dùng stored command receipt, không replay worker | Unit; process timeout thật cũng kiểm tra child không viết muộn | PASS |
| Native từ chối commit422 | NOT_APPLIED/FAILED; submit lại cùng key vẫn lỗi, POST count1 | Synthetic Native contract | PASS |
| Hai marker / không marker / sai marker | UNKNOWN, tối đa3READ, không success giả | Unit | PASS |
| Sai project/type/author/parent/assignee/subject/description | Không reconcile | Unit exact-match tests | PASS |
| Thu hồi quyền / đổi dữ liệu sau receipt | Không công bố verified success; Native fresh ACL và read-version gate | Unit + scoped API/browser role isolation | PASS |
| Nhiều tools | Chỉ sửa đúng tool theo command key/index; tool unknown khác giữ nguyên | Unit | PASS |
| Bản ghi/audit race | Reconciliation receipt/audit chỉ một commit, không duplicate | Store transaction unit | PASS |
| Model bị dừng | Native confirmed riêng, raw worker/error giữ; summary SYSTEM có nhãn | Actual clone worker/projection/browser + Main #367 | PASS |
| Native read→model | Không model tools/write; Native read trướcSDK, hard1generation/2HTTP | Actual candidate worker+Native clone, SDK MockTransport | PASS offline |
| Citation/facts | Chặn ID lạ/thiếu, #ID ngoài nguồn, parent/assignee sai; canonical claims do host tạo | Unit + structured contract | PASS offline |

Windows118 tests exit0; Linux candidate114 tests exit0; Chromium21 assertions exit0. Chi tiết từng TestCaseID/expected/actual/evidence/source version: TEST_RESULTS.csv. Linux không chạy4 test phụ thuộc host broker/development fixture; cả4 PASS trên Windows. Không thêm prototype vào serving image để ép import tests.

## Native clone thực

clone-native-proof.json ghi332→332 Work Packages, fixture369 đã tồn tại, source marker/author/current actor được chứng minh bằng Native GET. Local receipt được mô phỏng lost-response, dispatcher tự đối soát, worker gốc failed_or_unknown và effective state reconciled_success. Tất cả probe methods là GET; zero Google, zero Native mutation. Đây không phải một CREATE mới trên Main hoặc bằng chứng Gemini Live WRITE trên image mới.

clone-browser.json:5 synthetic roles login/TOTP; read result, system Native result, graph4process nodes, final output, history filter, mobile390×844/no document overflow, desktop1366×900, no JS errors, cross-actor JSON403. SDK mock được ghi MOCK_SUCCESS/model_used=false. clone-images.json khớp exact candidate. Screenshots clone-*.png chỉ chứng minh clone.

Main process/lifecycle: original write6276720c… giữ raw failed_or_unknown, effective RECONCILED_SUCCESS và SYSTEM_GENERATED; hai read Live lỗi giữ FAILED/UNAVAILABLE, không có model success giả. Historical legacy OFFLINE text được bảo toàn trong lỗi cũ; receipts HTTP200 cho thấy đó không phải bằng chứng network outage. Source mới phân loại content validation thành INVALID_OUTPUT.

Không chạy Native WRITE mới trên Main, capacity20 người, fault injection, Docker Desktop restart hoặc fresh full restore rehearsal. PostgreSQL dump TOC và online SQLite backup integrity_check đã kiểm tra; không restore lên Main.
