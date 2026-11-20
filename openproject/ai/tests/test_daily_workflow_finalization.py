"""The actual generated n8n Code boundary must reject incomplete HTTP-200 collectors."""
import json
import subprocess
import unittest

from automation.deploy_real_n8n_workflows import build_workflows


class DailyWorkflowFinalizationTests(unittest.TestCase):
    def test_daily_collector_requires_ready_before_n8n_success(self):
        workflow = build_workflows()['WF07']
        validators = [n for n in workflow['nodes'] if n['id'] == 'daily_business_result']
        self.assertEqual(len(validators), 1, 'WF07_HTTP_200_PARTIAL_MUST_NOT_BECOME_SUCCESS')
        code = validators[0]['parameters']['jsCode']
        script = "const assert=require('assert');const validate=new Function('$json','$input',"+json.dumps(code)+");"
        script += "const input={all:()=>['kept']};assert.deepEqual(validate({result:{state:'COMPLETED',status:'READY'}},input),['kept']);"
        script += "for(const result of [{state:'COMPLETED',status:'PARTIAL'},{state:'RUNNING'},{state:'FAILED'},null])assert.throws(()=>validate({result},input),/DAILY_REPORT_NOT_READY/);"
        result = subprocess.run(['node', '-e', script], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = next(n for n in workflow['nodes'] if n['id'] == 'report')
        self.assertEqual(workflow['connections'][report['name']]['main'][0][0]['node'], validators[0]['name'])
