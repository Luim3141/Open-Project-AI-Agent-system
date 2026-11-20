# P01-02 — Ports / networks / volumes

Observed15/10/2026. `P01-02-ports.json` captures desired/actual mappings, immutable images, Compose file provenance and networks. `P01-02-excluded-ports.txt` is actual Windows netsh output.

| Port | Observed / proposed | Scope |
|---|---|---|
| 8088 | Desired proxy bind127.0.0.1, actual Docker mapping empty; host unreachable | Main unchanged |
| 8090 | Desired gateway bind127.0.0.1, actual mapping empty; host unreachable | Main unchanged |
| 18091 | Bound127.0.0.1, core health200 | Existing staging |
| 18092 | Bound127.0.0.1, gateway health200 | Existing staging |
| 5678 | Free before provision; proposed127.0.0.1 only | n8n owner editor |
| 443 | No listener; future trusted-LAN TLS pending explicit network scope | Not opened |

Windows exclusion8025–8124 contains both8088/8090; several adjoining reserved ranges exist. Container desired binds remain but NetworkSettings.Ports show empty arrays. This directly explains unavailable published endpoints; do not assume container internal health means main user access. No OS reserved-range/Hyper-V/firewall workaround or main port change performed. Repeated main restart is not a reliable fix for OS-reserved ports.

Existing stage-db/stage-assets volumes remain qldapm-ai-stage; main pgdata/opdata stay qldapm-openproject. Stage networks stage(internal)/stage-front, main frontend/backend and AI networks are distinct. Historical test volumes/networks retained; no pruning. Unrelated birdsong untouched.

New overlay will retain exact stage core/gateway/db IDs, signed key/proof mounts, existing actor workspaces, and add n8n-data + one internal automation network. No seeder in explicit up/start service list. Base Compose still contains historical seeder; never run unscoped up. Public tunnel profiles remain unused/stopped. No DB port or gateway/editor LAN publish.

Config projection2tests PASS for merged existing3files+new overlay; checks image pins, secret file only, internal network, loopback publish, no Docker socket/privileged service. Missing secret-path test refuses configuration before provisioning. See P01-03-compose-tests.log. Network/device LAN acceptance remains P01-11.
