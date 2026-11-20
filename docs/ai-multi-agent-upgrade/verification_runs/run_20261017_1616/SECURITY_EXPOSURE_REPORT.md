# SECURITY & PORT EXPOSURE REPORT — WAVE 0

**Audit Run:** `run_20261017_1616`  
**Date:** 2026-10-17  
**Scope:** Docker Network & Host Port Bindings Inspection (BASE-02, BASE-03, QTT-06)

---

### 1. Host Port Bindings Audit
All active containers were inspected for listening ports and host interfaces:

| Container Name | Internal Port | Host Binding | Intended Audience | Security Verdict |
|---|---|---|---|---|
| `qldapm-openproject-proxy-1` | 80/tcp | `127.0.0.1:8088` | Local Main OpenProject | **PASS (Loopback only)** |
| `qldapm-ai-gateway-1` | 8090/tcp | `127.0.0.1:8090` | Local Main AI Gateway | **PASS (Loopback only)** |
| `qldapm-ai-stage-staging-web-1` | 8080/tcp | `127.0.0.1:18091` | Local Staging Web | **PASS (Loopback only)** |
| `qldapm-ai-stage-staging-gateway-1` | 8090/tcp | `127.0.0.1:18092` | Local Staging Gateway | **PASS (Loopback only)** |
| `qldapm-ai-stage-n8n-editor-1` | 5678/tcp, 18090/tcp | `127.0.0.1:5678`, `127.0.0.1:18090` | Admin / Operator Only | **PASS (Loopback only)** |
| `qldapm-openproject-db-1` | 5432/tcp | None (internal network) | Internal containers | **PASS (No host port)** |
| `qldapm-ai-stage-db-1` | 5432/tcp | None (internal network) | Internal containers | **PASS (No host port)** |
| `qldapm-ai-stage-n8n-1` | 5678/tcp | None (internal network) | Internal containers | **PASS (No host port)** |
| `qldapm-ai-stage-local-backup-1` | 8080/tcp | None (internal network) | Internal containers | **PASS (No host port)** |
| `qldapm-ai-stage-quick-tunnel-1` | Outbound only | Outbound to Cloudflare Edge | Public remote users | **PASS (Target: staging-web only)** |

**Key Finding:** No database (5432), cache (11211), internal gateway, or n8n admin interfaces are bound to `0.0.0.0`. All admin ports are strictly locked to `127.0.0.1` (loopback).

---

### 2. Secret Storage & Git Hygiene (BASE-03)
- **Credential Storage:** 
  - Gemini API key, n8n encryption keys, and OpenProject user API tokens are stored in:
    `C:\Users\LUIM\AppData\Local\QLDAPM\openproject-ai\`
  - This directory is completely outside the Git repository root (`D:\AI project\QLDAPM chat`).
- **Git Status:** 
  - `git status -uno` confirms 0 uncommitted tracked changes on `codex/local-multi-agent-upgrade`.
  - No secret tokens, credentials, or private keys are tracked in Git.
- **Verdict:** **PASS**. Credential storage meets strict separation requirements.
