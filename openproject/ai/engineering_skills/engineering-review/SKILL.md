---
name: engineering-review
description: Independently review an actual feature diff against its specification, including changed tests, or verify a reworked revision.
metadata:
  version: 1.0.0
---

ID `qldapm.review.v1`; version `1.0.0`. Local adaptation of Superpowers code-review and verification practices; Agency Agents reality-checker/reviewer responsibilities.

Inputs: AC/spec, base revision, actual diff hash and files. Tools: read only; Dev session state is not review evidence. Trigger: initial or rework review assigned by QLDAPM.

Read the actual changed files and diff. Map each AC to behavior and tests. Check correctness, persistence/reopen semantics, parameterized SQL, input validation and whether tests could pass with broken behavior. Check both code and tests. Report only actionable defects with severity, relative file, one-based line and revision. Distinguish an observed defect from a concern requiring a test. Re-review the final revision after changes.

Artifact: JSON verdict, exact diff SHA256 and findings. Verification: host rejects a verdict for a different revision and rechecks the tree after QA. PASS is allowed when no defect is found; do not invent a defect. Failure: return FAIL/blocker with evidence; never edit code or approve an unseen revision.
