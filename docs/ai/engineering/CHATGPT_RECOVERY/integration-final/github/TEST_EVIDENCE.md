# GitHub projection — candidate evidence, 03/11/2026

**Gateway/Core đã deploy và tự động đồng bộ được kiểm tra trên MAIN.** Bundle `candidate-20261103g/manifest.json` lưu source và ảnh; Gateway `e9af9565...`, Core `b5f3913a...`. GitHub polling actor18/300s đã bật. Poll đầu SUCCESS 11 PR/10 thay đổi Project6; poll tự nhiên thứ hai SUCCESS 11 PR/0 thay đổi. Sau cả hai, 10 Native journal markers mỗi marker đúng một lần; release projection `DEPLOYED_TO_DEMO` đúng SHA `01d765c...`. Xem `main-github-readback-20261103T124816Z.json` và `main-github-readback-20261103T125148Z.json`.

- GitHub API thật, read-only: 11/11 PR lấy được review/check details, 0 lỗi trong 8,464 giây; `github-readonly-projection-rotated.json`. Không lưu token hoặc review bodies. `NO_REVIEWS` và `NOT_CONFIGURED` không phải review/CI PASS.
- 45 unit/integration tests cho GitHub projection, sync, journal, recovery và poller PASS. Gồm test giới hạn đồng thời ba PR, luân phiên batch đầu mỗi năm phút, giữ thứ tự, không nhận review/check sai head, và neutral/skipped/unknown không báo SUCCESS.
- Qualification chạy lại 74 tests PASS, bao gồm 9 test helper: rollback Core failure, config, thứ tự stop → SQLite backup và reject Core reuse khi source/base/image/proof sai. SQLite backup bằng API mode=ro từ ephemeral container; hai DB thật đã được integrity_check read-only. Main không được ghi từ test này.
- Actual GitHub PR6 → Native Project6 clone WP386 marker/journal → outbox → n8n WF04 execution11 / receipt ACKED đã PASS; sync lặp UNCHANGED. `poll.tick` thật kiểm tra 11 PR, ghi 5 activity trên clone và lần kế NOT_DUE. Evidence trong `../n8n/business-clone-result.json`; không có Native writes trên MAIN.
- Core image `b5f3913a` clone PASS Rails session/CSRF/render và GitHub release fragment với synthetic Gateway boundary; `core-candidate-clone-result.json`. Đây là chứng cứ Core image cụ thể, không xác nhận các thay đổi Gateway sau đó.
- Combined clone `../n8n/business-clone-result.json` PASS 4/4, gồm Project5/Project6 local file, producer/index events và GitHub; service hash `32b94f54...`, WF01 adapter hash `e3c3bf9b...`.

Qualification `qualification.json` có trạng thái PASS cho candidate Gateway/Core GitHub/event/UI, SHA256 `3b83dae13a95f0ea12e8b683e4d25a07b9e631e867e20bfec8796a9290ac8f8b`. Deployment chứng minh riêng bằng `candidate-20261103g/deployment.json` và `../integration-activation.json`; semantic RAG chưa đạt gate.

Chi tiết polling: ba requests PR tối đa đồng thời, mỗi request dùng timeout không vượt phần thời gian 20 giây còn lại. Socket/DNS hệ điều hành bị kẹt ngoài timeout chưa được chứng minh có hard kill. Không có database restore tự động khi rollback image/config.
