FROM qldapm-recovery-base:core-a4fa8150728b
COPY --chown=app:app core/overlay/app/controllers/qldapm_ai_controller.rb /app/app/controllers/qldapm_ai_controller.rb
COPY --chown=app:app core/overlay/app/views/qldapm_ai/_engineering_command_center.html.erb /app/app/views/qldapm_ai/_engineering_command_center.html.erb
