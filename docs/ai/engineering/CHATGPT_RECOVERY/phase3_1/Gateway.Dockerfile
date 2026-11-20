FROM qldapm-gateway:phase31-base-ce047
COPY gateway/engineering.py gateway/engineering_auto.py gateway/engineering_lifecycle.py gateway/engineering_operator.py gateway/engineering_monitor.py gateway/engineering_owner_control.py gateway/engineering_reporting.py gateway/engineering_observability.py gateway/engineering_health.py gateway/service.py /app/gateway/

