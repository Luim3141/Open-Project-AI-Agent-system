# P00-06 — RBAC / native gate freeze

15/10/2026 actual read-only native Rails transaction: `artifacts/P00-06-native-role-matrix.json`. Both databases kept intact; no role, user, permission or work-package mutation.

| Environment | Project | PM | BA | BE | FE | QA |
|---|---|---:|---:|---:|---:|---:|
| Main | 5 | 19 (`ba-pm`) | 20 (`pm`) | 21 | 22 | 23 |
| Staging | 3 | 7 (`pm`) | 6 (`ba-pm`) | 8 | 9 | 10 |

Staging five business accounts active/non-admin. PM add/edit/board true, manage_members false; BA/BE/FE/QA add/edit/board false; every role read/comment true. Staging Administrator12 is retained separately and has PM membership plus system administration, not a sixth business-agent identity. Do not enroll/use it as n8n or business AI.

Main remains official legacy deployment: BA/BE/FE/QA add/edit true, PM manage_members true. The new policy is **not activated on main**. No source-only edit can truthfully fix this deployment gap without approved coupled release.

Preserve native permission ceilings, membership freshness, cross-project isolation, PM-only business mutation, independent reviewer/contributor checks, signed actor bridge/nonces, preview/consent, idempotency, native readback receipts and private conversations. Comments remain allowed by native permission and cannot carry unrelated business fields. Machine identity must never reuse PM/admin tokens. Business agents get no shell/Docker socket.

Executed offline policy: 42 valid and 42 wrong-role edges PASS, self-approval/evidence/empty Epic protections PASS (`artifacts/P00-08-policy.log`). Python147 baseline PASS includes REST/MCP mocked native permission checks and tool filtering. This does not replace live five-account E2E.

Known gaps: historical four MCP bearers expired (no renewal); legacy UI test suite has four BE-write expectations contrary to current PM-only policy; old Jira-import configuration fixture assumes single-project PM and now fails with Administrator's existing three memberships. Do not modify roles/bootstrap/memberships to satisfy these fixtures. Full mutative legacy suites not executed on live/staging during P00.
