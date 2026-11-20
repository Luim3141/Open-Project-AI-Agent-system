# COMMAND LOG — WAVE 0 AUDIT

**Run Directory:** `docs/ai-multi-agent-upgrade/verification_runs/run_20261017_1616/`  
**Started:** 2026-10-17T16:15:55+07:00  

| Command | Exit Code | Purpose / Output Summary |
|---|---|---|
| `git status -s; git branch -v; git log -1 --oneline` | 0 | Baseline git check; HEAD de7fe8f; branch codex/local-multi-agent-upgrade |
| `git status -uno` | 0 | Verified clean tracked working tree; 0 uncommitted changes |
| `powershell -Command "Get-Date...; docker ps -a ..."` | 0 | Discovered 18 running containers; quick-tunnel-1 is unhealthy |
| `& openproject/ai/.venv/Scripts/python.exe audit_claims.py ...` | 0 | Generated READ_ONLY_FILE_INVENTORY.json: 113 tasks discovered |
| `docker compose files discovery` | 0 | Located all compose definitions across openproject |
| `docker logs --tail 30 qldapm-ai-stage-quick-tunnel-1` | 0 | Discovered DEF-01: Unauthorized: Tunnel not found on Cloudflare edge |
| `docker stats --no-stream ...` | 0 | Discovered DEF-04: Staging 1.67 GiB + Main 2.34 GiB = ~4.23 GiB total RAM |
| `docker network ls & docker inspect` | 0 | Verified origin isolation: quick-tunnel only touches staging-web |
| `& openproject/ai/.venv/Scripts/python.exe build_claim_ledger.py` | 0 | Built CLAIM_LEDGER.csv with 124 claims/tasks mapped to disk evidence |
| `python count_statuses.py` | 0 | Status distribution: 27 PASS, 93 PASS_WITH_LIMITATIONS, 3 FAIL, 1 BLOCKED |
