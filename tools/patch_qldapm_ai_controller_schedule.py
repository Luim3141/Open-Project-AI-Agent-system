"""Script to patch qldapm_ai_controller.rb to permit reporting schedule & notification tools."""
from pathlib import Path

path = Path("openproject/ai/core/overlay/app/controllers/qldapm_ai_controller.rb")
content = path.read_text(encoding="utf-8")

old_perm_1 = """      return head :forbidden unless %w[PM AI_SYSTEM_OWNER].include?(@role) && %w[engineering_status engineering_run_once engineering_control engineering_plan engineering_cancel engineering_resume engineering_github_sync engineering_report_generate engineering_report_list engineering_report_get].include?(action)"""

new_perm_1 = """      return head :forbidden unless %w[PM AI_SYSTEM_OWNER].include?(@role) && %w[engineering_status engineering_run_once engineering_control engineering_plan engineering_cancel engineering_resume engineering_github_sync engineering_report_generate engineering_report_list engineering_report_get engineering_report_schedule_get engineering_report_schedule_update engineering_notifications_list engineering_notifications_dismiss].include?(action)"""

assert old_perm_1 in content, "old_perm_1 not found"
content = content.replace(old_perm_1, new_perm_1, 1)

old_perm_2 = """      @tools = %w[engineering_status engineering_run_once engineering_control engineering_plan engineering_cancel engineering_resume engineering_github_sync engineering_report_generate engineering_report_list engineering_report_get]"""

new_perm_2 = """      @tools = %w[engineering_status engineering_run_once engineering_control engineering_plan engineering_cancel engineering_resume engineering_github_sync engineering_report_generate engineering_report_list engineering_report_get engineering_report_schedule_get engineering_report_schedule_update engineering_notifications_list engineering_notifications_dismiss]"""

assert old_perm_2 in content, "old_perm_2 not found"
content = content.replace(old_perm_2, new_perm_2, 1)

path.write_text(content, encoding="utf-8")
print("SUCCESSFULLY PATCHED qldapm_ai_controller.rb")
