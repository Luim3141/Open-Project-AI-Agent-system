# QLDAPM — Project instructions

- Use Vietnamese for explanations. Inspect current state before changing Jira or project files.
- For Jira setup, reads, edits, backlog imports, workflow or Sprint work, read `jira-management.md` first. Use the authenticated Atlassian MCP. If the hosted plugin reports `USER_NOT_LOGGED_IN`, use `tools/jira_mcp.py` with the separately authenticated local MCP.
- For workflow, scope-change, acceptance or new-project WBS work, read `jira-workflows.md`. It is an approved specification, not proof of deployment; verify live configuration and test evidence before claiming completion.
- Before importing an item, resolve the explicitly authorized target project in `jira-management.md`, then search its `source-<ID>` label within that project. Update an exact match or create if absent; report ambiguous duplicates. Never fall back to KAN. Preserve KAN unless the user explicitly requests a change to it.
- For system design or implementation changes, read and update `architecture.md` in the same change. Distinguish target architecture from implemented behavior and external tooling.
- Keep estimates, assignments and completion statuses evidence-based. A created ticket is not implemented functionality.
