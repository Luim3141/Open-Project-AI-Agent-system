"""Compare private mount hashes without exporting hashes, key values or Google calls."""
import json
from local_runtime import RUNTIME
from jira_sync_backup import command

manifest = json.loads((RUNTIME / 'operator/local-runtime/stage-runtime.json').read_text())
expected = manifest['gateway_files_before']
program = '''import json,hashlib
from pathlib import Path
names = ''' + repr(list(expected)) + '''
print(json.dumps({n:hashlib.sha256((Path('/state')/n).read_bytes()).hexdigest() for n in names}))
'''
actual = json.loads(command(['docker', 'exec', 'qldapm-ai-stage-staging-gateway-1', 'python', '-c', program]))
assert actual == expected, 'GATEWAY_CONFIG_OR_KEY_CHANGED'
program = "const f=require('fs'),c=require('crypto');console.log(c.createHash('sha256').update(f.readFileSync('/run/secrets/n8n_encryption_key')).digest('hex'))"
actual = command(['docker', 'exec', 'qldapm-ai-stage-n8n-1', 'node', '-e', program]).decode().strip()
assert actual == manifest['n8n_key_sha256'], 'N8N_KEY_CHANGED'
print(json.dumps({'gateway_config_credentials_key_exact_bytes_retained': True,
                  'n8n_private_key_loaded_matches_saved': True, 'google_called': False,
                  'provider_enabled': json.loads((RUNTIME / 'stage-ai/gemini.json').read_text())['enabled']}))
