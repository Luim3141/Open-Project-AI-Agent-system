FROM qldapm-phase2-base:core-08df5e2bda40
COPY --chown=app:app core/overlay/config/routes.rb /app/config/routes.rb
COPY --chown=app:app core/overlay/app/models/qldapm/rbac.rb /app/app/models/qldapm/rbac.rb
COPY --chown=app:app core/overlay/lib/api/v3/qldapm/gates_api.rb /app/lib/api/v3/qldapm/gates_api.rb
COPY --chown=app:app core/overlay/config/initializers/qldapm_gates.rb /app/config/initializers/qldapm_gates.rb
COPY --chown=app:app core/overlay/app/controllers/qldapm_ai_controller.rb /app/app/controllers/qldapm_ai_controller.rb
COPY --chown=app:app core/overlay/app/views/qldapm_ai/ /app/app/views/qldapm_ai/
