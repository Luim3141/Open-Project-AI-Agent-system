# Qualified dependency base; source overlay is versioned and tested before any promotion.
ARG GATEWAY_IMAGE=qldapm-rd-base:gateway-006b9c6c
FROM ${GATEWAY_IMAGE}
ARG SOURCE_SHA256
COPY gateway/ /app/gateway/
LABEL org.qldapm.policy="FREE_ONLY" org.qldapm.source.sha256=${SOURCE_SHA256} org.qldapm.deployment="candidate-only"
