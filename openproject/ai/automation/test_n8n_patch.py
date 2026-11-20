import os
import requests
import json
import sys

COOKIE = os.environ.get("QLDAPM_N8N_SESSION", "")
HEADERS = {'Cookie': f'n8n-auth={COOKIE}', 'Content-Type': 'application/json'}

def check_methods(wfid):
    print("Testing PATCH on workflow:", wfid)
    r = requests.get(f'http://localhost:5679/rest/workflows/{wfid}', headers=HEADERS, timeout=5)
    print("GET status:", r.status_code)

if __name__ == "__main__":
    check_methods('XoP4M520TMG3WgeY')
