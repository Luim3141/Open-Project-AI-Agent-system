import json
with open('C:/Users/LUIM/.gemini/antigravity/brain/e2384b7c-637b-4eed-a83f-1359e13ac0e7/.system_generated/logs/transcript.jsonl', encoding='utf-8') as f:
    for i, line in enumerate(f):
        data = json.loads(line)
        if data.get('source') == 'USER_INPUT' or data.get('type') == 'USER_INPUT':
            txt = data.get('content', '')[:100].replace('\n', ' ')
            print(f"Line {i}: {data.get('created_at')} - {txt}")
