ARG OPENPROJECT_IMAGE=openproject/openproject:17.9.1-slim@sha256:2beeecac788d4f423c46a95ffbd04e6479491938b9924b610e9f47d81a38303c
FROM ${OPENPROJECT_IMAGE}
COPY --chown=app:app core/overlay/ /app/
LABEL org.qldapm.base="OpenProject v17.9.1 Community" org.qldapm.change="workflow-gates"
