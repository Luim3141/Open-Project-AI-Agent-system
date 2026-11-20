import re

path = 'openproject/ai/automation/generate_n8n_main_workflows.py'
content = open(path, encoding='utf-8').read()

import uuid

def replacer(match):
    prefix = match.group(0)
    uid = str(uuid.uuid4())
    return prefix + f'\n                "webhookId": "{uid}",'

new_content = re.sub(r'"type": "n8n-nodes-base\.webhook",\s*"typeVersion": 1,', replacer, content)
open(path, 'w', encoding='utf-8').write(new_content)
print("Updated generate_n8n_main_workflows.py with unique webhookIds")
