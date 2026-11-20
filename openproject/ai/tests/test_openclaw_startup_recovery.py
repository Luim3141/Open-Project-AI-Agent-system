"""Service recovery must not become agent admission or bypass runtime fencing."""
import json,tempfile,unittest,threading
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from automation import openclaw_health as health,engineering_worker as worker


class RuntimeRecoveryTests(unittest.TestCase):
    def test_stopped_distro_is_never_woken_by_health(self):
        calls=[]
        def run(args,**kwargs):
            calls.append(args)
            return SimpleNamespace(returncode=0,stdout='docker-desktop\r\n'.encode('utf-16-le'))
        result=health.collect(run)
        self.assertEqual(result['last_error'],'OPENCLAW_WSL_STOPPED')
        self.assertEqual(calls,[['wsl','--list','--running','--quiet']])

    def test_status_failure_does_not_attempt_active_probe(self):
        calls=[]
        def run(args,**kwargs):
            calls.append(args)
            return SimpleNamespace(returncode=1,stdout=b'')
        self.assertEqual(health.collect(run)['health'],'DOWN')
        self.assertEqual(calls,[['wsl','--list','--running','--quiet']])

    def snapshot(self,ready=False,process='stopped'):
        return {'health':'READY' if ready else 'DOWN','gateway_rpc_ok':ready,'process_state':process,'service_loaded':True}

    def test_health_does_not_claim_ready_when_rpc_or_service_is_down(self):
        def run(args,**kwargs):
            if '--list' in args:return SimpleNamespace(returncode=0,stdout='OpenClawGateway\r\n'.encode('utf-16-le'))
            v={'ok':True} if 'health' in args else {'rpc':{'ok':False},'service':{'loaded':True,'runtime':{'status':'stopped'}}}
            return SimpleNamespace(returncode=0,stdout=json.dumps(v).encode())
        self.assertEqual(health.collect(run)['health'],'DOWN')

    def test_existing_ready_runtime_is_reused_without_start(self):
        with patch.object(health,'collect',return_value=self.snapshot(True,'running')),patch.object(health.subprocess,'run') as run:
            self.assertEqual(health.ensure()['health'],'READY')
            run.assert_not_called()

    def test_start_exit_failure_can_converge_to_rpc_ready_once(self):
        with patch.object(health,'collect',side_effect=[self.snapshot(),self.snapshot(False,'running'),self.snapshot(True,'running')]),patch.object(health.subprocess,'run',return_value=SimpleNamespace(returncode=1)) as run,patch.object(health.time,'sleep'):
            value=health.ensure()
        self.assertEqual(value['health'],'READY');self.assertEqual(run.call_count,1)
        self.assertEqual(run.call_args.args[0][-2:],['gateway','start'])
        self.assertNotIn('agent',run.call_args.args[0])

    def test_running_but_unready_is_not_restarted_or_stopped(self):
        with patch.object(health,'collect',return_value=self.snapshot(False,'running')) as probe,patch.object(health.subprocess,'run') as run,patch.object(health.time,'sleep'):
            self.assertEqual(health.ensure()['health'],'DOWN')
        run.assert_not_called();self.assertLessEqual(probe.call_count,5)

    def test_unavailable_cli_never_runs_blind_start(self):
        with patch.object(health,'collect',return_value={'health':'DOWN','last_error':'OPENCLAW_CLI_UNAVAILABLE_OR_TIMEOUT'}),patch.object(health.subprocess,'run') as run,patch.object(health.time,'sleep'):
            self.assertEqual(health.ensure()['health'],'DOWN')
        run.assert_not_called()

    def test_worker_only_repairs_idle_runtime(self):
        for claim,journal,repair in [(None,None,True),({'id':'fixture'},None,False),(None,object(),False)]:
            with self.subTest(repair=repair),patch.object(worker,'CURRENT_CLAIM',claim),patch.object(worker,'CURRENT_JOURNAL',journal),patch.object(health,'persist') as persist:
                worker.runtime_health();persist.assert_called_once_with(recover=repair,recovery_guard=worker.runtime_idle)

    def test_read_only_persist_does_not_start_service(self):
        with tempfile.TemporaryDirectory() as folder,patch.object(health,'collect',return_value=self.snapshot()),patch.object(health,'ensure') as ensure:
            health.persist(Path(folder));ensure.assert_not_called()

    def test_claim_arriving_during_health_probe_defers_recovery_start(self):
        def probe():
            worker.CURRENT_CLAIM={'id':'fixture-arrived-after-initial-idle-check'}
            return self.snapshot()
        with tempfile.TemporaryDirectory() as folder,patch.dict(worker.os.environ,{'LOCALAPPDATA':folder}),patch.object(worker,'CURRENT_CLAIM',None),patch.object(worker,'CURRENT_JOURNAL',None),patch.object(health,'collect',side_effect=probe),patch.object(health.subprocess,'run',return_value=SimpleNamespace(returncode=0)) as start,patch.object(health.time,'sleep'):
            (Path(folder)/'QLDAPM/openproject-ai/gateway').mkdir(parents=True)
            worker.runtime_health()
            start.assert_not_called()

    def test_fencing_failure_cannot_enter_recovering_worker(self):
        with tempfile.TemporaryDirectory() as folder,patch.dict(worker.os.environ,{'LOCALAPPDATA':folder}),patch.object(worker,'fence_runtime',side_effect=SystemExit('fixture fence failure')),patch.object(worker,'watch') as watch:
            with self.assertRaises(SystemExit):worker.main()
            watch.assert_not_called()

    def test_failed_terminal_fence_retains_claim_until_process_exit(self):
        claim={'id':'fixture'}
        with patch.object(worker,'CURRENT_CLAIM',None),patch('automation.engineering_delivery.run',return_value={}),patch.object(worker,'fence_runtime',side_effect=SystemExit('fixture failed fence')):
            with self.assertRaises(SystemExit):worker.execute(claim)
            self.assertIs(worker.CURRENT_CLAIM,claim)

    def test_runtime_start_guard_and_claim_assignment_are_mutually_exclusive(self):
        entered=threading.Event();ran=threading.Event()
        def execute():
            entered.set();worker.execute({'id':'fixture'})
        with patch.object(worker,'CURRENT_CLAIM',None),patch.object(worker,'CURRENT_JOURNAL',None),patch('automation.engineering_delivery.run',side_effect=lambda *args:ran.set()),patch.object(worker,'fence_runtime'):
            with worker.runtime_idle() as allowed:
                self.assertTrue(allowed)
                thread=threading.Thread(target=execute);thread.start()
                self.assertTrue(entered.wait(2));self.assertFalse(ran.wait(.1))
            thread.join(2);self.assertFalse(thread.is_alive());self.assertTrue(ran.is_set())


if __name__=='__main__':unittest.main()
