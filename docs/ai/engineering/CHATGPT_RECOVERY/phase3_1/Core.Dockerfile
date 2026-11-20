FROM qldapm-core:phase31-base-7649
USER root
COPY --chown=app:app app/controllers/qldapm_ai_controller.rb /app/app/controllers/qldapm_ai_controller.rb
COPY --chown=app:app app/helpers/qldapm_report_reader_helper.rb /app/app/helpers/qldapm_report_reader_helper.rb
COPY --chown=app:app app/views/qldapm_ai/_engineering_command_center.html.erb /app/app/views/qldapm_ai/_engineering_command_center.html.erb
COPY --chown=app:app app/views/qldapm_ai/_engineering_live_activity.html.erb /app/app/views/qldapm_ai/_engineering_live_activity.html.erb
COPY --chown=app:app app/views/qldapm_ai/_engineering_work_list.html.erb /app/app/views/qldapm_ai/_engineering_work_list.html.erb
COPY --chown=app:app app/views/qldapm_ai/_engineering_plans.html.erb /app/app/views/qldapm_ai/_engineering_plans.html.erb
COPY --chown=app:app app/views/qldapm_ai/_engineering_workforce.html.erb /app/app/views/qldapm_ai/_engineering_workforce.html.erb
COPY --chown=app:app app/views/qldapm_ai/_engineering_notifications.html.erb /app/app/views/qldapm_ai/_engineering_notifications.html.erb
COPY --chown=app:app app/views/qldapm_ai/_engineering_owner_ux_script.html.erb /app/app/views/qldapm_ai/_engineering_owner_ux_script.html.erb
COPY --chown=app:app app/views/qldapm_ai/_engineering_report_reader.html.erb /app/app/views/qldapm_ai/_engineering_report_reader.html.erb
COPY --chown=app:app app/views/qldapm_ai/_engineering_integrations.html.erb /app/app/views/qldapm_ai/_engineering_integrations.html.erb
USER app

