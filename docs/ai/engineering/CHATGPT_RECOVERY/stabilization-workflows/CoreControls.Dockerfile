FROM qldapm-core:stabilization-base
USER root
COPY --chown=app:app app/controllers/qldapm_ai_controller.rb /app/app/controllers/qldapm_ai_controller.rb
COPY --chown=app:app app/views/qldapm_ai/_engineering_command_center.html.erb /app/app/views/qldapm_ai/_engineering_command_center.html.erb
USER app
