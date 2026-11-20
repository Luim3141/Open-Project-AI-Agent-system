"""Test script to reproduce and verify the @role initialization in QldapmAIController#command.
"""
import re
from pathlib import Path

controller_path = Path("openproject/ai/core/overlay/app/controllers/qldapm_ai_controller.rb")
content = controller_path.read_text(encoding="utf-8")

# Check if @role is initialized before the check on line 174
command_match = re.search(r'def command\s*(.*?)(?:if engineering_project\?|\n\s*action =)', content, re.DOTALL)
if command_match:
    pre_check_block = command_match.group(1)
    has_role_init = "@role = " in pre_check_block or "@role=" in pre_check_block
    print(f"Has @role initialization before engineering check: {has_role_init}")
    if not has_role_init:
        print("REPRODUCED BUG: @role is uninitialized (nil) when checking %w[PM AI_SYSTEM_OWNER].include?(@role)")
        print("This causes ALL command requests to return 403 Forbidden!")
    else:
        print("VERIFIED FIX: @role is initialized before the permission check.")
else:
    print("Could not find def command pattern")
