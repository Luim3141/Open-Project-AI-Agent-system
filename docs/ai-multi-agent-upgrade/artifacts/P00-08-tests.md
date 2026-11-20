# P00-08 — Safe test baseline

- Windows existing venv: `.venv/Scripts/python.exe -m unittest discover -s tests -v` from `openproject/ai`: **147 tests PASS**, 59.527 seconds; log `P00-08-unit.log`. HTTP/Google fixtures are mocked; tests use temporary state, not runtime DB/provider credentials.
- After adding data-only restore boundary tests: targeted `tests.test_jira_sync tests.test_release`: **29 PASS**, 0.872 seconds; `P00-07-regression.log`.
- Read-only inventory projection tests: **2 PASS**; `P00-audit-tests.log`. Guards prove raw environment values/private key/credential/UI-key contents are not serialized.
- Pinned core image, network=none, Ruby `/trusted/test_policy.rb`: **PASS** 42 valid +42 wrong-role edges and self-approval/evidence/empty-Epic checks; `P00-08-policy.log`.
- Actual read-only native permissions for five roles on both deployments: PASS capture `P00-06-native-role-matrix.json`. Initial audit script used a wrong Member association; corrected to actual Member/User lookup and reran within read-only transactions; no business write.
- Actual source/image parity for staging core+gateway: PASS `P00-03-parity.json`.
- Actual isolated data restores: PASS `P00-07-restore-result.json` + `P00-07-sqlite-restore.json`.

Failed/known: initial audit JSON aggregate parser failed on multiline JSON, changed to compact jsonb and real inventory reran PASS. Legacy full Jira configuration rehearsal FAIL `PM_ROLE_NOT_PROJECT_SCOPED`; this remains a qualification blocker. Current data-only restore never authorizes Jira import/release. Four legacy UI BE-write expectations not executed/claimed green. No native business mutation/inference integration suites, new login/token enrollment, Docker engine shutdown, LAN TLS or main release test during P00.

Final complete Windows suite rerun after helper changes: **149 tests PASS**, 65.998s, exit0, no skips; `P00-08-unit-final.log`. Baseline logs contain fixture-only messages about authorization/mutations; those are not runtime actions or Google evidence.
