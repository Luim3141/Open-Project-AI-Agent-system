# Reuse the serving Core dependency/runtime; monitor assets are Rails view partials.
ARG CORE_IMAGE
FROM ${CORE_IMAGE}
ARG SOURCE_SHA256
COPY --chown=app:app core/overlay/ /app/
LABEL org.qldapm.source.sha256=${SOURCE_SHA256} org.qldapm.deployment="execution-monitor-candidate"
