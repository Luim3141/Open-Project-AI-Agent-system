# Reuse the audited SDK/runtime layers; change Gateway source only.
ARG GATEWAY_IMAGE=qldapm-ai:dates-final-20261015
FROM ${GATEWAY_IMAGE}
COPY gateway/ /app/gateway/
LABEL org.qldapm.policy="FREE_ONLY"
