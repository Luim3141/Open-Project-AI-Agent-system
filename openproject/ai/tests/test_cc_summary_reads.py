import tempfile,time,unittest
from pathlib import Path
from types import SimpleNamespace
from gateway.store import Store,canonical
from gateway.engineering_observability import describe_run,describe_runs


class SummaryReadTests(unittest.TestCase):
    def test_shared_read_connection_keeps_each_runs_own_evidence(self):
        with tempfile.TemporaryDirectory() as folder:
            service=SimpleNamespace(store=Store(Path(folder)),config={});runs=[]
            with service.store.connect() as db:
                for identifier,cap in [('first',4),('second',8)]:
                    payload={'definition':{'title':identifier},'budget':{'attempt_calls':cap}}
                    db.execute("INSERT INTO ai_queue(id,actor,payload,state,created,kind) VALUES(?,20,?,'finished',?,'agent')",(identifier,canonical(payload),time.time()-100))
                    runs.append({'id':identifier,'native_id':394,'result':{'status':'succeeded'},'created_at':time.time()-100,'queue_state':'finished'})
                    db.execute('INSERT INTO gemini_call_receipts VALUES(?,?,?,?,?)',(identifier,'fixture',20,identifier,canonical({'phase':'generateContent','agent':'dev','call_cap':cap,'at':time.time()-100})))
                db.execute('INSERT INTO gemini_call_receipts VALUES(?,?,?,?,?)',('foreign','fixture',21,'first',canonical({'phase':'generateContent','agent':'qa','call_cap':99,'at':time.time()-50})))
            separate=[describe_run(service,run) for run in runs]
            with service.store.connect() as db:shared=[describe_run(service,run,connection=db) for run in runs]
            self.assertEqual(shared,separate)
            self.assertEqual(describe_runs(service,runs),separate)
            self.assertEqual([r['title'] for r in shared],['first','second'])
            self.assertEqual([r['budget']['call_cap'] for r in shared],[4,8])
