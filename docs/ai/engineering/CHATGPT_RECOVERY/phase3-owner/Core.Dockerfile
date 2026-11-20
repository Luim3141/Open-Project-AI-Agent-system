FROM qldapm-core:phase2-final
USER root
COPY --chown=app:app app/controllers/qldapm_ai_controller.rb /app/app/controllers/qldapm_ai_controller.rb
COPY --chown=app:app app/views/qldapm_ai/_engineering_command_center.html.erb app/views/qldapm_ai/_engineering_live_activity.html.erb /app/app/views/qldapm_ai/
USER app
