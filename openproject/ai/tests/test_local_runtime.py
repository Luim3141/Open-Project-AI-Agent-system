"""Compose boundary checks only: no Docker engine, real secrets or runtime mutation."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from contextlib import nullcontext

ROOT = Path(__file__).resolve().parents[1]


class LocalRuntimeTests(unittest.TestCase):
    def test_gateway_upgrade_never_selects_any_other_service(self):
        from provision_local_stage import selected_services, provision_locked
        self.assertEqual(selected_services(False, False, True, 'backup', None, gateway_only=True), ['staging-gateway'])
        for changes in ({}, {'gateway_image': 'image', 'core_image': 'core'},
                        {'gateway_image': 'image', 'backup_image': 'backup'},
                        {'gateway_image': 'image', 'enable_quick': True},
                        {'gateway_image': 'image', 'enable_radmin': True},
                        {'gateway_image': 'image', 'application_only': True}):
            with self.subTest(changes=changes), self.assertRaisesRegex(ValueError, 'GATEWAY_ONLY_REQUIRES'):
                provision_locked(gateway_only=True, **changes)

    def test_application_upgrade_never_selects_tunnel_database_or_n8n(self):
        from provision_local_stage import selected_services,provision_locked
        self.assertEqual(selected_services(True,True,True,'backup','core'),['staging-web','staging-gateway'])
        self.assertEqual(selected_services(False,False,True,'backup','core'),
            ['quick-tunnel','staging-web','staging-gateway','n8n','n8n-editor','local-backup'])
        for changes in ({},{'gateway_image':'gateway'},{'core_image':'core'},
                        {'gateway_image':'gateway','core_image':'core','enable_quick':True}):
            with self.assertRaisesRegex(ValueError,'APPLICATION_ONLY_REQUIRES'):
                provision_locked(application_only=True,**changes)

    def test_native_report_override_requires_immutable_qualified_lineage_and_fixed_scope(self):
        from provision_local_stage import daily_report_core
        previous = {'RootFS': {'Layers': ['audited-native']}}
        candidate = {'Id': 'sha256:' + 'e' * 64, 'RootFS': {'Layers': ['audited-native', 'views-only']},
                     'Config': {'Labels': {'org.qldapm.report': 'actor-daily-read-only'}}}
        self.assertEqual(daily_report_core(candidate, previous), candidate['Id'])
        for changed in ({**candidate, 'Id': 'mutable:tag'}, {**candidate, 'Config': {'Labels': {}}},
                        {**candidate, 'RootFS': {'Layers': ['different-native']}}):
            with self.assertRaises(ValueError):
                daily_report_core(changed, previous)

    def test_backup_retains_exact_audited_base_when_native_adds_qualified_report_layers(self):
        from provision_local_stage import backup_base
        audited = {'RootFS': {'Layers': ['audited-native']}}
        core = {'RootFS': {'Layers': ['audited-native', 'qualified-ui']}}
        built = {'Config': {'Labels': {'org.qldapm.operator': 'local-backup'}},
                 'RootFS': {'Layers': ['audited-native', 'python-backup-cli']}}
        backup_base(built, core, audited)
        for changed in ({**built, 'Config': {'Labels': {}}}, {**built, 'RootFS': {'Layers': ['unrelated']}}):
            with self.assertRaises(ValueError):
                backup_base(changed, core, audited)
        with self.assertRaises(ValueError):
            backup_base(built, {'RootFS': {'Layers': ['different-native']}}, audited)
    def test_n8n_unused_external_catalog_disabled_and_owner_backup_mount_readonly(self):
        self.assertIn('N8N_DISABLED_MODULES: mcp-registry', (ROOT / 'local-runtime.stage.yml').read_text())
        self.assertIn('${AI_RUNTIME}/operator/n8n-owner:/n8n-owner:ro', (ROOT / 'backup.stage.yml').read_text())

    def test_enabled_provider_requires_saved_free_only_proof_without_network_probe(self):
        from provision_local_stage import check_provider_configuration
        with tempfile.TemporaryDirectory() as directory, patch('provision_local_stage.command') as command:
            root = Path(directory)
            for invalid in (None, 1, 'true'):
                (root / 'gemini.json').write_text(json.dumps({'enabled': invalid}))
                with self.assertRaisesRegex(ValueError, 'BOOLEAN'):
                    check_provider_configuration(root)
            (root / 'gemini.json').write_text('{"enabled":false}')
            self.assertFalse(check_provider_configuration(root))
            command.assert_not_called()
            (root / 'gemini.json').write_text('{"enabled":true}')
            self.assertTrue(check_provider_configuration(root))
            self.assertIn('g.settings()', command.call_args.args[0][-1])
            self.assertNotIn('g.run(', command.call_args.args[0][-1])
            command.side_effect = RuntimeError('proof denied')
            with self.assertRaisesRegex(RuntimeError, 'proof denied'):
                check_provider_configuration(root)

    def test_gateway_upgrade_requires_immutable_same_base_and_free_only_policy(self):
        from provision_local_stage import free_only_gateway
        good = {'Id': 'sha256:' + 'a' * 64, 'Config': {'Labels': {'org.qldapm.policy': 'FREE_ONLY'}},
                'RootFS': {'Layers': ['audited-sdk', 'new-source']}}
        previous = {'RootFS': {'Layers': ['audited-sdk']}}
        self.assertEqual(free_only_gateway(good, previous), good['Id'])
        for bad in ({**good, 'Id': 'mutable:tag'}, {**good, 'Config': {'Labels': {}}},
                    {**good, 'RootFS': {'Layers': ['different-runtime']}}):
            with self.assertRaisesRegex(ValueError, 'BASE_OR_POLICY_MISMATCH'):
                free_only_gateway(bad, previous)

    def test_key_presence_never_claims_google_ready(self):
        from local_runtime import provider_status
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory)
            (state / 'gemini.json').write_text('{"enabled":false}')
            self.assertEqual(provider_status(state), 'BLOCKED_KEY')
            (state / 'gemini.key').write_text('truncated')
            self.assertEqual(provider_status(state), 'BLOCKED_KEY')
            (state / 'gemini.key').write_text('fixture-key-not-a-real-secret' * 2)
            self.assertEqual(provider_status(state), 'CONFIGURED_DISABLED')
            (state / 'gemini.json').write_text('{"enabled":true}')
            self.assertEqual(provider_status(state), 'READINESS_NOT_VERIFIED')

    def test_operator_stop_refuses_active_or_unknown_job_before_any_stop(self):
        import local_runtime
        info = {'Image': 'x', 'State': {'Running': True}, 'Config': {'Labels': {}}}
        with patch.object(local_runtime, 'operator_lease', return_value=nullcontext()), \
                patch.object(local_runtime, 'expected_images', return_value={}), \
                patch.object(local_runtime, 'inspect', return_value=info), \
                patch.object(local_runtime, 'check_owned'), \
                patch.object(local_runtime, 'command', return_value=b'1') as command:
            with self.assertRaisesRegex(ValueError, 'ACTIVE_OR_UNKNOWN_JOB_BLOCKS_STOP'):
                local_runtime.stop()
            self.assertEqual(command.call_count, 1)
            self.assertEqual(command.call_args.args[0][:2], ['docker', 'exec'])

    def test_operator_denies_wrong_project_or_service_or_image(self):
        from local_runtime import check_owned, name
        good = {'Image': 'expected', 'Config': {'Labels': {
            'com.docker.compose.project': 'qldapm-ai-stage', 'com.docker.compose.service': 'n8n'}}}
        check_owned('n8n', good, {'n8n': 'expected'})
        for field, bad in [('com.docker.compose.project', 'qldapm-openproject'),
                           ('com.docker.compose.service', 'db')]:
            candidate = {'Image': 'expected', 'Config': {'Labels': {**good['Config']['Labels'], field: bad}}}
            with self.assertRaisesRegex(ValueError, 'MISMATCH'):
                check_owned('n8n', candidate, {'n8n': 'expected'})
        with self.assertRaisesRegex(ValueError, 'MISMATCH'):
            check_owned('n8n', good, {'n8n': 'different'})
        with self.assertRaisesRegex(ValueError, 'DENIED'):
            name('main')

    def test_health_wait_rejects_exit_and_timeout(self):
        from local_runtime import wait_healthy
        with patch('local_runtime.inspect', return_value={'State': {'Running': False}}):
            with self.assertRaisesRegex(RuntimeError, 'SERVICE_EXITED'):
                wait_healthy('n8n')
        with self.assertRaisesRegex(RuntimeError, 'HEALTH_TIMEOUT'):
            wait_healthy('n8n', seconds=0)

    def test_old_lock_accepts_db_only_from_matching_observed_baseline(self):
        from provision_local_stage import pinned_images
        infos = {s: {'Image': 'sha256:' + letter * 64, 'State': {'Running': True},
                     'Config': {'Labels': {'com.docker.compose.project': 'qldapm-ai-stage'}}}
                 for s, letter in [('db', 'c'), ('staging-web', 'b'), ('staging-gateway', 'a')]}
        lock = {s: infos[s]['Image'] for s in ('staging-web', 'staging-gateway')}
        self.assertEqual(pinned_images(infos, lock, {'db': infos['db']['Image']})['db'], infos['db']['Image'])
        for baseline in ({}, {'db': 'sha256:' + 'd' * 64}):
            with self.assertRaisesRegex(ValueError, 'STAGE_IMAGE_OR_OWNERSHIP_MISMATCH'):
                pinned_images(infos, lock, baseline)
        infos['db']['Config']['Labels']['com.docker.compose.project'] = 'qldapm-openproject'
        with self.assertRaisesRegex(ValueError, 'STAGE_IMAGE_OR_OWNERSHIP_MISMATCH'):
            pinned_images(infos, lock, {'db': infos['db']['Image']})

    def configuration(self, include_radmin=False, include_backup=False, include_quick=False, **overrides):
        env = {**os.environ, 'AI_RUNTIME': ROOT.as_posix(), 'AI_IMAGE': 'sha256:' + 'a' * 64,
               'CORE_IMAGE': 'sha256:' + 'b' * 64, 'POSTGRES_IMAGE': 'sha256:' + 'c' * 64,
               'POSTGRES_PASSWORD': 'fixture-only', 'SECRET_KEY_BASE': 'fixture-only',
               'QLDAPM_N8N_KEY_PATH': (ROOT / 'fixture-secret-not-read.key').as_posix(), **overrides}
        if include_backup:
            env['LOCAL_BACKUP_IMAGE'] = 'sha256:' + 'd' * 64
        argv = ['docker', 'compose', '--project-name', 'qldapm-ai-stage', '--env-file', os.devnull]
        for name in ('stage.yml', 'deep-ai.stage.yml', 'gemini-free.stage.yml', 'local-runtime.stage.yml'):
            argv += ['-f', str(ROOT / name)]
        if include_radmin:
            argv += ['-f', str(ROOT / 'radmin.stage.yml')]
        if include_quick:
            argv += ['-f', str(ROOT / 'quick.stage.yml')]
        if include_backup:
            argv += ['-f', str(ROOT / 'backup.stage.yml')]
        return subprocess.run(argv + ['config', '--format', 'json'], env=env, capture_output=True, text=True, timeout=20)

    def test_quick_tunnel_targets_only_native_web_and_keeps_metadata_private(self):
        result = self.configuration(include_quick=True, include_backup=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        services = json.loads(result.stdout)['services']
        tunnel = services['quick-tunnel']
        self.assertFalse(tunnel.get('ports'))
        self.assertEqual(set(tunnel['networks']), {'stage-front'})
        self.assertIsNone(tunnel.get('command'))
        self.assertIn('http://staging-web:8080',(ROOT/'automation/quick_tunnel_supervisor.sh').read_text())
        self.assertNotIn('gateway:8090',(ROOT/'automation/quick_tunnel_supervisor.sh').read_text())
        self.assertEqual(tunnel['restart'], 'unless-stopped')
        self.assertRegex(tunnel['image'], r'^sha256:[a-f0-9]{64}$')
        self.assertEqual(services['staging-web']['command'], ['ruby', '/qldapm-operator/quick_tunnel_web.rb'])
        self.assertTrue(all(p['host_ip'] == '127.0.0.1' for p in services['n8n-editor']['ports']))
        self.assertEqual({p['published'] for p in services['n8n-editor']['ports']}, {'5678', '18090'})
        self.assertTrue(all('docker.sock' not in m['target'] for s in services.values() for m in s.get('volumes', [])))

    def test_backup_operator_has_only_readonly_sources_and_no_business_or_docker_interface(self):
        result = self.configuration(include_radmin=True, include_backup=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        services = json.loads(result.stdout)['services']
        backup = services['local-backup']
        self.assertFalse(backup.get('ports'))
        self.assertEqual(set(backup['networks']), {'stage'})
        self.assertEqual(backup['environment']['PGOPTIONS'], '-c default_transaction_read_only=on -c statement_timeout=120000')
        self.assertTrue(backup['read_only'])
        for mount in backup['volumes']:
            self.assertNotIn('docker.sock', mount['target'])
            if mount['target'] != '/backup':
                self.assertTrue(mount['read_only'])
        self.assertTrue(any(m['target'] == '/provider-policy' and m['read_only'] for m in backup['volumes']))
        self.assertNotIn('local-backup', services['n8n']['networks'])

    def test_radmin_overlay_keeps_native_https_and_only_vpn_publish(self):
        result = self.configuration(include_radmin=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        services = json.loads(result.stdout)['services']
        self.assertEqual(services['staging-web']['environment']['OPENPROJECT_HTTPS'], 'true')
        self.assertEqual(services['staging-web']['environment']['OPENPROJECT_HOST__NAME'], '26.88.211.101')
        proxy = services['radmin-proxy']
        self.assertEqual(len(proxy['ports']), 1)
        self.assertEqual(proxy['ports'][0]['host_ip'], '26.88.211.101')
        self.assertEqual(proxy['ports'][0]['published'], '443')
        self.assertEqual(set(proxy['networks']), {'stage-front'})
        self.assertEqual(services['staging-gateway']['ports'][0]['host_ip'], '127.0.0.1')
        self.assertFalse(services['n8n'].get('ports'))

    def test_configuration_preserves_native_boundary_and_pins_n8n(self):
        result = self.configuration()
        self.assertEqual(result.returncode, 0, result.stderr)
        config = json.loads(result.stdout)
        services = config['services']
        self.assertEqual(set(services), {'db', 'seeder', 'staging-web', 'staging-gateway', 'n8n', 'n8n-editor'})
        n8n = services['n8n']
        self.assertRegex(n8n['image'], r'^docker\.n8n\.io/n8nio/n8n:2\.43\.6@sha256:[a-f0-9]{64}$')
        self.assertFalse(n8n.get('ports'))
        self.assertEqual(services['n8n-editor']['ports'][0]['host_ip'], '127.0.0.1')
        self.assertEqual(set(services['n8n-editor']['networks']), {'automation', 'editor'})
        self.assertEqual(services['n8n-editor']['cap_add'], ['NET_BIND_SERVICE'])
        self.assertEqual(services['n8n-editor']['cap_drop'], ['ALL'])
        self.assertEqual(set(n8n['networks']), {'automation'})
        self.assertTrue(config['networks']['automation']['internal'])
        self.assertEqual(n8n['restart'], 'unless-stopped')
        self.assertTrue(n8n['read_only'])
        self.assertEqual(n8n['environment']['N8N_ENCRYPTION_KEY_FILE'], '/run/secrets/n8n_encryption_key')
        self.assertNotIn('N8N_ENCRYPTION_KEY', n8n['environment'])
        self.assertEqual(n8n['environment']['N8N_BLOCK_ENV_ACCESS_IN_NODE'], 'true')
        for service in services.values():
            self.assertFalse(service.get('privileged', False))
            self.assertFalse(any('docker.sock' in v.get('target', '') for v in service.get('volumes', [])))
        self.assertEqual(services['staging-gateway']['image'], 'sha256:' + 'a' * 64)
        self.assertEqual(services['staging-web']['image'], 'sha256:' + 'b' * 64)
        self.assertIn('stage-front', services['staging-gateway']['networks'])
        self.assertIn('automation', services['staging-gateway']['networks'])
        self.assertIn("headers={'Host':'gateway:8090'}", services['staging-gateway']['healthcheck']['test'][-1])
        self.assertTrue(any(v['target'] == '/qldapm-policy/free-tier-proof.json' and v['read_only']
                            for v in services['staging-gateway']['volumes']))

    def test_missing_key_path_fails_configuration_without_provisioning(self):
        result = self.configuration(QLDAPM_N8N_KEY_PATH='')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Prepare private persistent n8n key once', result.stderr)

    def test_operator_repair_idempotency_and_no_business_mutation(self):
        import local_runtime
        with patch.object(local_runtime, 'operator_lease', return_value=nullcontext()), \
                patch.object(local_runtime, 'expected_images', return_value={s: 'sha256:' + 'a'*64 for s in local_runtime.SERVICES}), \
                patch.object(local_runtime, 'inspect', return_value={'State': {'Running': True, 'Health': {'Status': 'healthy'}}, 'Config': {'Labels': {'com.docker.compose.project': 'qldapm-ai-stage', 'com.docker.compose.service': 'db'}}, 'Image': 'sha256:' + 'a'*64}), \
                patch.object(local_runtime, 'check_owned'), \
                patch.object(local_runtime, 'wait_healthy'), \
                patch.object(local_runtime, 'provision_locked', return_value={'status': 'ok'}), \
                patch.object(local_runtime, 'status', return_value={'all_healthy': True}):
            # Verify repair calls start idempotently
            res = local_runtime.start()
            self.assertTrue(res['status']['all_healthy'])
            self.assertFalse(res['health_pending'])


if __name__ == '__main__':
    unittest.main()

