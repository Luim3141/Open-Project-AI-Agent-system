"""Record exact hashes and each executed unittest result; fixture evidence only."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import time
import unittest

ROOT=Path.cwd()
OUT=Path(__file__).parent
NAME=sys.argv[1] if len(sys.argv)>1 else 'targeted-tests'
sys.path.insert(0,str(ROOT/'openproject/ai'))
MODULES=['tests.test_engineering_reporting','tests.test_engineering_reporting_contract',
         'tests.test_operational_reports','tests.test_takeover_workflows',
         'tests.test_daily_workflow_finalization','tests.test_scheduled_weekly_summary',
         'tests.test_weekly_accuracy']
FILES=['gateway/engineering_reporting.py','tests/test_engineering_reporting.py',
       'automation/deploy_real_n8n_workflows.py','gateway/daily_brief.py',
       'gateway/weekly_report.py','gateway/native.py',
       *[name.replace('.','/')+'.py' for name in MODULES]]
records=[]
started=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
hashes={f:hashlib.sha256((ROOT/'openproject/ai'/f).read_bytes()).hexdigest() for f in FILES}


class Result(unittest.TextTestResult):
    def startTest(self,test):
        self.start_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
        super().startTest(test)

    def addSuccess(self,test):
        records.append({'test':test.id(),'utc':self.start_utc,'outcome':'PASS'})
        super().addSuccess(test)

    def addFailure(self,test,error):
        records.append({'test':test.id(),'utc':self.start_utc,'outcome':'FAIL'})
        super().addFailure(test,error)

    def addError(self,test,error):
        records.append({'test':test.id(),'utc':self.start_utc,'outcome':'ERROR'})
        super().addError(test,error)

    def addSkip(self,test,reason):
        records.append({'test':test.id(),'utc':self.start_utc,'outcome':'SKIP','reason':reason})
        super().addSkip(test,reason)


with (OUT/(NAME+'.log')).open('w',encoding='utf-8') as log:
    result=unittest.TextTestRunner(stream=log,verbosity=2,resultclass=Result).run(unittest.defaultTestLoader.loadTestsFromNames(MODULES))
data={'started_utc':started,'completed_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
      'source_git_head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
      'source_note':'working tree uncommitted; per-file hashes identify tested revision',
      'source_sha256':hashes,'tested_image':None,'serving_baseline_gateway_image':'sha256:698db791f8e96e8c0db6253457a75348eade5dff3c89e2d1ae314083387fcceb',
      'command':'openproject/ai/.venv/Scripts/python.exe docs/ai/engineering/CHATGPT_RECOVERY/phase2-final/workflows/record_tests.py'+(' '+NAME if len(sys.argv)>1 else ''),
      'environment':'Windows Python '+sys.version.split()[0]+'; isolated temporary SQLite + Native/GitHub fixtures; no MAIN writes',
      'evidence_path':str(OUT/(NAME+'.log')),'status':'PASS' if result.wasSuccessful() else 'FAIL','tests':records}
assert len(records)==result.testsRun
assert hashes=={f:hashlib.sha256((ROOT/'openproject/ai'/f).read_bytes()).hexdigest() for f in FILES},'SOURCE_CHANGED_DURING_TESTS'
(OUT/(NAME+'.json')).write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':data['status'],'tests':result.testsRun,'failed':len(result.failures),'errors':len(result.errors)}))
sys.exit(0 if result.wasSuccessful() else 1)
