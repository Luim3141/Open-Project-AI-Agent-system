# 07 — CODE EXAMPLES: CÁCH VIẾT TEST DỰA SOURCE THẬT

Đây là các mẫu an toàn. **Không copy vào product và kết luận PASS** nếu chưa điều chỉnh chính xác selectors/endpoints/fixtures theo Rails/gateway đang chạy. Tất cả mutations test phải dùng disposable stage có bằng chứng DB/volume độc lập.

## A. Thí dụ Python `unittest` cho idempotency/concurrency
Viết bằng testing seam của source hiện tại. Mẫu này là hợp đồng để agent biến thành executable test khi đã tìm class thật:
```python
import unittest

class NativeWriteSafetyContract(unittest.TestCase):
    def test_timeout_after_native_commit_does_not_duplicate(self):
        # Arrange: isolated staging fixture; one stable idempotency key;
        # inject network timeout AFTER native mutation may have committed.
        service = make_REAL_service_with_fault_injector()  # replace with actual fixture
        initial = native_query_fixture_count()            # actual readback
        first = service.submit(request_id="fixture-123")
        second = service.retry_or_reconcile(request_id="fixture-123")
        after = native_query_fixture_count()
        self.assertEqual(after, initial + 1)
        self.assertEqual(first.receipt_id, second.receipt_id)
```
**Không chạy đoạn có placeholder**. Tìm actual `store.py`, `service.py`, `native.py` và `ai_worker.py`, xây fake tại network boundary và one real staging readback. Làm 1 test xấu fail trước khi fix, rồi 2 test normal/stale.

## B. Browser role-test Playwright (khung bắt buộc phát triển)
```ts
import { test, expect } from '@playwright/test';

const baseURL = process.env.QLDAPM_TEST_BASE_URL;
if (!baseURL) throw new Error('Require QLDAPM_TEST_BASE_URL for safe stage test');

test('anonymous cannot read protected work packages over Quick Tunnel', async ({ page }) => {
  // Insert the REAL route found from Rails route list; do not guess.
  const protectedRoute = process.env.QLDAPM_TEST_PROTECTED_ROUTE;
  if (!protectedRoute) throw new Error('Set tested route, do not invent');
  const response = await page.goto(new URL(protectedRoute, baseURL).toString());
  expect(response).not.toBeNull();
  const status = response!.status();
  // Browser may be redirected to login (200 final); verify that protected
  // content IS NOT displayed, not just status 200/302.
  expect(await page.locator('[data-test="private-business-content"]').count()).toBe(0);
  expect([200, 302, 401, 403]).toContain(status);
});
```
Ví dụ locator `[data-test="private-business-content"]` phải thay bằng selector **có thật** hoặc assertion nội dung fixture không xuất hiện. Không chấp nhận một test xanh chỉ vì selector luôn không tồn tại. Nên kiểm tra cả negative control (logged-in PM thấy đúng fixture) và assertion route server deny theo network response.

## C. 20 users: phân biệt browser sessions và LLM calls
- Tạo/nhập **20 accounts fixture** trên staging theo policy, password dùng test vault riêng và không xuất log.
- Playwright tạo 20 browser contexts khác nhau (mỗi context một storage state được tạo sau login thật), đi qua 1–2 page read-only, xác nhận account ID/role khác nhau và không đọc được business data ngoài scope.
- Test permission matrix với 5 roles và nhiều người/role; tách login flows với credential rate limiting.
- Test load chỉ HTTP GET read-only trên LAN stage với k6; test 20 AI users bằng **mock/fake provider** để không tiêu Gemini daily quota.
- Test live Gemini smoke tối đa số lời gọi nhỏ thực sự cần, nếu billing/quota hợp lệ và được owner cho phép.

## D. k6 read-only LAN smoke (mẫu chạy được khi URL valid)
Save `qa-k6-readonly.js` trong audit harness:
```js
import http from 'k6/http';
import { check, sleep } from 'k6';
export const options = {
  stages: [
    { duration: '20s', target: 1 },
    { duration: '30s', target: 5 },
    { duration: '30s', target: 10 },
    { duration: '30s', target: 20 },
    { duration: '15s', target: 0 },
  ],
  thresholds: {
    http_req_failed: ['rate<0.02'],
    http_req_duration: ['p(95)<5000'],
  },
};
const base = __ENV.BASE_URL;
if (!base) throw Error('BASE_URL required (STAGING LAN ONLY)');
export default function () {
  const r = http.get(base + '/login', { tags: { scenario: 'read-only-login-smoke' } });
  check(r, { 'read-only page responds': x => [200, 302].includes(x.status) });
  sleep(1);
}
```
Run on PowerShell only AFTER verifying `/login` actual URL, network, auth and budget:
```powershell
$env:BASE_URL = 'http://<staging-lan-host>:<port>'
k6 run .\qa-k6-readonly.js
```
**Cảnh báo:** Đây mới kiểm thử tải endpoint đăng nhập, không chứng minh được 20 authenticated users hay tốc độ AI. Agent phải viết test có 20 session riêng và workload hợp pháp trước khi claim 20 users PASS. Nếu p95 threshold dự kiến không phù hợp máy thực, đo baseline rồi công khai chọn SLO có lý do, không nới lỏng để giả PASS.

## E. Quick Tunnel remote tests
- Từ **thiết bị ở mạng khác** (điện thoại 4G hoặc remote test device được owner cấp) test:
  - Trang login qua HTTPS thành công, anonymous không thấy task.
  - PM thấy đúng scope; BA/FE/BE/QA read/comment, mutation bị deny.
  - Logout hết hiệu lực session và CSRF trên write protected path.
  - `Host`/forwarded-proto/redirect hoạt động, không lộ internal host IP/credentials.
  - Tìm đúng current random URL sau restart trong runtime log, không tưởng hostname cố định.
- Không chạy authentication brute force, port scan, 20-VU performance test qua URL tunnel public.

## F. Fault injection/quota
- Mock `httpx`/SDK model transport bằng adapter/fake provider có clock ảo, trả 429, 503, connection reset, timeout, malformed tool payload.
- Assert queue bounded; waiting user-visible; requests not duplicated; deterministic endpoints still read native data.
- Fake RPD boundary at project-configured midnight timezone logic; verify DST/timezone assumptions instead of blindly hardcode PST offset.
- For 503, do not automatically claim “quota exhausted”; verify provider code/message from raw sanitized trace.

## G. Security static checks
```powershell
# No physical secret printing; scanner config may require exclusion/sanitization.
# Review Trivy license and exact version before installing:
trivy fs --scanners vuln,misconfig .\openproject\ai
# Scan image name/digest learned from running docker first:
trivy image <verified-image-tag-or-digest>
```
Trivy output findings require human triage and patched/upstream compatibility check. Không gắn Docker daemon socket vào container chỉ để lấy metadata khi có thể scan từ local CLI. Không chạy ZAP active attack; passive baseline staging chỉ sau khi xem target/config và phê duyệt loại scan.

## H. Regression for native mutation and role ceiling
Viết test tương ứng `PM`, `BA`, `FE`, `BE`, `QA` với 3 tầng Rails core, Gateway REST và MCP. Dùng entity IDs fixture **tạo riêng**, không hardcode staging project ID 3 cho main. Snapshot số WP và content before/after; submit denied mutation và verify no write; positive PM case verify native receipts, workflow/gates calendar normalization.
