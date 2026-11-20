from pathlib import Path

p = Path('openproject/ai/core/overlay/app/views/qldapm_ai/_engineering_command_center.html.erb')
text = p.read_text(encoding='utf-8')

target = '<div class="qcc-plans-section" style="margin-bottom: 20px;">'
replacement = '<div class="qcc-plans-section qcc-planning-specs-card" style="margin-bottom: 20px;">'

assert target in text, 'Target not found'
p.write_text(text.replace(target, replacement), encoding='utf-8')
print('Added qcc-planning-specs-card class!')
