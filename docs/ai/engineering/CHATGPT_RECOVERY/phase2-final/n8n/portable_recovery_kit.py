"""Create an AES-256-GCM recovery kit; verify Linux restoration without DPAPI or MAIN mounts."""
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess
import sys
import tarfile
import uuid

import cryptography
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parents[5]
sys.path.insert(0, str(WORKSPACE / 'openproject/ai'))
from free_tier_staging import private_directory

MAGIC = b'QLDAPM-N8N-RECOVERY-V1\n'
IMAGE = 'sha256:39299c2133d148edb9cabfe7e6ef1137a8f1ac179e9f86b0ca2351526abd1795'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def verify_acl(path):
    # Query Windows SIDs, not localized display names; fail before writing secrets if unsupported.
    for part in (path, *path.parents):
        if part.is_symlink() or getattr(part.stat(), 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
            raise PermissionError('RECOVERY_REPARSE_POINT_DENIED')
    script = r'''$ErrorActionPreference='Stop'; $a=Get-Acl -LiteralPath $env:QLDAPM_RECOVERY_ACL_PATH;
$u=[Security.Principal.WindowsIdentity]::GetCurrent().User.Value;
$rules=@($a.Access); $ids=@($rules | ForEach-Object {$_.IdentityReference.Translate([Security.Principal.SecurityIdentifier]).Value} | Sort-Object -Unique);
$bad=@($rules | Where-Object {($_.IdentityReference.Translate([Security.Principal.SecurityIdentifier]).Value -notin @($u,'S-1-5-18')) -or $_.AccessControlType -ne 'Allow' -or (($_.FileSystemRights -band [Security.AccessControl.FileSystemRights]::FullControl) -ne [Security.AccessControl.FileSystemRights]::FullControl)});
if($ids.Count -ne 2 -or $bad.Count -ne 0){throw 'RECOVERY_ACL_DENIED'};
@{restricted_to_current_user_and_system=$true; principal_count=$ids.Count; inheritance_protected=$a.AreAccessRulesProtected} | ConvertTo-Json -Compress'''
    result = subprocess.run(['pwsh', '-NoProfile', '-Command', script],
                            env=dict(os.environ, QLDAPM_RECOVERY_ACL_PATH=str(path)), capture_output=True, text=True, timeout=30)
    if result.returncode:
        raise PermissionError('RECOVERY_ACL_VERIFICATION_FAILED')
    return json.loads(result.stdout)


def private_new_directory(path):
    path.mkdir(exist_ok=False)
    private_directory(path)
    acl = verify_acl(path)
    assert acl['inheritance_protected'], 'RECOVERY_DIRECTORY_INHERITANCE_NOT_PROTECTED'
    return acl


def create():
    sys.path.insert(0, str(HERE.parents[1] / 'stabilization-n8n'))
    from inspect_backup import private, unprotect
    reference = json.loads((HERE / 'clone-key-diagnostic-result.json').read_text(encoding='utf8'))
    inventory = json.loads((HERE / 'private-inventory.json').read_text(encoding='utf8'))
    snapshot = private / 'n8n-cold-volume.tar.dpapi'
    env_snapshot = private / 'preserved.env.dpapi'
    assert sha(snapshot.read_bytes()) == reference['backup_archive_sha256'], 'ARCHIVE_PROVENANCE_CHANGED'
    assert sha(env_snapshot.read_bytes()) == reference['backup_environment_sha256'], 'ENVIRONMENT_PROVENANCE_CHANGED'
    archive = unprotect(snapshot)
    original_env = unprotect(env_snapshot)
    originals = {entry['name']: entry['sha256'] for entry in inventory['entries']}
    assert sha(archive) == originals['n8n-cold-volume.tar'], 'ORIGINAL_ARCHIVE_BYTES_CHANGED'
    assert sha(original_env) == originals['preserved.env'], 'ORIGINAL_ENVIRONMENT_BYTES_CHANGED'
    with tarfile.open(fileobj=io.BytesIO(archive), mode='r:*') as tar:
        names = [member.name.removeprefix('./') for member in tar]
        assert all(not PurePosixPath(name).is_absolute() and '..' not in PurePosixPath(name).parts for name in names)
        assert all(member.isfile() or member.isdir() for member in tar.getmembers())
        assert {'database.sqlite', 'database.sqlite-wal', 'database.sqlite-shm', 'config'} <= set(names)
    kit = private.parent / ('portable-n8n-recovery-' + uuid.uuid4().hex[:12])
    assert WORKSPACE not in kit.parents, 'RECOVERY_KIT_MUST_BE_OUTSIDE_REPOSITORY'
    acls = {'kit': private_new_directory(kit), 'ciphertext': private_new_directory(kit / 'ciphertext'),
            'recovery_custody': private_new_directory(kit / 'recovery-custody')}
    manifest = {'archive_plaintext_sha256': sha(archive), 'environment_plaintext_sha256': sha(original_env),
                'source_archive_dpapi_sha256': sha(snapshot.read_bytes()),
                'source_environment_dpapi_sha256': sha(env_snapshot.read_bytes()),
                'origin': 'existing cold snapshot from 2026-11-01; old key only; not a new MAIN snapshot'}
    payload = json.dumps({'schema': 'qldapm.n8n.recovery-payload.v1', 'manifest': manifest,
                          'archive_base64': base64.b64encode(archive).decode('ascii'),
                          'environment_base64': base64.b64encode(original_env).decode('ascii')}, separators=(',', ':')).encode()
    recovery_key = AESGCM.generate_key(bit_length=256)
    nonce = os.urandom(12)
    encrypted = MAGIC + nonce + AESGCM(recovery_key).encrypt(nonce, payload, MAGIC)
    key_path = kit / 'recovery-custody/recovery.key'
    ciphertext_path = kit / 'ciphertext/n8n-recovery-v1.aesgcm'
    # Parent DACL is verified before creation; exclusive create prevents overwriting anything.
    with key_path.open('xb') as file:
        file.write(recovery_key)
    acls['recovery_key_file'] = verify_acl(key_path)
    with ciphertext_path.open('xb') as file:
        file.write(encrypted)
    acls['ciphertext_file'] = verify_acl(ciphertext_path)
    with (kit / 'ciphertext/portable_recovery_restore.js').open('xb') as file:
        file.write((HERE / 'portable_recovery_restore.js').read_bytes())
    with (kit / 'ciphertext/FORMAT.json').open('x', encoding='utf8') as file:
        json.dump({'schema': 'QLDAPM-N8N-RECOVERY-V1', 'image': IMAGE,
                   'restore_script_sha256': sha((HERE / 'portable_recovery_restore.js').read_bytes()),
                   'key_bytes': 32, 'nonce_bytes': 12, 'tag_bytes': 16,
                   'aad_ascii': MAGIC.decode('ascii'), 'original_manifest': manifest}, file, indent=2)
    # No decrypted content is materialized outside process memory or the disposable Linux tmpfs.
    assert AESGCM(recovery_key).decrypt(nonce, encrypted[len(MAGIC) + 12:], MAGIC) == payload
    corrupted = bytearray(encrypted[len(MAGIC) + 12:])
    corrupted[len(corrupted) // 2] ^= 1
    try:
        AESGCM(recovery_key).decrypt(nonce, bytes(corrupted), MAGIC)
    except InvalidTag:
        pass
    else:
        raise AssertionError('HOST_TAMPER_REJECTION_FAILED')
    return kit, {'source_manifest': manifest, 'acls_at_creation': acls, 'host_exact_roundtrip': True,
                 'host_tamper_rejected': True}


def verify(kit):
    assert kit.parent.resolve(strict=True) == (Path(os.environ['LOCALAPPDATA']) / 'QLDAPM/openproject-ai/operator').resolve(strict=True)
    assert kit.name.startswith('portable-n8n-recovery-'), 'RECOVERY_PATH_SCOPE_DENIED'
    verify_acl(kit)
    kit = kit.resolve(strict=True)
    acls = {part: verify_acl(kit / part) for part in ('ciphertext', 'recovery-custody',
            'ciphertext/n8n-recovery-v1.aesgcm', 'recovery-custody/recovery.key',
            'ciphertext/portable_recovery_restore.js', 'ciphertext/FORMAT.json')}
    packaged_script_hash = sha((kit / 'ciphertext/portable_recovery_restore.js').read_bytes())
    assert packaged_script_hash == sha((HERE / 'portable_recovery_restore.js').read_bytes()), 'PACKAGED_VERIFIER_SOURCE_CHANGED'
    assert json.loads((kit / 'ciphertext/FORMAT.json').read_text(encoding='utf8'))['restore_script_sha256'] == packaged_script_hash
    key = (kit / 'recovery-custody/recovery.key').read_bytes()
    assert len(key) == 32, 'RECOVERY_KEY_LENGTH_INVALID'
    container = 'qldapm-portable-recovery-' + uuid.uuid4().hex[:12]
    command = ['docker', 'run', '--rm', '-i', '--pull', 'never', '--name', container,
               '--network', 'none', '--read-only', '--tmpfs', '/tmp:rw,uid=1000,gid=1000,mode=0700,size=512m',
               '--mount', f'type=bind,source={kit / "ciphertext"},target=/kit,readonly',
               '--entrypoint', 'node', IMAGE,
               '/kit/portable_recovery_restore.js', '/kit/n8n-recovery-v1.aesgcm']
    try:
        result = subprocess.run(command, input=key, capture_output=True, timeout=240)
        if result.returncode:
            raise RuntimeError('PORTABLE_LINUX_RESTORE_FAILED')
        verified = json.loads(result.stdout)
        assert verified['status'] == 'PORTABLE_LINUX_RESTORE_VERIFIED_OLD_KEY_ONLY'
    finally:
        # Only the random disposable clone is targeted, even after a timeout.
        subprocess.run(['docker', 'rm', '-f', container], capture_output=True, timeout=30)
    return {'acls_at_verify': acls, 'docker_command': command, 'clone_result': verified,
            'packaged_restore_script_sha256': packaged_script_hash,
            'ciphertext_sha256': sha((kit / 'ciphertext/n8n-recovery-v1.aesgcm').read_bytes()),
            'ciphertext_bytes': (kit / 'ciphertext/n8n-recovery-v1.aesgcm').stat().st_size}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', type=Path, help='Verify an existing kit without reading DPAPI source')
    args = parser.parse_args()
    if os.name != 'nt':
        raise PermissionError('WINDOWS_PRIVATE_ACL_SUPPORT_REQUIRED')
    report = {'started_at': datetime.now(timezone.utc).isoformat(), 'source_commit': subprocess.check_output(
        ['git', 'rev-parse', 'HEAD'], text=True).strip(), 'image': IMAGE, 'cryptography_version': cryptography.__version__,
        'schema': 'magic ASCII + nonce12 + AES256GCM(ciphertext || tag16), AAD=magic; JSON payload v1',
        'code_sha256': {path.name: sha(path.read_bytes()) for path in (Path(__file__), HERE / 'portable_recovery_restore.js')}}
    if args.verify:
        kit, created = args.verify, {}
    else:
        kit, created = create()
    report.update(created)
    report.update(verify(kit))
    report.update({'completed_at': datetime.now(timezone.utc).isoformat(), 'kit_directory': str(kit),
                   'status': 'PORTABLE_KIT_LINUX_CLONE_VERIFIED_OLD_KEY_ONLY',
                   'physical_machine_dr': 'NOT_TESTED', 'off_host_copy': 'NOT_CREATED',
                   'owner_recovery_key_custody': 'PENDING_OWNER_SEPARATE_SECURE_CUSTODY',
                   'master_key_cutover': 'BLOCKED_UNCHANGED', 'main_mutation': False})
    output = HERE / ('portable-recovery-verification-result.json' if args.verify else 'portable-recovery-creation-result.json')
    if output.exists():
        output = output.with_name(output.stem + '-' + uuid.uuid4().hex[:12] + output.suffix)
    with output.open('x', encoding='utf8') as file:
        file.write(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
