FROM qldapm-gateway:phase2-reporting-provenance
COPY gateway/engineering.py gateway/engineering_auto.py gateway/engineering_github_sync.py gateway/engineering_owner_control.py gateway/engineering_telemetry.py gateway/service.py /app/gateway/
