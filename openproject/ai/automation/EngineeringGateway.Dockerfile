FROM qldapm-phase2-base:gateway-eaaa1217ac79
USER root
COPY --chown=10001:10001 gateway/engineering.py /app/gateway/engineering.py
COPY --chown=10001:10001 gateway/engineering_operator.py /app/gateway/engineering_operator.py
COPY --chown=10001:10001 gateway/native.py /app/gateway/native.py
COPY --chown=10001:10001 gateway/store.py /app/gateway/store.py
COPY --chown=10001:10001 gateway/service.py /app/gateway/service.py
COPY --chown=10001:10001 gateway/permissions.py /app/gateway/permissions.py
COPY --chown=10001:10001 gateway/catalog.py /app/gateway/catalog.py
COPY --chown=10001:10001 gateway/bridge.py /app/gateway/bridge.py
COPY --chown=10001:10001 gateway/app.py /app/gateway/app.py
COPY --chown=10001:10001 gateway/agent_registry.py /app/gateway/agent_registry.py
COPY --chown=10001:10001 gateway/openproject_loader.py /app/gateway/openproject_loader.py
COPY --chown=10001:10001 gateway/engineering_units.py /app/gateway/engineering_units.py
COPY --chown=10001:10001 gateway/engineering_lifecycle.py /app/gateway/engineering_lifecycle.py
COPY --chown=10001:10001 gateway/engineering_planning.py /app/gateway/engineering_planning.py
COPY --chown=10001:10001 gateway/engineering_personas.py /app/gateway/engineering_personas.py
COPY --chown=10001:10001 gateway/engineering_monitor.py /app/gateway/engineering_monitor.py
COPY --chown=10001:10001 gateway/business_runs.py /app/gateway/business_runs.py
COPY --chown=10001:10001 gateway/engineering_state_sync.py /app/gateway/engineering_state_sync.py
COPY --chown=10001:10001 gateway/engineering_github_sync.py /app/gateway/engineering_github_sync.py
COPY --chown=10001:10001 gateway/engineering_auto.py /app/gateway/engineering_auto.py
COPY --chown=10001:10001 gateway/engineering_reporting.py /app/gateway/engineering_reporting.py
COPY --chown=10001:10001 gateway/knowledge_lock.py /app/gateway/knowledge_lock.py
COPY --chown=10001:10001 gateway/knowledge_search.py /app/gateway/knowledge_search.py
COPY --chown=10001:10001 gateway/gemini.py /app/gateway/gemini.py
COPY --chown=10001:10001 engineering_skills /app/engineering_skills
USER 10001
