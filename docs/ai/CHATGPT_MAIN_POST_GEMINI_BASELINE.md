# QLDAPM Main — C0 post-Gemini baseline

Observed: 2026-10-27T02:50:22.510492+00:00. Branch `codex/local-multi-agent-upgrade`, HEAD `de7fe8f10ed23bb392b6661b0c7ccf9967524b4e`.

| Component | Reported | Actual source | Actual runtime | Evidence | Verdict |
|---|---|---|---|---|---|
| Gateway | ce1d9784 | 78 deployed files compared; no changed deployed module; 7 extra host modules absent from image | sha256:ce1d9784d5c1a61f92f7b7e46834fe9be3052889cd35aa9801cc3b72874b30ea | CHATGPT_MAIN_RUNTIME_CHECKPOINT.json | VERIFIED with explicit inventory limit |
| Core | unchanged scheduled-parent image | 58 overlay files compared; mismatches 0 | sha256:46bf443035d63d58f3bb5d0a90d303c52b64a28ff2a84045dd56283fcd9b7bb0 | same checkpoint | VERIFIED |
| Native | 338 visible /375 physical,371v4 | Exact consumed transition ledger retained | 375 physical,371v4 status37/gate3,338 latest read-only evidence | Runtime SQL + immutable approval/receipt | VERIFIED observed state; no new mutation |
| n8n |16 active, inventory nodes_count0 | Actual definitions read, not list projection |16 active, each3–5 nodes; versions retained | runtime checkpoint/workflow private snapshot | VERIFIED configuration, not all business E2E |
| Qdrant/Ollama |1742/1024/BGE-M3 | No indexing or schema change |1742 points,1024 Cosine,bge-m3 listed | runtime checkpoint | VERIFIED metadata; live embedding not repeated |
|203-test claim |40 suites PASS | Different subset from prior606 qualification | Union execution pending | regression module manifests | PARTIAL coverage claim |
| Overall production |FULL_INTEGRATION_QUALIFIED | WF09/WF11 full application chain still missing |No evidence removes recovery/provenance/external/UAT limits | claim audit and old acceptance matrix | PARTIAL, not FULL_GO |

Single writer: latest user handoff authorizes takeover, no competing writer observed; source hashes stayed stable during preflight. Process presence alone is not proof. 4011 untracked paths preserved; no tracked diff/reset/clean/commit.

Fresh individual PostgreSQL and Linux-owned SQLite backups are private; this is not an atomic full DR proof. No Native/model/credential/Staging mutation in C0. Older Codex/Sonnet/Gemini checkpoint and handoff files were not overwritten.

The previous Codex Manager409 candidate is already included in Gemini image through the Sonnet deployment; do not deploy the older candidate over Gemini fixes.
