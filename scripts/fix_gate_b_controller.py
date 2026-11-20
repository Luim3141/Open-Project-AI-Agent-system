import os

path = r"openproject/ai/core/overlay/app/controllers/qldapm_ai_controller.rb"
with open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
for i, line in enumerate(lines):
    # Fix 1: def command mutation guard for admin
    if "return head :forbidden if User.current.admin? && User.current.id == 5" in line:
        new_lines.append("    return head :forbidden if User.current.admin?\n")
    # Fix 2: load_project check actor role -> deny_access
    elif "item = WorkPackage.visible(User.current).where(project: @project).first!" in line:
        new_lines.append("    item = WorkPackage.visible(User.current).where(project: @project).first\n")
    elif "raise ActiveRecord::RecordNotFound unless item.qldapm_actor(User.current)[\"role\"]" in line:
        new_lines.append("    raise ActiveRecord::RecordNotFound unless item\n\n")
        new_lines.append("    actor_info = item.qldapm_actor(User.current)\n\n")
        new_lines.append("    return deny_access unless actor_info && actor_info[\"role\"].present?\n")
    # Fix 3: bridge identity
    elif "actor = (User.current.admin? && User.current.id == 5) ?" in line:
        new_lines.append("    Qldapm::AiBridge.call(@project, User.current, \"command\", {action:, arguments:, idempotency_key: key})\n")
    elif "Qldapm::AiBridge.call(@project, actor, \"command\"" in line:
        # Skip the old call since replaced above
        continue
    else:
        new_lines.append(line)

with open(path, "w", encoding="utf-8", newline="\n") as f:
    f.writelines(new_lines)

print("Gate B controller fix applied successfully!")
