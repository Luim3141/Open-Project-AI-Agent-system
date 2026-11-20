"""Main-only operator boundary; fixture Docker runner never contacts Main or Staging."""
import copy
import unittest
from unittest.mock import patch


class MainOperationsTests(unittest.TestCase):
    def fixture(self):
        from automation.main_operations import TARGETS
        rows={name:{'Name':'/'+name,'Id':format(i+1,'x')*64,'Image':'sha256:'+'a'*64,
              'Config':{'Labels':{'com.docker.compose.project':project,'com.docker.compose.service':service} if project else {}},
              'State':{'Status':'running','Health':{'Status':'healthy'}}}
              for i,(name,(project,service)) in enumerate(TARGETS.items())}
        manifest={'version':1,'project_id':5,'containers':{name:{'id':r['Id'],'image':r['Image']} for name,r in rows.items()}}
        return rows,manifest

    def test_manifest_must_name_all_exact_main_identities_before_any_action(self):
        from automation.main_operations import verify
        rows,manifest=self.fixture()
        with patch('automation.main_operations.inspect',side_effect=lambda name:rows[name]):
            self.assertEqual(set(verify(manifest)),set(rows))
            for change in ['extra','name','id','image','label']:
                altered=copy.deepcopy(manifest);current=copy.deepcopy(rows)
                if change=='extra':altered['containers']['qldapm-ai-stage-db-1']={'id':'x','image':'x'}
                if change=='name':current[next(iter(current))]['Name']='/qldapm-ai-stage-gateway-1'
                if change=='id':current[next(iter(current))]['Id']='b'*64
                if change=='image':current[next(iter(current))]['Image']='sha256:'+'b'*64
                if change=='label':current[next(iter(current))]['Config']['Labels']['com.docker.compose.project']='qldapm-ai-stage'
                with patch('automation.main_operations.inspect',side_effect=lambda name:current[name]):
                    with self.assertRaises(ValueError):verify(altered)

    def test_plan_has_fixed_dependencies_and_refuses_unrecognized_operation(self):
        from automation.main_operations import plan
        rows,manifest=self.fixture()
        with patch('automation.main_operations.inspect',side_effect=lambda name:rows[name]):
            start=plan('start',manifest);stop=plan('stop',manifest)
            self.assertEqual(start['containers'][0],'qldapm-openproject-db-1')
            self.assertEqual(stop['containers'][-1],'qldapm-openproject-db-1')
            self.assertEqual(set(start['containers']),set(stop['containers']))
            self.assertFalse(start['staging_operations'])
            with self.assertRaises(ValueError):plan('restart-docker',manifest)

    def test_stop_refuses_active_or_new_unknown_work_and_never_force_removes(self):
        from automation.main_operations import apply
        rows,manifest=self.fixture()
        with patch('automation.main_operations.inspect',side_effect=lambda name:rows[name]),patch('automation.main_operations.command') as cmd:
            with patch('automation.main_operations.work_state',return_value={'active':1,'unknown_sha256':'known'}):
                with self.assertRaises(ValueError):apply('stop',manifest)
            with patch('automation.main_operations.work_state',return_value={'active':0,'unknown_sha256':'new'}):
                manifest['unknown_sha256']='known'
                with self.assertRaises(ValueError):apply('stop',manifest)
            cmd.assert_not_called()

    def test_graceful_stop_and_start_only_call_fixed_main_names_and_private_backup_path(self):
        from automation.main_operations import apply,private_path
        from pathlib import Path
        import tempfile
        rows,manifest=self.fixture();manifest['unknown_sha256']='known'
        with patch('automation.main_operations.inspect',side_effect=lambda name:rows[name]),patch('automation.main_operations.command') as cmd,patch('automation.main_operations.work_state',return_value={'active':0,'unknown_sha256':'known'}):
            stopped=apply('stop',manifest)
            self.assertEqual(set(stopped['changed']),set(rows))
            self.assertTrue(all(c.args[:3]==('stop','--time','60') and c.args[3] in rows for c in cmd.call_args_list))
            cmd.reset_mock();self.assertEqual(apply('start',manifest)['changed'],[]);cmd.assert_not_called()
        with tempfile.TemporaryDirectory() as folder,patch('automation.main_operations.PRIVATE_ROOT',Path(folder)):
            self.assertEqual(private_path(Path(folder)/'new'),Path(folder).resolve()/'new')
            for path in [Path(folder),Path(folder).parent/'outside']:
                with self.assertRaises(ValueError):private_path(path)

    def test_cold_start_harness_waits_for_each_pinned_dependency(self):
        from automation.main_operations import apply
        rows,manifest=self.fixture()
        for row in rows.values():row['State']['Status']='exited'
        def start(*args,**kwargs):
            self.assertEqual(args[0],'start');rows[args[1]]['State']['Status']='running';return b''
        with patch('automation.main_operations.inspect',side_effect=lambda name:rows[name]),patch('automation.main_operations.command',side_effect=start) as cmd:
            result=apply('start',manifest)
            self.assertEqual(result['changed'],list(rows));self.assertEqual(len(cmd.call_args_list),10)
