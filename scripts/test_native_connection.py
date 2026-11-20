import os
import json
import sys
from pathlib import Path

REPO = Path('.')
sys.path.insert(0, str(REPO / 'openproject/ai'))
from gateway.native import Native

runtime = Path(os.environ['LOCALAPPDATA']) / 'QLDAPM/openproject-ai'
token_19 = json.loads((runtime / 'gateway/credentials.json').read_text())['19']

try:
    # Test Main
    native_main = Native('http://localhost:8088', token_19, 5)
    id_main = native_main.identity(19)
    print("Main identity 19:", id_main)
except Exception as e:
    print("Main error:", e)

try:
    # Test Clone
    native_clone = Native('http://localhost:18095', token_19, 5)
    id_clone = native_clone.identity(19)
    print("Clone identity 19:", id_clone)
except Exception as e:
    print("Clone error:", e)
