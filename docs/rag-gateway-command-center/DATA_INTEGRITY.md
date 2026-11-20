# Data / configuration preservation

[Before](integrity-before.json), [after](integrity-after.json), [source/index/PR readback](final-integrity.json), [baseline](baseline.json). Actual before/after hashes, not inferred from healthy status.

| Invariant | Verified |
|---|---|
| Native_projects_roles_workflows_passwords | True |
| Native398_entire_row | True |
| runtime_tasks_runs_checkpoints_units_control_tokens | True |
| config_secrets | True |
| environment_except_authorized_image | True |
| other_image_pins | True |
| OFF_idle | True |
| n8n_workflows_credentials | True |
| bot_keys_notification_keys | True |
| pairing_approval_outbox_context | True |
| old_provider_receipts_immutable | True |
| new_receipts_only_authorized_RAG | True |

Whole Native398row stable v10; READY FOR RELEASE/AWAITING_OWNER_APPROVAL. Engineering tasks/runs/queue/plans/checkpoints/unit catalog/control/tokens hashes unchanged. Catalog14/14 ceiling preserved, SupervisorOFF/active0; noTask399. Old620provider receipt rows byte-content hash preserved;8new Gateway receipts are purposeknowledge/actor18/runNone (count+generation ×4; one generation503, later explicit negativeABSTAIN). No new AgentRun. Bot bucket20769 used18→20; natural UTC20770 used2/20 (one memoryfailure + one freshfinalPASS), no manual reset/increase or hidden Gatewaymodelcall in Botextract.

All project5 rows / old project6 statuses,roles,membership,workflows,auth,password hashes stable. n8n workflow/credential fingerprint and container/image unchanged; pairing/codes/confirmations/notification contexts/outbox unchanged (7SENThistory), no completion sent for398. PR15freshGitHubOPEN/unmerged, checks0≠CIpassed; deployed mini app head01d765 unchanged.

Corpus metadata/pins/roles/contentlength and2485chunks/2488points unchanged. Whole point/payload fingerprint c945eb2c94e435359a23f4ed0618b131fe639b96b690fd828938903984cfeba4 matches exact baseline normalization.3orphan old points not deleted. No reindex/upsert/collection reset or volume deletion, no DB restore.

Only authorized image pins changed: AI_IMAGE, CORE_IMAGE/bridge image. Gateway config/key/model/caps exact hashes stable, Bot env/mount/network/restart semantic parity. .env whitespace diagnostic: raw-normalized hash changed; exact private pre-release backup matched before fingerprint, **every nonempty line exceptAI_IMAGE identical**; blank lines 3234→3774 from existing text-mode CRLF operator. [Diagnostic](integrity-after-line-ending-diagnostic.json) retained; this is not a secret/config-value change. No user credentials printed.

Source image parity all present files: Core82/Gateway115/Bot10; same7legacyGWabsences. Exact11changed product files in final-integrity.json. Baseline có8507untracked files; chỉ các file được giao trong whitelist được sửa/stage, không addall/clean/reset. Private DB/cookies/keys/cache/operator backup/contexts excluded from handoff commits.
