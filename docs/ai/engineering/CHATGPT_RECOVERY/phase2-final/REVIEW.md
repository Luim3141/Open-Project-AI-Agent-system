# Independent integrity review and fix evidence

Reviewer inspected current source/callers and ran the original 12 fencing cases on 2026-11-02. Two Important findings were reproduced and fixed before rollout:

1. A lease expiring during embedding still allowed knowledge vector publication. The new regression failed with a late UPSERT, then passed after claim checks at knowledge SQLite commits and Qdrant mutation boundaries. Bound engineering operations carry their Gateway Store to these boundaries; normal ingestion has no engineering claim. A separate real HTTP transport fixture checks expiry between collection read and vector PUT; a SQLite test checks rollback when expiry occurs inside a write.
2. Failure disabling the provider transport skipped the hard runtime stop. The new regression first observed zero stop calls, then passed after cleanup always attempted both actions and exited fail-closed if either failed. The host process lock remains held through cleanup.

Other reviewed behavior: durable UUID worker/claim identity, served generation (the UUID token is the authority), same-run resume identity replacement, late completion rejection, global queue admission, Native pending receipt no-replay and worker process locking. Requests already sent to external systems cannot be revoked; Native unknown receipts remain pending and require reconciliation. Git publication has stable branch/SHA read-back and the delivery journal retains unknown outcomes.

Scope limits: reviewer used isolated SQLite/HTTP/subprocess fixtures, not production fault injection or live provider. No merge or Owner acceptance occurred. The review does not prove generic protection from an adversary with Docker/OS operator privileges.
