# Qualified native base plus an ACL-scoped read projection and report card; no migration.
ARG CORE_IMAGE
FROM ${CORE_IMAGE}
COPY --chown=app:app core/overlay/app/views/qldapm_ai/show.html.erb /app/app/views/qldapm_ai/show.html.erb
COPY --chown=app:app core/overlay/app/views/qldapm_ai/_daily_brief.html.erb /app/app/views/qldapm_ai/_daily_brief.html.erb
COPY --chown=app:app core/overlay/app/views/qldapm_ai/_control_center.html.erb /app/app/views/qldapm_ai/_control_center.html.erb
COPY --chown=app:app core/overlay/app/views/qldapm_ai/_result.html.erb /app/app/views/qldapm_ai/_result.html.erb
COPY --chown=app:app core/overlay/app/controllers/qldapm_ai_controller.rb /app/app/controllers/qldapm_ai_controller.rb
COPY --chown=app:app core/overlay/app/services/work_packages/set_attributes_service/derive_progress_values_status_based.rb /app/app/services/work_packages/set_attributes_service/derive_progress_values_status_based.rb
COPY --chown=app:app core/overlay/lib/api/v3/qldapm/gates_api.rb /app/lib/api/v3/qldapm/gates_api.rb
LABEL org.qldapm.report="actor-daily-read-only"
