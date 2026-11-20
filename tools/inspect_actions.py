import re
from pathlib import Path

p = Path("openproject/ai/core/overlay/app/views/qldapm_ai/_engineering_command_center.html.erb")
text = p.read_text(encoding="utf-8")

print("=== FORMS IN COMMAND CENTER ===")
for m in re.finditer(r'<form\s+([^>]+)>', text):
    print("FORM:", m.group(1)[:120])

print("\n=== BUTTONS / INPUTS IN COMMAND CENTER ===")
for m in re.finditer(r'<(button|input|a)\s+([^>]+)>', text):
    tag, attrs = m.group(1), m.group(2)
    if any(k in attrs.lower() for k in ["run", "auto", "pause", "sync", "report", "schedule", "refresh", "action", "submit"]):
        print(f"<{tag}>:", attrs[:140])
