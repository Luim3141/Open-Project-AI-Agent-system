"""Fixed local configuration runner; never an AI approval or arbitrary Rails endpoint."""
import json
import re
import sys
from pathlib import Path

from jira_sync_backup import SPECS, command, inspect, digest, verify_archive


def configuration(target, approved_hash=None):
    if approved_hash is not None and not getattr(target, 'rehearsal', False):
        if not sys.stdin.isatty() or getattr(target, 'confirmed_config_hash', None) != approved_hash:
            raise PermissionError('LOCAL_INTERACTIVE_OPERATOR_REQUIRED_NO_AI_APPROVAL')
    root = Path(__file__).resolve().parent
    source = (root / 'core/jira_sync_configuration.rb').read_text(encoding='utf-8')
    if approved_hash is not None and not re.fullmatch(r'[a-f0-9]{64}', approved_hash):
        raise ValueError('CONFIGURATION_APPROVAL_HASH_REQUIRED')
    invocation = (f'JiraSyncConfiguration.preview({target.project})' if approved_hash is None else
                  f'Project.transaction {{ JiraSyncConfiguration.apply_in_transaction!({target.project}, "{approved_hash}") }}')
    packet = (source + '\nputs JSON.generate(' + invocation + ')\n').encode()
    if getattr(target, 'rehearsal', False):
        output = target.fixed_runner(packet)
    else:
        spec = SPECS[target.name]
        info = inspect(spec['web'])
        if info['Config']['Labels'].get('com.docker.compose.project') != spec['label']:
            raise ValueError('CONFIGURATION_TARGET_MISMATCH')
        output = command(['docker', 'exec', '-i', spec['web'], 'bundle', 'exec', 'rails', 'runner', '-'], packet)
    value = json.loads(output.decode().splitlines()[-1])
    if value['before']['project_id'] != target.project:
        raise ValueError('CONFIGURATION_PROJECT_MISMATCH')
    return value


def script_hashes():
    root = Path(__file__).resolve().parent
    names = ['jira_sync.py', 'jira_sync_apply.py', 'jira_sync_records.py', 'jira_sync_target.py',
             'jira_sync_operator.py', 'jira_sync_backup.py', 'jira_sync_cli.py', 'jira_sync_rehearsal.py',
             'core/jira_sync_configuration.rb', 'core/jira_sync_configuration_test.rb',
             'core/overlay/app/services/qldapm/insights.rb']
    return {name: digest(root / name) for name in names}


def backup_proof(directory, target):
    directory = Path(directory).resolve()
    metadata = json.loads((directory / 'backup.json').read_text())
    verify_archive(directory, metadata['manifest'])
    if metadata['target'] != target.name or metadata['project_id'] != target.project:
        raise ValueError('BACKUP_TARGET_MISMATCH')
    receipts = [json.loads(path.read_text()) for path in directory.glob('restore-*/result.json')]
    image = inspect(SPECS[target.name]['web'])['Image']
    scripts = script_hashes()
    matching = [row for row in receipts if row.get('passed') and row.get('database_assets_config') and
                row.get('configuration_transaction') and row.get('backup_hash') == digest(directory / 'backup.json') and
                row.get('tested_core_image') == image and (row.get('import_exercise') or {}).get('passed') and
                row['import_exercise'].get('sample_only') is False and row['import_exercise'].get('rows') == 329 and
                row['import_exercise'].get('scripts') == scripts]
    if not matching:
        raise ValueError('RESTORE_REHEARSAL_PROOF_REQUIRED')
    return {'directory': str(directory), 'backup_hash': digest(directory / 'backup.json'),
            'proof': max(matching, key=lambda row: row['at']), 'restored_config_files': len([key for key in metadata['manifest'] if key.startswith('config/')])}
