# DEFECT REGISTER — INDEPENDENT QA & REPAIR

**Audit Run:** `run_20261017_1616`  
**Date:** 2026-10-17  
**Auditor:** Independent Principal QA & Security Reviewer (Antigravity)  
**Total Defects:** 5  
**Fixed:** 1  
**Open:** 4  

---

### [DEF-01] Quick Tunnel Ephemeral Session Disconnect (Unauthorized: Tunnel not found)
- **Status:** **FIXED**
- **Severity:** P0 (Operational Availability / Remote Access)
- **Component:** `qldapm-ai-stage-quick-tunnel-1` (`cloudflare/cloudflared:2026.10.0`), `openproject/ai/local_runtime.py`
- **Observed Behavior:** Container was `Up 7 hours (unhealthy)`. Logs: `ERR Register tunnel error from server side error="Unauthorized: Tunnel not found"`.
- **Root Cause:** Ephemeral trycloudflare tunnels expire on Cloudflare edge after several hours. Cloudflared attempted to reconnect to the dead tunnel ID endlessly without re-registering.
- **Remediation Applied:** 
  1. Patched `local_runtime.py` (`start()` function) to detect if `quick-tunnel` is in `unhealthy` state and issue a container restart rather than an ineffective `docker start`.
  2. Executed restart of `qldapm-ai-stage-quick-tunnel-1`.
- **Verification Evidence:**
  - Container status transitioned to `Up (healthy)`.
  - Tunnel acquired new Cloudflare edge connection (`hkg09 QUIC`).
  - `quick_tunnel_web.rb` dynamically detected new hostname `standards-hourly-taxi-table.trycloudflare.com` and updated `access/current-url.json`.

---

### [DEF-02] 20 LAN Users Not Provisioned in Staging Database
- **Status:** **OPEN**
- **Severity:** P1 (Scope & Capacity Requirement)
- **Component:** `qldapm-ai-stage-db-1` (Postgres table `users`), `stage-ai/config.json`, `stage-ai/credentials.json`
- **Observed Behavior:** Database query `SELECT id, login FROM users` confirmed only 5 project member users exist (`ba-pm`, `pm`, `be`, `fe`, `qa`). Runtime credentials only contain tokens for those 5 users.
- **Root Cause:** The earlier session only implemented 20-user concurrency tests in-memory using `MockNativeLoad`, without executing user creation and project membership enrollment in OpenProject PostgreSQL database.
- **Impact:** While Python Fair Queue logic supports 20 users, only 5 actual user accounts can log into OpenProject.
- **Action Required:** Execute Rails runner script to create 15 additional user accounts and memberships in project 3 (`qldapm-local`) and generate API tokens.

---

### [DEF-03] Synthetic Model Identifier in Configuration (`gemini-3.5-flash-lite`)
- **Status:** **OPEN (DOCUMENTED)**
- **Severity:** P1 (Configuration & Provider Standards)
- **Component:** `stage-ai/gemini.json`, `stage-ai/gemini-readiness.json`
- **Observed Behavior:** Configuration specifies `"model": "gemini-3.5-flash-lite"`. Official public Gemini catalog lists `gemini-1.5-flash` and `gemini-2.0-flash`.
- **Runtime Observation:** Live regression execution demonstrated that Google's v1beta API endpoint actually returned `HTTP/1.1 200 OK` for this model string during tests, but public documentation does not guarantee long-term availability for this identifier.
- **Action Required:** Update canonical model identifier in configuration to `gemini-1.5-flash` once owner verifies project eligibility in AI Studio.

---

### [DEF-04] RAM Footprint Understated (Actual Coexistence: ~4.23 GiB)
- **Status:** **OPEN (DOCUMENTED)**
- **Severity:** P2 (Capacity Planning)
- **Component:** `RELEASE_NOTES_LOCAL_V2.md`, `PROJECT_STATE.md`
- **Observed Behavior:** Documentation claimed total system RAM footprint is 2.4–2.8 GB. Measurement via `docker stats --no-stream` showed:
  - Staging cluster (`qldapm-ai-stage-*`): 1.67 GiB
  - Main cluster (`qldapm-openproject-*`): 2.34 GiB
  - Retrieval service: 0.22 GiB
  - Total Docker RAM footprint: **4.23 GiB**.
- **Root Cause:** Documentation measured only a single stack in isolation, ignoring that migration requires both stacks to run simultaneously.
- **Action Required:** Update operational documentation to specify a minimum of 6–8 GB host RAM when both clusters run concurrently, or shut down main cluster if only staging is in use.

---

### [DEF-05] Acceptance Tests Rely on Tautological Mocks
- **Status:** **OPEN**
- **Severity:** P1 (Test Rigor & Quality Gate)
- **Component:** `openproject/ai/tests/test_p10_docker_and_lan_acceptance.py`
- **Observed Behavior:** 
  - Docker 3-cycle restart test verifies file existence in a temporary directory instead of calling Docker engine APIs.
  - 20-user RBAC test asserts `can_write = (role == "PM")` inside the test body instead of passing through Gateway enforcement.
- **Root Cause:** Shortcuts taken to achieve fast test execution (31.2s).
- **Action Required:** Develop true integration tests with live HTTP requests to `staging-gateway` (port 18092) and `staging-web` (port 18091).
