# P01-06 — actual Stop/Repair/Status/Logs

Stop-QLDAPM-Local.ps1 actually stopped all5stage services in reverse dependency order, no volume removal. Status after Stop: all running=false, stopped_requires_repair=true, key present/provider CONFIGURED_DISABLED. Repair actually started existing locked DB/core/Gateway then idempotent overlay up-d for n8n/editor, waited healthy and returned all_healthy=true with original key/config bytes. No re-entry, seeder, main promotion or credential reset. Logs script stores bounded raw logs only in private owner/SYSTEM folder; public result includes path/status only.

Evidence P01-06-stop.log/P01-06-stopped-status.json/P01-06-repair.log/P01-06-repaired-status.json/P01-06-private-logs-summary.json. Tests include refusal of active/failed_or_unknown job before ANY docker stop; image/service/project mismatches; health exit/timeout. Final targeted8tests PASS in P01-12-tests.log (includes P01-06 cases). Docker cannot prove every stopped exit was intentional: expose exit/OOM facts rather than inventing crash classification. Normal daemon restart is automatic only for previously running unless-stopped containers; explicit Stop requires Repair once.

No raw private logs, keys or business content printed to evidence. Existing disabled QLDAPM-Jira-MCP-Monitor and Docker Run entry retained; Docker AutoStart=false; no new Windows startup registration.
