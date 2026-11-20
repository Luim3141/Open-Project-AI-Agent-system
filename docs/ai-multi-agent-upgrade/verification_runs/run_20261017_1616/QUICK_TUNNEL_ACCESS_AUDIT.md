# QUICK TUNNEL ACCESS & SECURITY AUDIT — WAVE 0

**Target:** `qldapm-ai-stage-quick-tunnel-1`  
**Configuration File:** `openproject/ai/quick.stage.yml`  
**Orchestration Script:** `openproject/ai/automation/quick_tunnel_web.rb`  
**Network Vantage:** Docker Engine on Windows WSL2  
**Owner Mandate (`CR-KEEP-QUICK-TUNNEL`):** Cloudflare Quick Tunnel is an **APPROVED, REQUIRED** feature for remote access. Do NOT remove or disable it.

---

### 1. Architectural & Network Isolation (QTT-01, QTT-06)
- **Target URL:** `http://staging-web:8080` (OpenProject Web on staging cluster).
- **Network Attachment:** The container is attached **ONLY** to network `qldapm-ai-stage_stage-front` (`172.29.0.0/16`).
- **Other Containers on `stage-front`:** Only `qldapm-ai-stage-staging-web-1` (`172.29.0.3`).
- **Internal / Sensitive Services Verification:**
  - `qldapm-ai-stage-db-1` (Postgres 5432): Attached only to `qldapm-ai-stage_stage` (internal). **NOT REACHABLE** via Quick Tunnel.
  - `qldapm-ai-stage-staging-gateway-1` (Gateway internal API): Attached only to `qldapm-ai-stage_stage`. Bound to `127.0.0.1:18092`. **NOT REACHABLE** via Quick Tunnel.
  - `qldapm-ai-stage-n8n-editor-1` (n8n Web UI 5678): Attached to `qldapm-ai-stage_editor`. Bound to `127.0.0.1:18090` and `127.0.0.1:5678`. **NOT REACHABLE** via Quick Tunnel.
  - **Verdict:** Network-level origin isolation is **CONFIRMED PASS**. No administrative, database, or workflow editor ports are exposed to the public internet.

---

### 2. Public Exposure & Hostname Mapping
- **Assigned Hostname (scrubbed):** `https://[redacted].trycloudflare.com` (recorded in `access/current-url.json`).
- **OpenProject Integration:** `quick_tunnel_web.rb` queries `http://quick-tunnel:2000/quicktunnel` for the ephemeral hostname, sets `OPENPROJECT_HOST__NAME` and `OPENPROJECT_HTTPS=true`, and dynamically reconfigures OpenProject allowed hosts.
- **Access Portal:** Published locally to `${AI_RUNTIME}/access/index.html` and `current-url.json`. Not committed to Git.

---

### 3. Operational Health Check & Defect Finding (DEF-01)
- **Live Status:** `Up 7 hours (unhealthy)`.
- **Cloudflared Error Log:**
  ```text
  ERR Register tunnel error from server side error="Unauthorized: Tunnel not found" connIndex=0 event=0 ip=198.41.200.33
  INF Retrying connection in up to 32s connIndex=0 event=0 ip=198.41.200.33
  ```
- **Analysis:** Cloudflare quick tunnels expire after several hours of idle or network disconnect. When cloudflared attempts to reconnect to the previously issued tunnel ID, Cloudflare edge responds with 401 Unauthorized ("Tunnel not found"). The container loops indefinitely without acquiring a new tunnel.
- **Recommended Remediation:** 
  1. Add a healthcheck restart policy or a script check that signals `quick_tunnel_web.rb` to restart `quick-tunnel` when edge registration fails repeatedly.
  2. Implement a safe recovery command in `Repair-QLDAPM-Local.ps1`.

---

### 4. Remote Authentication & Session Security (QTT-02, QTT-03)
- **Authentication Boundary:** Handled by OpenProject Rails session authentication.
- **Anonymous Entry:** Anonymous users hitting `https://[redacted].trycloudflare.com` are presented with OpenProject login screen (`/login`).
- **RBAC:** PM-only write and project permissions are enforced within OpenProject database and AI Gateway tokens.
- **Caveat:** Live remote Playwright tests across 5 roles (Wave 3) will verify session fixation, secure cookies (`SameSite`, `Secure`), and CSRF token transmission through the Cloudflare reverse proxy headers.
