FROM docker.n8n.io/n8nio/n8n:2.43.6
USER root
COPY automation/n8n_storage_redaction.js automation/patch_n8n_storage.js /opt/qldapm/
RUN node /opt/qldapm/patch_n8n_storage.js
USER node
