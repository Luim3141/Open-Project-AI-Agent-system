import copy
from contextlib import ExitStack
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from automation import integration_pair_release as release


class IntegrationPairReleaseTests(unittest.TestCase):
    def test_config_delta_preserves_lifecycle_and_secrets_without_enabling_events(self):
        before={'project_id':5,'engineering':{'actors':{'18':'AI_SYSTEM_OWNER'},'github_token':'private'},
                'n8n_lifecycle':{'enabled':True,'signing_key':'private'},'n8n_integration':{'base_url':'http://n8n:5678'}}
        saved=copy.deepcopy(before);after=release.next_config(before)
        self.assertEqual(before,saved)
        self.assertEqual(after['n8n_lifecycle'],before['n8n_lifecycle'])
        self.assertEqual(after['engineering']['github_token'],'private')
        self.assertEqual(after['engineering']['github_sync'],{'enabled':False,'actor':18,'interval_seconds':300})
        self.assertFalse(after['n8n_integration']['enabled'])
        self.assertEqual(after['n8n_integration']['base_url'],'http://n8n:5678')

    def test_qualification_rejects_partial_or_stale_scoped_source(self):
        files={key:'a'*64 for key in release.SOURCES}
        proof={'status':'PASS','source_hashes':files,'checks':{'github':True,'events':True,'core':True}}
        release.qualified(proof,files)
        for changed in [dict(proof,status='PARTIAL'),dict(proof,checks={'github':True,'events':False,'core':True}),
                        dict(proof,source_hashes={**files,next(iter(files)):'b'*64})]:
            with self.assertRaises(ValueError):release.qualified(changed,files)

    def test_source_guard_rejects_edit_after_prepare(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'fixture.py').write_text('before')
            expected={'fixture.py':release.sha(root/'fixture.py')}
            release.guard_sources(root,expected)
            (root/'fixture.py').write_text('after')
            with self.assertRaisesRegex(ValueError,'SOURCE_CHANGED'):release.guard_sources(root,expected)

    def test_compose_delta_accepts_image_only_and_rejects_mount_or_environment_change(self):
        before={'image':'old','environment':{'A':'private'},'volumes':['source:/state']}
        release.image_only(before,{**before,'image':'new','pull_policy':'never'})
        for field,value in [('environment',{}),('volumes',[])]:
            with self.assertRaisesRegex(ValueError,'COMPOSE_PARITY'):
                release.image_only(before,{**before,field:value,'image':'new'})

    def test_rollback_attempts_both_images_even_when_first_restore_fails(self):
        calls=[]
        def restore(role,image):
            calls.append((role,image))
            if role=='gateway':raise RuntimeError('fixture')
        with self.assertRaisesRegex(RuntimeError,'ROLLBACK_INCOMPLETE'):
            release.restore_pair(restore,{'gateway':'old-gateway','core':'old-core'})
        self.assertEqual(calls,[('gateway','old-gateway'),('core','old-core')])

    def test_snapshot_uses_sqlite_read_only_integrity_checked_backup_without_network(self):
        with tempfile.TemporaryDirectory() as directory:
            calls=[]
            def run(args,**kwargs):
                calls.append(args)
                return b'fixture-sqlite-bytes'
            with patch.object(release,'run',side_effect=run):release.snapshot_sqlite(Path(directory))
            self.assertEqual(len(calls),2)
            for args in calls:
                self.assertIn('--network',args);self.assertEqual(args[args.index('--network')+1],'none')
                self.assertIn('--volumes-from',args)
                self.assertIn("?mode=ro",args[-1]);self.assertIn('integrity_check',args[-1])
            self.assertEqual((Path(directory)/'gateway.sqlite').read_bytes(),b'fixture-sqlite-bytes')
            self.assertEqual((Path(directory)/'knowledge.sqlite').read_bytes(),b'fixture-sqlite-bytes')

    def test_reuse_core_requires_qualified_exact_image_source_and_baseline(self):
        with tempfile.TemporaryDirectory() as directory:
            previous=Path(directory)/'previous';previous.mkdir();core_keys=[k for k in release.SOURCES if release.SOURCES[k][0]=='core']
            files={k:'a'*64 for k in release.SOURCES};core_image='sha256:'+'b'*64
            saved={'state':'BUILT_NOT_DEPLOYED','source_hashes':files,'images':{'core':core_image},
                   'initial_runtime':{'core':{'image':release.BASE_IMAGES['core']}}}
            (previous/'manifest.json').write_text(json.dumps(saved))
            (previous.parent/'core-candidate-clone-result.json').write_text(json.dumps({'status':'PASS','image':core_image}))
            expected={k:files[k] for k in core_keys}
            with patch.object(release,'runtime_hashes',return_value=expected):
                self.assertEqual(release.reuse_core(previous,files),core_image)
                for change in [dict(saved,state='PREPARED_NOT_BUILT_OR_DEPLOYED'),
                               dict(saved,initial_runtime={'core':{'image':'wrong'}}),
                               dict(saved,source_hashes={**files,core_keys[0]:'c'*64})]:
                    (previous/'manifest.json').write_text(json.dumps(change))
                    with self.assertRaises(ValueError):release.reuse_core(previous,files)
            (previous/'manifest.json').write_text(json.dumps(saved))
            with patch.object(release,'runtime_hashes',return_value={core_keys[0]:'c'*64}):
                with self.assertRaises(ValueError):release.reuse_core(previous,files)
            (previous.parent/'core-candidate-clone-result.json').write_text(json.dumps({'status':'PASS','image':'sha256:'+'d'*64}))
            with patch.object(release,'runtime_hashes',return_value=expected):
                with self.assertRaises(ValueError):release.reuse_core(previous,files)

    def test_exact_scope_excludes_other_gateway_modules_and_uses_offline_copy_only_build(self):
        self.assertEqual(len(release.SOURCES),9)
        dockerfile=release.dockerfile('gateway',release.BASE_IMAGES['gateway'],'a'*32)
        self.assertNotIn('RUN ',dockerfile)
        self.assertNotIn('COPY gateway/ /app',dockerfile)
        self.assertIn('gateway/integration_events.py /app/gateway/integration_events.py',dockerfile)
        self.assertNotIn('native_incremental.py',dockerfile)
        self.assertIn('FROM qldapm-local-base:integration-3c06559033eb-'+'a'*32,dockerfile)

    def test_rollout_core_failure_restores_both_images_and_all_config_bytes(self):
        with tempfile.TemporaryDirectory() as directory,ExitStack() as stack:
            root=Path(directory);runtime=root/'QLDAPM';bundle=root/'bundle';bundle.mkdir()
            config=runtime/'openproject-ai/gateway/config.json';config.parent.mkdir(parents=True)
            core=runtime/'openproject';core.mkdir()
            config.write_text(json.dumps({'project_id':5,'n8n_lifecycle':{'enabled':True,'signing_key':'private'}}))
            (runtime/'openproject-ai/.env').write_text('AI_IMAGE=old\nKEEP=private\n')
            (core/'.env').write_text('KEEP=private\n')
            (core/'ui-bridge.yml').write_text(json.dumps({'services':{'web':{'image':'old'}}}))
            (runtime/'openproject-ai/image-lock.json').write_text(json.dumps({'AI_IMAGE':'old','CORE_IMAGE':'old','OTHER':'kept'}))
            paths=[config,runtime/'openproject-ai/.env',core/'.env',core/'ui-bridge.yml',runtime/'openproject-ai/image-lock.json']
            originals={path:path.read_bytes() for path in paths}
            files={key:'a'*64 for key in release.SOURCES};images={'gateway':'sha256:'+'b'*64,'core':'sha256:'+'c'*64}
            manifest={'images':images,'source_hashes':files,'protected_inputs':{str(path):'ignored' for path in paths},
                      'initial_runtime':{role:{'compose':['docker','compose','-p',role]} for role in release.TARGETS}}
            proof=root/'qualification.json';proof.write_text(json.dumps({'status':'PASS','checks':{'github':True,'events':True,'core':True},'source_hashes':files}))
            calls=[]
            def run(args,**kwargs):
                calls.append(args)
                if 'config' in args:return json.dumps({'services':{'gateway':{'image':'old'},'web':{'image':'old'}}}).encode()
                return b''
            def health(role,image):
                if role=='core' and image==images['core']:raise RuntimeError('injected-core-health-failure')
            stack.enter_context(patch.dict(os.environ,{'LOCALAPPDATA':str(root)}))
            stack.enter_context(patch.object(release,'load_guarded',return_value=(bundle,manifest)))
            stack.enter_context(patch.object(release,'runtime_hashes',side_effect=lambda role,image=None:{key:value for key,value in files.items() if release.SOURCES[key][0]==role}))
            stack.enter_context(patch.object(release,'queue',return_value={'active':0,'mode':'OFF'}))
            stack.enter_context(patch.object(release,'powershell',return_value='Running'))
            stack.enter_context(patch.object(release,'stop_worker'))
            def backup(private):
                self.assertEqual([a[-1] for a in calls if a[:2]==['docker','stop']],
                                 [release.TARGETS[role][0] for role in release.TARGETS])
            stack.enter_context(patch.object(release,'snapshot_sqlite',side_effect=backup))
            stack.enter_context(patch.object(release,'healthy',side_effect=health))
            stack.enter_context(patch.object(release,'run',side_effect=run))
            with self.assertRaisesRegex(RuntimeError,'injected-core-health-failure'):release.rollout(bundle,proof)
            self.assertEqual({path:path.read_bytes() for path in paths},originals)
            restored=[]
            for args in calls:
                if 'up' in args:
                    override=Path(args[args.index('-f')+1]);spec=json.loads(override.read_text());service=next(iter(spec['services']))
                    restored.append((service,spec['services'][service]['image']))
            self.assertEqual(restored[-2:],[('gateway',release.BASE_IMAGES['gateway']),('web',release.BASE_IMAGES['core'])])


if __name__=='__main__':unittest.main()
