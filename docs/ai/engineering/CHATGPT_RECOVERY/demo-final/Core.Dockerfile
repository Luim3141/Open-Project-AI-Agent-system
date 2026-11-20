FROM qldapm-core:demo-final-base
USER root
COPY --chown=app:app app/views/qldapm_ai/_engineering_integrations.html.erb /app/app/views/qldapm_ai/_engineering_integrations.html.erb
USER app
