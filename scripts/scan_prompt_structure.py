with open('scripts/full_user_prompt.txt', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if line.startswith('#') or 'BƯỚC' in line or 'PHASE' in line or '.md' in line or 'BÁO CÁO' in line:
        print(f"L{i:4d}: {line.strip()[:100]}")
