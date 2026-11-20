with open('scripts/full_user_prompt.txt', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(2070, min(2140, len(lines))):
    print(f"{lines[i]}", end='')
