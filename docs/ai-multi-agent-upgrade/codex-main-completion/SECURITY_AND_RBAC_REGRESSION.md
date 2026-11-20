# Security / RBAC regression —21/10/2026

**PASS theo phạm vi đã chạy**, không phải kiểm toán mọi đường tấn công.

Main Native/API+serviceHMAC có25checks PASS (`main-native-views-security-readback.json`): năm danh tính19..23 đọc đúngproject5/views/columnqueries; owner19 đọc run local;20..23 đọc run đó bị403; wrongproject3, admin18khôngmember, badsignature và replaynonce đều bị403. Không dùng Admin token thayPM, không tạo Mainbrowser session giả.

Clone actual browser/API:24checks choBA/BE/FE/QA,72Nativeviewschecks gồm4nonPMconfigwrite-denials và PMNative drag/revert. Nativegates42valid+42wrongroleedges và controller/view regressions PASS. Gateway19Windows+19Linux checks phân biệt deterministic fixtures với HTTP/native/browser.

Main trước/sau app rollout giữ fingerprint work_packages,relations,members,member_roles,roles,role_permissions,TOTP; credential/key files giữ nguyên ngoài enrollment3tokens được Owner duyệt riêng. Schedule chỉ ghiownedclone. Không đổi password/TOTP/key/model/billing, tắtCSRF/HMAC/RBAC hoặc mởpublicMain. Business Assistant Native catalog không chứaoperator/shelltools.

Các bài chưa chạy: bốnrole Mainbrowser, Mainbusinessmutation/approval/rejection (cấmtesttrực tiếp), fullLiveGemini chain,capacity20. Evidenceclone không thay MainUI acceptance.

Rủi ro source tồn tại: legacy `openproject/ai/tests/test_boards_playwright.py` có credential literal theo điều tra trước; không chạy/đọc/ghi lại giá trị. Cần remediate test fixture sang private/synthetic credentials trước khi dùng lại; không tự rotate credential đang phục vụ khi chưa duyệt.

Post-UAT Native re-login thayđổi `last_used_at` củadevice2/user19. Read-only comparison vớiDBrestore08:25 xácminh mọi fieldkhác, gồmsecret/active/default/owner,giữnguyên; khôngclaimfulltablehashTOTPunchanged sauOwnerlogin. Xemmain-totp-usage-readback.json.

SecondBrainclone16realUIchecksPASS,5NativeTOTPfixturelogins và4rolecross-indexdenials. Không phải bypassMainMFA; Main4nonPMbrowser vẫnNOT_RUN.
