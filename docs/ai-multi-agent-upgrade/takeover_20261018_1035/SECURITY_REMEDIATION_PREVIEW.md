# TOTP remediation preview — NOT EXECUTED / requires new owner approval

> OWNER RESPONSE18Oct2026: **NOT_APPROVED_DO_NOT_ROTATE**. Fresh read-only recheck completed; old23–28 still active/default,35–40 absent, actual Rails/psql same cluster/database. Read `totp_recheck_20261018_1049/TOTP_RECHECK_REPORT.md`. No credential/device/Main/tunnel mutation authorized or performed. Time-window diagnosis remains a hypothesis, not confirmed root cause.


## Concrete target and observed before state

| Login | Actual user | Current active/default device |
|---|---|---|
| ba-pm |6|27|
| pm |7|24|
| be |8|23|
| fe |9|25|
| qa |10|26|
| stage-owner |5|28|

New IDs35–40 do not exist; allocate actual new IDs during an approved repair, never hardcode those IDs or user13. Existing saved secrets match old active devices. Do not reuse historical approval A as permission to run a new rotation.

## Proposed authorized operation

After owner approves: fix and offline-test the rotation operator for time-window drift (Python OTP is currently generated before a slow Rails boot), correct actual identity mapping, full transaction/failed-attempt cleanup and crash-consistent private credential persistence. First take a verified scoped Staging backup including native devices and private credential recovery material. Prepare new cryptographic keys only in private unmounted storage; verify read-back and key validity before revoking old keys, persist mapping and protect owner/SYSTEM ACL. Preserve original valid passwords from stage/accounts.json for the five members; do not reset passwords or change roles. The stale copied password fields must not be used as proof accounts are broken.

Verify all six old devices inactive/non-default and exactly one active/default new device per actual account; fresh browser2FA for five members and owner access as available; old-key rejection without printing any key/code. Public/internal paths must not serve secret files. Main, API key, billing, tunnel and business data untouched. No public downtime or tunnel restart is part of this approval.

## Impact and recovery

Six users must enroll the new TOTP key once through private delivery. Existing business roles/data/passwords remain. A partially failed operation must retain a usable verified device and private recovery mapping, stop with a checkpoint, and not retry blindly. Do not restore a leaked old key as routine rollback; use the validated new recovery device or an owner-approved forward fix. The serving tunnel remains as requested; while approval is pending the historically exposed old TOTP keys remain a material risk. No credential mutation has been made in this takeover.
