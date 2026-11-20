from pathlib import Path

# 1. Patch ERB
erb_path = Path("openproject/ai/core/overlay/app/views/qldapm_ai/_engineering_command_center.html.erb")
erb_content = erb_path.read_text(encoding="utf-8")
old_args = "{repo: 'Luim3141/mini-task-manager'}.to_json"
new_args = "{}.to_json"
if old_args in erb_content:
    erb_content = erb_content.replace(old_args, new_args)
    erb_path.write_text(erb_content, encoding="utf-8")
    print("ERB patched: replaced repo argument with empty hash")
else:
    print("Warning: old_args not found in ERB")

# 2. Patch Controller defensive handling
ctl_path = Path("openproject/ai/core/overlay/app/controllers/qldapm_ai_controller.rb")
ctl_content = ctl_path.read_text(encoding="utf-8")
old_plan = "elsif action == 'engineering_plan'"
new_plan = """elsif action == 'engineering_github_sync'
          arguments = {}
        elsif action == 'engineering_plan'"""
if old_plan in ctl_content and "action == 'engineering_github_sync'" not in ctl_content:
    ctl_content = ctl_content.replace(old_plan, new_plan, 1)
    ctl_path.write_text(ctl_content, encoding="utf-8")
    print("Controller patched: defensive arguments normalization for engineering_github_sync")
else:
    print("Controller already patched or target not found")
