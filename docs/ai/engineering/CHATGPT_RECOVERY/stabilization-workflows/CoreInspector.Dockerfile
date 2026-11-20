FROM qldapm-core:stabilization-controls
USER root
COPY --chown=app:app app/views/qldapm_ai/_engineering_command_center.html.erb /app/app/views/qldapm_ai/_engineering_command_center.html.erb
USER app
