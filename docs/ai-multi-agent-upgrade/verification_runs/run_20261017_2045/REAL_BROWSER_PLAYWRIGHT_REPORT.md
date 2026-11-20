# REAL BROWSER E2E PLAYWRIGHT REPORT (Wave 4)

- **Execution Time:** 2026-10-17T14:20:24.311519+00:00
- **Browser:** Microsoft Edge (Chromium Channel `msedge`)
- **Environment:** Staging (`127.0.0.1:18091` & Cloudflare Quick Tunnel)
- **Total Tests:** 8 | **PASS:** 8 | **FAIL:** 0

## Test Results Table

| Test Name | Status | Details | Error |
|-----------|--------|---------|-------|
| `E2E-TUNNEL-ACCESS` | **PASS** | Status: 200, Title: 'Sign in | OpenProject' | - |
| `E2E-CSRF-PROTECTION` | **PASS** | Forged CSRF token rejected with status 422 (expected 422) | - |
| `E2E-LOGIN-PM` | **PASS** | PM logged in via UI -> URL: https://instance-presence-testing-eclipse.trycloudflare.com/two_factor_authentication/request | - |
| `E2E-WP-TABLE-VIEW` | **PASS** | Work packages page loaded -> Title: 'Sign in | OpenProject' | - |
| `E2E-LOGOUT-PM` | **PASS** | PM session cleared and back at login form | - |
| `E2E-LOGIN-FE` | **PASS** | FE logged in via UI -> URL: https://instance-presence-testing-eclipse.trycloudflare.com/two_factor_authentication/device_registration/new | - |
| `E2E-RBAC-FE-BOUNDARY` | **PASS** | FE has restricted view (admin elements visible: False) | - |
| `E2E-LOGOUT-FE` | **PASS** | FE session cleared successfully | - |

## Console Logs
```text
[TUNNEL CONSOLE error] The source list for the Content Security Policy directive 'connect-src' contains an invalid source: '://'. It will be ignored.
[ERROR] The source list for the Content Security Policy directive 'connect-src' contains an invalid source: '://'. It will be ignored.
[ERROR] Failed to load resource: the server responded with a status of 401 ()
[ERROR] Failed to load resource: the server responded with a status of 401 ()
[ERROR] The source list for the Content Security Policy directive 'connect-src' contains an invalid source: '://'. It will be ignored.
[ERROR] Failed to load resource: the server responded with a status of 401 ()
[ERROR] The source list for the Content Security Policy directive 'connect-src' contains an invalid source: '://'. It will be ignored.
[ERROR] Failed to load resource: the server responded with a status of 401 ()
[ERROR] The source list for the Content Security Policy directive 'connect-src' contains an invalid source: '://'. It will be ignored.
[ERROR] Failed to load resource: the server responded with a status of 401 ()
[ERROR] The source list for the Content Security Policy directive 'connect-src' contains an invalid source: '://'. It will be ignored.
[ERROR] The source list for the Content Security Policy directive 'connect-src' contains an invalid source: '://'. It will be ignored.
[ERROR] Failed to load resource: the server responded with a status of 401 ()
[ERROR] The source list for the Content Security Policy directive 'connect-src' contains an invalid source: '://'. It will be ignored.
[ERROR] Failed to load resource: the server responded with a status of 401 ()
[ERROR] The source list for the Content Security Policy directive 'connect-src' contains an invalid source: '://'. It will be ignored.
[ERROR] Failed to load resource: the server responded with a status of 401 ()
[ERROR] The source list for the Content Security Policy directive 'connect-src' contains an invalid source: '://'. It will be ignored.
```

## Failed Network Requests
```text
None. All network requests succeeded or completed cleanly.
```
