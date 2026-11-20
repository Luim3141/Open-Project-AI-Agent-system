path = 'openproject/ai/core/overlay/config/routes.rb'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

target = '  get "/projects/:project_id/qldapm-ai/executions/:run_id", to: "qldapm_ai#execution", as: :project_qldapm_ai_execution'
replacement = target + '\n  get "/projects/:project_id/qldapm-ai/execution", to: "qldapm_ai#execution"'

if target in content:
    content = content.replace(target, replacement, 1)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('PATCH_ROUTES_SUCCESS')
else:
    print('TARGET_NOT_FOUND')
