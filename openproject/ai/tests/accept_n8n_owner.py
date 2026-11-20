"""Actual pinned n8n bootstrap/restart on a private backup clone, never the primary volume."""
import argparse
from contextlib import ExitStack
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import secrets
import sqlite3
import subprocess
import sys
import tarfile
import time
import traceback
from unittest.mock import patch
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from n8n_owner import IMAGE, LocalN8n, check_primary_backup, private_directory, provision
from local_backup import archive, sqlite_snapshot
from gateway.automation import signing_key

EDITOR_IMAGE = "sha256:d8542f48d34a9cf4e4c11a478865229840e87e4c96ea3f439101f31a5d35f75f"

def docker(*args):
    timeout = 600 if '/qa/container_daily_scope.py' in args else 90
    result = subprocess.run(["docker", *args], capture_output=True, timeout=timeout)
    if args[0] == "exec" and "n8n" in args and getattr(docker, "private_logs", None):
        (docker.private_logs / (str(time.time_ns()) + '.log')).write_bytes(result.stdout + result.stderr)
    if result.returncode:
        if getattr(docker, 'private_logs', None):
            (docker.private_logs / ('failed-' + str(time.time_ns()) + '.log')).write_bytes(result.stdout + result.stderr)
        raise RuntimeError("CLONE_DOCKER_OPERATION_FAILED: " + args[0])
    return result.stdout.decode().strip()


def ready():
    client = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    deadline = time.monotonic() + 150
    while time.monotonic() < deadline:
        try:
            with client.open("http://localhost:25678/healthz/readiness", timeout=2) as response:
                if response.status == 200:
                    return
        except (OSError, urllib.error.URLError):
            pass
        time.sleep(2)
    raise RuntimeError("CLONE_NOT_READY")


def fixture(container, secret=None):
    if secret:
        objects = {
            "credentials": [{"id": "p04EncryptedFixture", "name": "P04 synthetic credential", "type": "httpHeaderAuth",
                              "data": {"name": "X-P04-Fixture", "value": secret}}],
            "workflow": [{"id": "p04WorkflowFixture", "name": "P04 inactive persistence fixture", "active": False,
                          "nodes": [{"id": "manual", "name": "Manual", "type": "n8n-nodes-base.manualTrigger",
                                     "typeVersion": 1, "position": [0, 0], "parameters": {}}],
                          "connections": {}, "settings": {"executionOrder": "v1"}}]}
        for kind, document in objects.items():
            path = "/tmp/p04-input-" + kind + ".json"
            process = subprocess.run(["docker", "exec", "-i", container, "node", "-e",
                                      "require('fs').writeFileSync(process.argv[1],require('fs').readFileSync(0))", path],
                                     input=json.dumps(document).encode(), capture_output=True, timeout=20)
            assert process.returncode == 0
            docker("exec", container, "n8n", "import:" + kind, "--input=" + path)
        return
    docker("exec", container, "n8n", "export:credentials", "--all", "--decrypted", "--output=/tmp/p04-credentials.json")
    docker("exec", container, "n8n", "export:workflow", "--all", "--output=/tmp/p04-workflow.json")
    return (json.loads(docker("exec", container, "cat", "/tmp/p04-credentials.json")),
            json.loads(docker("exec", container, "cat", "/tmp/p04-workflow.json")))


