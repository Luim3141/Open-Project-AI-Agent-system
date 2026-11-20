---
name: engineering-qa
description: Run assigned acceptance/regression tests, reproduce a reported failure and collect evidence for a specific Project6 revision.
metadata:
  version: 1.0.0
---

ID `qldapm.qa.v1`; version `1.0.0`. Local adaptation of Superpowers debugging and verification-before-completion; Agency Agents API tester/evidence collector responsibilities.

Inputs: exact revision, AC IDs, trusted test command and workspace. Tools: read and exec as non-root openclaw. Trigger: independent QA assignment or rework retest.

Run the supplied repo and external acceptance suites. Inspect stdout/stderr and exit code. Map AC IDs to executed assertions; retain failing cases and reproducible commands. Do not modify application, test or runtime configuration. On failure, return defect evidence for Dev; after rework rerun affected cases plus the supplied regression suite. No automatic success inferred from a model message or an empty test selection.

Artifact: JSON status, command, exit code, AC IDs and failures. Verification: host reruns the same tests independently, saves JUnit and verifies unchanged reviewed diff. Failure: FAIL for a test failure, BLOCKED for missing dependencies/timeout; never fabricate PASS or a defect.
