The local Demo was still running older task APIs while PRs #6–#10 remained stacked on feature branches. This integration branch includes that chain and the current `main` ancestry, adds explicit release identity, and has been deployed locally as an **unmerged integration test release**.

Changes:
- Includes summary, detail, exists, title, and CSV export endpoints from #6–#10 without merging or changing those PRs.
- Exposes the exact revision and release label through `/release`, HTTP headers, and the HTML interface.
- Neutralizes formula-bearing CSV title cells with a quoted tab prefix. JSON titles and SQLite values remain unchanged; normal Unicode/comma/quote/newline CSV round-trips remain intact. Programmatic CSV readers see the tab prefix on dangerous titles.

Validation:
- 52 repository/existing acceptance tests passed on the isolated pinned Python runtime, including the existing JavaScript VM tests.
- Eleven actual read-only API checks passed on the local Demo at port18791, with revision `01d765c01d62a0d636e276f72bdc5cdc62db8c5a` in the response headers.
- Actual HTTP tests on the same release with an isolated temporary SQLite verified CRUD, filters, summary/detail/exists/title, Unicode, CSV escaping and formula neutralization.
- The live Demo SQLite schema, tasks and sequence hashes matched before and after deployment. A pre-change SQLite/source/service backup is retained privately.

PRs #6–#10 remain OPEN. This PR is prepared for Owner review and does not authorize merging it or call the candidate a `main` release. Computer Use acceptance is a separate final phase. Spreadsheet application import/export behavior varies; no Excel/Calc GUI test is claimed here.
