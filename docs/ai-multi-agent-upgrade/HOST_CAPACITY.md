# P01-01 — Host capacity observed15/10/2026

Windows11Enterprise10.0.26200; i5-12500H12cores/16threads; usable RAM23.71GiB, free2.97GiB at capture. Docker Desktop4.90.0/Engine29.7.2, WSL2.7.13/kernel6.18.33.2, Docker allocation11.54GiB/16vCPU. C:38.4GiB free, D:324.5GiB free. Raw measurements artifacts/P01-01-host.json.

Docker idle sample: stagecore872MiB/gateway63MiB/DB76MiB; mainweb1001MiB/worker786MiB/hocuspocus114MiB; unrelated birdsong preserved. This is idle footprint, not five-user load acceptance. Add one bounded n8n container (512MiB cap/0.5CPU) initially; no local model/Redis/large parallel workers. Do not change Windows/WSL memory/power settings or claim headroom under peak load; measure at P09.
