"""Separate worker processes and disposable SQLite; no Main volumes or Native HTTP."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class DurableRecoveryProcessTests(unittest.TestCase):
    def worker(self, root, code):
        env = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[1]), QLDAPM_AI_RUNTIME='')
        result = subprocess.run([sys.executable, '-c',
            'import json,sys\nfrom gateway.store import Store\ns=Store(sys.argv[1])\n'+code, str(root)],
            env=env, capture_output=True, text=True, timeout=30, check=True)
        return json.loads(result.stdout)

    def seed(self, root):
        return self.worker(root, """
s.begin(19,'isolated-native-receipt',{'action':'update_work_package','arguments':{'id':12}})
r={'result':{'id':12,'lockVersion':2}}
s.finish(19,'isolated-native-receipt',r,knowledge_id=12)
print(json.dumps({'job':r['knowledge_sync']['id'],'claim':s.claim_knowledge_sync(now=1000)}))
""")

    def test_worker_exit_recovers_expired_lease_and_stale_worker_cannot_finish(self):
        with tempfile.TemporaryDirectory() as root:
            first = self.seed(root)
            claim = json.dumps(first['claim'])
            result = self.worker(root, f"""
old=json.loads({claim!r})
assert s.claim_knowledge_sync(now=1001) is None
fresh=s.claim_knowledge_sync(now=1301)
assert fresh['lease']!=old['lease'] and fresh['attempts']==2
assert s.finish_knowledge_sync(old,{{'vector_indexed':True}},now=1302) is False
assert s.finish_knowledge_sync(fresh,{{'vector_indexed':True,'native_id':12,'lock_version':2}},now=1302) is True
print(json.dumps(s.knowledge_sync(19,fresh['id'])))
""")
            self.assertEqual(result['state'], 'verified')
            final = self.worker(root, f"print(json.dumps({{'job':s.knowledge_sync(19,{first['job']!r}),'request':s.request_status(19,'isolated-native-receipt'),'claim':s.claim_knowledge_sync(now=2000)}}))")
            self.assertEqual(final['job']['state'], 'verified')
            self.assertEqual(final['request']['state'], 'done')
            self.assertIsNone(final['claim'])

    def test_process_restarts_preserve_backoff_dlq_and_authorized_recovery(self):
        with tempfile.TemporaryDirectory() as root:
            seeded = self.seed(root)
            now = 1301
            for attempt in range(2, 6):
                result = self.worker(root, f"""
c=s.claim_knowledge_sync(now={now})
assert c['attempts']=={attempt}
assert s.finish_knowledge_sync(c,None,error='ISOLATED_VECTOR_OUTAGE',now={now})
print(json.dumps(s.knowledge_sync(19,c['id'])))
""")
                self.assertEqual(result['next_at'], now + 5 * 2**(attempt-1))
                now = result['next_at']
            self.assertEqual(result['state'], 'dlq')
            final = self.worker(root, f"""
assert s.claim_knowledge_sync(now={now+1000}) is None
try:s.retry_knowledge_sync(20,{seeded['job']!r})
except PermissionError:pass
else:raise AssertionError('cross-actor recovery permitted')
s.retry_knowledge_sync(19,{seeded['job']!r})
c=s.claim_knowledge_sync(now={now+1001})
assert c['attempts']==1
s.finish_knowledge_sync(c,{{'vector_indexed':True}},now={now+1002})
print(json.dumps({{'job':s.knowledge_sync(19,c['id']),'request':s.request_status(19,'isolated-native-receipt')}}))
""")
            self.assertEqual(final['job']['state'], 'verified')
            self.assertEqual(final['request']['result']['result']['lockVersion'], 2)


if __name__ == '__main__':
    unittest.main()
