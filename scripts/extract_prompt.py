import json

path = 'C:/Users/LUIM/.gemini/antigravity/brain/e2384b7c-637b-4eed-a83f-1359e13ac0e7/.system_generated/logs/transcript_full.jsonl'
with open(path, encoding='utf-8') as f:
    for i, line in enumerate(f):
        if i == 1622:
            data = json.loads(line)
            content = data.get('content', '')
            with open('scripts/full_user_prompt.txt', 'w', encoding='utf-8') as out:
                out.write(content)
            print("Wrote prompt to scripts/full_user_prompt.txt, length:", len(content))
            break