def accept(backup, output, persistence=False, workflow=False, daily_image=None, daily_core=None, json_recovery=None, errors=False):
    check_primary_backup(backup)
    events = []
    def checkpoint(phase):
        events.append({'phase': phase, 'at': time.time()})
        output.write_text(json.dumps({'passed': None, 'state': 'RUNNING', 'events': events}, indent=2))
        print('Clone checkpoint: ' + phase, flush=True)
    if output.exists():
        raise ValueError('NEW_ACCEPTANCE_OUTPUT_REQUIRED')
    checkpoint('backup_verified')
    if json_recovery and (persistence or not workflow or not daily_image):
        raise ValueError('JSON_RECOVERY_REQUIRES_EMPTY_INSTANCE_AND_FIXED_WORKFLOWS')
    if errors and (not persistence or not daily_image or json_recovery):
        raise ValueError('ERROR_ACCEPTANCE_REQUIRES_QUALIFIED_PERSISTENT_DAILY_CLONE')
    if daily_image and (not workflow or not (persistence or json_recovery) or not daily_core or not re.fullmatch(r'sha256:[a-f0-9]{64}', daily_image)):
        raise ValueError('DAILY_ACCEPTANCE_REQUIRES_PINNED_WORKFLOW_RESTORE')
    if daily_image:
        candidate = json.loads(docker('image', 'inspect', daily_image))[0]
        baseline = json.loads(docker('image', 'inspect', 'sha256:58937bdd43a4aa0c23d0a722e71968856c3e171f9b904704d09e062ecd6c2d7b'))[0]
        layers = baseline['RootFS']['Layers']
        assert candidate['Config']['Labels'].get('org.qldapm.policy') == 'FREE_ONLY' and candidate['RootFS']['Layers'][:len(layers)] == layers
    root = Path(os.environ["LOCALAPPDATA"]) / "QLDAPM/openproject-ai/operator" / ("n8n-owner-clone-" + str(time.time_ns()))
    private_directory(root)
    docker.private_logs = root / 'cli-logs'
    docker.private_logs.mkdir()
    data = root / "data"
    data.mkdir()
    if not json_recovery:
        with tarfile.open(backup / "config/n8n-files.tar") as incoming:
            incoming.extractall(data, filter="data")
        shutil.copyfile(backup / "config/n8n.sqlite", data / "database.sqlite")
    shutil.copyfile(backup / "config/n8n.key", root / "encryption.key")
    original_key = hashlib.sha256((root / "encryption.key").read_bytes()).digest()
    primary = json.loads(docker("inspect", "qldapm-ai-stage-n8n-1"))[0]
    name = "qldapm-p04-owner-clone-" + str(time.time_ns())
    label = "qldapm.acceptance.p04-owner=" + name
    docker("network", "create", "--internal", "--label", label, name)
    core_stack = ExitStack()
    try:
        if json_recovery:
            from n8n_workflow_export import verify_bundle
            exported = verify_bundle(json_recovery)
            core_stack.enter_context(patch('n8n_status_workflow.SOURCE', exported['qldapmManualStatus']))
            core_stack.enter_context(patch('n8n_status_workflow.DAILY_SOURCE', exported['qldapmDailyBrief']))
            if 'qldapmWorkflowErrors' in exported:
                core_stack.enter_context(patch('n8n_status_workflow.ERROR_SOURCE', exported['qldapmWorkflowErrors']))
        args = ["run", "-d", "--name", name, "--label", label, "--network", name, "--network-alias", "n8n",
                "--read-only", "--cap-drop", "ALL",
                "--security-opt", "no-new-privileges:true", "--memory", "512m", "--pids-limit", "128",
                "--tmpfs", "/tmp:size=64m,mode=1777", "--tmpfs", "/home/node/.cache:size=128m,uid=1000,gid=1000,mode=0700",
                "--mount", "type=bind,src=" + str(data) + ",dst=/home/node/.n8n",
                "--mount", "type=bind,src=" + str(root / "encryption.key") + ",dst=/run/secrets/n8n_encryption_key,readonly"]
        names = {"TZ", "GENERIC_TIMEZONE", "N8N_HOST", "N8N_EDITOR_BASE_URL", "N8N_ENCRYPTION_KEY_FILE",
                 "N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS", "N8N_BLOCK_ENV_ACCESS_IN_NODE", "N8N_BLOCK_FILE_ACCESS_TO_N8N_FILES",
                 "N8N_COMMUNITY_PACKAGES_ENABLED", "N8N_DIAGNOSTICS_ENABLED", "N8N_VERSION_NOTIFICATIONS_ENABLED",
                 "N8N_TEMPLATES_ENABLED", "NODES_EXCLUDE", "NODE_OPTIONS", "N8N_DISABLED_MODULES"}
        for value in primary["Config"]["Env"]:
            if value.split("=", 1)[0] in names:
                args.extend(["--env", value])
        docker(*args, IMAGE)
        caddyfile = Path(__file__).resolve().parents[1] / "automation/Caddyfile"
        docker("create", "--name", name + "-editor", "--label", label, "--network", "bridge",
               "--publish", "127.0.0.1:25678:5678", "--read-only", "--user", "1000:1000",
               "--cap-drop", "ALL", "--cap-add", "NET_BIND_SERVICE", "--security-opt", "no-new-privileges:true",
               "--memory", "64m", "--pids-limit", "64", "--tmpfs", "/data:size=8m,uid=1000,gid=1000,mode=0700",
               "--tmpfs", "/config:size=8m,uid=1000,gid=1000,mode=0700", "--mount",
               "type=bind,src=" + str(caddyfile) + ",dst=/etc/caddy/Caddyfile,readonly", EDITOR_IMAGE)
        docker("network", "connect", name, name + "-editor")
        docker("start", name + "-editor")
        print("Isolated n8n clone started; waiting for readiness", flush=True)
        ready()
        credential_root = root / "owner"
        if persistence or json_recovery:
            private_directory(credential_root)
            state = json.loads((backup / "config/n8n-owner.json").read_text())
            state["endpoint"] = "http://localhost:25678"  # Only isolated clone origin changes; saved primary access stays intact.
            (credential_root / "owner.json").write_text(json.dumps(state))
        first = provision(credential_root, LocalN8n("http://localhost:25678"))
        assert first["owner_created_now"] is not persistence
        before = (credential_root / "owner.json").read_bytes()
        assert not provision(credential_root, LocalN8n("http://localhost:25678"))["owner_created_now"]
        workflow_checks = []
        daily_checks = []
        error_checks = []
        if json_recovery:
            with sqlite3.connect((backup / 'config/n8n.sqlite').as_uri() + '?mode=ro&immutable=1', uri=True) as database:
                columns = ('id', 'name', 'type', 'data')
                encrypted = [dict(zip(columns, row)) for row in database.execute('SELECT id,name,type,data FROM credentials_entity ORDER BY id')]
            assert {row['id'] for row in encrypted} == {'qldapmMachineStatus', 'qldapmCommandHmac'}
            from n8n_machine import command
            with patch('n8n_machine.CONTAINER', name):
                path = '/tmp/p04-json-encrypted-credentials.json'
                command('node', '-e', "require('fs').writeFileSync(process.argv[1],require('fs').readFileSync(0),{flag:'wx',mode:384})", path,
                        payload=json.dumps(encrypted).encode())
                command('n8n', 'import:credentials', '--input=' + path)
                command('node', '-e', "require('fs').unlinkSync(process.argv[1])", path)
            checkpoint('empty_instance_owner_and_encrypted_credentials_recovered')
            if 'qldapmWorkflowErrors' in exported:
                from n8n_error_workflow import ErrorWorkflowOwner
                from n8n_status_workflow import install, ERROR_WORKFLOW_ID
                with patch('n8n_machine.CONTAINER', name):
                    client = ErrorWorkflowOwner('http://localhost:25678')
                    client.workflow_id = ERROR_WORKFLOW_ID
                    install(credential_root, client)
                    client.publish_error()
        if errors:
            from n8n_error_workflow import enroll as enroll_errors
            with patch('n8n_machine.CONTAINER', name):
                error_checks.append(enroll_errors(credential_root, 'http://localhost:25678'))
            checkpoint('published_error_workflow_and_field_only_bindings_verified')
        if workflow:
            assert persistence or json_recovery
            from n8n_status_workflow import LocalWorkflow, install_and_run
            gateway_data = root / 'gateway'
            gateway_data.mkdir()
            shutil.copyfile(backup / 'config/automation.key', gateway_data / 'automation.key')
            if daily_image:
                config = json.loads((backup / 'config/ai-config.json').read_text())
                config['hosts'] = ['gateway:8090']
                (gateway_data / 'config.json').write_text(json.dumps(config))
                shutil.copyfile(backup / 'config/ai-credentials.json', gateway_data / 'credentials.json')
            else:
                (gateway_data / 'config.json').write_text(json.dumps({'hosts': ['gateway:8090'], 'project_id': 3, 'users': {}, 'openproject_url': 'http://blocked.invalid'}))
            gateway_image = daily_image or 'sha256:58937bdd43a4aa0c23d0a722e71968856c3e171f9b904704d09e062ecd6c2d7b'
            gateway_args = ['run', '-d', '--name', name + '-gateway', '--label', label, '--network', name, '--network-alias', 'gateway',
                   '--read-only', '--user', '10001:10001', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges:true',
                   '--memory', '384m', '--pids-limit', '64', '--tmpfs', '/tmp:size=64m,mode=1777', '--env', 'QLDAPM_AI_RUNTIME=/state',
                   '--mount', 'type=bind,src=' + str(gateway_data) + ',dst=/state']
            if daily_image:
                from daily_core_clone import core_clone
                core_ip = core_stack.enter_context(core_clone(docker, daily_core, name + '-core', label, root))
                gateway_args.extend(['--add-host', 'staging-web:' + core_ip])
                gateway_args.extend(['--mount', 'type=bind,src=' + str(Path(__file__).resolve().parent) + ',dst=/qa,readonly',
                                     '--entrypoint', 'python', gateway_image, '/qa/daily_gateway_readonly.py'])
            else:
                gateway_args.append(gateway_image)
            docker(*gateway_args)
            if daily_image:
                docker('network', 'connect', 'qldapm-ai-stage_stage', name + '-gateway')
            docker('exec', name + '-gateway', 'python', '-c', "import time,urllib.request\nfor i in range(30):\n try:\n  urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8090/health',headers={'Host':'gateway:8090'}),timeout=1);break\n except OSError:time.sleep(1)\nelse:raise RuntimeError('NOT_READY')")
            with patch('n8n_machine.CONTAINER', name):
                workflow_checks.append(install_and_run(credential_root, LocalWorkflow('http://localhost:25678')))
                if daily_image:
                    if json_recovery:
                        from n8n_daily_workflow import LocalDailyWorkflow, enroll
                        daily_checks.append(enroll(credential_root, LocalDailyWorkflow('http://localhost:25678'), publish=True))
                    else:
                        from daily_workflow_probe import exercise
                        daily_checks.append(exercise(credential_root, 'http://localhost:25678'))
            if daily_image and not json_recovery:
                daily_checks.append(json.loads(docker('exec', name + '-gateway', 'python', '/qa/container_daily_scope.py')))
                checkpoint('daily_schedule_and_five_native_roles_passed')
        fixture_secret = secrets.token_urlsafe(32) if persistence else None
        if persistence:
            fixture(name, fixture_secret)
        print("Clone bootstrap and credential reuse passed; restarting only clone", flush=True)
        docker("restart", "--time", "30", name)
        checkpoint('clone_restarted')
        ready()
        assert not provision(credential_root, LocalN8n("http://localhost:25678"))["owner_created_now"]
        assert (credential_root / "owner.json").read_bytes() == before
        assert hashlib.sha256((root / "encryption.key").read_bytes()).digest() == original_key
        if json_recovery:
            credentials, workflows = fixture(name)
            assert {row['id'] for row in workflows} == set(exported)
            assert any(row['id'] == 'qldapmMachineStatus' and row['data'] == {'name': 'X-QLDAPM-Machine-Key', 'value': (backup / 'config/automation.key').read_text()} for row in credentials)
            assert any(row['id'] == 'qldapmCommandHmac' and row['data'] == {'hmacSecret': signing_key((backup / 'config/automation.key').read_text())} for row in credentials)
            with patch('n8n_machine.CONTAINER', name):
                workflow_checks.append(install_and_run(credential_root, LocalWorkflow('http://localhost:25678')))
                daily_checks.append(enroll(credential_root, LocalDailyWorkflow('http://localhost:25678'), publish=True))
            assert workflow_checks[0]['workflow_created_now'] and not workflow_checks[-1]['workflow_created_now']
            assert daily_checks[0]['workflow_created_now'] and not daily_checks[-1]['workflow_created_now']
            assert daily_checks[0]['run_id'] == daily_checks[-1]['run_id']
            checkpoint('json_import_manual_daily_and_restart_key_reuse_passed')
        if persistence:
            credentials, workflows = fixture(name)
            assert any(c["id"] == "p04EncryptedFixture" and c["data"]["value"] == fixture_secret for c in credentials)
            assert any(w["id"] == "p04WorkflowFixture" and w["active"] is False for w in workflows)
            docker("stop", "--time", "30", name)
            snapshot = root / "fixture-backup"
            snapshot.mkdir()
            sqlite_snapshot(data / "database.sqlite", snapshot / "n8n.sqlite")
            with sqlite3.connect((snapshot / "n8n.sqlite").as_uri() + '?mode=ro&immutable=1', uri=True) as database:
                encrypted = database.execute('select data from credentials_entity where id=?', ('p04EncryptedFixture',)).fetchone()[0]
                assert fixture_secret not in encrypted and not encrypted.startswith('{')
            archive(data, snapshot / "n8n-files.tar", ("database.sqlite", "n8nEventLog", "crash.journal"))
            restored = root / "restored-data"
            restored.mkdir()
            with tarfile.open(snapshot / "n8n-files.tar") as stream:
                stream.extractall(restored, filter="data")
            shutil.copyfile(snapshot / "n8n.sqlite", restored / "database.sqlite")
            info = json.loads(docker("inspect", name))[0]
            assert info["Image"] == IMAGE and info["Config"]["Labels"].get("qldapm.acceptance.p04-owner") == name
            docker("rm", name)
            args[args.index("type=bind,src=" + str(data) + ",dst=/home/node/.n8n")] = "type=bind,src=" + str(restored) + ",dst=/home/node/.n8n"
            docker(*args, IMAGE)
            print("Clone restored into fresh private data directory; verifying decryption and owner", flush=True)
            ready()
            checkpoint('fresh_directory_restore_ready')
            assert not provision(credential_root, LocalN8n("http://localhost:25678"))["owner_created_now"]
            credentials, workflows = fixture(name)
            assert any(c["id"] == "p04EncryptedFixture" and c["data"]["value"] == fixture_secret for c in credentials)
            assert any(w["id"] == "p04WorkflowFixture" and w["active"] is False for w in workflows)
            assert (credential_root / "owner.json").read_bytes() == before
            if workflow:
                with patch('n8n_machine.CONTAINER', name):
                    workflow_checks.append(install_and_run(credential_root, LocalWorkflow('http://localhost:25678')))
                    if daily_image:
                        daily_checks.append(exercise(credential_root, 'http://localhost:25678', restart_check=True))
                if daily_image:
                    daily_checks.append(json.loads(docker('exec', name + '-gateway', 'python', '/qa/container_daily_scope.py')))
                    checkpoint('startup_catchup_and_restored_five_native_roles_passed')
            machine_key = backup / 'config/automation.key'
            if machine_key.exists():
                assert any(c['id'] == 'qldapmMachineStatus' and c['type'] == 'httpHeaderAuth'
                           and c['data'] == {'name': 'X-QLDAPM-Machine-Key', 'value': machine_key.read_text()} for c in credentials)
                crypto = next((c for c in credentials if c['id'] == 'qldapmCommandHmac'), None)
                if crypto:
                    assert crypto['type'] == 'crypto' and crypto['data'] == {'hmacSecret': signing_key(machine_key.read_text())}
        if errors:
            from workflow_error_probe import exercise as exercise_errors
            with patch('n8n_machine.CONTAINER', name):
                error_checks.append(exercise_errors(credential_root, 'http://localhost:25678', name, name + '-gateway', backup, docker, ready))
            checkpoint('actual_trigger_error_metadata_dedup_project_ui_verified')
        info = json.loads(docker("inspect", name))[0]
        editor = json.loads(docker("inspect", name + "-editor"))[0]
        assert info["Image"] == IMAGE and not info["HostConfig"]["PortBindings"]
        assert editor["Image"] == EDITOR_IMAGE and editor["HostConfig"]["PortBindings"]["5678/tcp"][0]["HostIp"] == "127.0.0.1"
        assert all("docker.sock" not in mount["Destination"] for mount in info["Mounts"])
        result = {"passed": True, "image": IMAGE, "backup_id": backup.name,
                  "isolated_bootstrap": True, "login_after_restart": True,
                  "credential_and_encryption_key_unchanged": True, "existing_owner_not_replaced": True,
                  "loopback_only": True, "primary_data_mounted": False, "license_activation": False}
        if persistence:
            result.update({"actual_workflow_restart_restore": True, "credential_encrypted_at_rest": True,
                           "credential_decrypted_after_restore": True, "primary_fixture_writes": 0})
            if (backup / 'config/automation.key').exists():
                result['restored_machine_credential_key_pair'] = True
                if any(c['id'] == 'qldapmCommandHmac' for c in credentials):
                    result['restored_purpose_derived_hmac_credential'] = True
        if workflow:
            result['manual_product_workflow_before_after_restore'] = workflow_checks
        if daily_image:
            result['actual_daily_workflow_and_five_native_roles'] = daily_checks
            result.update(candidate_gateway=daily_image, candidate_core=daily_core,
                          candidate_core_database_readonly_verified=True, primary_core_replaced=False)
        if json_recovery:
            result.update(empty_instance_json_recovery=True, exported_product_json_imported=True, workflow_json_count=len(exported),
                          private_encrypted_credentials_and_saved_owner_reused=True)
        if errors:
            result['actual_error_workflow_and_native_ui'] = error_checks
        result['qualification_events'] = events
        output.write_text(json.dumps(result, indent=2))
        print(json.dumps(result), flush=True)
    finally:
        resources = [(name + "-editor", EDITOR_IMAGE), (name, IMAGE)]
        if workflow:
            resources.append((name + '-gateway', daily_image or 'sha256:58937bdd43a4aa0c23d0a722e71968856c3e171f9b904704d09e062ecd6c2d7b'))
        for container, image in resources:
            found = docker("ps", "-aq", "--filter", "name=^/" + container + "$", "--filter", "label=" + label)
            if found:
                info = json.loads(docker("inspect", container))[0]
                assert info["Image"] == image and info["Config"]["Labels"].get("qldapm.acceptance.p04-owner") == name
                docker("stop", "--time", "30", container)
                docker("rm", container)
        for network_name in (name,):
            network = json.loads(docker("network", "inspect", network_name))[0]
            assert network["Labels"].get("qldapm.acceptance.p04-owner") == name and not network["Containers"]
            docker("network", "rm", network_name)
        core_stack.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("backup", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--persistence", action="store_true")
    parser.add_argument('--workflow', action='store_true')
    parser.add_argument('--daily-image')
    parser.add_argument('--daily-core')
    parser.add_argument('--json-recovery', type=Path)
    parser.add_argument('--errors', action='store_true')
    options = parser.parse_args()
    started = time.time()
    try:
        accept(options.backup, options.output, options.persistence, options.workflow, options.daily_image, options.daily_core, options.json_recovery, options.errors)
    except Exception as error:
        if options.output.exists():
            progress = json.loads(options.output.read_text())
            if progress.get('state') == 'RUNNING' and progress['events'][0]['at'] >= started:
                progress.update(passed=False, state='FAILED', error_type=type(error).__name__)
                options.output.write_text(json.dumps(progress, indent=2))
        print(json.dumps({"passed": False, "error_type": type(error).__name__, "message": str(error) if isinstance(error, RuntimeError) else "PRIVATE_DETAILS_REDACTED",
                          "frames": [{"file": Path(frame.filename).name, "line": frame.lineno, "function": frame.name}
                                     for frame in traceback.extract_tb(error.__traceback__)]}))
        raise SystemExit(1)
