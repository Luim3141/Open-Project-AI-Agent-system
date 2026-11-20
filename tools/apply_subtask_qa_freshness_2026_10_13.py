"""Apply only the owner's exact approved additive Subtask preview; never replay."""
import hashlib
import json
from pathlib import Path
import jira_admin_mcp as admin

root=Path(__file__).resolve().parents[1]
assert hashlib.sha256((root/'forge/qag3-validator/manifest.yml').read_bytes()).hexdigest() == '6b4782bda709d0e3333ff8f547b59d23139d5cf0cfedb7715246f476ec13d3df'
assert hashlib.sha256((root/'forge/qag3-validator/manifest.subtask-cost-candidate.yml').read_bytes()).hexdigest() == 'dc5d99b77b98dd3d1f307344bfef394ed8ed5021e1579e9db04b151a65ff4d7b'
result=admin.apply_change('234e8874-df07-4bb7-a767-de68791df3ab',
                         'd48a8f29aab199acad9d9c2d0c223d27a7a9ed0f03babdb1291b4586e55d328c')
assert result['status']=='VERIFIED'
print(json.dumps({'previewId':result['previewId'],'status':result['status'],
                  'workflowVersion':result['workflow']['workflows'][0]['version']}))
