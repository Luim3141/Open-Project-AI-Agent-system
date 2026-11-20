"""WF01 file requests may select only the existing Engineering project scope."""
import json
import shutil
import subprocess
import unittest
from pathlib import Path

from automation.deploy_real_n8n_workflows import build_workflows
from automation.n8n_integration_adapter import attach


class Project6FileWorkflowTests(unittest.TestCase):
    def test_published_wf01_adapter_is_idempotent_and_preserves_graph(self):
        original=build_workflows()['WF01'];candidate=attach(original)
        self.assertEqual(attach(candidate),candidate)
        self.assertEqual({k:v for k,v in candidate['connections'].items() if not k.startswith('Integration WF01 ')},original['connections'])
        self.assertEqual(candidate['settings'],original['settings'])
        self.assertEqual([n['id'] for n in candidate['nodes'] if not n['id'].startswith('integration-')],[n['id'] for n in original['nodes']])
        self.assertEqual([n['id'] for n in candidate['nodes'] if n['id'].startswith('integration-')],['integration-trigger','integration-callback','integration-business','integration-reply'])
        node=next(n for n in candidate['nodes'] if n['id']=='explicit_request')
        js=node['parameters']['jsCode']
        self.assertIn('project_id',js)
        runtime=shutil.which('node')
        if not runtime:self.skipTest('Node required for n8n code node verification')
        script=r'''
const assert=require('node:assert/strict'),src=require('node:fs').readFileSync(0,'utf8');
const run=body=>new Function('$input',src)({first:()=>({json:{body}})})[0].json;
const id='12345678-1234-4234-8234-123456789012';
assert.deepEqual(run({source_key:'p6-file',request_id:id,project_id:6}),{action:'knowledge_file_ingest',arguments:{source_key:'p6-file'},idempotency_key:'wf01-file-'+id,project_id:6});
assert.deepEqual(run({source_key:'p6-file',operation:'search',query:'evidence',project_id:6}),{action:'knowledge_file_search',arguments:{source_key:'p6-file',query:'evidence'},project_id:6});
assert.deepEqual(run({source_key:'p6-file',operation:'read',document_id:'a'.repeat(64),project_id:6}),{action:'knowledge_file_read',arguments:{source_key:'p6-file',document_id:'a'.repeat(64)},project_id:6});
assert.equal(Object.hasOwn(run({source_key:'old',request_id:id}),'project_id'),false);
for(const project_id of [5,7,0,'6',true,null])assert.equal(run({source_key:'p6-file',request_id:id,project_id}).action,'INVALID_FILE_SOURCE_REQUEST');
for(const extra of [{path:'x'},{file_path:'x'},{content:'x'},{id:2}])assert.equal(run({source_key:'p6-file',request_id:id,project_id:6,...extra}).action,'INVALID_FILE_SOURCE_REQUEST');
'''
        run=subprocess.run([runtime,'-e',script],input=js,text=True,capture_output=True,timeout=15)
        self.assertEqual(run.returncode,0,run.stderr)

    def test_published_definition_patch_is_narrow_and_refuses_source_drift(self):
        root=Path(__file__).resolve().parents[3]
        rows=json.loads((root/'docs/ai/engineering/CHATGPT_RECOVERY/demo-final/n8n/published-after.json').read_text())
        row=next(row for row in rows if row['name'].startswith('WF01'))
        original={**row,'nodes':json.loads(row['nodes']),'connections':json.loads(row['connections']),'settings':json.loads(row['settings'])}
        candidate=attach(original)
        self.assertEqual(attach(candidate),candidate)
        self.assertEqual({k:v for k,v in candidate['connections'].items() if not k.startswith('Integration WF01 ')},original['connections'])
        self.assertEqual(candidate['settings'],original['settings'])
        self.assertEqual([n for n in candidate['nodes'] if n['id']!='explicit_request' and not n['id'].startswith('integration-')],[n for n in original['nodes'] if n['id']!='explicit_request'])
        unsafe=json.loads(json.dumps(original));node=next(n for n in unsafe['nodes'] if n['id']=='explicit_request')
        node['parameters']['jsCode']='// unexpected incompatible workflow body'
        with self.assertRaisesRegex(ValueError,'WF01_SOURCE_CONTRACT_CHANGED'):attach(unsafe)
