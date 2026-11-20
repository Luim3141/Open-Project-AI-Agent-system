import copy
import datetime as dt
import unittest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from automation.natural_schedule_observation import WORKFLOWS, assess, due_time, observe, main


class NaturalObservationTests(unittest.TestCase):
    def fixture(self,code='WF07'):
        at=due_time(code,{'WF07':'2026-10-29T08:00:00+07:00','WF12':'2026-10-30T17:00:00+07:00','WF16':'2026-10-29T03:45:00+07:00'}[code])
        business={'authority':'machine','actor_id':None,'project_id':5,'model_calls':0,'native_write_allowed':False,'state':'COMPLETED','status':'READY','ready':5,'targets':5,'run_id':'receipt','request_key':'daily:2026-10-29','kind':'daily_brief'}
        ledger={'id':'receipt','actor':None,'result':business,'request_key':business['request_key']}
        if code=='WF12':business.update(kind='weekly_summary',request_key='weekly:2026-10-26');ledger['request_key']=business['request_key']
        if code=='WF16':business['state']='HEALTHY';ledger.update(hash_valid=True,sha256='h',request_key=str(int(at.timestamp())//900))
        output={'result':business,'sha256':'h','correlation_id':'receipt'}
        row={'id':1,'mode':'trigger','status':'success','finished':1,'execution_error':False,'workflow_version':'v','startedAt':at.astimezone(dt.timezone.utc).isoformat(),'stoppedAt':(at+dt.timedelta(seconds=2)).isoformat(),'output':output}
        w={'id':WORKFLOWS[code][0],'active':True,'activeVersionId':'v','settings':{'timezone':'Asia/Bangkok'},'nodes':[{'type':'n8n-nodes-base.scheduleTrigger','parameters':{'rule':{'interval':[{'expression':WORKFLOWS[code][1]}]}}}]}
        return at,{'workflow':w,'executions':[row]},ledger,at+dt.timedelta(minutes=6)

    def test_future_observation_never_accesses_docker_or_claims_pass(self):
        at,snapshot,ledger,now=self.fixture()
        with patch('automation.natural_schedule_observation.docker') as docker:
            self.assertEqual(observe('WF07',at,at-dt.timedelta(seconds=1))['status'],'PENDING_SCHEDULED_OBSERVATION')
            docker.assert_not_called()

    def test_all_three_real_contract_shapes_require_matching_durable_receipt(self):
        for code in WORKFLOWS:
            at,snapshot,ledger,now=self.fixture(code)
            self.assertIn(assess(code,at,snapshot,ledger,now)['status'],{'OBSERVED_READY','OBSERVED_HEALTHY'})
            changed=copy.deepcopy(ledger);changed['result']['model_calls']=1
            self.assertEqual(assess(code,at,snapshot,changed,now)['status'],'RECEIPT_OR_AUTHORITY_MISMATCH')

    def test_http_success_partial_or_wrong_date_is_never_business_pass(self):
        at,snapshot,ledger,now=self.fixture()
        snapshot['executions'][0]['output']['result']['status']='PARTIAL'
        self.assertEqual(assess('WF07',at,snapshot,ledger,now)['status'],'BUSINESS_RESULT_NOT_READY')
        snapshot['executions'][0]['output']['result']['status']='READY';ledger['request_key']='daily:2026-10-28'
        self.assertEqual(assess('WF07',at,snapshot,ledger,now)['status'],'BUSINESS_RESULT_NOT_READY')

    def test_monitor_stale_bucket_and_hash_are_denied(self):
        at,snapshot,ledger,now=self.fixture('WF16');ledger['hash_valid']=False
        self.assertEqual(assess('WF16',at,snapshot,ledger,now)['status'],'RECEIPT_HASH_MISMATCH')
        ledger['hash_valid']=True;ledger['request_key']='wrong'
        self.assertEqual(assess('WF16',at,snapshot,ledger,now)['status'],'RECEIPT_HASH_MISMATCH')

    def test_manual_runs_duplicates_missing_and_failed_executions_are_distinct(self):
        at,snapshot,ledger,now=self.fixture();snapshot['executions'][0]['mode']='manual'
        self.assertEqual(assess('WF07',at,snapshot,ledger,now)['status'],'SCHEDULE_NOT_OBSERVED')
        snapshot['executions'][0]['mode']='trigger';snapshot['executions']*=2
        self.assertEqual(assess('WF07',at,snapshot,ledger,now)['status'],'DUPLICATE_SCHEDULED_EXECUTIONS')
        snapshot['executions']=snapshot['executions'][:1];snapshot['executions'][0]['status']='error'
        self.assertEqual(assess('WF07',at,snapshot,ledger,now)['status'],'FAILED_OR_UNFINISHED_EXECUTION')

    def test_non_production_time_or_timezone_is_not_accepted(self):
        for code,value in [('WF07','2026-10-29T08:00:00'),('WF12','2026-10-29T17:00:00+07:00'),('WF16','2026-10-29T03:46:00+07:00')]:
            with self.assertRaises(ValueError):due_time(code,value)

    def test_execution_of_an_old_version_does_not_qualify_current_publication(self):
        at,snapshot,ledger,now=self.fixture();snapshot['executions'][0]['workflow_version']='old'
        self.assertEqual(assess('WF07',at,snapshot,ledger,now)['status'],'EXECUTION_VERSION_NOT_VERIFIED')

    def test_due_mode_does_not_repeat_an_already_qualified_observation(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);at='2026-10-28T08:00:00+07:00'
            (root/'plan.json').write_text(json.dumps([{'workflow':'WF07','scheduled_at':at}]))
            (root/'WF07-2026-10-28-latest.json').write_text(json.dumps({'scheduled_at':at,'status':'OBSERVED_READY'}))
            with patch('automation.natural_schedule_observation.ROOT',root),patch('sys.argv',['observer','--due']),patch('automation.natural_schedule_observation.observe') as probe,patch('builtins.print'):
                self.assertEqual(main(),0);probe.assert_not_called()
