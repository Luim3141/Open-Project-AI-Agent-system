FROM qldapm-n8n:demo-base-39299
USER root
COPY automation/n8n_storage_redaction.js automation/patch_n8n_lifecycle_storage.js /opt/qldapm/
RUN node /opt/qldapm/patch_n8n_lifecycle_storage.js
USER node
